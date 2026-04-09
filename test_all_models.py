#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

MAX_CONCURRENCY = 5
REQUEST_TIMEOUT = 30
PAUSE_BETWEEN_ROUNDS = 2
TEST_PROMPT = "hi"
MAX_TOKENS = 5

MODELS_CACHE = Path(os.path.expanduser("~/.cache/opencode/models.json"))
AUTH_CONFIG = Path(os.path.expanduser("~/.local/share/opencode/auth.json"))
OPENCODE_CONFIG = Path(os.path.expanduser("~/.config/opencode/opencode.json"))


@dataclass
class ModelResult:
    model_id: str
    provider: str = ""
    endpoint: str = ""
    api_key: str = ""
    connected: bool = False
    status: int = 0
    latency: float = 0.0
    error: str = ""
    max_safe_concurrency: int = 0
    concurrency_details: list = field(default_factory=list)


def load_testable_models():
    try:
        output = subprocess.check_output(["opencode", "models"], text=True)
    except FileNotFoundError:
        print("ERROR: 'opencode' command not found. Please ensure opencode is installed and in PATH.", file=sys.stderr)
        sys.exit(1)
    
    visible_models = set()
    for line in output.splitlines():
        line = line.strip()
        if line and '/' in line:
            visible_models.add(line)
    
    if not visible_models:
        print("ERROR: No models found from 'opencode models' command", file=sys.stderr)
        sys.exit(1)

    if not MODELS_CACHE.exists():
        print(f"ERROR: Models cache not found: {MODELS_CACHE}", file=sys.stderr)
        sys.exit(1)

    with open(MODELS_CACHE) as f:
        data = json.load(f)

    api_keys = {}
    if AUTH_CONFIG.exists():
        with open(AUTH_CONFIG) as f:
            auth = json.load(f)
        for provider, cred in auth.items():
            if cred.get("key"):
                api_keys[provider] = cred["key"]

    provider_overrides = {}
    if OPENCODE_CONFIG.exists():
        with open(OPENCODE_CONFIG) as f:
            occ = json.load(f)
        for provider, cfg in occ.get("provider", {}).items():
            opts = cfg.get("options", {})
            override = {}
            if opts.get("baseURL"):
                override["endpoint"] = opts["baseURL"]
            if opts.get("apiKey"):
                override["api_key"] = opts["apiKey"]
            if cfg.get("models"):
                override["models"] = list(cfg["models"].keys())
            if override:
                provider_overrides[provider] = override

    testable = []
    missing_auth = set()
    
    for full_model_id in visible_models:
        if '/' not in full_model_id:
            continue
        provider, model_id = full_model_id.split('/', 1)
        
        if provider not in data:
            continue
            
        prov = data[provider]
        override = provider_overrides.get(provider, {})

        if "models" in override:
            if model_id not in override["models"]:
                continue
            model_ids = [model_id]
        else:
            if model_id not in prov.get("models", {}):
                continue
            model_ids = [model_id]

        if not model_ids:
            continue

        api_endpoint = (
            override.get("endpoint")
            or prov.get("api", "")
        )
        if not api_endpoint:
            print(f"  WARN: {provider} has no API endpoint, skipping", file=sys.stderr)
            continue

        key = override.get("api_key") or api_keys.get(provider, "")
        if not key:
            for env_var in prov.get("env", []):
                val = os.environ.get(env_var, "")
                if val:
                    key = val
                    break

        if not key:
            missing_auth.add(provider)

        for model_id in model_ids:
            full_id = f"{provider}/{model_id}"
            testable.append({
                "model_id": full_id,
                "provider": provider,
                "endpoint": api_endpoint,
                "api_key": key,
            })

    for p in sorted(missing_auth):
        print(f"  WARN: {p} has no API key (checked opencode.json, auth.json, env vars); models will likely fail auth")

    testable.sort(key=lambda x: x["model_id"])
    return testable, api_keys


def resolve_endpoint(model_info):
    return model_info.get("endpoint", "")


def strip_model_prefix(full_model_id):
    if "/" in full_model_id:
        return full_model_id.split("/", 1)[1]
    return full_model_id


def single_request(endpoint, api_key, api_model):
    url = f"{endpoint}/chat/completions"
    payload = json.dumps({
        "model": api_model,
        "messages": [{"role": "user", "content": TEST_PROMPT}],
        "max_tokens": MAX_TOKENS,
    }).encode("utf-8")

    req = Request(url, data=payload, method="POST")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "curl/8.5.0")
    req.add_header("Accept", "*/*")

    start = time.monotonic()
    try:
        resp = urlopen(req, timeout=REQUEST_TIMEOUT)
        latency = time.monotonic() - start
        if resp.status == 200:
            return {"success": True, "status": resp.status, "latency": latency, "error": ""}
        body = resp.read().decode("utf-8", errors="replace")
        return {"success": False, "status": resp.status, "latency": latency, "error": body[:120]}
    except HTTPError as e:
        latency = time.monotonic() - start
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
            j = json.loads(body)
            if "error" in j:
                err_obj = j["error"]
                if isinstance(err_obj, dict):
                    body = err_obj.get("message", str(err_obj)[:120])
                else:
                    body = str(err_obj)[:120]
            else:
                body = body[:120]
        except (json.JSONDecodeError, AttributeError, KeyError):
            body = (body or str(e))[:120]
        return {"success": False, "status": e.code, "latency": latency, "error": body}
    except Exception as e:
        latency = time.monotonic() - start
        return {"success": False, "status": 0, "latency": latency, "error": str(e)[:120]}


def test_connectivity(models):
    print("\n" + "=" * 60)
    print("Phase 1: Connectivity Test")
    print("=" * 60)

    results = []
    for m in models:
        endpoint = resolve_endpoint(m)
        api_model = strip_model_prefix(m["model_id"])

        r = single_request(endpoint, m["api_key"], api_model)

        mr = ModelResult(
            model_id=m["model_id"],
            provider=m["provider"],
            endpoint=m["endpoint"],
            api_key=m["api_key"],
            connected=r["success"],
            status=r["status"],
            latency=r["latency"],
            error=r["error"],
        )

        if r["success"]:
            print(f"  \u2705 {mr.model_id:<45} {r['status']} ({r['latency']:.1f}s)")
        else:
            print(f"  \u274c {mr.model_id:<45} {r['status']} \u2014 {r['error'][:60]}")

        results.append(mr)

    return results


def test_concurrency_model(endpoint, api_key, api_model, concurrency):
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [
            pool.submit(single_request, endpoint, api_key, api_model)
            for _ in range(concurrency)
        ]
        responses = [f.result() for f in as_completed(futures)]

    ok = sum(1 for r in responses if r["success"])
    rate_limited = sum(1 for r in responses if r["status"] == 429)
    avg_latency = sum(r["latency"] for r in responses) / len(responses) if responses else 0
    return ok, rate_limited, avg_latency


def test_concurrency(results):
    print("\n" + "=" * 60)
    print("Phase 2: Concurrency Test")
    print("=" * 60)

    for mr in results:
        if not mr.connected:
            print(f"\n  {mr.model_id}: SKIPPED (not connected)")
            continue

        api_model = strip_model_prefix(mr.model_id)
        print(f"\n  {mr.model_id}:")

        for c in range(1, MAX_CONCURRENCY + 1):
            ok, limited, avg = test_concurrency_model(mr.endpoint, mr.api_key, api_model, c)
            total = c
            detail = f"concurrency={c}: {ok}/{total} ok"
            if limited > 0:
                detail += f" \u26a0\ufe0f {limited}x 429"
            else:
                detail += " \u2705"
            detail += f" ({avg:.1f}s avg)"
            print(f"    {detail}")
            mr.concurrency_details.append(detail)

            if limited > 0:
                mr.max_safe_concurrency = c - 1
                break
            else:
                mr.max_safe_concurrency = c

            time.sleep(PAUSE_BETWEEN_ROUNDS)

        print(f"    \u2192 MAX_SAFE_CONCURRENCY = {mr.max_safe_concurrency}")

    return results


def print_summary(results):
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    print(f"  {'Model':<45} {'Connect':<10} {'MaxConc':<10}")
    print(f"  {'-' * 43}   {'-' * 8}   {'-' * 8}")

    for r in results:
        conn = "\u2705" if r.connected else "\u274c"
        conc = str(r.max_safe_concurrency) if r.connected else "\u2014"
        print(f"  {r.model_id:<45} {conn:<10} {conc:<10}")

    print()
    risky = [r for r in results if r.connected and r.max_safe_concurrency < 3]
    if risky:
        print("\u26a0\ufe0f  Models with concurrency < 3 (risk of rate-limiting):")
        for r in risky:
            print(f"    {r.model_id}: max {r.max_safe_concurrency} concurrent")
        print()


def save_json(results, output_file="test_results.json"):
    connected = sum(1 for r in results if r.connected)
    failed = [r for r in results if not r.connected]

    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_models": len(results),
        "connected": connected,
        "failed": len(failed),
        "models": [
            {
                "model_id": r.model_id,
                "provider": r.provider,
                "endpoint": r.endpoint,
                "connected": r.connected,
                "status": r.status,
                "latency": round(r.latency, 2),
                "max_safe_concurrency": r.max_safe_concurrency,
                "error": r.error,
            }
            for r in results
        ],
        "failed_models": [
            {"model_id": r.model_id, "error": r.error}
            for r in failed
        ],
    }

    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {output_file}")


def main():
    models, api_keys = load_testable_models()
    print(f"Loaded {len(models)} testable models")

    results = test_connectivity(models)

    connected = sum(1 for r in results if r.connected)
    print(f"\nConnectivity: {connected}/{len(results)} models OK")

    if connected == 0:
        print("No models connected. Exiting.")
        sys.exit(1)

    results = test_concurrency(results)
    print_summary(results)
    save_json(results)


if __name__ == "__main__":
    main()