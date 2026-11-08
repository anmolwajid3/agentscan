# Pilot scorecard

Run: 2026-11-08T01:41+00:00

The pass bars were fixed in the scripts before the counts were read.

| Check | Result | Pass | If it fails |
| --- | --- | --- | --- |
| 1. Enough data | 67 projects with an AI signal and at least 5 earlier ADRs; 273 without a signal and at least 5 ADRs; 133 superseded decisions in those windows. | yes | Stop or change the study. The full design is not possible in this form. |
| 2. AI signal | 19 of 20 flagged projects show use after the signal. 14 of 19 observable start dates fall within 92 days. 0 of 20 unflagged projects have a hidden trace. Maintainer replies so far: 0. | no | Use only the strongest signal, or call projects AI-configured rather than AI-using. |
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

## Check 4 detail

- Check 4 is a fresh sample of 30, seed 20261110. It shares no file with the first 30 (`check4_development_sample.csv`), which is where the pointer-phrase misses were found. That first sample is not the reported accuracy. The fresh mix is 9 replaced, 4 no-longer-needed, 1 rejected-before-use, 16 cleanup-or-rename. The measured repositories only contain 9 rejected-before-use transitions and 9 no-longer-needed transitions, and the first sample had already taken most of them.

## How to read a failure

All six pass: the full study can go ahead.
Some fail: keep the parts that passed. A smaller study is still a paper.
Check 1 fails: do not spend months on this design.
