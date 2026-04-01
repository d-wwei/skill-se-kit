# 技能自进化套件（Agent-Native）

## 1. 概述

本文件是 **Agent-Native Skill Self-Evolution Kit** 的核心指令文件。它指导 AI Agent 如何在任务执行过程中积累、检索、进化和管理可复用技能。

### 1.1 Agent-Native 范式

传统技能进化系统依赖外部运行时（Python SDK、sidecar 进程、数据库）。Agent-Native 范式的核心洞察是：

> **Agent 本身就是运行时。** Agent 已经具备语义理解、JSON 读写、文件操作和决策推理能力。不需要外部代码来完成这些工作。

本套件由三部分组成：
- **本文件（SKILL.md）** — Agent 遵循的指令和决策逻辑
- **JSON Schemas** — 数据格式的严格定义
- **工作区文件** — Agent 直接读写的 JSON 文件

零外部依赖。不需要 pip install、npm install、sidecar 进程或数据库。

### 1.2 协议兼容性

本套件兼容 [Skill Evolution Protocol v1.0.0](https://github.com/d-wwei/skill-evolution-protocol)。生成的所有制品（manifest、技能条目、审计记录等）符合协议定义的 schema。

### 1.3 双循环架构

系统运行两个循环：
- **执行循环（左循环）**：检索相关技能 → 注入上下文 → 执行任务
- **学习循环（右循环）**：提取反馈 → 记录经验 → 更新技能库

每次任务交互都有可能让系统变得更好。

---

## 2. 快速开始

最少步骤开始使用：

1. **初始化工作区**（第 3.1 节）：创建目录和核心文件
2. **执行任务**（第 4 节）：检索技能 → 注入上下文 → 执行
3. **学习**（第 5 节）：提取反馈 → 记录经验 → 更新技能库

首次使用时，技能库为空，Agent 直接执行任务。随着交互积累，技能库逐渐充实，后续执行将受益于历史经验。

---

## 3. 工作区

### 3.1 初始化新工作区

在技能根目录下创建以下结构：

```
<skill-root>/
  manifest.json        # 身份 + 治理 + 合约配置
  skill_bank.json      # 技能库（核心价值资产）
  experience/          # 学习历史记录
  audit/               # 决策审计日志
  snapshots/           # 回滚快照
```

**步骤 1：创建目录**

```
mkdir -p experience/ audit/ snapshots/
```

**步骤 2：创建 manifest.json**

```json
{
  "skill_id": "<技能标识符，格式：小写字母、数字、点、连字符、下划线>",
  "name": "<技能的人类可读名称>",
  "version": "0.1.0",
  "description": "<技能的简要描述>",
  "protocol_version": "1.0.0",
  "metadata": {
    "created_at": "<ISO 8601 UTC，例如 2026-03-31T00:00:00Z>",
    "updated_at": "<ISO 8601 UTC>",
    "author": "<作者标识符>",
    "contract": {
      "min_feedback_confidence": 0.35,
      "synthesis_threshold": 15,
      "auto_promote": true,
      "managed_files": []
    }
  },
  "governance": {
    "mode": "standalone"
  }
}
```

`skill_id` 格式规则：仅允许小写字母、数字、点（`.`）、连字符（`-`）、下划线（`_`），必须以字母或数字开头。正则：`^[a-z0-9][a-z0-9._-]*$`

`governance.mode` 可选值：
- `"standalone"` — 完全自治，Agent 自主决策所有技能变更
- `"governed"` — 受治理，技能库变更需要 governor 批准

**步骤 3：创建 skill_bank.json**

```json
{
  "skills": []
}
```

**步骤 4：确认治理模式**

读取 `manifest.json` 中的 `governance.mode`，确认是 `standalone` 还是 `governed`。后续学习循环的行为取决于此设置（第 6 节）。

### 3.2 恢复已有工作区

当工作区已存在时：

1. **加载 manifest.json**
   - 验证 `skill_id` 存在且格式正确
   - 验证 `protocol_version` 为 `"1.0.0"`
   - 读取 `governance.mode`
   - 读取 `metadata.contract` 中的阈值配置

2. **加载 skill_bank.json**
   - 验证文件存在且包含 `"skills"` 数组
   - 验证每个技能条目包含必需字段：`skill_entry_id`、`title`、`content`、`version`、`updated_at`

3. **验证目录结构**
   - 确认 `experience/`、`audit/`、`snapshots/` 目录存在
   - 如缺失，创建缺失的目录

---

## 4. 执行循环（左循环）

### 4.1 技能检索（Skill Retrieval）

1. 读取 `skill_bank.json`
2. 对每个技能条目，用你的语义理解能力判断与当前任务的相关性。考虑以下维度：
   - `task_signature` 是否与当前任务类型匹配
   - `keywords` 是否与当前任务存在关键词重叠
   - `content` 内容与当前任务的语义相似度
3. 选择前 3-5 个最相关的技能条目
4. IF 技能库为空（`skills` 数组长度为 0）：
   - 跳过注入，直接执行任务

### 4.2 上下文注入（Context Injection）

将选中的技能格式化为 `skill_guidance` 文本块，注入到任务执行上下文中：

```
=== 技能引导（来自进化历史）===
[1] {title} (v{version})
{content}

[2] {title} (v{version})
{content}

[3] {title} (v{version})
{content}
===
```

每个技能条目按相关性降序排列。`content` 字段直接展示，不做截断或改写。

### 4.3 任务执行（Task Execution）

- 使用增强后的上下文执行任务
- 在当前会话中保持执行结果，供学习循环使用
- 注意观察执行过程中的成功模式和失败模式

---

## 5. 学习循环（右循环）

### 5.1 反馈提取（Feedback Extraction）

按以下决策树从上到下匹配，取第一个命中的分支：

```
IF 存在用户显式反馈（用户说了"这个有效"、"失败因为…"、"下次应该…"等）
  → status = 根据用户说法判断 "positive" 或 "negative"
  → lesson = 用户的洞见，标准化为可复用表述
  → source = "explicit"
  → confidence = 0.9

ELSE IF 执行产生了错误、异常或明确的失败结果
  → status = "negative"
  → lesson = 什么出了问题，以及如何在未来避免
  → source = "execution_result"
  → confidence = 0.7

ELSE IF 执行成功且有可观察的改进（比上次更快、更准确、产出更好）
  → status = "positive"
  → lesson = 什么方法有效，应该在类似场景中重复使用
  → source = "execution_result"
  → confidence = 0.6

ELSE IF 用户输入包含偏好标记词：
  英文："always", "never", "should", "avoid", "prefer", "must", "do not"
  中文："每次都", "必须", "不要", "避免", "优先", "总是", "绝不"
  → status = "positive"
  → lesson = 将偏好标准化为通用陈述
  → source = "user_input"
  → confidence = 0.8

ELSE（无明显信号）
  → status = "positive"
  → lesson = "保持当前方法"
  → source = "default"
  → confidence = 0.2
```

### 5.2 置信度门控（Confidence Gate）

```
IF feedback.confidence < manifest.metadata.contract.min_feedback_confidence（默认：0.35）
  → 执行 5.3 节（记录经验）
  → 不修改技能库
  → 写审计条目："低置信度反馈已记录但技能库未修改"
  → 在此处停止学习循环
```

此门控确保低质量信号不会污染技能库。经验仍然被记录，以备未来回顾。

### 5.3 记录经验（Record Experience）

创建经验条目，写入 `experience/` 目录。

**JSON 模板：**

```json
{
  "experience_id": "exp-{生成12个十六进制字符}",
  "skill_id": "{来自 manifest.json 的 skill_id}",
  "recorded_at": "{ISO 8601 UTC，例如 2026-03-31T14:30:00Z}",
  "task_signature": "{标准化任务类型，例如 code_review, document_drafting}",
  "lesson": "{提取的经验教训，必须具体到可指导未来行为}",
  "feedback_status": "{positive|negative}",
  "feedback_source": "{explicit|user_input|execution_result|default}",
  "feedback_confidence": 0.0,
  "execution_id": "{可选：执行引用标识符}"
}
```

**文件路径：** `experience/exp-{id}.json`

其中 `{id}` 是 `experience_id` 字段中的完整值（例如 `experience/exp-a1b2c3d4e5f6.json`）。

**字段规则：**
- `experience_id`：格式 `exp-{12个十六进制字符}`，从 uuid4 截取
- `skill_id`：必须与 `manifest.json` 中的 `skill_id` 完全一致
- `recorded_at`：ISO 8601 UTC，必须以 `Z` 结尾
- `task_signature`：标准化的任务类型标识符，使用蛇形命名（snake_case）
- `lesson`：必须具体且可操作，不能是泛泛的"做得好"
- `feedback_status`：仅允许 `"positive"` 或 `"negative"`
- `feedback_source`：仅允许 `"explicit"` | `"user_input"` | `"execution_result"` | `"default"`
- `feedback_confidence`：0.0 到 1.0 之间的浮点数

### 5.4 技能更新决策（Skill Update Decision）

按以下决策树确定对技能库的操作：

```
IF 经验教训包含丢弃标记：
   英文："one-off", "temporary", "do not reuse", "ignore this"
   中文："一次性", "临时", "不要复用", "忽略这次"
  → ACTION = DISCARD
  → 写审计条目："经验教训已丢弃：{原因}"
  → 不修改技能库
  → 停止

ELSE 扫描 skill_bank.json 寻找语义匹配：
  FOR 每个已有技能条目：
    用你的语义理解能力判断：这个新经验教训是否针对相同的主题或领域？

  IF 找到匹配技能 且 经验教训兼容（补充现有建议，不矛盾）：
    → ACTION = MERGE
    → 将新要点追加到已有技能的 content 中
    → 补丁版本递增（例如 0.1.0 → 0.1.1，或 0.2.3 → 0.2.4）
    → 将 experience_id 添加到 source_experience_ids 数组
    → 更新 updated_at 时间戳

  ELSE IF 找到匹配技能 且 经验教训矛盾（推翻或替代现有建议）：
    → ACTION = SUPERSEDE
    → 用新理解重写技能的 content
    → 次版本递增（例如 0.1.1 → 0.2.0，或 0.3.5 → 0.4.0）
    → 将 experience_id 添加到 source_experience_ids 数组
    → 更新 updated_at 时间戳

  ELSE（无匹配技能）：
    → ACTION = ADD
    → 创建新技能条目（模板见下方）

AFTER 任何 ADD / MERGE / SUPERSEDE 操作：
  统计受影响技能的 content 中 markdown 要点（bullet point）数量
  IF 要点数量 > manifest.metadata.contract.synthesis_threshold（默认：15）：
    → ACTION = SYNTHESIZE
    → 压缩技能内容：去除重复要点、合并相似建议、抽象为更通用的模式
    → 保留最通用和可复用的表述，删除过于具体的细节
    → 补丁版本递增
    → 写审计条目记录合成操作
```

**新技能条目 JSON 模板（ACTION = ADD 时使用）：**

```json
{
  "skill_entry_id": "skl-{生成12个十六进制字符}",
  "title": "{一行人类可读的技能摘要}",
  "content": "{markdown 要点格式的技能内容，每个要点是一条可复用指南}",
  "version": "0.1.0",
  "task_signature": "{标准化任务类型}",
  "keywords": ["{搜索关键词1}", "{搜索关键词2}"],
  "source_experience_ids": ["{触发创建此技能的 experience_id}"],
  "updated_at": "{ISO 8601 UTC}"
}
```

**字段规则：**
- `skill_entry_id`：格式 `skl-{12个十六进制字符}`，从 uuid4 截取
- `title`：简洁的一行描述，说明这个技能解决什么问题
- `content`：使用 markdown 无序列表格式（`- ` 开头），每个要点是一条独立的、可复用的指南
- `version`：新创建时始终为 `"0.1.0"`
- `task_signature`：与经验记录中的 `task_signature` 一致
- `keywords`：3-7 个搜索关键词，用于辅助检索匹配
- `source_experience_ids`：触发此技能创建或更新的所有经验 ID
- `updated_at`：ISO 8601 UTC，必须以 `Z` 结尾

### 5.5 修改技能库（Mutate Skill Bank）

**每次修改前必须执行以下步骤，顺序不可打乱：**

```
1. 创建快照（第 7.1 节）
   → 将当前 manifest.json 和 skill_bank.json 的完整内容保存到 snapshots/ 目录

2. 读取当前 skill_bank.json
   → 确保操作基于最新版本

3. 应用决策的操作
   → ADD：将新技能条目追加到 skills 数组
   → MERGE：更新匹配技能的 content、version、source_experience_ids、updated_at
   → SUPERSEDE：重写匹配技能的 content，更新 version、source_experience_ids、updated_at
   → SYNTHESIZE：压缩匹配技能的 content，更新 version、updated_at

4. 写入更新后的 skill_bank.json
   → 确保 JSON 格式正确，缩进为 2 空格

5. 写审计条目（5.6 节）
   → 记录此次变更的完整上下文
```

### 5.6 审计日志（Audit Log）

为每个决策写审计条目，写入 `audit/` 目录。

**JSON 模板：**

```json
{
  "audit_id": "aud-{生成12个十六进制字符}",
  "created_at": "{ISO 8601 UTC}",
  "event_type": "{见下方允许值}",
  "skill_id": "{来自 manifest.json 的 skill_id}",
  "subject_id": "{受影响的 skill_entry_id 或 experience_id}",
  "actor": "{agent 模型名称或标识符}",
  "details": {
    "action": "{ADD|MERGE|SUPERSEDE|DISCARD|SYNTHESIZE}",
    "lesson": "{经验教训文本}",
    "confidence": 0.0,
    "reasoning": "{为什么做出此决策的简要说明}"
  }
}
```

**文件路径：** `audit/aud-{id}.json`

**event_type 允许值：**

| event_type | 触发时机 |
|---|---|
| `skill_added` | 新技能条目被添加到技能库 |
| `skill_merged` | 经验教训被合并到已有技能 |
| `skill_superseded` | 已有技能被新理解替代 |
| `skill_discarded` | 经验教训被丢弃（匹配丢弃标记） |
| `skill_synthesized` | 技能内容被压缩合成 |
| `experience_recorded` | 新经验记录被写入（包括低置信度） |
| `snapshot_created` | 快照被创建 |
| `rollback_executed` | 回滚操作被执行 |
| `proposal_created` | 技能变更提案被创建（governed 模式） |
| `proposal_submitted` | 提案被提交给 governor |
| `proposal_accepted` | 提案被 governor 接受 |
| `proposal_rejected` | 提案被 governor 拒绝 |
| `governance_decision` | governor 做出治理决策 |
| `provenance_source` | 来源溯源记录 |
| `provenance_lineage` | 谱系溯源记录 |

**字段规则：**
- `audit_id`：格式 `aud-{12个十六进制字符}`，从 uuid4 截取
- `created_at`：ISO 8601 UTC，必须以 `Z` 结尾
- `skill_id`：必须与 `manifest.json` 中的 `skill_id` 完全一致
- `subject_id`：被操作对象的 ID（技能条目 ID 或经验 ID）
- `actor`：执行操作的 Agent 标识（例如 `"claude-opus-4"`, `"gpt-4o"`）
- `details`：事件特定的详情对象，内容因 `event_type` 而异

---

## 6. 治理（Governance）

### 6.1 模式检测

读取 `manifest.json` → `governance.mode`：

```
IF governance.mode == "standalone"
  → 执行第 6.2 节
ELSE IF governance.mode == "governed"
  → 执行第 6.3 节
```

### 6.2 Standalone 模式（自治）

在 standalone 模式下，Agent 拥有完全自主权限：

- 直接执行学习循环（第 5 节）的所有步骤
- 技能库变更无需外部批准
- 所有决策通过审计日志记录，确保可追溯性
- IF `manifest.metadata.contract.auto_promote` 为 `true`（默认）：
  - 自动应用所有通过置信度门控的技能变更
- IF `auto_promote` 为 `false`：
  - 向用户展示拟议变更，等待用户确认后再执行

### 6.3 Governed 模式（受治理）

在 governed 模式下，技能库变更需要 governor 批准：

**步骤 1：创建 SkillProposal**

当学习循环产生 ADD / MERGE / SUPERSEDE / SYNTHESIZE 决策时，不直接修改技能库，而是创建提案文档：

```json
{
  "proposal_id": "prop-{生成12个十六进制字符}",
  "created_at": "{ISO 8601 UTC}",
  "skill_id": "{来自 manifest.json}",
  "proposed_action": "{ADD|MERGE|SUPERSEDE|SYNTHESIZE}",
  "proposed_changes": {
    "skill_entry_id": "{目标技能条目 ID，ADD 时为新 ID}",
    "title": "{技能标题}",
    "content": "{拟议的技能内容}",
    "version": "{拟议的版本号}"
  },
  "justification": {
    "experience_ids": ["{支持此提案的经验 ID}"],
    "lesson": "{核心经验教训}",
    "confidence": 0.0,
    "reasoning": "{为什么建议此变更}"
  },
  "status": "pending"
}
```

**步骤 2：写审计条目**

```
event_type = "proposal_created"
```

**步骤 3：等待 governor 决策**

提案创建后，暂停技能库修改。Governor 可以通过协议兼容的接口返回决策：

```
IF governor 决策 == "accepted"
  → 执行提案中描述的变更（遵循第 5.5 节流程）
  → 写审计条目：event_type = "proposal_accepted"

ELSE IF governor 决策 == "rejected"
  → 不修改技能库
  → 写审计条目：event_type = "proposal_rejected"
  → 可选：记录拒绝原因供未来参考

ELSE IF governor 决策 == "modified"
  → 应用 governor 修改后的变更
  → 写审计条目：event_type = "governance_decision"
```

---

## 7. 回滚（Rollback）

### 7.1 创建快照（Create Snapshot）

**触发时机：** 每次技能库变更前必须创建（第 5.5 节步骤 1）。

**JSON 模板：**

```json
{
  "snapshot_id": "snap-{生成12个十六进制字符}",
  "created_at": "{ISO 8601 UTC}",
  "reason": "{创建原因，例如 'before skill bank mutation: ADD skl-a1b2c3d4e5f6'}",
  "manifest": {
    // manifest.json 的完整内容拷贝
  },
  "skill_bank": {
    // skill_bank.json 的完整内容拷贝
  }
}
```

**文件路径：** `snapshots/snap-{id}.json`

**字段规则：**
- `snapshot_id`：格式 `snap-{12个十六进制字符}`，从 uuid4 截取
- `reason`：必须说明为什么创建此快照（哪个操作触发的）
- `manifest`：`manifest.json` 的完整 JSON 对象拷贝
- `skill_bank`：`skill_bank.json` 的完整 JSON 对象拷贝

### 7.2 从快照恢复（Restore from Snapshot）

当需要回滚时（用户请求、发现错误、governor 要求等）：

```
1. 确定要恢复到的快照
   → 读取 snapshots/ 目录中的快照文件
   → 根据 created_at 时间戳或 snapshot_id 选择目标快照

2. 读取快照文件
   → 解析 manifest 和 skill_bank 字段

3. 覆盖当前文件
   → 将 snapshot.manifest 写入 manifest.json
   → 将 snapshot.skill_bank 写入 skill_bank.json

4. 写审计条目
   → event_type = "rollback_executed"
   → details.snapshot_id = "{使用的快照 ID}"
   → details.reason = "{回滚原因}"
```

---

## 8. 文件格式参考

本节汇总所有 JSON 文件的完整模板，供快速查阅。

### 8.1 manifest.json

```json
{
  "skill_id": "my-skill",
  "name": "My Skill",
  "version": "0.1.0",
  "description": "A skill that does something useful.",
  "protocol_version": "1.0.0",
  "metadata": {
    "created_at": "2026-03-31T00:00:00Z",
    "updated_at": "2026-03-31T00:00:00Z",
    "author": "agent-name",
    "contract": {
      "min_feedback_confidence": 0.35,
      "synthesis_threshold": 15,
      "auto_promote": true,
      "managed_files": [
        {
          "path": "relative/path/to/file",
          "kind": "markdown"
        }
      ]
    }
  },
  "governance": {
    "mode": "standalone"
  }
}
```

### 8.2 skill_bank.json

```json
{
  "skills": [
    {
      "skill_entry_id": "skl-a1b2c3d4e5f6",
      "title": "Effective code review practices",
      "content": "- Always check for edge cases in boundary conditions\n- Verify error handling covers all failure modes\n- Suggest specific improvements, not vague critiques",
      "version": "0.1.2",
      "task_signature": "code_review",
      "keywords": ["review", "code quality", "feedback"],
      "source_experience_ids": ["exp-111111111111", "exp-222222222222"],
      "updated_at": "2026-03-31T14:30:00Z"
    }
  ]
}
```

### 8.3 经验条目（Experience Item）

```json
{
  "experience_id": "exp-a1b2c3d4e5f6",
  "skill_id": "my-skill",
  "recorded_at": "2026-03-31T14:30:00Z",
  "task_signature": "code_review",
  "lesson": "When reviewing async code, always verify that all promises have proper error handling with .catch() or try/catch blocks.",
  "feedback_status": "positive",
  "feedback_source": "explicit",
  "feedback_confidence": 0.9,
  "execution_id": "exec-optional-reference"
}
```

### 8.4 审计条目（Audit Entry）

```json
{
  "audit_id": "aud-a1b2c3d4e5f6",
  "created_at": "2026-03-31T14:31:00Z",
  "event_type": "skill_merged",
  "skill_id": "my-skill",
  "subject_id": "skl-a1b2c3d4e5f6",
  "actor": "claude-opus-4",
  "details": {
    "action": "MERGE",
    "lesson": "When reviewing async code, always verify promise error handling.",
    "confidence": 0.9,
    "reasoning": "New lesson complements existing code review skill without contradiction."
  }
}
```

### 8.5 快照（Snapshot）

```json
{
  "snapshot_id": "snap-a1b2c3d4e5f6",
  "created_at": "2026-03-31T14:29:00Z",
  "reason": "before skill bank mutation: MERGE into skl-a1b2c3d4e5f6",
  "manifest": {
    "skill_id": "my-skill",
    "name": "My Skill",
    "version": "0.1.0",
    "description": "...",
    "protocol_version": "1.0.0",
    "metadata": { "..." : "..." },
    "governance": { "mode": "standalone" }
  },
  "skill_bank": {
    "skills": [ "..." ]
  }
}
```

---

## 9. 规则与常量

| 规则 | 值 | 说明 |
|---|---|---|
| 置信度门控（confidence gate） | `0.35` | `manifest.metadata.contract.min_feedback_confidence` 的默认值。低于此值的反馈仅记录经验，不修改技能库。 |
| 合成阈值（synthesis threshold） | `15` | `manifest.metadata.contract.synthesis_threshold` 的默认值。技能 content 中要点数超过此值时触发合成压缩。 |
| 快照前置规则 | **必须** | 任何技能库变更前必须创建快照，无例外。 |
| ID 格式 — 技能条目 | `skl-{12 hex}` | 从 uuid4 截取 12 个十六进制字符。正则：`^skl-[a-f0-9]{12}$` |
| ID 格式 — 经验 | `exp-{12 hex}` | 从 uuid4 截取 12 个十六进制字符。正则：`^exp-[a-f0-9]{12}$` |
| ID 格式 — 审计 | `aud-{12 hex}` | 从 uuid4 截取 12 个十六进制字符。正则：`^aud-[a-f0-9]{12}$` |
| ID 格式 — 快照 | `snap-{12 hex}` | 从 uuid4 截取 12 个十六进制字符。正则：`^snap-[a-f0-9]{12}$` |
| ID 格式 — 提案 | `prop-{12 hex}` | 从 uuid4 截取 12 个十六进制字符。正则：`^prop-[a-f0-9]{12}$` |
| ID 格式 — skill_id | `^[a-z0-9][a-z0-9._-]*$` | 小写字母、数字、点、连字符、下划线。必须以字母或数字开头。 |
| 时间戳格式 | ISO 8601 UTC | 所有时间戳必须以 `Z` 结尾。例如：`2026-03-31T14:30:00Z` |
| 版本号格式 | 语义化版本 | `MAJOR.MINOR.PATCH`。正则：`^\d+\.\d+\.\d+$` |
| 版本递增 — MERGE | 补丁递增 | `0.1.0` → `0.1.1` |
| 版本递增 — SUPERSEDE | 次版本递增 | `0.1.1` → `0.2.0` |
| 版本递增 — SYNTHESIZE | 补丁递增 | `0.2.3` → `0.2.4` |
| 版本递增 — ADD | 初始版本 | 新条目始终为 `0.1.0` |
| 丢弃标记 — 英文 | `"one-off"`, `"temporary"`, `"do not reuse"`, `"ignore this"` | 经验教训中包含这些词时触发 DISCARD |
| 丢弃标记 — 中文 | `"一次性"`, `"临时"`, `"不要复用"`, `"忽略这次"` | 经验教训中包含这些词时触发 DISCARD |
| 偏好标记 — 英文 | `"always"`, `"never"`, `"should"`, `"avoid"`, `"prefer"`, `"must"`, `"do not"` | 用户输入中包含这些词时提取为偏好反馈 |
| 偏好标记 — 中文 | `"每次都"`, `"必须"`, `"不要"`, `"避免"`, `"优先"`, `"总是"`, `"绝不"` | 用户输入中包含这些词时提取为偏好反馈 |
| 反馈置信度 — explicit | `0.9` | 用户显式陈述 |
| 反馈置信度 — user_input | `0.8` | 从偏好标记推断 |
| 反馈置信度 — execution_result (failure) | `0.7` | 执行失败 |
| 反馈置信度 — execution_result (success) | `0.6` | 执行成功且有改进 |
| 反馈置信度 — default | `0.2` | 无明显信号 |
| 技能检索数量 | 3-5 | 每次任务执行时选择的最相关技能数量 |
| JSON 缩进 | 2 空格 | 所有 JSON 文件使用 2 空格缩进 |
| 治理模式 | `standalone` 或 `governed` | manifest.json → governance.mode |
| managed_files.kind | `markdown`, `code`, `config`, `other` | 受管文件的类型分类 |

---

## 10. 协议兼容性

本套件兼容 **Skill Evolution Protocol v1.0.0**。

- 协议仓库：[skill-evolution-protocol](https://github.com/d-wwei/skill-evolution-protocol)
- 所有生成的制品（manifest、技能条目、审计记录、快照等）符合协议定义的 JSON Schema
- 治理模式（standalone / governed）遵循协议规范
- 提案格式与 governor 接口兼容

在 governed 模式下，本套件生成的 SkillProposal 可被任何协议兼容的 governor 系统消费和处理。

---

## 11. 研究基础

本项目的核心架构受两篇开创性学术论文的启发：

### AutoSkill — 基于经验的终身学习中的技能自进化

- **作者**：华东师范大学 ICALK 实验室 & 上海人工智能实验室
- **论文**：[arXiv:2603.01145](https://arxiv.org/abs/2603.01145)
- **代码**：[ECNU-ICALK/AutoSkill](https://github.com/ECNU-ICALK/AutoSkill)

AutoSkill 提出了**双循环架构**：左循环检索相关技能并执行任务，右循环从交互中提取新技能并决定添加、合并或丢弃。每次用户交互都应让系统变得更好。

### XSKILL — 多模态 Agent 中基于经验和技能的持续学习

- **作者**：香港科技大学、浙江大学 & 华中科技大学
- **论文**：[arXiv:2603.12056](https://arxiv.org/abs/2603.12056)
- **代码**：[XSkill-Agent/XSkill](https://github.com/XSkill-Agent/XSkill)
- **项目主页**：[xskill-agent.github.io](https://xskill-agent.github.io/xskill_page/)

XSKILL 引入了**双流知识系统**——技能库（结构化程序，如驾驶手册）和经验库（上下文化行动提示，如驾驶直觉），以及**跨 rollout 批评**机制，通过比较多次执行尝试来提取因果性经验教训。

### 概念映射

| 概念 | 来源 | 本套件中的实现 |
|---|---|---|
| 双循环架构 | AutoSkill | 第 4 节（执行循环）+ 第 5 节（学习循环） |
| 版本化技能库 | AutoSkill + XSKILL | `skill_bank.json` 中的语义化版本管理 |
| 经验库 | XSKILL | `experience/` 目录中的经验记录 |
| 添加/合并/丢弃决策 | 两者 | 第 5.4 节的决策树（ADD / MERGE / SUPERSEDE / DISCARD） |
| 执行时技能检索 | AutoSkill | 第 4.1 节的语义匹配检索 |
| 层次化合成 | XSKILL | 第 5.4 节的 SYNTHESIZE 操作 |
| 置信度过滤 | 两者（隐含） | 第 5.2 节的置信度门控 |

### 超越论文的工程化扩展

论文描述的是研究框架。本套件是面向生产环境的工程实现，增加了：

- **协议兼容性** — 所有制品符合 Skill Evolution Protocol schema
- **Agent-Native 范式** — 零外部依赖，Agent 自身作为运行时
- **治理模式** — governor 审批机制，适用于需要外部权限控制的场景
- **审计和溯源** — 所有决策留下不可变的审计记录
- **回滚能力** — 快照机制支持操作恢复
- **多语言支持** — 英文和中文的偏好检测和丢弃标记
