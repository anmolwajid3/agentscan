# Fresh reversal funnel v2 (interim)

Interim. No builds were run. This is not a pass or fail. v1 files were not rewritten.

Sample seed: 20261114. Review seed: 20261114.
The original 1,500 repositories stay in the draw. Newly discovered repository names were shuffled with the same seed and added after them.
The implementing-commit window is 180 days before and 180 days after the new ADR's author date.
One commit is chosen per pair. A title match outranks a dependency-manifest edit.

## Step 1. ADR folders

v1 universe: 1598. v1 draw kept: 1500.
New repositories added by the extra folder queries: 993.
Repositories in this run: 2493.

- src_adr: returned 5, Sourcegraph matchCount 5.
- docs_arch_decisions_hyphen: returned 9, Sourcegraph matchCount 9.
- docs_architecture_adr: returned 24, Sourcegraph matchCount 24.
- docs_architecture_adrs: returned 1, Sourcegraph matchCount 1.
- docs_architecture_decisions: returned 34, Sourcegraph matchCount 34.
- doc_arch_decisions: returned 4, Sourcegraph matchCount 4.
- doc_arch_decisions_hyphen: returned 1, Sourcegraph matchCount 1.
- doc_arch: returned 8, Sourcegraph matchCount 8.
- documentation_arch_decisions: returned 2, Sourcegraph matchCount 2.
- source_adr_records: returned 0, Sourcegraph matchCount 0.
- docs_architecture: returned 1195, Sourcegraph matchCount 1195.

Markdown files in general folders (docs/architecture and the other broad folders) removed because the filename has no number and the file has no Status section: 5875.

`first_adr_date` is the author date of the oldest commit that touches any ADR file still kept after the copied-file and general-folder filters. Every kept pair has one.

## Step 2. Not a fork, not archived, has a build file

Screened: 2493.
Kept: 2036.
- fork: 0.
- archived: 3.
- no build file: 452.
- api error: 2.

## Step 3. Real replacement pairs

Repositories whose clone or read failed: 4.
Pairs removed because an ADR file is copied, vendored, or from another project: 48.
Pairs removed because an ADR file is a template: 23.
ADR links that are not a real replacement sentence: 25514.
Replacement sentences that do not name a resolvable ADR: 9359. This includes ordinary prose such as "replaces the client" as well as a status line whose ADR number cannot be found.
Pairs from more than one repository with the same ADR text, recorded as duplicates: 58.
Pairs kept: 2108.
Of those, partial supersedes: 33.

### Compared with v1

v1 pairs: 2397.
v1 pairs that survive into v2 (same project and the same two ADR files, either order): 1343.
Of the surviving pairs, direction flipped: 441.
v1 pairs whose target changed: 373.
v1 pairs dropped: 681.

### New ADR year

Before 2026: 64.
2026: 2032.
unknown: 12.

The top 10 repositories account for 717 of 2108 kept pairs.

- ghuntley/overalls: 156.
- ngophatneknha/ai-engineering-hub: 93.
- TheRealSavi/iOpenPod: 78.
- DavidObando/gsharp: 76.
- BotHarness/DeepSeekBot: 67.
- chattocorp/chatto: 61.
- vastsa/PI-Desktop: 58.
- prisma/orm: 49.
- fullsend-ai/fullsend: 40.
- kachofugetsu09/akashic-agent: 39.

## Step 4. One implementing commit

high_topic: 1386.
high_cooccur: 449.
Medium: 1.
Low: 259.
No commit found: 13.

### Confidence, new ADR before 2026

- high_topic: 27.
- high_cooccur: 23.
- low: 14.

### Confidence, new ADR 2026

- high_topic: 1359.
- high_cooccur: 426.
- medium: 1.
- low: 245.
- no commit: 1.

### Confidence, new ADR unknown

- no commit: 12.

Pairs lost at this step:

- 12: new ADR commit not found
- 1: git log timed out

## Known-case check

- SukramJ/aiohomematic: best commit `34d1218731675d3fd9886c1f9ac0dfab7f074b71` (high_topic). Title: Async RPC server is now the standard implementation (#2837). Why: commit title matches the new ADR: async, server; removes or replaces something named in the old ADR; changes application code. It matches the expected prefix 34d1218731.
- chrisbanes/haze: best commit `d3384f5611b34cb5f353ef2b5a2dacbb91508ad3` (high_topic). Title: Use one Android fused Glass renderer for all RuntimeShader features (#1094). Why: commit title matches the new ADR: android, fused, glass, renderer; removes or replaces something named in the old ADR; changes application code. It matches the expected prefix d3384f5611.
- alphagov/whitehall: best commit `c20949e10475fd479ac0dc86ae0f843b9df45454` (high_topic). Title: Correct configurable document schema validation test filename. Why: commit title matches the new ADR: schema, document; removes or replaces something named in the old ADR; changes application code.

## Step 5. Comparison with the old 133

Old superseded records reconstructed from the saved measurements: 133.
Kept pairs whose old ADR is in that set: 4.

Review packets are in `review_v2/`: 5 high_topic, 5 high_cooccur, 1 medium, and 5 whose new ADR is before 2026. Only one pair in the kept set is medium, so that band has one packet and the folder has 16.
