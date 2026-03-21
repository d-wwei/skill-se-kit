# Skill-SE-Kit

[English](README.md)

`Skill-SE-Kit` 是一个兼容协议、可审计、可治理、可自我进化的技能运行时底座。
它提供了单个 skill 在 `standalone` 和 `governed` 两种模式下所需的通用运行时能力。

对外产品名和包名为 `Skill-SE-Kit`，内部 Python 模块路径为 `skill_se_kit`。

## 核心能力

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
```

## 集成入口

建议从这些文档开始：

- [集成指南](docs/integration-guide.md)
- [架构说明](docs/architecture.md)
- [MVP 计划](docs/mvp-plan.md)
- [最小集成示例](examples/minimal_skill_integration.py)

## 与其他仓库的关系

- [Skill Evolution Protocol](https://github.com/d-wwei/skill-evolution-protocol)：协议与 schema 来源
- [Agent Skill Governor](https://github.com/d-wwei/agent-skill-governor)：在 governed 模式下负责 official promotion 的外部治理层
- [Remix](https://github.com/d-wwei/remix)：独立的重构系统，在需要自我进化与 governed handoff 时集成 `Skill-SE-Kit`

