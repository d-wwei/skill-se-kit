# Compatibility Issues And TODOs

## Overlay Supersession Field

`overlay.schema.json` requires `supersedes_overlay_id` when an overlay has status `superseded`.

The field name suggests a forward reference, while the lifecycle text suggests the overlay was replaced by a newer overlay. This implementation records the replacing overlay id in `supersedes_overlay_id` on the superseded overlay and treats the schema as authoritative.

## Standalone Promotion Artifact Gap

The protocol defines `PromotionDecision` with `decider.authority=governor` only.

That leaves no protocol object for local standalone promotion receipts. This implementation therefore stores standalone promotion receipts in an implementation-local `.skill_se_kit/local_promotions/` area and does not fabricate protocol `PromotionDecision` objects.

The hidden directory now defaults to `.skill_se_kit`, while the legacy
`.skillkit` location remains readable for backward compatibility even though
the external product name is now `Skill-SE-Kit`.
