# Skill-SE-Kit

[English](README.md)

`Skill-SE-Kit` 是一个兼容协议、可审计、可治理、可自我进化的技能运行时底座。
它提供了单个 skill 在 `standalone` 和 `governed` 两种模式下所需的通用运行时能力。

对外产品名和包名为 `Skill-SE-Kit`，内部 Python 模块路径为 `skill_se_kit`。

## 学术背景

本项目是两篇前沿论文的工程化落地实现。这两篇来自顶流机构的工作不约而同地指向同一个认知：

> **静态的 Skill 只是高级 Prompt，能自我进化的 Skill 才是真正的数字资产。**

### AutoSkill — 基于经验的终身学习与技能自进化

- **作者**: 华东师范大学 ICALK 实验室 & 上海人工智能实验室
- **论文**: [arXiv:2603.01145](https://arxiv.org/abs/2603.01145)
- **代码**: [ECNU-ICALK/AutoSkill](https://github.com/ECNU-ICALK/AutoSkill)

AutoSkill 提出了一个激进但合理的观点：用户的每一次反馈都应该让系统变得更聪明。
它的核心是**双循环架构**——左循环检索相关 Skill 生成当前回答，右循环从用户交互
中提取新 Skill 或更新现有 Skill，两个循环并行运行。

### XSKILL — 多模态 Agent 的经验与技能协同进化

- **作者**: 香港科技大学、浙江大学 & 华中科技大学
- **论文**: [arXiv:2603.12056](https://arxiv.org/abs/2603.12056)
- **代码**: [XSkill-Agent/XSkill](https://github.com/XSkill-Agent/XSkill)
- **项目页**: [xskill-agent.github.io](https://xskill-agent.github.io/xskill_page/)

XSKILL 回答了"Skill 如何横向适应复杂环境"的问题。它引入了**双流知识架构**——
Skill Library（结构化任务流程，类似"驾驶手册"）和 Experience Bank（情境化
动作提示，类似"驾驶直觉"），以及 **Cross-Rollout Critique**——对比多次执行
的成功与失败，提取因果经验。

### Skill-SE-Kit 借鉴了什么

| 概念 | 来源 | 在 Skill-SE-Kit 中的实现 |
|------|------|--------------------------|
| 双循环架构 | AutoSkill | `run_integrated_skill()` 在一次调用中编排执行 + 学习 |
| 版本化 Skill Bank | AutoSkill + XSKILL | `local/skill_bank/skills.json`，每次更新自动 `bump_patch_version()` |
| Experience Bank | XSKILL | `local/experience_bank/` — 情境化经验条目，可检索 |
| Add / Merge / Discard 决策 | 两者 | `UpdateDecision`，支持 `add`、`merge`、`discard`、`supersede` |
| 执行时技能检索 | AutoSkill | `retrieve_knowledge()` 将 `skill_guidance` 注入 executor 上下文 |
| Cross-Rollout Critique | XSKILL | 对比近期 rollout 的成功/失败模式，将 critique 写入经验 |
| 层级化知识压缩 | XSKILL | `synthesize_skill()` 在 bullet 数超过阈值时自动压缩、去重、解决冲突 |
| 置信度过滤 | 两者（隐含） | `min_feedback_confidence` 门禁，低于阈值的信号不推动 skill bank 变更 |

### Skill-SE-Kit 在论文之上增加了什么

论文描述的是研究框架，Skill-SE-Kit 是面向生产环境的工程实现，补充了：

- **协议兼容** — 所有产物遵循 [Skill Evolution Protocol](https://github.com/d-wwei/skill-evolution-protocol) schema
- **治理模式** — governor 握手、外部晋升权限、governed overlay 消费
- **审计与溯源** — 一等公民的决策日志、证据产物、来源归因
- **自动代码修复** — 内置修复适配器（`replace_text`、`insert_after`、`python_dict_set` 等），能落地真实代码修复，不只是学规则
- **Agent-Driven 集成** — LLM agent 用 CLI 做存储，自身提供智能层，宿主侧零 Python 代码
- **可插拔智能后端** — 本地 Jaccard 引擎和 LLM 语义推理之间自由切换
- **多语言支持** — 中英文偏好检测与检索 token
- **回归门禁晋升** — candidate 仅在通过 evaluation case 和 verification hook 后才能晋升
- **回滚与快照** — 基于版本化快照的运维恢复

## 核心能力

- 面向 agent 和 skill 的一键轻松集成
- **Agent-Driven 集成模式**：LLM agent 用 CLI 做结构化存储，自身提供智能层——宿主侧零 Python 代码
- 可插拔智能后端：内置本地 Jaccard 引擎，或通过 `LLMBackend` 接入任意 LLM
- `skill-se-kit init` 自动接管式初始化
- 可配置运行模式：`off`、`manual`、`auto`
- 从用户输入和执行结果中自动提取反馈
- 基于置信度的学习门禁，默认跳过弱信号
- 中英文偏好表达识别
- 支持英文和中文知识复用的多语言检索 token
- 面向人类的可读进化报告
- 面向集成 skill 的自治双循环进化
- 针对 managed files 的自动补丁生成、代码修复与代码优化
- 执行时从 skill bank 与 experience bank 检索知识
- 从交互反馈中自动提炼经验
- `add / merge / discard` 的 skill 管理
- 带回归门禁的 candidate rewrite bundle 与本地推广
- governor 握手与 governed 模式约束
- audit 产物生成
- provenance 记录
- verification hooks 与晋升门禁
- SDK 版本兼容性检查

## 支持的协议

- protocol version：`1.0.0`
- governance modes：`standalone`、`governed`

`Skill-SE-Kit` 直接消费 [skill-evolution-protocol](https://github.com/d-wwei/skill-evolution-protocol) 中的 canonical schema 和 examples。

## 仓库结构

```text
skill-se-kit/
  README.md
  README.zh-CN.md
  src/skill_se_kit/
    audit/
    runtime/
    storage/
    evolution/
    evaluation/
    feedback/
    governance/
    intelligence/
    integration/
    provenance/
    protocol/
    repair/
    reporting/
    verification/
  schemas/             # feedback 输入和 run 输出的 JSON Schema
  tests/
  examples/
  docs/
```

## 集成决策树

```text
你的宿主系统是什么？
├─ LLM Agent（Claude、GPT、Agent 框架）
│   ├─ 想零代码集成？→ Agent-Driven 模式（推荐）
│   │     CLI 负责存储 + agent 自身提供智能
│   └─ 想深度定制？→ Python API + register_intelligence_backend()
├─ 自动化管道（CI/CD、脚本、非 agent 代码）
│   ├─ 只记录经验？→ Learning-Only 模式
│   ├─ 要自动修复代码？→ Native Repair 模式
│   └─ 多脚本/工具路由？→ Multi-Script Dispatcher 模式
└─ CLI manual 模式 → 用于人工监督、调试、审计
```

详见 [集成模式规范](docs/integration-modes.md)。

## 快速开始

```bash
python3 -m pip install .
python3 -m pytest tests/
```

把一个已有 skill 自动接入：

```bash
skill-se-kit init --skill-root /path/to/skill --protocol-root /path/to/skill-evolution-protocol
skill-se-kit run --skill-root /path/to/skill --input-json '{"task":"draft memo","user_input":"Always include a summary."}'
skill-se-kit report --skill-root /path/to/skill
skill-se-kit rollback --skill-root /path/to/skill --snapshot-id snapshot-xxxx
```

Agent-Driven 模式下，直接传入结构化 feedback：

```bash
skill-se-kit run --skill-root /path/to/skill \
  --input-json '{"task":"browse","url":"https://example.com"}' \
  --feedback-json '{"status":"positive","lesson":"用 page.evaluate() 穿透 shadow DOM","source":"explicit","confidence":0.9}'
```

## 傻瓜式使用

可以使用 `EasyIntegrator.one_click(...)` 或
`SkillRuntime.enable_easy_integration(...)` 一步完成：

- 初始化 skill workspace
- 注册 executor
- 设置运行模式
- 打开自动反馈
- 打开人类可读报告

如果是已有 skill，优先使用 `skill-se-kit init`。它会自动：

- 发现 protocol 仓库
- 在缺失时补齐 manifest 和 workspace 布局
- 尽量自动识别标准 executor
- 当还缺 dispatcher 时，给出脚本清单提示
- 生成 `.skill_se_kit/auto_integration.json`
- 若存在 `SKILL.md`，自动写入 wrapper 提示
- 打通 `run` 和 `report` CLI 入口，方便 agent 与人类使用
- 提供 `rollback` CLI 入口，便于恢复

运行模式：

- `off`：不运行 kit，只直接调用 executor
- `manual`：运行 kit，但不自动学习
- `auto`：运行 kit，并自动触发进化

自动反馈默认会优先消费：

- 显式偏好，如 `always`、`never`、`must`、`每次都`、`必须`、`不要`
- 结果中的失败信号，如错误状态、stderr、非零退出码
- 低置信度的泛化信号会被记录，但默认不会推动 skill bank 变更

## Skill 存储分层

```text
<skill-root>/
  manifest.json
  official/
    manifest.json
  local/
    experiences/
    proposals/
    overlays/
    evaluations/
    rollouts/
    experience_bank/
    skill_bank/
  governed/
    decisions/
    overlays/
  audit/
    summaries/
    decision_logs/
    evidence/
  provenance/
    sources/
    lineage/
  .skill_se_kit/
    snapshots/
    framework_policy/
    skill_contract.json
    auto_integration.json
  reports/
    evolution/
```

## 集成入口

建议从这些文档开始：

- [集成指南](docs/integration-guide.md) — 决策树、职责划分、检查清单
- [集成模式规范](docs/integration-modes.md) — Agent-Driven、Learning-Only、Native Repair、Multi-Script Dispatcher
- [自治进化说明](docs/autonomous-evolution.md)
- [架构说明](docs/architecture.md)

合约 Schema：

- [Feedback JSON Schema](schemas/feedback.schema.json) — `--feedback-json` 的输入格式
- [Run Result JSON Schema](schemas/run-result.schema.json) — `skill-se-kit run` 的输出格式

示例：

- [最小集成](examples/minimal_skill_integration.py)
- [一键模式](examples/easy_mode_skill.py)
- [自治 skill](examples/autonomous_native_skill.py)
- [自治代码修复](examples/autonomous_code_repair.py)

如果你希望 kit 真的去修代码，而不只是学规则，一定先读
[集成模式规范](docs/integration-modes.md)，确认你接的是原生修复模式，
而不是"执行在外部，kit 只做事后记录"的模式。

## 与其他仓库的关系

- [Skill Evolution Protocol](https://github.com/d-wwei/skill-evolution-protocol)：协议与 schema 来源
- [Agent Skill Governor](https://github.com/d-wwei/agent-skill-governor)：在 governed 模式下负责 official promotion 的外部治理层
- [Remix](https://github.com/d-wwei/remix)：独立的重构系统，在需要自我进化与 governed handoff 时集成 `Skill-SE-Kit`

## 致谢

Skill-SE-Kit 站在两项开创性研究工作的肩膀上：

- **AutoSkill** — 华东师范大学 ICALK 实验室 & 上海人工智能实验室
  ([arXiv:2603.01145](https://arxiv.org/abs/2603.01145),
  [GitHub](https://github.com/ECNU-ICALK/AutoSkill)) — 建立了任务执行
  与技能进化并行的双循环范式，以及 add/merge/discard 技能管理框架。

- **XSKILL** — 香港科技大学、浙江大学 & 华中科技大学
  ([arXiv:2603.12056](https://arxiv.org/abs/2603.12056),
  [GitHub](https://github.com/XSkill-Agent/XSkill),
  [项目页](https://xskill-agent.github.io/xskill_page/)) — 提出了
  Skill Library + Experience Bank 的双流知识架构、Cross-Rollout Critique
  方法论，以及层级化技能压缩机制。

这两项工作证明了自我进化的技能不仅在理论上成立，而且在实践中可行。
Skill-SE-Kit 将它们的研究洞见转化为一个生产级、协议兼容的运行时底座，
供任何 agent 系统集成使用。
