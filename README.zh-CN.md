# Skill SE Kit（Agent-Native）

**协议驱动的 AI Agent 技能自进化。零依赖。**

Agent 读取 SKILL.md，管理 JSON 文件，自主进化技能库。无需运行时、无需 sidecar、无需安装任何包。

## 为什么选择 Agent-Native？

传统技能进化套件以库的形式发布（Python / TypeScript），Agent 需要调用它们。这带来了跨语言集成的痛苦、部署复杂度、以及低质量的智能（Jaccard 词袋匹配 vs. Agent 语义理解）。

Agent-Native 的方式：**Agent 本身就是运行时。** 套件是协议规范 + JSON Schema，Agent 直接遵循协议执行。

| | 库方案 | Agent-Native |
|---|---|---|
| 集成方式 | pip install / npm install | 复制文件 |
| 跨语言 | 需要 sidecar + adapter | 到处可用 |
| 智能水平 | Jaccard 词袋匹配 | Agent 语义理解 |
| 依赖 | Python 3.9+ / Node 18+ | 无 |
| 部署 | 进程管理 | 无需部署 |

## 快速开始

### 1. 复制到你的技能项目

```
your-skill/
  SKILL.zh-CN.md        ← 从本仓库复制
  schemas/              ← 从本仓库复制
  manifest.json         ← 从 workspace-template/ 复制
  skill_bank.json       ← 从 workspace-template/ 复制
  experience/           ← 创建空目录
  audit/                ← 创建空目录
  snapshots/            ← 创建空目录
```

### 2. 编辑 manifest.json

替换所有 `REPLACE_WITH_*` 占位符。

### 3. 让 Agent 遵循 SKILL.md

在 Agent 指令中添加：
```
遵循 SKILL.zh-CN.md 中的技能进化协议。
执行前：从 skill_bank.json 检索相关技能。
执行后：提取反馈，记录经验，更新技能库。
```

### 4. 完成

Agent 现在会从每次执行中学习并积累可复用的技能。

## 工作原理

**双循环架构**（灵感来自 AutoSkill & XSKILL 研究）：

```
左循环（执行）：                  右循环（学习）：
  读取技能库                        提取反馈
  → 查找相关技能                    → 记录经验
  → 注入引导                        → 决策：ADD / MERGE / SUPERSEDE / DISCARD
  → 执行任务                        → 快照 → 修改技能库 → 审计
```

Agent 使用原生语义理解进行技能检索和反馈提取——没有 Jaccard 相似度，没有关键词启发式。

## 工作区结构

```
<skill-root>/
  manifest.json        身份 + 治理 + 合约配置
  skill_bank.json      积累的技能（核心价值）
  experience/          学习历史
  audit/               决策审计
  snapshots/           回滚快照
```

5 个目录，仅此而已。

## 治理模式

- **Standalone 模式**：Agent 自主推进技能变更。
- **Governed 模式**：Agent 创建提案；外部 Governor 审批或拒绝。

兼容 [Skill Evolution Protocol](https://github.com/d-wwei/skill-evolution-protocol) v1.0.0。

## 文档

- [SKILL.md](SKILL.md) — 核心指令文件（英文）
- [SKILL.zh-CN.md](SKILL.zh-CN.md) — 核心指令文件（中文）
- [集成指南](docs/integration-guide.md) — 如何集成到任何技能
- [设计理念](docs/design-philosophy.md) — 为什么选择 Agent-Native
- [工作区参考](docs/workspace-reference.md) — 文件格式详情
- [迁移指南](docs/migration-from-runtime.md) — 从 Python 运行时版本迁移
- [协议参考](protocol/protocol-ref.md) — 协议兼容性

## 示例

- [Standalone 演练](examples/standalone-walkthrough.md) — 完整进化周期
- [Governed 演练](examples/governed-walkthrough.md) — 受治理模式周期
- [示例技能库](examples/example-skill-bank.json) — 已填充的技能库
- [示例经验记录](examples/example-experience.json) — 经验记录

## 研究基础

本套件实现了两篇 2026 年研究论文的核心概念：

- **AutoSkill**（华东师大 ICALK Lab & 上海人工智能实验室，[arXiv:2603.01145](https://arxiv.org/abs/2603.01145)）— 双循环架构，add/merge/discard 技能管理
- **XSKILL**（港科大、浙大、华科，[arXiv:2603.12056](https://arxiv.org/abs/2603.12056)）— 双流技能库 + 经验库，跨 rollout 批判

Agent-Native 版本通过用 Agent 语义理解替代程序化匹配，扩展了这些概念。

## 历史版本

Python 运行时版本已归档至 [skill-se-kit-python](https://github.com/d-wwei/skill-se-kit-python)。该版本提供 CLI、HTTP sidecar 和 NPM adapter，适用于不需要 AI Agent 的确定性执行场景。

## 许可证

MIT
