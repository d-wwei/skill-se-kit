# Skill-SE-Kit

[English](README.md)

`Skill-SE-Kit` 是一个兼容协议、可审计、可治理、可自我进化的技能运行时底座。
它提供了单个 skill 在 `standalone` 和 `governed` 两种模式下所需的通用运行时能力。

对外产品名和包名为 `Skill-SE-Kit`，内部 Python 模块路径为 `skill_se_kit`。

## 核心能力

- 面向 agent 和 skill 的一键轻松集成
- 可配置运行模式：`off`、`manual`、`auto`
- 从用户输入和执行结果中自动提取反馈
- 面向人类的可读进化报告
- 面向集成 skill 的自治双循环进化
- 执行时从 skill bank 与 experience bank 检索知识
- 从交互反馈中自动提炼经验
- `add / merge / discard` 的 skill 管理
- 带回归门禁的 candidate rewrite bundle 与本地推广
- experience 记录
- proposal 生成
- overlay 应用
- 本地评估
- `standalone` 模式下的本地晋升
- governor 握手与 governed 模式约束
- audit 产物生成
- provenance 记录
- verification hooks 与晋升门禁

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
    governance/
    provenance/
    protocol/
    verification/
  tests/
  examples/
  docs/
```

## 快速开始

```bash
python3 -m pip install .
python3 -m unittest discover -s tests -p 'test_*.py'
```

## 傻瓜式使用

可以使用 `EasyIntegrator.one_click(...)` 或
`SkillRuntime.enable_easy_integration(...)` 一步完成：

- 初始化 skill workspace
- 注册 executor
- 设置运行模式
- 打开自动反馈
- 打开人类可读报告

运行模式：

- `off`：不运行 kit，只直接调用 executor
- `manual`：运行 kit，但不自动学习
- `auto`：运行 kit，并自动触发进化

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
  reports/
    evolution/
```

## 集成入口

建议从这些文档开始：

- [集成指南](docs/integration-guide.md)
- [自治进化说明](docs/autonomous-evolution.md)
- [架构说明](docs/architecture.md)
- [MVP 计划](docs/mvp-plan.md)
- [最小集成示例](examples/minimal_skill_integration.py)
- [一键模式示例](examples/easy_mode_skill.py)
- [自治 skill 示例](examples/autonomous_native_skill.py)

## 与其他仓库的关系

- [Skill Evolution Protocol](https://github.com/d-wwei/skill-evolution-protocol)：协议与 schema 来源
- [Agent Skill Governor](https://github.com/d-wwei/agent-skill-governor)：在 governed 模式下负责 official promotion 的外部治理层
- [Remix](https://github.com/d-wwei/remix)：独立的重构系统，在需要自我进化与 governed handoff 时集成 `Skill-SE-Kit`
