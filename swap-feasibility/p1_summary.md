# P1 summary

This file is the five-project trial. The full population has not been run.
The pass rule is not applied to five projects, and the thresholds were not changed.

**Full-run result: not run.** Waiting for approval before cloning the He et al. list.

Cut-off: 2026-11-08. Control window starts 2025-01-01.
Same-commit pass bar: at least 100 ai_after swaps from more than 20 projects, and at least as many control_same_period swaps.

## same commit

| Group | Swaps | Projects | Exposure (project-months) | Swaps per 100 project-months | Share from top 5 |
| --- | --- | --- | --- | --- | --- |
| ai_after | 0 | 0 | 30.7 | 0.000 | NA |
| ai_before | 12 | 3 | 730.6 | 1.643 | 100.0% |
| control_same_period | 0 | 0 | 44.4 | 0.000 | NA |

## 30-day window

| Group | Swaps | Projects | Exposure (project-months) | Swaps per 100 project-months | Share from top 5 |
| --- | --- | --- | --- | --- | --- |
| ai_after | 0 | 0 | 30.7 | 0.000 | NA |
| ai_before | 3 | 2 | 730.6 | 0.411 | 100.0% |
| control_same_period | 0 | 0 | 44.4 | 0.000 | NA |

Same-commit ai_after swaps with an AI co-author or agent author: 0 of 0.

## Most common same-commit pairs: ai_after

None.

## Most common same-commit pairs: ai_before

- 2: org.powermock:powermock-api-mockito -> org.powermock:powermock-api-mockito2
- 1: com.google.collections:google-collections -> com.google.guava:guava
- 1: junit:junit -> org.junit.jupiter:junit-jupiter-api
- 1: junit:junit -> org.junit.jupiter:junit-jupiter-engine
- 1: junit:junit -> org.junit.vintage:junit-vintage-engine
- 1: org.powermock:powermock-module-junit4 -> org.mockito:mockito-core
- 1: org.junit.vintage:junit-vintage-engine -> org.junit.jupiter:junit-jupiter-api
- 1: org.sonatype.sisu:sisu-guice -> com.google.inject:guice
- 1: org.eclipse.aether:aether-api -> org.apache.maven.resolver:maven-resolver-api
- 1: xmlunit:xmlunit -> org.xmlunit:xmlunit-core
- 1: ant:ant -> org.apache.ant:ant

## Most common same-commit pairs: control_same_period

None.

## Same-commit swaps by quarter

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
| 2024 Q1 | 1 | 0 |
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
## Estimate before a full run

- He et al. project list: 19652 repositories. All of them are marked fork=False in that file, and all have a pom file count above zero.
- 13791 had at least 50 commits at the paper's crawl, whose timestamps end around January 2020. That count is not the 2023 commit count.
- Those 13791 repositories had a combined GitHub `size` of 440 GiB at the crawl. A blobless clone is smaller than that checkout size. The five trial clones together are 118 MiB.
- Commits during 2023, a pom.xml still present before 2024, and archive status are not in the file. They need a live git history. The eligible count is therefore not known yet. The 2,000-project stop line cannot be judged until that history is read. The crawl already shows more than 2,000 repositories with 50 commits, so the list itself is large enough to continue to the trial.
- No GITHUB_TOKEN is set. Unauthenticated API access is too slow to screen archive status for the whole list. Eligibility for the full list would be computed from partial clones.
- The five trial repositories finished their blobless clones in a few seconds each and the swap pass on all five took about two minutes once pom blobs were fetched in batches. The largest repositories in the list, such as elasticsearch, are not in this trial, so a full run would be slower than five times this sample.
