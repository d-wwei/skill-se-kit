# Skill Self-Evolution Kit (Agent-Native)

## 1. Overview

This document is the complete operational specification for the Agent-Native Skill Self-Evolution Kit. Any AI agent that reads this file gains the ability to manage self-evolving skills through structured file operations.

**Agent-Native paradigm**: The agent IS the runtime. There are no external libraries, no daemon processes, no programmatic dependencies. The agent reads JSON files, applies semantic reasoning, makes decisions via decision trees defined here, and writes JSON files. All matching, scoring, and synthesis operations use the agent's native language understanding rather than algorithmic implementations.

**Protocol compatibility**: All artifacts produced by this kit conform to the [Skill Evolution Protocol](https://github.com/d-wwei/skill-evolution-protocol) v1.0.0. Manifests, proposals, and experience records can interoperate with any protocol-compliant system.

**Architecture**: Dual-loop design inspired by AutoSkill (ECNU ICALK Lab & Shanghai AI Lab) and XSKILL (HKUST, Zhejiang, HUST).
- **Left Loop (Execution)**: Retrieve relevant skills, inject as context, execute task.
- **Right Loop (Learning)**: Extract feedback, record experience, update skill bank.

---

## 2. Quick Start

1. Initialize workspace (Section 3.1).
2. Execute a task with the Execution Loop (Section 4).
3. After execution, run the Learning Loop (Section 5).
4. On next task, the Execution Loop retrieves accumulated skills automatically.

Minimum viable cycle: init workspace, execute one task, extract one lesson, write one skill entry.

---

## 3. Workspace

### 3.1 Initialize New Workspace

Create the following directory structure:

```
{workspace_root}/
  manifest.json
  skill_bank.json
  experience/
  audit/
  snapshots/
```

**Step 1**: Create directories.

```
experience/
audit/
snapshots/
```

**Step 2**: Create `manifest.json` from this template:

```json
{
  "schema_name": "SkillManifest",
  "schema_version": "1.0.0",
  "protocol_version": "1.0.0",
  "skill_id": "{lowercase-kebab-case-identifier}",
  "name": "{Human Readable Skill Name}",
  "version": "0.1.0",
  "description": "{What this skill does}",
  "governance": {
    "mode": "standalone",
    "official_status": "local"
  },
  "capability": {
    "level": "native",
    "summary": "{Brief capability description}"
  },
  "compatibility": {
    "min_protocol_version": "1.0.0",
    "max_protocol_version": "1.0.0"
  },
  "metadata": {
    "owner": "{owner identifier}",
    "contract": {
      "min_feedback_confidence": 0.35,
      "synthesis_threshold": 15,
      "auto_promote": true,
      "managed_files": [
        {"path": "SKILL.md", "kind": "markdown"}
      ]
    }
  }
}
```

**Step 3**: Create `skill_bank.json`:

```json
{
  "skills": []
}
```

**Step 4**: Determine governance mode.

```
IF the skill operates independently (single agent, personal workspace)
  → Set governance.mode = "standalone"

ELSE IF the skill is part of a multi-agent system or requires approval workflow
  → Set governance.mode = "governed"
  → See Section 6.3 for governed mode behavior
```

### 3.2 Resume Existing Workspace

```
1. Read manifest.json
   IF file is missing or unparseable
     → ABORT. Workspace is corrupt. Re-initialize (Section 3.1).

2. Validate manifest structure:
   - REQUIRED fields: schema_name, skill_id, version, governance.mode
   IF any required field is missing
     → ABORT. Manifest is invalid.

3. Read skill_bank.json
   IF file is missing
     → Create empty skill bank: {"skills": []}
   IF file is unparseable
     → ABORT. Skill bank is corrupt. Restore from latest snapshot (Section 7.2).

4. Verify directory existence: experience/, audit/, snapshots/
   IF any directory is missing
     → Create it.

5. Workspace is ready. Proceed to Execution Loop (Section 4).
```

---

## 4. Execution Loop (Left Loop)

Execute Sections 4.1 through 4.3 in sequence for every task.

### 4.1 Skill Retrieval

```
1. Read skill_bank.json → extract the skills array.

2. IF skills array is empty
     → Set skill_guidance = "" (empty string)
     → Proceed to Section 4.3

3. FOR each skill entry in the skills array:
     Score the entry against the current task using these signals:
     a. task_signature exact or partial match (highest weight)
     b. keywords overlap with task description
     c. Semantic similarity between skill content and task context

4. Rank all skill entries by relevance score (descending).

5. Select the top N entries where N = min(5, number of entries with non-trivial relevance).
   IF no entries have meaningful relevance
     → Set skill_guidance = "" (empty string)

6. Proceed to Section 4.2 with selected entries.
```

### 4.2 Context Injection

Format selected skill entries into a guidance block using this template:

```
=== Skill Guidance (from evolution history) ===
[1] {title} (v{version})
{content}

[2] {title} (v{version})
{content}

[N] {title} (v{version})
{content}
=== End Skill Guidance ===
```

Inject this block into the execution context before task processing. The agent treats this as advisory context, not hard constraints.

### 4.3 Task Execution

Execute the task with the enriched context from Section 4.2. Retain the execution result (output, errors, user responses) in session memory for the Learning Loop.

---

## 5. Learning Loop (Right Loop)

Execute Sections 5.1 through 5.6 in sequence after task execution completes.

### 5.1 Feedback Extraction

Apply the following decision tree to extract structured feedback from the execution:

```
IF explicit user feedback is present
   (user stated: "this worked", "this failed", "the problem was...", "good job on...",
    "这个有效", "这个有问题", "失败原因是...")
  → status   = infer from user statement ("positive" or "negative")
  → lesson   = user's stated insight, normalized to a reusable guideline
  → source   = "explicit"
  → confidence = 0.9

ELSE IF execution produced an error, exception, or observable failure
  → status   = "negative"
  → lesson   = what went wrong and how to avoid it in future executions
  → source   = "execution_result"
  → confidence = 0.7

ELSE IF execution succeeded with observable improvement over previous attempts
  → status   = "positive"
  → lesson   = what worked well and should be repeated
  → source   = "execution_result"
  → confidence = 0.6

ELSE IF user input contains preference markers:
   English: "always", "never", "should", "avoid", "prefer", "make sure", "don't"
   Chinese: "每次都", "必须", "不要", "避免", "优先", "一定要", "千万别"
  → status   = "positive"
  → lesson   = normalized preference statement (rewrite as a directive)
  → source   = "user_input"
  → confidence = 0.8

ELSE
  → status   = "positive"
  → lesson   = "No specific insight extracted. Current approach maintained."
  → source   = "default"
  → confidence = 0.2
```

The output is a Feedback object: `{status, lesson, source, confidence}`.

### 5.2 Confidence Gate

```
Read manifest.json → metadata.contract.min_feedback_confidence
  IF value is absent → use default: 0.35

IF feedback.confidence < min_feedback_confidence
  → Record experience (Section 5.3)
  → Write audit entry:
      event_type = "experience_recorded"
      details.action = "GATE_BLOCKED"
      details.reasoning = "Confidence {feedback.confidence} below threshold {min_feedback_confidence}"
  → DO NOT proceed to Section 5.4
  → STOP the Learning Loop here

ELSE
  → Proceed to Section 5.3
```

### 5.3 Record Experience

Create an experience item and write it to the `experience/` directory.

**Generate the experience item**:

```json
{
  "experience_id": "exp-{12 lowercase hex chars}",
  "skill_id": "{value from manifest.json skill_id}",
  "recorded_at": "{current UTC time in ISO 8601, e.g., 2026-03-31T14:30:00Z}",
  "task_signature": "{normalized task type, e.g., 'code_review', 'data_analysis', 'report_writing'}",
  "lesson": "{the extracted lesson from Section 5.1}",
  "feedback_status": "{positive|negative}",
  "feedback_source": "{explicit|user_input|execution_result|default}",
  "feedback_confidence": 0.0
}
```

**Write** to file path: `experience/{experience_id}.json`

**Write audit entry**:
```
event_type = "experience_recorded"
subject_id = "{experience_id}"
details.action = "RECORD"
details.lesson = "{lesson text}"
details.confidence = {confidence value}
```

Proceed to Section 5.4.

### 5.4 Skill Update Decision

Apply the following decision tree to determine how the skill bank should change.

```
STEP 1: Check for discard tokens.

  IF lesson contains ANY of these tokens (case-insensitive):
     "one-off", "temporary", "do not reuse", "ignore this",
     "one time", "just this once",
     "一次性", "临时", "不要复用", "忽略这次", "仅此一次"
    → ACTION = DISCARD
    → Write audit entry:
        event_type = "skill_discarded"
        details.action = "DISCARD"
        details.reasoning = "Lesson contains discard token"
    → STOP. Do not proceed further.


STEP 2: Search for semantic matches in skill bank.

  Read skill_bank.json → skills array.

  FOR each existing skill entry:
    Using semantic understanding, judge:
    Does this new lesson address the SAME topic, domain, or task pattern
    as the existing skill entry?

    Consider: title similarity, content overlap, task_signature match,
    keyword intersection.

  Classify the best match (if any) into one of:
    a. NO_MATCH    — no existing skill covers this topic
    b. COMPATIBLE  — an existing skill covers this topic, and the new lesson
                     adds to or reinforces existing advice without contradiction
    c. CONTRADICT  — an existing skill covers this topic, but the new lesson
                     contradicts or invalidates existing advice


STEP 3: Determine action.

  IF classification = NO_MATCH
    → ACTION = ADD
    → Create new skill entry:
        {
          "skill_entry_id": "skl-{12 lowercase hex chars}",
          "title": "{concise one-line summary of the lesson}",
          "content": "- {lesson as a bullet point}",
          "version": "0.1.0",
          "task_signature": "{normalized task type}",
          "keywords": ["{keyword1}", "{keyword2}", "{keyword3}"],
          "source_experience_ids": ["{experience_id}"],
          "updated_at": "{current UTC ISO 8601}"
        }

  ELSE IF classification = COMPATIBLE
    → ACTION = MERGE
    → Target: the matched skill entry
    → Append new bullet point(s) to existing content field
    → Bump PATCH version: x.y.z → x.y.(z+1)
    → Append experience_id to source_experience_ids array
    → Update updated_at to current UTC timestamp

  ELSE IF classification = CONTRADICT
    → ACTION = SUPERSEDE
    → Target: the matched skill entry
    → Rewrite the content field with the corrected understanding
    → Preserve any non-contradicted bullets from the original
    → Bump MINOR version: x.y.z → x.(y+1).0
    → Append experience_id to source_experience_ids array
    → Update updated_at to current UTC timestamp


STEP 4: Check synthesis threshold.

  AFTER any ADD, MERGE, or SUPERSEDE action:

  Count the number of bullet points in the affected skill entry's content.
  (Count lines matching the pattern "^- " or "^  - ".)

  Read manifest.json → metadata.contract.synthesis_threshold
    IF value is absent → use default: 15

  IF bullet_count > synthesis_threshold
    → ACTION = SYNTHESIZE (applied after the primary action)
    → Compress the content:
        1. Remove exact duplicate bullets
        2. Merge bullets that express the same idea in different words
        3. Abstract specific examples into general patterns where possible
        4. Retain the most general and reusable formulations
    → Bump PATCH version: x.y.z → x.y.(z+1)
    → Updated content should have noticeably fewer bullets than before


Proceed to Section 5.5 with the determined action.
```

### 5.5 Mutate Skill Bank

```
BEFORE any mutation, execute ALL of the following in order:

1. Create snapshot (Section 7.1).
   Reason: "Before {ACTION} on skill entry {skill_entry_id or 'new'}"

2. Read current skill_bank.json.

3. Apply the decided action:
   IF ACTION = ADD
     → Append the new skill entry to the skills array

   IF ACTION = MERGE
     → Find the target skill entry by skill_entry_id
     → Update its content, version, source_experience_ids, updated_at

   IF ACTION = SUPERSEDE
     → Find the target skill entry by skill_entry_id
     → Overwrite its content, version, source_experience_ids, updated_at

   IF ACTION = SYNTHESIZE
     → Find the target skill entry by skill_entry_id
     → Replace its content with the synthesized version
     → Update version, updated_at

4. Write the updated skill_bank.json.

5. Write audit entry (Section 5.6).
```

### 5.6 Audit Logging

Write an audit entry for every decision that modifies or intentionally does not modify the skill bank.

**Generate the audit entry**:

```json
{
  "audit_id": "aud-{12 lowercase hex chars}",
  "created_at": "{current UTC ISO 8601}",
  "event_type": "{see event_type table below}",
  "skill_id": "{from manifest.json skill_id}",
  "subject_id": "{the skill_entry_id or experience_id affected}",
  "actor": "{agent model identifier, e.g., 'claude-opus-4-6'}",
  "details": {
    "action": "{ADD|MERGE|SUPERSEDE|DISCARD|SYNTHESIZE|RECORD|GATE_BLOCKED}",
    "lesson": "{the lesson text}",
    "confidence": 0.0,
    "reasoning": "{why this decision was made}"
  }
}
```

**Event type mapping**:

| Action     | event_type         |
|------------|--------------------|
| ADD        | skill_added        |
| MERGE      | skill_merged       |
| SUPERSEDE  | skill_superseded   |
| DISCARD    | skill_discarded    |
| SYNTHESIZE | skill_synthesized  |
| RECORD     | experience_recorded|
| GATE_BLOCKED | experience_recorded |

**Write** to file path: `audit/{audit_id}.json`

---

## 6. Governance

### 6.1 Mode Detection

```
Read manifest.json → governance.mode

IF governance.mode = "standalone"
  → Follow Section 6.2

ELSE IF governance.mode = "governed"
  → Follow Section 6.3

ELSE
  → Default to "standalone"
```

### 6.2 Standalone Mode

In standalone mode, the agent has full authority over the skill bank. The Learning Loop (Section 5) executes directly: experience is recorded, skill bank is mutated, and audit entries are written without external approval.

```
Read manifest.json → metadata.contract.auto_promote

IF auto_promote = true (default)
  → All skill bank mutations apply immediately after snapshot

IF auto_promote = false
  → Write proposed changes to audit/ as a proposal (Section 6.3 format)
  → Apply the mutation immediately afterward
  → The proposal serves as a detailed change record, not a gate
```

### 6.3 Governed Mode

In governed mode, skill bank mutations require governor approval. The Learning Loop diverges after Section 5.4 (Skill Update Decision).

**Instead of executing Section 5.5 directly**:

```
STEP 1: Create a SkillProposal document.

  {
    "schema_name": "SkillProposal",
    "schema_version": "1.0.0",
    "protocol_version": "1.0.0",
    "proposal_id": "prop-{12 lowercase hex chars}",
    "skill_id": "{from manifest.json skill_id}",
    "created_at": "{current UTC ISO 8601}",
    "proposer": {
      "authority": "local",
      "id": "{agent identifier}"
    },
    "status": "candidate",
    "proposal_type": "{new_skill|skill_update}",
    "base_version": "{current manifest.json version}",
    "target_version": "{version after proposed change}",
    "change_summary": "{description of proposed change}",
    "proposed_action": "{ADD|MERGE|SUPERSEDE|SYNTHESIZE}",
    "proposed_payload": {
      "{the skill entry to add or the updated fields}"
    },
    "artifacts": [
      {
        "type": "evidence",
        "ref": "{experience_id}"
      }
    ]
  }

STEP 2: Write proposal to audit/{proposal_id}.json

STEP 3: Write audit entry.
  event_type = "proposal_created"
  subject_id = "{proposal_id}"
  details.action = "PROPOSE"
  details.reasoning = "Governed mode: awaiting governor decision"

STEP 4: DO NOT mutate skill_bank.json.

STEP 5: When a PromotionDecision document is received:

  IF outcome = "promoted"
    → Create snapshot (Section 7.1)
    → Apply the proposed mutation to skill_bank.json
    → Write audit entry: event_type = "proposal_accepted"

  ELSE IF outcome = "rejected"
    → Write audit entry: event_type = "proposal_rejected"
    → Do not mutate skill_bank.json

  ELSE IF outcome = "deferred"
    → Write audit entry: event_type = "governance_decision", details.action = "DEFERRED"
    → Retain proposal for future processing
```

---

## 7. Rollback

### 7.1 Create Snapshot

**MUST be called before every skill bank mutation.** No exceptions.

```json
{
  "snapshot_id": "snap-{12 lowercase hex chars}",
  "created_at": "{current UTC ISO 8601}",
  "reason": "{why this snapshot was created}",
  "manifest": {},
  "skill_bank": {}
}
```

Populate `manifest` with a complete copy of the current `manifest.json` contents.
Populate `skill_bank` with a complete copy of the current `skill_bank.json` contents.

**Write** to file path: `snapshots/{snapshot_id}.json`

**Write audit entry**:
```
event_type = "snapshot_created"
subject_id = "{snapshot_id}"
details.action = "SNAPSHOT"
details.reasoning = "{reason}"
```

### 7.2 Restore from Snapshot

```
1. Identify the target snapshot.
   IF a specific snapshot_id is provided
     → Read snapshots/{snapshot_id}.json
   ELSE
     → List all files in snapshots/ directory
     → Sort by created_at descending
     → Select the most recent snapshot

2. IF snapshot file is missing or unparseable
     → ABORT. Cannot restore.

3. Overwrite manifest.json with snapshot.manifest

4. Overwrite skill_bank.json with snapshot.skill_bank

5. Write audit entry:
     event_type = "rollback_executed"
     subject_id = "{snapshot_id}"
     details.action = "ROLLBACK"
     details.reasoning = "{why rollback was triggered}"
```

---

## 8. File Format Reference

### 8.1 manifest.json (SkillManifest)

Protocol-compatible skill manifest with embedded evolution contract.

```json
{
  "schema_name": "SkillManifest",
  "schema_version": "1.0.0",
  "protocol_version": "1.0.0",
  "skill_id": "{lowercase-kebab-case, e.g., 'code-review-assistant'}",
  "name": "{Human Readable Name}",
  "version": "0.1.0",
  "description": "{What this skill does}",
  "governance": {
    "mode": "{standalone|governed}",
    "official_status": "local"
  },
  "capability": {
    "level": "native",
    "summary": "{Brief capability description}"
  },
  "compatibility": {
    "min_protocol_version": "1.0.0",
    "max_protocol_version": "1.0.0"
  },
  "metadata": {
    "owner": "{owner identifier}",
    "contract": {
      "min_feedback_confidence": 0.35,
      "synthesis_threshold": 15,
      "auto_promote": true,
      "managed_files": [
        {"path": "SKILL.md", "kind": "markdown"}
      ]
    }
  }
}
```

**Field constraints**:
- `skill_id`: must match pattern `^[a-z0-9][a-z0-9._-]*$`
- `version`: must match pattern `^\d+\.\d+\.\d+$`
- `governance.mode`: one of `"standalone"`, `"governed"`
- `governance.official_status`: one of `"local"`, `"submitted"`, `"official"`, `"deprecated"`

### 8.2 skill_bank.json (SkillBank)

```json
{
  "skills": [
    {
      "skill_entry_id": "skl-{12 lowercase hex chars}",
      "title": "{one-line summary}",
      "content": "- {bullet 1}\n- {bullet 2}\n- {bullet 3}",
      "version": "0.1.0",
      "task_signature": "{normalized task type}",
      "keywords": ["{keyword1}", "{keyword2}"],
      "source_experience_ids": ["{exp-id-1}", "{exp-id-2}"],
      "updated_at": "{ISO 8601 UTC}"
    }
  ]
}
```

**Field constraints**:
- `skill_entry_id`: must match pattern `^skl-[a-f0-9]{12}$`
- `title`: non-empty string
- `content`: non-empty string, formatted as markdown bullet list
- `version`: semver string `^\d+\.\d+\.\d+$`
- `updated_at`: ISO 8601 UTC timestamp ending with `Z`
- `task_signature`, `keywords`, `source_experience_ids`: optional but recommended

### 8.3 Experience Item (ExperienceItem)

```json
{
  "experience_id": "exp-{12 lowercase hex chars}",
  "skill_id": "{from manifest.json}",
  "recorded_at": "{ISO 8601 UTC}",
  "task_signature": "{normalized task type}",
  "lesson": "{reusable insight}",
  "feedback_status": "{positive|negative}",
  "feedback_source": "{explicit|user_input|execution_result|default}",
  "feedback_confidence": 0.0,
  "execution_id": "{optional reference}",
  "reasoning": "{optional detailed reasoning}",
  "cross_rollout_critique": "{optional cross-rollout comparison}",
  "metadata": {}
}
```

**Field constraints**:
- `experience_id`: must match pattern `^exp-[a-f0-9]{12}$`
- `skill_id`: must match pattern `^[a-z0-9][a-z0-9._-]*$`
- `feedback_status`: one of `"positive"`, `"negative"`
- `feedback_source`: one of `"explicit"`, `"user_input"`, `"execution_result"`, `"default"`
- `feedback_confidence`: number in range `[0.0, 1.0]`

File path: `experience/{experience_id}.json`

### 8.4 Audit Entry (AuditEntry)

```json
{
  "audit_id": "aud-{12 lowercase hex chars}",
  "created_at": "{ISO 8601 UTC}",
  "event_type": "{see enumeration below}",
  "skill_id": "{from manifest.json}",
  "subject_id": "{ID of affected entity}",
  "actor": "{agent identifier}",
  "details": {
    "action": "{action name}",
    "lesson": "{lesson text if applicable}",
    "confidence": 0.0,
    "reasoning": "{decision rationale}"
  },
  "evidence_refs": ["{optional file paths or URLs}"]
}
```

**event_type enumeration**:
`skill_added`, `skill_merged`, `skill_superseded`, `skill_discarded`, `skill_synthesized`, `experience_recorded`, `snapshot_created`, `rollback_executed`, `proposal_created`, `proposal_submitted`, `proposal_accepted`, `proposal_rejected`, `governance_decision`, `provenance_source`, `provenance_lineage`

**Field constraints**:
- `audit_id`: must match pattern `^aud-[a-f0-9]{12}$`
- `details`: required, object with arbitrary additional properties

File path: `audit/{audit_id}.json`

### 8.5 Snapshot

```json
{
  "snapshot_id": "snap-{12 lowercase hex chars}",
  "created_at": "{ISO 8601 UTC}",
  "reason": "{why this snapshot was created}",
  "manifest": { "...full copy of manifest.json..." },
  "skill_bank": { "...full copy of skill_bank.json..." }
}
```

**Field constraints**:
- `snapshot_id`: must match pattern `^snap-[a-f0-9]{12}$`
- `reason`: non-empty string
- `manifest`: complete manifest.json object
- `skill_bank`: complete skill_bank.json object

File path: `snapshots/{snapshot_id}.json`

### 8.6 SkillProposal (Governed Mode)

```json
{
  "schema_name": "SkillProposal",
  "schema_version": "1.0.0",
  "protocol_version": "1.0.0",
  "proposal_id": "prop-{12 lowercase hex chars}",
  "skill_id": "{from manifest.json}",
  "created_at": "{ISO 8601 UTC}",
  "proposer": {
    "authority": "local",
    "id": "{agent identifier}"
  },
  "status": "candidate",
  "proposal_type": "{new_skill|skill_update}",
  "base_version": "{current version}",
  "target_version": "{proposed version}",
  "change_summary": "{description}",
  "proposed_action": "{ADD|MERGE|SUPERSEDE|SYNTHESIZE}",
  "proposed_payload": {},
  "artifacts": [
    {
      "type": "evidence",
      "ref": "{experience_id}"
    }
  ]
}
```

File path: `audit/{proposal_id}.json`

---

## 9. Rules and Constants

| Rule | Value | Description |
|------|-------|-------------|
| min_feedback_confidence | 0.35 | Below this threshold, experience is recorded but skill bank is NOT mutated |
| synthesis_threshold | 15 | Trigger synthesis when a skill entry exceeds this many bullet points |
| snapshot-before-mutate | MANDATORY | Always create a snapshot before ANY skill bank mutation |
| ID format | `{prefix}-{12 lowercase hex chars}` | Generate from uuid4().hex[:12]. Prefixes: `skl`, `exp`, `aud`, `snap`, `prop` |
| Timestamp format | ISO 8601 UTC | Always end with `Z`. Example: `2026-03-31T14:30:00Z` |
| Version bump (MERGE) | x.y.z -> x.y.(z+1) | Patch increment for compatible additions |
| Version bump (SUPERSEDE) | x.y.z -> x.(y+1).0 | Minor increment for contradictory rewrites |
| Version bump (SYNTHESIZE) | x.y.z -> x.y.(z+1) | Patch increment for compression |
| Version bump (ADD) | starts at 0.1.0 | New skill entries begin at 0.1.0 |
| Discard tokens (EN) | one-off, temporary, do not reuse, ignore this, one time, just this once | Case-insensitive match against lesson text |
| Discard tokens (ZH) | 一次性, 临时, 不要复用, 忽略这次, 仅此一次 | Match against lesson text |
| Preference markers (EN) | always, never, should, avoid, prefer, make sure, don't | Triggers user_input feedback source |
| Preference markers (ZH) | 每次都, 必须, 不要, 避免, 优先, 一定要, 千万别 | Triggers user_input feedback source |
| Protocol version | 1.0.0 | Compatible Skill Evolution Protocol version |
| Max skill retrieval | 5 | Maximum number of skills injected into execution context |
| Skill bank file | skill_bank.json | Single source of truth for accumulated skills |
| Manifest file | manifest.json | Skill identity, governance, and contract configuration |

---

## 10. Protocol Compatibility

This kit produces artifacts conforming to the [Skill Evolution Protocol](https://github.com/d-wwei/skill-evolution-protocol) v1.0.0.

**Protocol schemas referenced**:

| Protocol Schema | Kit Usage |
|----------------|-----------|
| SkillManifest | `manifest.json` — skill identity, versioning, governance |
| ExperienceRecord | Experience items can be promoted to protocol ExperienceRecords |
| SkillProposal | Governed mode proposals (`audit/{proposal_id}.json`) |
| PromotionDecision | Governor response documents consumed in governed mode |

**Kit-specific schemas** (in `schemas/` directory):

| Schema File | Validates |
|-------------|-----------|
| feedback.schema.json | Feedback extraction output (Section 5.1) |
| skill-bank.schema.json | skill_bank.json structure and skill entries |
| experience-item.schema.json | Experience items in `experience/` |
| snapshot.schema.json | Snapshots in `snapshots/` |
| audit-entry.schema.json | Audit entries in `audit/` |
| skill-contract.schema.json | Contract object in manifest.json metadata |

**Interoperability**: Any tool or agent that reads Skill Evolution Protocol v1.0.0 documents can consume artifacts from this kit. The `schema_name` and `schema_version` fields in manifests and proposals serve as type discriminators.

---

## 11. Research Foundations

This kit implements concepts from two 2025-2026 research papers on agent skill evolution:

**AutoSkill** (ECNU ICALK Lab & Shanghai AI Lab, arXiv:2603.01145)
- Dual-loop architecture: execution loop (left) + skill evolution loop (right)
- Skill management operations: add, merge, discard
- Feedback-driven learning from task execution outcomes

**XSKILL** (HKUST, Zhejiang University, HUST, arXiv:2603.12056)
- Dual-stream design: Skill Library (structured) + Experience Bank (contextual)
- Cross-rollout critique for quality learning across execution attempts
- Experience-to-skill promotion pipeline

**Agent-Native extensions** beyond the original research:
- Replaces programmatic vector matching with agent semantic understanding
- Replaces runtime library dependencies with protocol-driven file operations
- Adds governance modes (standalone/governed) for multi-agent environments
- Adds rollback via immutable snapshots
- Adds full audit trail for every evolution decision
- Adds confidence gating to prevent low-quality skill mutations
- Adds synthesis to prevent unbounded skill growth
