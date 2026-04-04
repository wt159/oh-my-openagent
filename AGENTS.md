# AGENTS.md — Oh-My-OpenCode Model Policy

> 目标：当可用模型变化时，快速、可判定地更新 `oh-my-opencode.json`。

---

## 0. 执行顺序

1. 先运行 `opencode models`。
2. 先改本目录的 `oh-my-opencode.json`。
3. 再覆盖 `~/.config/opencode/oh-my-opencode.json`。
4. 只做必要替换，不重排无关项。

---

## 1. 模型分层

| Tier | 格式 | 用途 |
|---|---|---|
| T1 | `openai/<model>` | 只放关键位置 |
| T2 | `zhipuai-coding-plan/<model>` | 核心执行位 |
| T3 | `opencode/<model>-free` | 高频低价值位 |

### 1.1 当前参考

> 以 `opencode models` 的输出为准。

**T1 — OpenAI**
- `openai/gpt-5.4`

**T2 — ZhiPu Coding Plan**
- `zhipuai-coding-plan/glm-5.1`
- `zhipuai-coding-plan/glm-5`
- `zhipuai-coding-plan/glm-4.7`
- `zhipuai-coding-plan/glm-4.6`

**T3 — OpenCode Free**
- `opencode/qwen3.6-plus-free`
- `opencode/glm-5-free`
- `opencode/kimi-k2.5-free`
- `opencode/minimax-m2.1-free`
- `opencode/big-pickle`

---

## 2. 固定规则

1. **OpenAI 只按用户规则放关键位置**。
2. **其它模型按能力分配**。
3. **能力分配仅适用于非 OpenAI 模型**。
4. **优先级：** T1 > T2 > T3。
5. **替换原则：** 同 Tier 优先；跨 Tier 仅在明确需要时调整。

### 2.1 OpenAI 固定位置

| 位置 | 模型 |
|---|---|
| `oracle` | `openai/gpt-5.4` (`high`) |
| `ultrabrain` | `openai/gpt-5.4` (`xhigh`) |
| `multimodal-looker` | `openai/gpt-5.4` |
| `deep` | `openai/gpt-5.4` |

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

| Agent | 模型 |
|---|---|
| `sisyphus` | `zhipuai-coding-plan/glm-5.1` |
| `hephaestus` | `zhipuai-coding-plan/glm-5` |
| `oracle` | `openai/gpt-5.4` |
| `explore` | `opencode/qwen3.6-plus-free` |
| `multimodal-looker` | `openai/gpt-5.4` |
| `prometheus` | `zhipuai-coding-plan/glm-5` |
| `metis` | `zhipuai-coding-plan/glm-5` |
| `momus` | `zhipuai-coding-plan/glm-5.1` |
| `atlas` | `opencode/kimi-k2.5-free` |
| `sisyphus-junior` | `opencode/glm-5-free` |

### 4.2 Categories

| Category | 模型 |
|---|---|
| `visual-engineering` | `zhipuai-coding-plan/glm-5` |
| `ultrabrain` | `openai/gpt-5.4` |
| `deep` | `openai/gpt-5.4` |
| `artistry` | `zhipuai-coding-plan/glm-5` |
| `quick` | `opencode/glm-5-free` |
| `unspecified-low` | `opencode/qwen3.6-plus-free` |
| `unspecified-high` | `zhipuai-coding-plan/glm-4.7` |
| `writing` | `zhipuai-coding-plan/glm-4.7` |

---

## 5. 变更流程

### 5.1 新模型可用

1. 跑 `opencode models`。
2. 判断 provider / tier。
3. 只在同 Tier 内优先替换。
4. 更新本文件“当前参考”。

### 5.2 模型失效

1. 确认失效的是哪个 provider / model。
2. 从同 Tier 选替代。
3. 批量更新 `oh-my-opencode.json`。

### 5.3 想省钱

1. 先保留 T1 固定位置。
2. 优先压缩 T2 → T3 的非关键位。
3. 不改 `oracle` / `ultrabrain`。

### 5.4 账号/环境变化

1. 先看 `opencode models` 的实际输出。
2. 新 provider：补到“当前参考”。
3. 旧 provider 消失：删掉所有引用。
4. 模型改名但能力接近：保持原 Tier。

---

## 6. 文件规则

### 6.1 工作副本

1. 编辑源：本目录 `oh-my-opencode.json`。
2. 落盘目标：`~/.config/opencode/oh-my-opencode.json`。
3. 顺序：先看工作区 diff，再同步到真实环境。

### 6.2 查看命令

```bash
opencode models
```

### 6.3 离线备选

```bash
python3 - <<'PY'
import json
data=json.load(open('$HOME/.cache/opencode/models.json'))
cfg=json.load(open('$HOME/.config/opencode/oh-my-opencode.json'))
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
