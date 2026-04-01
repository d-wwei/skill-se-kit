# Standalone Evolution Walkthrough

This walkthrough demonstrates a complete standalone skill evolution cycle from initialization to rollback.

## Scenario

A web scraping skill executes a task, encounters a failure, learns from it, and evolves.

---

## Step 1: Initialize Workspace

Create the workspace structure:

```
my-scraper-skill/
  manifest.json
  skill_bank.json
  experience/
  audit/
  snapshots/
```

**manifest.json:**
```json
{
  "schema_name": "SkillManifest",
  "schema_version": "1.0.0",
  "protocol_version": "1.0.0",
  "skill_id": "web-scraper.skill",
  "name": "Web Scraper Skill",
  "version": "0.1.0",
  "governance": { "mode": "standalone", "official_status": "local" },
  "capability": { "level": "native", "summary": "Web scraping with browser automation" },
  "compatibility": { "min_protocol_version": "1.0.0", "max_protocol_version": "1.0.0" },
  "metadata": {
    "owner": "dev-team",
    "contract": {
      "min_feedback_confidence": 0.35,
      "synthesis_threshold": 15,
      "auto_promote": true,
      "managed_files": [{"path": "SKILL.md", "kind": "markdown"}]
    }
  }
}
```

**skill_bank.json:**
```json
{"skills": []}
```

---

## Step 2: First Execution (Left Loop)

**Task:** Scrape product prices from an e-commerce site with lazy-loaded content.

1. **Retrieve skills** — Skill bank is empty, proceed without guidance.
2. **Execute** — Agent runs the scraping task.
3. **Result:** Failure. The scraper extracted 0 products because content was lazy-loaded and not present in initial DOM.

---

## Step 3: Learn from Failure (Right Loop)

### 3.1 Extract Feedback

The execution failed, so:
```
status: "negative"
lesson: "Lazy-loaded content requires waiting for network idle or specific selectors before extraction. Initial DOM snapshot misses dynamically inserted elements."
source: "execution_result"
confidence: 0.7
```

### 3.2 Confidence Gate

0.7 >= 0.35 (min_feedback_confidence) → **proceed with learning**.

### 3.3 Record Experience

Write `experience/exp-a1b2c3d4e5f6.json`:
```json
{
  "experience_id": "exp-a1b2c3d4e5f6",
  "skill_id": "web-scraper.skill",
  "recorded_at": "2026-03-31T10:00:00Z",
  "task_signature": "web_scraping_lazy_content",
  "lesson": "Lazy-loaded content requires waiting for network idle or specific selectors before extraction.",
  "feedback_status": "negative",
  "feedback_source": "execution_result",
  "feedback_confidence": 0.7,
  "execution_id": "exec-001"
}
```

### 3.4 Skill Update Decision

- No discard tokens in lesson → continue
- Scan skill bank → empty → no match
- **Decision: ADD**

### 3.5 Create Snapshot

Write `snapshots/snap-b2c3d4e5f6a7.json`:
```json
{
  "snapshot_id": "snap-b2c3d4e5f6a7",
  "created_at": "2026-03-31T10:00:01Z",
  "reason": "Before adding new skill from execution failure",
  "manifest": {"schema_name": "SkillManifest", "...": "..."},
  "skill_bank": {"skills": []}
}
```

### 3.6 Mutate Skill Bank

Add new skill entry to `skill_bank.json`:
```json
{
  "skills": [
    {
      "skill_entry_id": "skl-c3d4e5f6a7b8",
      "title": "Handle lazy-loaded content in web scraping",
      "content": "- Wait for network idle or specific selectors before extracting content\n- Initial DOM snapshot may miss dynamically inserted elements\n- Use waitForSelector() with appropriate timeout for lazy-loaded content",
      "version": "0.1.0",
      "task_signature": "web_scraping_lazy_content",
      "keywords": ["lazy-load", "dynamic", "waitForSelector", "network-idle"],
      "source_experience_ids": ["exp-a1b2c3d4e5f6"],
      "updated_at": "2026-03-31T10:00:02Z"
    }
  ]
}
```

### 3.7 Write Audit Entry

Write `audit/aud-d4e5f6a7b8c9.json`:
```json
{
  "audit_id": "aud-d4e5f6a7b8c9",
  "created_at": "2026-03-31T10:00:02Z",
  "event_type": "skill_added",
  "skill_id": "web-scraper.skill",
  "subject_id": "skl-c3d4e5f6a7b8",
  "actor": "claude-opus-4-6",
  "details": {
    "action": "ADD",
    "lesson": "Lazy-loaded content requires waiting for network idle or specific selectors.",
    "confidence": 0.7,
    "reasoning": "No existing skill matched. Created new skill for lazy-load handling."
  },
  "evidence_refs": ["experience/exp-a1b2c3d4e5f6.json"]
}
```

---

## Step 4: Second Execution (with Learned Skill)

**Task:** Scrape product prices from another e-commerce site (also lazy-loaded).

1. **Retrieve skills** — Found: "Handle lazy-loaded content in web scraping" (semantic match to "scrape products from lazy-loaded page").
2. **Inject guidance:**
   ```
   === Skill Guidance (from evolution history) ===
   [1] Handle lazy-loaded content in web scraping (v0.1.0)
   - Wait for network idle or specific selectors before extracting content
   - Initial DOM snapshot may miss dynamically inserted elements
   - Use waitForSelector() with appropriate timeout for lazy-loaded content
   ===
   ```
3. **Execute** — Agent waits for network idle, then extracts. **Success:** 47 products scraped.

---

## Step 5: Learn from Success

Feedback:
```
status: "positive"
lesson: "Network idle wait combined with product card selector verification reliably handles lazy-loaded e-commerce content."
source: "execution_result"
confidence: 0.6
```

Skill update decision:
- No discard tokens
- Matches existing skill "Handle lazy-loaded content" → compatible → **MERGE**

After merge, the skill becomes:
```json
{
  "skill_entry_id": "skl-c3d4e5f6a7b8",
  "title": "Handle lazy-loaded content in web scraping",
  "content": "- Wait for network idle or specific selectors before extracting content\n- Initial DOM snapshot may miss dynamically inserted elements\n- Use waitForSelector() with appropriate timeout for lazy-loaded content\n- Network idle wait combined with product card selector verification reliably handles lazy-loaded e-commerce content",
  "version": "0.1.1",
  "...": "..."
}
```

---

## Step 6: Rollback (if needed)

If the merged skill causes regressions:

1. Find the most recent snapshot: `snapshots/snap-b2c3d4e5f6a7.json`
2. Restore: overwrite `manifest.json` and `skill_bank.json` with snapshot copies
3. Write audit entry:
   ```json
   {
     "audit_id": "aud-e5f6a7b8c9d0",
     "event_type": "rollback_executed",
     "details": {
       "snapshot_id": "snap-b2c3d4e5f6a7",
       "reason": "Merged skill caused regression in static page scraping"
     }
   }
   ```

---

## Summary

This walkthrough demonstrated:
1. **Initialize** — workspace from template
2. **Execute** — task with skill retrieval (empty on first run)
3. **Learn** — extract feedback, record experience, decide ADD
4. **Evolve** — create snapshot, mutate skill bank, audit
5. **Re-execute** — with learned skill guidance
6. **Refine** — MERGE compatible lesson into existing skill
7. **Rollback** — restore from snapshot if needed
