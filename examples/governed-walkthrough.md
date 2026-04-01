# Governed Evolution Walkthrough

This walkthrough demonstrates a governed skill evolution cycle where skill mutations require governor approval.

## Scenario

An investment advisor skill learns a new pattern but cannot self-promote — a governor must approve changes to the skill bank.

---

## Step 1: Workspace State

The skill is already initialized in governed mode:

**manifest.json:**
```json
{
  "schema_name": "SkillManifest",
  "schema_version": "1.0.0",
  "protocol_version": "1.0.0",
  "skill_id": "investment-advisor.skill",
  "name": "Investment Advisor Skill",
  "version": "1.2.0",
  "governance": {
    "mode": "governed",
    "official_status": "official",
    "governor_id": "agent-skill-governor",
    "handshake_required": true
  },
  "capability": { "level": "native", "summary": "Financial analysis" },
  "compatibility": { "min_protocol_version": "1.0.0", "max_protocol_version": "1.0.0" },
  "official_ref": {
    "baseline_version": "1.2.0",
    "promotion_decision_id": "dec-aabbccddeeff"
  },
  "metadata": {
    "owner": "finance-team",
    "contract": {
      "min_feedback_confidence": 0.5,
      "synthesis_threshold": 10,
      "auto_promote": false
    }
  }
}
```

**skill_bank.json** already has 5 skills about market analysis.

---

## Step 2: Execution and Learning

**Task:** Analyze a portfolio with heavy exposure to semiconductor stocks.

1. **Execute** with skill guidance from existing skills
2. **Result:** Analysis missed the impact of export controls on semiconductor supply chain
3. **Feedback extraction:**
   ```
   status: "negative"
   lesson: "When analyzing semiconductor stocks, always check for recent export control policies and trade restrictions that affect supply chain."
   source: "execution_result"
   confidence: 0.75
   ```

---

## Step 3: Confidence Gate

0.75 >= 0.5 (governed mode has higher min_feedback_confidence) → **proceed**.

---

## Step 4: Record Experience

Write `experience/exp-112233445566.json` as normal.

---

## Step 5: Skill Update Decision

- No discard tokens
- Matches existing skill "Sector-specific risk analysis" → compatible → MERGE candidate
- **But governance.mode = "governed"** → cannot directly mutate skill bank

---

## Step 6: Create Proposal (Instead of Direct Mutation)

Write a SkillProposal to `audit/prop-aabbccddeeff.json`:

```json
{
  "schema_name": "SkillProposal",
  "schema_version": "1.0.0",
  "protocol_version": "1.0.0",
  "proposal_id": "prop-aabbccddeeff",
  "skill_id": "investment-advisor.skill",
  "created_at": "2026-03-31T15:00:00Z",
  "proposer": {
    "authority": "local",
    "id": "claude-opus-4-6"
  },
  "status": "candidate",
  "proposal_type": "skill_update",
  "base_version": "1.2.0",
  "target_version": "1.2.1",
  "change_summary": "MERGE: Add export control awareness to sector-specific risk analysis skill. New bullet: 'When analyzing semiconductor stocks, always check for recent export control policies and trade restrictions.'",
  "artifacts": [
    {
      "type": "evidence",
      "ref": "experience/exp-112233445566.json"
    }
  ]
}
```

Write audit entry:
```json
{
  "audit_id": "aud-bbccddeeff11",
  "event_type": "proposal_created",
  "details": {
    "proposal_id": "prop-aabbccddeeff",
    "action": "MERGE",
    "target_skill": "Sector-specific risk analysis",
    "reason": "Governed mode requires proposal — cannot directly mutate skill bank"
  }
}
```

**Skill bank is NOT mutated.** The agent continues using existing skills until governor approves.

---

## Step 7: Governor Decision

The governor (external process) reviews the proposal and writes a PromotionDecision:

```json
{
  "schema_name": "PromotionDecision",
  "schema_version": "1.0.0",
  "protocol_version": "1.0.0",
  "decision_id": "dec-ccddeeff1122",
  "proposal_id": "prop-aabbccddeeff",
  "skill_id": "investment-advisor.skill",
  "decided_at": "2026-03-31T16:00:00Z",
  "decider": {
    "authority": "governor",
    "id": "agent-skill-governor"
  },
  "outcome": "promoted",
  "reason": "Lesson is well-supported by evidence. Export control awareness is critical for semiconductor analysis.",
  "effective_version": "1.2.1",
  "evidence_refs": ["experience/exp-112233445566.json"]
}
```

---

## Step 8: Apply Governor Decision

When the agent detects the governor's decision:

1. **Create snapshot** (mandatory before mutation)
2. **Apply the MERGE** to skill_bank.json
3. **Update manifest.json** version to 1.2.1 and official_ref
4. **Write audit entry** with event_type "proposal_accepted"

---

## Key Differences from Standalone

| Aspect | Standalone | Governed |
|--------|-----------|----------|
| Skill bank mutation | Direct | Requires proposal + governor approval |
| Confidence threshold | 0.35 (default) | Often higher (e.g., 0.5) |
| auto_promote | true | false |
| Governor decision | N/A | PromotionDecision document required |
| Latency | Immediate | Async (wait for governor) |
| Audit trail | Recommended | Mandatory (proposal + decision) |
