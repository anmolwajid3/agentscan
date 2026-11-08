# Pilot scorecard

Run: 2026-11-08T01:56+00:00

The pass bars were fixed in the scripts before the counts were read.

| Check | Result | Pass | If it fails |
| --- | --- | --- | --- |
| 1. Enough data | 67 projects with an AI signal and at least 5 earlier ADRs; 273 without a signal and at least 5 ADRs; 133 superseded decisions in those windows. All superseded records: 32 before adoption, 2 after adoption, 101 with no signal. | yes | Stop or change the study. The full design is not possible in this form. |
| 2. AI signal | 19 of 20 flagged projects show use on or after the earliest strong signal. 17 of 18 projects with a co-author or agent-author date fall within 92 days. A project with no such date is missing, not zero. 0 of 20 unflagged projects have a hidden trace. Maintainer replies so far: 0. | yes | Use only the strongest signal, or call projects AI-configured rather than AI-using. |
| 3. Decision date | 12 of 30 records placed as written-first or written-after (40%). Script commit agreed in 28 of 30 (93%). | no | Drop the timing question if most records were written after the decision. |
| 4. Endings | Script agreed with the hand label in 29 of 30 (97%). | yes | Tighten the rules, or check every reversal by hand. |
| 5. Two raters | Rater A labeled 15 cases. A second rater has not labeled them yet, so kappa is not computed. | no | Keep the yes/no hard dimension and drop the cheap/moderate/expensive scale. |
| 6. Developers | Emails are drafted. No maintainer has replied in the replies sheet yet. | no | Rethink the complexity measure. Five replies are already useful. |

## Check 1 detail

- Repositories in the sampling frame: 2338. AI-file hits in that frame: 1058. Measured in this run: 422. Not measured yet: 1916.
- Clone failures among the measured set: 33.
- Pass counts use the measured repositories. The first slice is every repository in the January 2022 census with at least 5 ADRs. A pass on that slice means at least that many projects qualify. Rows of the 2026 index that were not cloned are not in the pass count.
- AI-native (signal before any ADR, so no before period): 11.
- AI signal but fewer than 5 earlier ADRs: 1.
- Fewer than 5 ADRs and no signal: 35.
- Templates and catalogs set aside: 2.
- Stricter project filter (at least two authors and one year of history), not required by the pass bar: 67 AI, 200 non-AI, 116 superseded. That stricter bar passes.
- Superseded records in eligible projects only: 32 before adoption, 2 after adoption, 101 with no signal. The pass bar uses the before-adoption count plus the no-signal count. Records written after adoption are reported separately and do not fill that bar.

## Check 2 detail

- Check 2 is a fresh sample, seed 20261111. It excludes the 40 repositories in `check2_development_sample.csv`. The adoption date is the earliest instruction file, AI co-author line, or agent author. The gap is measured to the earliest co-author or agent author. An earlier commit-message mention does not move the date, and a project with no co-author or agent author keeps a blank gap.
- A hidden trace is a strict mention of Copilot, Claude, Cursor, or ChatGPT, or a co-author or agent author, in a project that has no instruction file, no AI co-author, and no agent author. A commit about a cursor position, or a product that happens to be named Copilot, is not a hidden trace. Zero hidden traces in a sample of 20 is not proof that unflagged projects never use AI.

## Check 4 detail

- Check 4 is a fresh sample of 30, seed 20261110. It shares no file with the first 30 (`check4_development_sample.csv`), which is where the pointer-phrase misses were found. That first sample is not the reported accuracy. The fresh mix is 9 replaced, 4 no-longer-needed, 1 rejected-before-use, 16 cleanup-or-rename. The measured repositories only contain 9 rejected-before-use transitions and 9 no-longer-needed transitions, and the first sample had already taken most of them.

## How to read a failure

All six pass: the full study can go ahead.
Some fail: keep the parts that passed. A smaller study is still a paper.
Check 1 fails: do not spend months on this design.
