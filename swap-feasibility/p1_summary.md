# P1 summary

This file is the five-project trial. The sample of eligible projects has not been run.
No pass or fail is declared from five projects.

The main counts use the 802 rules whose type does not start with `rename`.
The 392 rename rules are reported in their own section and are not included in the main counts or the projection.

Cut-off: 2026-11-08. Control window starts 2025-01-01.
The full-run bar, unchanged and not applied here, is at least 100 same-commit ai_after swaps from more than 20 projects, and at least as many control_same_period swaps.

## Main rules: same commit

| Group | Swaps | Projects | Exposure (project-months) | Swaps per 100 project-months | Share from top 5 |
| --- | --- | --- | --- | --- | --- |
| ai_after | 0 | 0 | 30.7 | 0.000 | NA |
| ai_before | 5 | 3 | 730.6 | 0.684 | 100.0% |
| control_same_period | 0 | 0 | 44.4 | 0.000 | NA |

## Main rules: 30-day window

| Group | Swaps | Projects | Exposure (project-months) | Swaps per 100 project-months | Share from top 5 |
| --- | --- | --- | --- | --- | --- |
| ai_after | 0 | 0 | 30.7 | 0.000 | NA |
| ai_before | 2 | 2 | 730.6 | 0.274 | 100.0% |
| control_same_period | 0 | 0 | 44.4 | 0.000 | NA |

Same-commit main-rule ai_after swaps with an AI co-author or agent author: 0 of 0.

## Most common same-commit pairs (Main rules): ai_after

None.

## Most common same-commit pairs (Main rules): ai_before

- 2: org.powermock:powermock-api-mockito -> org.powermock:powermock-api-mockito2
- 1: com.google.collections:google-collections -> com.google.guava:guava
- 1: org.powermock:powermock-module-junit4 -> org.mockito:mockito-core
- 1: org.sonatype.sisu:sisu-guice -> com.google.inject:guice

## Most common same-commit pairs (Main rules): control_same_period

None.

## Same-commit main-rule swaps by quarter

| Quarter | AI projects | Controls |
| --- | --- | --- |
| 2022 Q1 | 0 | 0 |
| 2022 Q2 | 0 | 0 |
| 2022 Q3 | 0 | 0 |
| 2022 Q4 | 0 | 0 |
| 2023 Q1 | 0 | 0 |
| 2023 Q2 | 0 | 0 |
| 2023 Q3 | 0 | 0 |
| 2023 Q4 | 1 | 0 |
| 2024 Q1 | 0 | 0 |
| 2024 Q2 | 0 | 0 |
| 2024 Q3 | 0 | 0 |
| 2024 Q4 | 0 | 0 |
| 2025 Q1 | 0 | 0 |
| 2025 Q2 | 0 | 0 |
| 2025 Q3 | 0 | 0 |
| 2025 Q4 | 0 | 0 |
| 2026 Q1 | 0 | 0 |
| 2026 Q2 | 0 | 0 |
| 2026 Q3 | 0 | 0 |
| 2026 Q4 | 0 | 0 |

## Rename rules, separate from the main count

Rename rows in the rule file: 392. Rename swaps detected: 18.

## Rename rules: same commit

| Group | Swaps | Projects | Exposure (project-months) | Swaps per 100 project-months | Share from top 5 |
| --- | --- | --- | --- | --- | --- |
| ai_after | 0 | 0 | 30.7 | 0.000 | NA |
| ai_before | 7 | 3 | 730.6 | 0.958 | 100.0% |
| control_same_period | 0 | 0 | 44.4 | 0.000 | NA |

## Rename rules: 30-day window

| Group | Swaps | Projects | Exposure (project-months) | Swaps per 100 project-months | Share from top 5 |
| --- | --- | --- | --- | --- | --- |
| ai_after | 0 | 0 | 30.7 | 0.000 | NA |
| ai_before | 1 | 1 | 730.6 | 0.137 | 100.0% |
| control_same_period | 0 | 0 | 44.4 | 0.000 | NA |

Unparsed dependency rows after placeholder resolution: 75.

## Projection

Projected ai_after swaps in the full eligible population: NA.
AI projects needed to reach 100: NA.
## Estimate before a full run

- He et al. project list: 19652 repositories. All of them are marked fork=False in that file, and all have a pom file count above zero.
- 13791 had at least 50 commits at the paper's crawl, whose timestamps end around January 2020. That count is not the 2023 commit count.
- Those 13791 repositories had a combined GitHub `size` of 440 GiB at the crawl. A blobless clone is smaller than that checkout size. The five trial clones together are 118 MiB.
- Commits during 2023, a pom.xml still present before 2024, and archive status are not in the file. They need a live git history. The eligible count is therefore not known yet. The 2,000-project stop line cannot be judged until that history is read. The crawl already shows more than 2,000 repositories with 50 commits, so the list itself is large enough to continue to the trial.
- No GITHUB_TOKEN is set. Unauthenticated API access is too slow to screen archive status for the whole list. Eligibility for the full list would be computed from partial clones.
- The five trial repositories finished their blobless clones in a few seconds each and the swap pass on all five took about two minutes once pom blobs were fetched in batches. The largest repositories in the list, such as elasticsearch, are not in this trial, so a full run would be slower than five times this sample.
