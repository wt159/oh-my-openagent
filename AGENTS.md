# AGENTS.md — Oh-My-OpenCode Model Policy

> 目标：当可用模型变化时，快速、可判定地更新 `oh-my-openagent.json`。

---

## 0. 执行顺序

1. 先运行 `python3 test_all_models.py`，刷新本目录的 `test_results.json`。
2. 再运行 `opencode models`。
3. 再读取本目录最新生成的 `test_results.json`。
4. 先用 `opencode models` 确认可见模型，再用最新 `test_results.json` 过滤出实际可用模型。
5. 先改本目录的 `oh-my-openagent.json`。
6. 再覆盖 `~/.config/opencode/oh-my-openagent.json`。
7. 只做必要替换，不重排无关项。

---

## 1. 模型分层

| Tier | 格式 | 用途 |
|---|---|---|
| T1 | `openai/<model>` (GPT / Claude / Gemini / Kimi 等) | Premium 能力池 — 按角色需求选最适合的模型 |
| T2 | `zhipuai-coding-plan/<model>` | 核心执行位 |
| T3 | `opencode/<model>-free` | 高频低价值位 |

### 1.1 当前参考

> 以 `opencode models` 和 `test_results.json` 的交集为准。
>
> `opencode models` 只表示“可见 / 可枚举”；`test_results.json` 中 `connected=true` 才表示“当前环境可用”。

**T1 — OpenAI**
- `openai/gpt-5.4`
- `openai/gpt-5.2`
- `openai/gpt-5.4-mini`

**T2 — ZhiPu Coding Plan**
- `zhipuai-coding-plan/glm-5.1`
- `zhipuai-coding-plan/glm-5`
- `zhipuai-coding-plan/glm-4.7`
- `zhipuai-coding-plan/glm-4.6`
- `zhipuai-coding-plan/glm-4.5`

**T3 — OpenCode Free**
- `opencode/nemotron-3-super-free`
- `opencode/minimax-m2.5-free`
- `opencode/big-pickle`

---

## 2. 固定规则

1. **选模型时必须同时参考 `opencode models` 和 `test_results.json`。**
2. **只有 `test_results.json` 中 `connected=true` 的模型，才允许进入候选集。**
3. **所有模型统一按能力竞争分配。**
4. **Token 预算敏感位（ultrabrain、deep）优先选 token 充裕的模型。**
5. **优先级：** T1 > T2 > T3。
6. **替换原则：** 同 Tier 优先；跨 Tier 仅在明确需要时调整。
7. **当前参考 / 固定位置 / 当前配置，都不得保留已在 `test_results.json` 中判定不可用的模型示例。**
8. **每次更新模型配置前，都必须先重跑模型测试并刷新 `test_results.json`，不得基于旧测试结果做决策。**

### 2.1 可用性门禁（AI MUST FOLLOW）

在任何模型选择动作之前，先执行以下判定：

```text
Step A. 读取 `opencode models`
Step B. 读取 `test_results.json`
Step C. 候选集 = 同时满足以下条件的模型：
  - 出现在 `opencode models`
  - `test_results.json.models[].connected == true`
Step D. 从候选集中按 Tier 和角色需求选择
Step E. 若同 Tier 无可用模型，才允许跨 Tier 回退，并记录原因
```

**MUST**
- 先运行 `python3 test_all_models.py`，刷新 `test_results.json`。
- 先检查 `test_results.json`，再决定模型。
- 只选择 `connected=true` 的模型。
- 同 Tier 有可用模型时，优先同 Tier 替换。

**MUST NOT**
- 不得因为模型出现在 `opencode models` 中就直接选用。
- 不得选择 `connected=false` 的模型。
- 不得选择 `status != 200` 或 `error` 非空的模型。
- 不得继续保留 `401 / 403 / 429 / 500 / timeout / not supported / Missing API key / auth_unavailable` 这类失败模型作为“当前参考”或默认示例。

### 2.2 T1 固定位置

| 位置 | 模型 | Variant | 选择理由 |
|---|---|---|---|
| `oracle` | `openai/gpt-5.4` | `high` | 当前测试中可用的 T1 高能力模型，适合作为只读咨询位 |
| `ultrabrain` | `openai/gpt-5.4` | `xhigh` | 超高难度逻辑需要大量 token |
| `multimodal-looker` | `openai/gpt-5.4` | `medium` | 当前测试集中无可用专用视觉 T1 模型，临时回退到可用通用 T1 |
| `deep` | `openai/gpt-5.4` | `medium` | 自主长链执行需要长上下文 |

---

## 3. 非 OpenAI 模型选择依据

### 3.1 评估维度

| 维度 | 优先看什么 | 适用位置 |
|---|---|---|
| 推理 | 复杂问题、长链路分析、冲突约束处理 | 关键决策位 |
| 代码 | 生成代码、改代码、理解项目结构 | 执行位 |
| 工具 | agent / function call / 多步执行稳定性 | 执行位 |
| 上下文 | 长上下文、跨文件关联、记忆保持 | 编排/审查位 |
| 速度/成本 | 高并发、简单任务、低价值任务 | 高频低价值位 |
| 视觉 | 截图、UI、图片理解 | 视觉位 |

### 3.2 分配规则

1. 关键决策位 → 先看推理 + 稳定性。
2. 执行位 → 先看代码 + 工具调用。
3. 编排/审查位 → 先看上下文。
4. 高频低价值位 → 先看速度 + 成本。
5. 视觉位 → 先看多模态能力。

---

## 4. 当前配置

### 4.1 Agents

| Agent | 模型 | Variant |
|---|---|---|
| `sisyphus` | `zhipuai-coding-plan/glm-5.1` | `max` |
| `hephaestus` | `zhipuai-coding-plan/glm-5` | `medium` |
| `oracle` | `openai/gpt-5.4` | `high` |
| `explore` | `opencode/big-pickle` | — |
| `multimodal-looker` | `openai/gpt-5.4` | `medium` |
| `prometheus` | `zhipuai-coding-plan/glm-5.1` | `max` |
| `metis` | `zhipuai-coding-plan/glm-5.1` | `max` |
| `momus` | `zhipuai-coding-plan/glm-5.1` | `xhigh` |
| `atlas` | `opencode/minimax-m2.5-free` | — |
| `sisyphus-junior` | `opencode/nemotron-3-super-free` | — |

### 4.2 Categories

| Category | 模型 | Variant |
|---|---|---|
| `visual-engineering` | `zhipuai-coding-plan/glm-5` | `high` |
| `ultrabrain` | `openai/gpt-5.4` | `xhigh` |
| `deep` | `openai/gpt-5.4` | `medium` |
| `artistry` | `zhipuai-coding-plan/glm-5` | `high` |
| `quick` | `opencode/nemotron-3-super-free` | — |
| `unspecified-low` | `opencode/big-pickle` | — |
| `unspecified-high` | `zhipuai-coding-plan/glm-5` | — |
| `writing` | `zhipuai-coding-plan/glm-5` | — |

---

## 5. 变更流程

### 5.0 选择前检查（必须）

1. 先跑 `python3 test_all_models.py`，刷新 `test_results.json`。
2. 再跑 `opencode models`。
3. 再读取最新的 `test_results.json`。
4. 建立候选集：仅保留同时满足“出现在 `opencode models`”且“`connected=true`”的模型。
5. 任何不在候选集中的模型，不得进入“当前参考”、固定位置或 `oh-my-openagent.json`。

### 5.1 新模型可用

1. 先跑 `python3 test_all_models.py`，生成最新测试结果。
2. 再跑 `opencode models`。
3. 读取最新的 `test_results.json`，过滤出 `connected=true` 的模型。
4. 判断 provider / tier。
5. 只在同 Tier 内优先替换。
6. 更新本文件“当前参考”。

### 5.2 模型失效

1. 在 `test_results.json` 中确认失效的是哪个 provider / model。
2. 失效判定：`connected=false`，或 `status != 200`，或 `error` 非空。
3. 从同 Tier 且 `connected=true` 的模型中选替代。
4. 批量更新 `oh-my-openagent.json`。

### 5.3 想省钱

1. 先保留 T1 固定位置。
2. 优先压缩 T2 → T3 的非关键位。
3. 不改 `oracle` / `ultrabrain`。

### 5.4 账号/环境变化

1. 先看 `opencode models` 的实际输出。
2. 再看 `test_results.json` 的实际连通结果。
3. 新 provider：只有在 `connected=true` 时才补到“当前参考”。
4. 旧 provider 消失，或该 provider 在 `test_results.json` 中全部失效：删掉所有引用。
5. 模型改名但能力接近，且测试通过：保持原 Tier。

---

## 6. 文件规则

### 6.1 工作副本

1. 编辑源：本目录 `oh-my-openagent.json`。
2. 落盘目标：`~/.config/opencode/oh-my-openagent.json`。
3. 顺序：先看工作区 diff，再同步到真实环境。

### 6.2 查看命令

```bash
python3 test_all_models.py

opencode models

python3 - <<'PY'
import json
data=json.load(open('test_results.json'))
for m in data['models']:
    if m.get('connected'):
        print(m['model_id'])
PY

python3 - <<'PY'
import json, subprocess

visible = {
    line.strip()
    for line in subprocess.check_output(['opencode', 'models'], text=True).splitlines()
    if '/' in line
}

data = json.load(open('test_results.json'))
connected = {
    m['model_id']
    for m in data['models']
    if m.get('connected') and m.get('status') == 200 and not m.get('error')
}

for model_id in sorted(visible & connected):
    print(model_id)
PY
```

> 每次更新模型配置前，都应先执行 `python3 test_all_models.py`，确保 `test_results.json` 是最新结果。
>
> 只有同时出现在以上两份结果中的模型，才允许被选择。
>
> 最后一个命令块会一键输出“最终候选集”：也就是同时满足“`opencode models` 可见”且“`test_results.json` 中 `connected=true`、`status == 200`、`error` 为空”的模型。

### 6.3 离线备选

```bash
python3 - <<'PY'
import json
data=json.load(open('$HOME/.cache/opencode/models.json'))
cfg=json.load(open('$HOME/.config/opencode/oh-my-openagent.json'))
used={v['model'].split('/')[0] for s in ('agents','categories') for v in cfg.get(s,{}).values() if '/' in v.get('model','')}
for pid in sorted(used):
    ms=data.get(pid,{}).get('models',{})
    if ms: print(f'\n=== {pid} ({len(ms)}) ==='); [print(f'  {pid}/{k} — {v.get("name","?")}') for k,v in sorted(ms.items())]
print('\n=== free ===')
for pid,prov in sorted(data.items()):
    free=[(k,v) for k,v in prov.get('models',{}).items() if 'free' in k.lower()]
    if free: print(f'\n=== {pid} ({len(free)}) ==='); [print(f'  {pid}/{k} — {v.get("name","?")}') for k,v in sorted(free)]
PY
```
