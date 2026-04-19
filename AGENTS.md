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

> **核心规则：不考虑成本，只按能力与角色匹配分配。**
>
> 模型来源不设预设优先级。
> 每个模型根据其在推理、代码、工具调用、上下文、速度、视觉等维度的实际表现，
> 与角色的能力需求匹配后决定分配。

### 1.1 当前候选模型

> 以 `opencode models` 和 `test_results.json` 的交集为准。
>
> `opencode models` 只表示"可见 / 可枚举"；`test_results.json` 中 `connected=true` 才表示"当前环境可用"。
>
> 只有同时满足以下条件的模型才允许进入候选集：
> - 出现在 `opencode models`
> - `test_results.json.models[].connected == true`
> - `status == 200`
> - `error` 为空

**OpenAI**
- `openai/gpt-5.4`
- `openai/gpt-5.4-mini`
- `openai/gpt-5.2`
- `openai/gpt-5.3-codex`

**OpenCode**
- `opencode/big-pickle`
- `opencode/minimax-m2.5-free`
- `opencode/nemotron-3-super-free`

**ZhiPu Coding Plan**
- `zhipuai-coding-plan/glm-4.5`
- `zhipuai-coding-plan/glm-4.5-air`
- `zhipuai-coding-plan/glm-4.5-flash`
- `zhipuai-coding-plan/glm-4.5v`
- `zhipuai-coding-plan/glm-4.6`
- `zhipuai-coding-plan/glm-4.6v`
- `zhipuai-coding-plan/glm-4.6v-flash`
- `zhipuai-coding-plan/glm-4.7`
- `zhipuai-coding-plan/glm-4.7-flash`
- `zhipuai-coding-plan/glm-5`
- `zhipuai-coding-plan/glm-5-turbo`
- `zhipuai-coding-plan/glm-5.1`

> 当前测试失败的模型，例如 `openai/gpt-5.2-codex`、`opencode/gpt-5-nano`、`zhipuai-coding-plan/glm-4.7-flashx`、`zhipuai-coding-plan/glm-5v-turbo`，不得进入候选集，也不得出现在“当前参考”或默认示例中。

### 1.2 能力评估依据

选择模型时参考以下依据（按可信度排序）：

1. **实际测试结果**：`test_results.json` 中的连通性、延迟、并发数据。
2. **公开基准测试**：官方 benchmark（如 MMLU、HumanEval、Arena Elo 等）。
3. **社区评测**：LMSys Chatbot Arena、独立评测报告。
4. **实际使用体感**：在当前项目中的代码生成质量、工具调用稳定性等主观经验。

> **注意**：能力优先于型号新旧、命名直觉或价格预期。不按 provider、品牌或价格做预设筛选。

---

## 2. 固定规则

1. **选模型时必须同时参考 `opencode models` 和 `test_results.json`。**
2. **只有 `test_results.json` 中 `connected=true`、`status == 200` 且 `error` 为空的模型，才允许进入候选集。**
3. **所有位置统一按能力竞争分配，不按 provider、品牌或价格预设优先级。**
4. **关键位置优先看推理、代码、工具调用与上下文能力。**
5. **替换原则：** 优先选能力最匹配当前角色需求的模型；能力相当时，优先保持现有已验证稳定的配置。**不得因为成本高低而替换。**
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
  - `status == 200`
  - `error` 为空
Step D. 从候选集中按角色能力需求选择最佳匹配模型
Step E. 若首选模型不可用，选能力最接近的可用替代，并记录原因
```

**MUST**
- 先运行 `python3 test_all_models.py`，刷新 `test_results.json`。
- 先检查 `test_results.json`，再决定模型。
- 只选择满足门禁条件的可用模型。
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
| `multimodal-looker` | `openai/gpt-5.4` | `medium` | 当前配置中由通用高能力模型承担视觉理解 |
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
| 速度 | 高频简单任务的响应效率 | 高频执行位 |
| 视觉 | 截图、UI、图片理解 | 视觉位 |

### 3.2 分配规则

1. 关键决策位 → 先看推理 + 稳定性。
2. 执行位 → 先看代码 + 工具调用。
3. 编排/审查位 → 先看上下文。
4. 高频执行位 → 先看能力是否足够，其次看速度。
5. 视觉位 → 先看多模态能力。

---

## 4. 当前配置

### 4.1 Agents

| Agent | 模型 | Variant |
|---|---|---|
| `sisyphus` | `openai/gpt-5.4` | `max` |
| `hephaestus` | `openai/gpt-5.3-codex` | `medium` |
| `oracle` | `openai/gpt-5.4` | `high` |
| `explore` | `openai/gpt-5.4-mini` | `medium` |
| `multimodal-looker` | `openai/gpt-5.4` | `medium` |
| `prometheus` | `openai/gpt-5.4` | `max` |
| `metis` | `openai/gpt-5.4` | `max` |
| `momus` | `openai/gpt-5.4` | `xhigh` |
| `atlas` | `openai/gpt-5.3-codex` | `medium` |
| `sisyphus-junior` | `openai/gpt-5.3-codex` | `medium` |

### 4.2 Categories

| Category | 模型 | Variant |
|---|---|---|
| `visual-engineering` | `openai/gpt-5.4` | `high` |
| `ultrabrain` | `openai/gpt-5.4` | `xhigh` |
| `deep` | `openai/gpt-5.4` | `medium` |
| `artistry` | `zhipuai-coding-plan/glm-4.6v` | `high` |
| `quick` | `openai/gpt-5.4-mini` | `medium` |
| `unspecified-low` | `openai/gpt-5.4-mini` | `medium` |
| `unspecified-high` | `openai/gpt-5.2` | `medium` |
| `writing` | `openai/gpt-5.4-mini` | `medium` |

---

## 5. 变更流程

### 5.0 选择前检查（必须）

1. 先跑 `python3 test_all_models.py`，刷新 `test_results.json`。
2. 再跑 `opencode models`。
3. 再读取最新的 `test_results.json`。
4. 建立候选集：仅保留同时满足“出现在 `opencode models`”且“`connected=true`、`status == 200`、`error` 为空”的模型。
5. 任何不在候选集中的模型，不得进入“当前参考”、固定位置或 `oh-my-openagent.json`。

### 5.1 新模型可用

1. 先跑 `python3 test_all_models.py`，生成最新测试结果。
2. 再跑 `opencode models`。
3. 读取最新的 `test_results.json`，过滤出满足门禁条件的可用模型。
4. 评估该模型在各维度的实际能力。
5. 按角色能力需求匹配分配；仅替换能力相当或更优的模型。
6. 更新本文件“当前参考”。

### 5.2 模型失效

1. 在 `test_results.json` 中确认失效的是哪个模型。
2. 失效判定：`connected=false`，或 `status != 200`，或 `error` 非空。
3. 从剩余可用模型中，选能力最接近失效模型的替代。
4. 批量更新 `oh-my-openagent.json`。

### 5.3 配置收敛原则

1. 先保留关键位置（oracle / ultrabrain / sisyphus）。
2. 非关键位也按能力调整，不因来源不同而预先排除模型。
3. 不因为成本、免费或 provider 变化而改动关键位。

### 5.4 账号/环境变化

1. 先看 `opencode models` 的实际输出。
2. 再看 `test_results.json` 的实际连通结果。
3. 新增模型：只有在满足门禁条件时才补到“当前参考”。
4. 某个模型消失，或该模型在 `test_results.json` 中失效：删掉所有引用。
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
    if (
        m.get('connected')
        and m.get('status') == 200
        and not m.get('error')
        and m.get('model_id', '').startswith('openai/')
    )
}

for model_id in sorted(visible & connected):
    print(model_id)
PY
```

> 每次更新模型配置前，都应先执行 `python3 test_all_models.py`，确保 `test_results.json` 是最新结果。
>
> 只有同时出现在以上两份结果中，且满足门禁条件的模型，才允许被选择。
>
> 最后一个命令块会一键输出“最终候选集”：也就是同时满足“`opencode models` 可见”且“`test_results.json` 中 `connected=true`、`status == 200`、`error` 为空”的模型。
