# Task Brief

## Objective

Choose 3 to 5 demo entities and create synthetic KYC baseline profiles for them. The baselines should represent what AMINA might have known at the last review date, before newer public evidence changed the picture.

The goal is not to perfectly model real AMINA customers. The goal is to create credible demo profiles that let the prototype show:

- What AMINA knew before.
- What changed after the last review.
- Why the change matters.
- Which teammate should collect evidence for the change.

## Priority

This is the highest-priority subtask.

If time is short, choose fewer entities with stronger evidence. Three excellent entities are better than five weak ones.

## What To Build

Create a baseline profile for each selected demo entity.

Each profile must include:

- Legal or public company name.
- Aliases.
- Domicile.
- Business area.
- Known jurisdictions.
- Known products or expected AMINA relationship.
- Directors, founders, executives, or other control persons if public.
- Investors if public and relevant.
- Subsidiaries if public and relevant.
- Websites and social handles.
- Known wallets only if publicly attributed.
- Last reviewed date.
- Demo story.
- Expected drift type.

## What Not To Do

Do not spend this subtask on:

- Building scrapers.
- Writing extraction algorithms.
- Creating UI.
- Making legal conclusions.
- Collecting private or non-public data.
- Guessing wallet ownership.

## Recommended Entity Mix

Pick entities that cover different stories:

1. **Risk drift entity**: new high-risk jurisdiction, sensitive sector, adverse media, enforcement, or crypto risk.
2. **Opportunity entity**: funding, growth, treasury need, hiring, international expansion, or digital-asset activity.
3. **Ownership/control entity**: new investor, acquisition, subsidiary, director, executive, or cap table signal.
4. **Optional mixed entity**: both risk and opportunity signals.

## Baseline Design Rule

The baseline should be intentionally historical.

Example:

- `last_reviewed_at`: `2026-01-15`
- Baseline known jurisdictions: `["Switzerland", "Germany"]`
- Current evidence discovered by teammate 2: new subsidiary or hiring in another jurisdiction

This creates a clear before/after comparison for the signal engine and dashboard.

## Handoff Notes

For every entity, add a short note:

- Why this entity was chosen.
- What drift we expect to find.
- Which sources teammate 2 should search first.
- Which AMINA product or risk concern it maps to.

