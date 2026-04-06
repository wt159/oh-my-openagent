# Oh-My-OpenAgent Model Config

[Oh-My-OpenAgent](https://github.com/code-yeongyu/oh-my-openagent) 的模型分配配置，用于 [OpenCode](https://github.com/opencode-ai/opencode)。

## 是什么

一个按能力分层、可判定更新的 Agent 模型配置方案。根据模型推理、代码、工具调用、上下文、速度、视觉等维度，将可用模型分配到 OpenCode 的各个 Agent 和 Category 位置。

## 分层策略

| Tier | 来源 | 用途 |
|---|---|---|
| T1 | OpenAI (`openai/*`) | 关键决策位 — oracle、ultrabrain、deep、multimodal-looker |
| T2 | ZhiPu (`zhipuai-coding-plan/*`) | 核心执行位 — sisyphus、prometheus、metis、momus 等 |
| T3 | Free (`opencode/*-free`) | 高频低价值位 — explore、atlas、sisyphus-junior、quick 等 |

优先级：T1 > T2 > T3。替换时同 Tier 优先，跨 Tier 仅在明确需要时调整。

## 文件说明

| 文件 | 用途 |
|---|---|
| `oh-my-openagent.json` | 实际配置，复制到 `~/.config/opencode/oh-my-openagent.json` 生效 |
| `AGENTS.md` | 分配策略文档 — 模型分层、固定规则、变更流程 |

## 使用方法

```bash
# 1. 查看当前可用模型
opencode models

# 2. 复制配置到 OpenCode
cp oh-my-openagent.json ~/.config/opencode/oh-my-openagent.json
```

## 变更流程

1. 运行 `opencode models` 获取最新可用模型列表
2. 按 AGENTS.md 中的分层规则和评估维度分配模型
3. 编辑本目录的 `oh-my-openagent.json`
4. 同步到 `~/.config/opencode/oh-my-openagent.json`

详细规则见 [AGENTS.md](./AGENTS.md)。

## 当前配置快照

**Agents：**

| Agent | 模型 | Variant |
|---|---|---|
| sisyphus | glm-5.1 | max |
| hephaestus | glm-5 | medium |
| oracle | gpt-5.4 | high |
| explore | qwen3.6-plus-free | — |
| multimodal-looker | gpt-5.4 | medium |
| prometheus | glm-5.1 | max |
| metis | glm-5.1 | max |
| momus | glm-5.1 | xhigh |
| atlas | minimax-m2.5-free | — |
| sisyphus-junior | nemotron-3-super-free | — |

**Categories：**

| Category | 模型 | Variant |
|---|---|---|
| visual-engineering | glm-5 | high |
| ultrabrain | gpt-5.4 | xhigh |
| deep | gpt-5.4 | medium |
| artistry | glm-5 | high |
| quick | nemotron-3-super-free | — |
| unspecified-low | qwen3.6-plus-free | — |
| unspecified-high | glm-5 | — |
| writing | glm-5 | — |

## License

MIT
