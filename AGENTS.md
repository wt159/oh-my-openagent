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

## 1. 模型选择原则

> **核心变更：模型不再硬性分层（T1/T2/T3），而是按实际能力竞争分配。**
>
> Provider（openai / zhipuai-coding-plan / opencode 等）仅作为标识，不决定优先级。
> 每个模型根据其在推理、代码、工具调用、上下文、速度/成本、视觉等维度的实际表现，
> 与角色的能力需求匹配后决定分配。

### 1.1 当前候选模型

> 以 `opencode models` 和 `test_results.json` 的交集为准。
>
> `opencode models` 只表示"可见 / 可枚举"；`test_results.json` 中 `connected=true` 才表示"当前环境可用"。

**OpenAI**
- `openai/gpt-5.4`
- `openai/gpt-5.4-mini`
- `openai/gpt-5.2`
- `openai/gpt-5.2-codex`
- `openai/gpt-5.3-codex`

**ZhiPu Coding Plan**
- `zhipuai-coding-plan/glm-5.1`
- `zhipuai-coding-plan/glm-5`
- `zhipuai-coding-plan/glm-5-turbo`
- `zhipuai-coding-plan/glm-4.7`
- `zhipuai-coding-plan/glm-4.6`
- `zhipuai-coding-plan/glm-4.6v`
- `zhipuai-coding-plan/glm-4.5`
- `zhipuai-coding-plan/glm-4.5-air`
- `zhipuai-coding-plan/glm-4.5-flash`
- `zhipuai-coding-plan/glm-4.5v`

**OpenCode Free**
- `opencode/nemotron-3-super-free`
- `opencode/minimax-m2.5-free`
- `opencode/big-pickle`

### 1.2 能力评估依据

选择模型时参考以下权威来源（按可信度排序）：

1. **实际测试结果**：`test_results.json` 中的连通性、延迟、并发数据。
2. **公开基准测试**：官方 benchmark（如 MMLU、HumanEval、Arena Elo 等）。
3. **社区评测**：LMSys Chatbot Arena、独立评测报告。
4. **实际使用体感**：在当前项目中的代码生成质量、工具调用稳定性等主观经验。

> **注意**：Provider 品牌不等于能力。一个 `opencode/*-free` 模型如果在推理维度表现优异，
> 完全可以分配到 `oracle` 等关键位置；反之，`openai/*` 模型如果在特定任务上表现不佳，
> 也不应仅因品牌而占据关键位置。

---

## 2. 固定规则

1. **选模型时必须同时参考 `opencode models` 和 `test_results.json`。**
2. **只有 `test_results.json` 中 `connected=true` 的模型，才允许进入候选集。**
3. **所有模型统一按能力竞争分配，不按 Provider 或品牌预设优先级。**
4. **Token 预算敏感位（ultrabrain、deep）优先选 token 充裕的模型。**
5. **替换原则：** 优先选能力最匹配当前角色需求的模型；能力相当时选成本更低的。
6. **当前参考 / 固定位置 / 当前配置，都不得保留已在 `test_results.json` 中判定不可用的模型示例。**
7. **每次更新模型配置前，都必须先重跑模型测试并刷新 `test_results.json`，不得基于旧测试结果做决策。**

### 2.1 可用性门禁（AI MUST FOLLOW）

在任何模型选择动作之前，先执行以下判定：

```text
Step A. 读取 `opencode models`
Step B. 读取 `test_results.json`
Step C. 候选集 = 同时满足以下条件的模型：
  - 出现在 `opencode models`
  - `test_results.json.models[].connected == true`
Step D. 从候选集中按角色能力需求选择最佳匹配模型
Step E. 若首选模型不可用，选能力最接近的替代，并记录原因
```

**MUST**
- 先运行 `python3 test_all_models.py`，刷新 `test_results.json`。
- 先检查 `test_results.json`，再决定模型。
- 只选择 `connected=true` 的模型。
**MUST NOT**
- 不得因为模型出现在 `opencode models` 中就直接选用。
- 不得选择 `connected=false` 的模型。
- 不得选择 `status != 200` 或 `error` 非空的模型。
- 不得继续保留 `401 / 403 / 429 / 500 / timeout / not supported / Missing API key / auth_unavailable` 这类失败模型作为“当前参考”或默认示例。

### 2.2 关键位置固定模型

| 位置 | 模型 | Variant | 选择理由 |
|---|---|---|---|
| `sisyphus` | `openai/gpt-5.4` | `max` | 主编排需要最强推理 + 工具调用 |
| `oracle` | `openai/gpt-5.4` | `high` | 只读咨询位需要高能力推理 |
| `ultrabrain` | `openai/gpt-5.4` | `xhigh` | 超高难度逻辑需要大量 token |
| `multimodal-looker` | `openai/gpt-5.4` | `medium` | 当前无可用专用视觉模型，回退到最强通用模型 |
| `deep` | `openai/gpt-5.4` | `medium` | 自主长链执行需要长上下文 |
| `prometheus` | `openai/gpt-5.4` | `max` | 计划构建需要强推理 |
| `metis` | `openai/gpt-5.4` | `max` | 预规划分析需要强推理 |
| `momus` | `openai/gpt-5.4` | `xhigh` | 评审需要深度推理 + 长上下文 |

---

## 3. 模型能力评估与分配

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
| `sisyphus` | `openai/gpt-5.4` | `max` |
| `hephaestus` | `openai/gpt-5.4-mini` | `medium` |
| `oracle` | `openai/gpt-5.4` | `high` |
| `explore` | `opencode/big-pickle` | — |
| `multimodal-looker` | `openai/gpt-5.4` | `medium` |
| `prometheus` | `openai/gpt-5.4` | `max` |
| `metis` | `openai/gpt-5.4` | `max` |
| `momus` | `openai/gpt-5.4` | `xhigh` |
| `atlas` | `opencode/minimax-m2.5-free` | — |
| `sisyphus-junior` | `opencode/nemotron-3-super-free` | — |

### 4.2 Categories

| Category | 模型 | Variant |
|---|---|---|
| `visual-engineering` | `openai/gpt-5.4` | `high` |
| `ultrabrain` | `openai/gpt-5.4` | `xhigh` |
| `deep` | `openai/gpt-5.4` | `medium` |
| `artistry` | `openai/gpt-5.4` | `high` |
| `quick` | `opencode/nemotron-3-super-free` | — |
| `unspecified-low` | `opencode/big-pickle` | — |
| `unspecified-high` | `openai/gpt-5.4-mini` | `medium` |
| `writing` | `openai/gpt-5.4-mini` | `medium` |

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
4. 评估该模型在各维度的实际能力。
5. 按角色能力需求匹配分配；仅替换能力相当或更优的模型。
6. 更新本文件"当前参考"。

### 5.2 模型失效

1. 在 `test_results.json` 中确认失效的是哪个 provider / model。
2. 失效判定：`connected=false`，或 `status != 200`，或 `error` 非空。
3. 从剩余可用模型中，选能力最接近失效模型的替代。
4. 批量更新 `oh-my-openagent.json`。

### 5.3 想省钱

1. 先保留关键位置（oracle / ultrabrain）。
2. 优先用免费或低成本模型替换非关键位。
3. 不改 `oracle` / `ultrabrain`。

### 5.4 账号/环境变化

1. 先看 `opencode models` 的实际输出。
2. 再看 `test_results.json` 的实际连通结果。
3. 新 provider：只有在 `connected=true` 时才补到"当前参考"。
4. 旧 provider 消失，或该 provider 在 `test_results.json` 中全部失效：删掉所有引用。
5. 模型改名但能力接近，且测试通过：保持原位置。

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
