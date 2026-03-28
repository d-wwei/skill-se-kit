# @skill-se-kit/adapter

TypeScript/JavaScript client for the [Skill-SE-Kit](https://github.com/d-wwei/skill-se-kit) HTTP sidecar.

## Prerequisites

Start the sidecar server:

```bash
pip install skill-se-kit
skill-se-kit init --skill-root /path/to/skill --protocol-root /path/to/protocol
skill-se-kit serve --skill-root /path/to/skill --port 9780
```

## Install

```bash
npm install @skill-se-kit/adapter
```

## Usage

```typescript
import { SkillSEKit } from '@skill-se-kit/adapter';

const kit = new SkillSEKit({ port: 9780 });

// Execute a skill turn with feedback
const result = await kit.run(
  { task: 'browse', url: 'https://example.com' },
  {
    status: 'positive',
    lesson: 'Use page.evaluate() to pierce shadow DOM',
    source: 'explicit',
    confidence: 0.9,
  }
);

// Read learned skills for prompt injection
const bank = await kit.getSkills();
const guidance = bank.skills.map(s => s.content).join('\n');

// Check evolution report
const report = await kit.getReport();

// Rollback if needed
await kit.rollback('snapshot-xxxx');
```

## API

| Method | Description |
|--------|-------------|
| `kit.health()` | Health check — version and status |
| `kit.run(input, feedback?, context?)` | Execute + learn |
| `kit.getSkills()` | Get current skill bank |
| `kit.getReport()` | Latest evolution summary (text) |
| `kit.getReportJson()` | Latest evolution report (JSON) |
| `kit.rollback(snapshotId)` | Revert to snapshot |

## Types

All types are exported and align with `schemas/feedback.schema.json` and `schemas/run-result.schema.json`.

```typescript
import type { Feedback, RunResult, SkillBank, SkillEntry } from '@skill-se-kit/adapter';
```

## Requirements

- Node.js >= 18 (uses built-in `fetch`)
- `skill-se-kit serve` running on localhost
