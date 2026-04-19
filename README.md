# Oh-My-OpenAgent Model Config

[Oh-My-OpenAgent](https://github.com/code-yeongyu/oh-my-openagent) 的模型分配配置，用于 [OpenCode](https://github.com/opencode-ai/opencode)。

## 是什么

一个按能力分层、可判定更新的 Agent 模型配置方案。根据模型推理、代码、工具调用、上下文、速度、视觉等维度，将可用模型分配到 OpenCode 的各个 Agent 和 Category 位置。

## 分层策略

| 策略 | 范围 | 用途 |
|---|---|---|
| Capability-first | `opencode models` 可见且 `test_results.json` 可用的模型 | 全部位置统一按能力与角色匹配分配，不考虑成本 |

优先级：统一以模型实际能力、可用性与角色匹配为准，不按 provider、品牌或价格预设优先级。

## 文件说明

| 文件 | 用途 |
|---|---|
| `oh-my-openagent.json` | 实际配置，复制到 `~/.config/opencode/oh-my-openagent.json` 生效 |
| `AGENTS.md` | 分配策略文档 — 模型分层、固定规则、变更流程 |

## 使用方法

```bash
# 1. 先重跑模型测试，刷新 test_results.json
python3 test_all_models.py

# 2. 查看当前可见模型
opencode models

# 3. 查看当前实际可用模型（connected=true）
python3 - <<'PY'
import json
data=json.load(open('test_results.json'))
for m in data['models']:
    if m.get('connected'):
        print(m['model_id'])
PY

# 4. 一键筛出最终候选集（可见 ∩ 可用）
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

# 5. 复制配置到 OpenCode
cp oh-my-openagent.json ~/.config/opencode/oh-my-openagent.json
```

最后一个命令块会直接输出“最终候选集”：也就是同时满足“`opencode models` 可见”且“`test_results.json` 中 `connected=true`、`status == 200`、`error` 为空”的模型。后续分配只按能力与角色匹配决定，不考虑成本。

## 变更流程

1. 先运行 `python3 test_all_models.py`，刷新 `test_results.json`
2. 运行 `opencode models` 获取当前可见模型列表
3. 读取最新的 `test_results.json`，过滤出 `connected=true` 的实际可用模型
4. 按 AGENTS.md 中的分层规则、可用性门禁和评估维度分配模型
5. 编辑本目录的 `oh-my-openagent.json`
6. 同步到 `~/.config/opencode/oh-my-openagent.json`

详细规则见 [AGENTS.md](./AGENTS.md)。

## 当前配置快照

**Agents：**

| Agent | 模型 | Variant |
|---|---|---|
| sisyphus | gpt-5.4 | max |
| hephaestus | gpt-5.3-codex | medium |
| oracle | gpt-5.4 | high |
| explore | gpt-5.4-mini | medium |
| multimodal-looker | gpt-5.4 | medium |
| prometheus | gpt-5.4 | max |
| metis | gpt-5.4 | max |
| momus | gpt-5.4 | xhigh |
| atlas | gpt-5.3-codex | medium |
| sisyphus-junior | gpt-5.3-codex | medium |

**Categories：**

| Category | 模型 | Variant |
|---|---|---|
| visual-engineering | gpt-5.4 | high |
| ultrabrain | gpt-5.4 | xhigh |
| deep | gpt-5.4 | medium |
| artistry | zhipuai-coding-plan/glm-4.6v | high |
| quick | gpt-5.4-mini | medium |
| unspecified-low | gpt-5.4-mini | medium |
| unspecified-high | gpt-5.2 | medium |
| writing | gpt-5.4-mini | medium |

## License

MIT
