# Output Checklist

Use this before handing off to the rest of the team.

## Required Files

- `data/baseline_snapshots.json`
- `data/demo_entity_notes.md`

## Baseline Checklist

For each demo entity:

- [ ] Has a stable `customer_id`.
- [ ] Has a legal or public entity name.
- [ ] Has aliases for searching.
- [ ] Has domicile.
- [ ] Has business area.
- [ ] Has known jurisdictions.
- [ ] Has known products or expected AMINA relationship.
- [ ] Has `last_reviewed_at`.
- [ ] Has one-sentence `demo_story`.
- [ ] Has expected drift types.
- [ ] Has suggested sources for teammate 2.
- [ ] Has AMINA relevance.

## Portfolio Checklist

Across all demo entities:

- [ ] At least 3 entities selected.
- [ ] At least 1 risk drift story.
- [ ] At least 1 opportunity drift story.
- [ ] At least 1 ownership/control, subsidiary, or jurisdiction story.
- [ ] At least 1 entity relevant to crypto or digital assets.
- [ ] At least 1 entity with high-quality public evidence likely available.

## Handoff Checklist

Before teammate 2 starts source collection:

- [ ] Search aliases are complete enough.
- [ ] Suggested source types are listed.
- [ ] Expected public events are clear.
- [ ] Weak or uncertain entities are marked as backup.

Before teammate 3 starts extraction/scoring:

- [ ] Baseline schema matches `03-baseline-schema-spec.md`.
- [ ] Expected drift types are machine-readable strings.
- [ ] `last_reviewed_at` dates are before expected current evidence.

Before teammate 4 starts demo UI:

- [ ] Top 3 demo stories are identified.
- [ ] Each story has a plain-English summary.
- [ ] Each story says whether it is risk, opportunity, ownership, or mixed.

## Ready-To-Handoff Summary Template

```markdown
# Demo Entity Handoff

## Top 3 Stories

1. [Entity]: [one-sentence drift story]
2. [Entity]: [one-sentence drift story]
3. [Entity]: [one-sentence drift story]

## Backup Entities

- [Entity]: [why backup]

## Risks

- [Any entity with weak evidence or ambiguous naming]

## Notes For Teammate 2

- [Best sources to collect first]

## Notes For Teammate 3

- [Expected drift fields and signal types]

## Notes For Teammate 4

- [Recommended demo order]
```

