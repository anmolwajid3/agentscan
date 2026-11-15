# smontlouis/bible-strong (high_cooccur)

Old ADR: `docs/adr/0015-use-storage-generation-for-offline-copy-updates.md`
New ADR: `docs/adr/0025-use-catalog-sha-for-r2-offline-copy-updates.md`
New ADR date: 2026-08-19T22:57:37+02:00
Partial: no

## Old ADR status line

Superseded by ADR-0025

## New ADR

ADR-0025: Use catalog SHA-256 for R2 offline-copy updates

Accepted

## Best commit

`271a5224972e4bda3c66430c2e19de7ab1259d3a` (before)

fix(resources): keep offline downloads on catalog CDN

commit title matches the new ADR: catalog, offline; changes application code

Changed files:

- M docs/agents/validation.md
- M docs/local-resource-bootstrap.md
- M resource-service/README.md
- M src/features/resources/resourceAccess.tsx
- M src/helpers/__tests__/mobileResourceCatalog-test.ts
- M src/helpers/mobileResourceCatalog.ts

## Other candidates

61cf39c8c4a6 chore(expo): log embedded Offline-copy key versions at prebuild; ca1d6cf99fbb fix(resources): reject incomplete offline catalogs; d288365c2858 feat(resources): publish encrypted Offline copies for every catalog resource; e12417b50e74 feat(expo): add native encrypted Offline-copy extraction module; ebbceb029563 feat(expo): acquire App Check only for Offline-copy downloads; 4a2db016614c Merge pull request #440 from smontlouis/feat/bhg-canonical-offline-copy; 1f45fbe738bd refactor(resources)!: consolidate authoring in resource studio; 2ba062954e29 feat(expo): draw the timeline on one axis, as the public site does
