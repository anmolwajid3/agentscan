# P1 summary (interim)

Interim. This is not the finished sample.
No pass or fail is declared.

Written: 2026-11-08T10:54+00:00.
Eligible projects with a finished analysis when this file was written: 1375.
The sample is still running. These rows are the eligible projects whose analysis files were already complete, including projects that finished ahead of slower repositories still in progress.
Main rules only: same-commit swaps whose rule type does not start with `rename`. Rename rules are excluded.
Cut-off: 2026-11-08. Control window starts 2025-01-01.
The full-run bar, recorded here and not applied as a verdict, is at least 100 same-commit ai_after swaps from more than 20 projects.

## AI signal

Projects with an AI signal: 514.
Projects without an AI signal: 861.

## Adoption dates by quarter

Quarters are the adoption date of projects with an AI signal.

| Quarter | Projects |
| --- | --- |
| 2015 Q3 | 1 |
| 2017 Q2 | 1 |
| 2023 Q1 | 1 |
| 2024 Q3 | 2 |
| 2024 Q4 | 2 |
| 2025 Q1 | 1 |
| 2025 Q2 | 22 |
| 2025 Q3 | 37 |
| 2025 Q4 | 56 |
| 2026 Q1 | 101 |
| 2026 Q2 | 124 |
| 2026 Q3 | 107 |
| 2026 Q4 | 59 |

## Same-commit swaps, main rules

| Group | Swaps | Projects | Exposure (project-months) | Swaps per 100 project-months |
| --- | --- | --- | --- | --- |
| ai_after | 14 | 11 | 3554.7 | 0.394 |
| ai_before | 523 | 183 | 84346.8 | 0.620 |
| control_same_period | 25 | 19 | 13588.5 | 0.184 |

## Projection

Interim projection. The rate is same-commit main-rule ai_after swaps per eligible project in this file, scaled to the 2,950 projects that passed the GitHub screen.

Eligible projects in this file: 1375.
Eligible population the projection scales to: 2950.
Same-commit main-rule ai_after swaps in this interim set: 14.
Projects contributing those swaps: 11.
Projected ai_after swaps in the 2,950: 30.0.
Projected projects contributing those swaps: 23.6.
The projected swap count is under 100. The projected project count is more than 20.
The projection is not a pass or fail.

## Unparsed rows

Unparsed dependency rows after placeholder resolution: 28125254.

| Reason | Rows |
| --- | --- |
| unresolved property | 38259 |
| missing groupId or artifactId | 20 |
| could not read pom.xml | 28084291 |
| broken XML | 2684 |

Largest unparsed counts:

- 6649990: xwiki/xwiki-platform
- 2190384: apache/tomee
- 2137610: nuxeo/nuxeo
- 1704009: spring-projects/spring-boot
- 1701383: apache/aries

## Suspicious adoption dates

Interim. These are the three projects behind the 2015 Q3, 2017 Q2, and 2023 Q1 rows in the adoption table above.
Each date is a false match. None is a real AI coding-tool signal.

| Project | Date the rule stored | Signal that set it | What matched | Judgment |
| --- | --- | --- | --- | --- |
| java-native-access/jna | 2015-08-01 | agent author | Author email `gottfried.haider@gmail.com` on commit [`f0ea52cc`](https://github.com/java-native-access/jna/commit/f0ea52cc47da13354ebecbf124c0cdc6171d4f9f), “Get additional library paths from ldconfig on Linux.” The address contains the letters `aider@`. | False match. The author is a person, gohai. |
| processing/processing-android | 2017-06-07 | agent author | The same author email on commit [`d0b6b1cc`](https://github.com/processing/processing-android/commit/d0b6b1cc4108ace0e160d064a3b81ffe5b03d3a1), “Add missing space to MISSING_SDK_MESSAGE.” | False match. Same person, same email rule. |
| TownyAdvanced/Towny | 2023-02-21 | co-author | `Co-authored-by: Josh Jameson <josh@codegen.ie>` on commit [`6690a240`](https://github.com/TownyAdvanced/Towny/commit/6690a240cb35f0ca071372bbd2c0a9146bf61646), “Option to prevent people from claiming in a straight line.” The domain contains `codegen`. | False match. Josh Jameson is a human co-author. `codegen.ie` is his email domain, not an AI coding agent. |

## Same-period comparison

Interim. Same-commit swaps under the non-rename rules, for projects with a finished analysis at this later cut.
Eligible projects in this comparison: 2092. With an AI signal: 806. Without: 1286.
Recorded adoption dates before 2025: 13 of the 806 AI projects. The 2022, 2023, and 2024 rows are therefore before adoption for almost every project in the AI column.
The three false matches above contributed no same-commit main-rule swaps in these four windows.
A year runs from 1 January through the next 1 January. The last window runs from 1 January 2025 through the cut-off, 2026-11-08.
Exposure is the overlap of each project's history, ending at the earlier of its last commit and the cut-off, with that window. The rate is swaps per 100 project-months.

| Period | Group | Swaps | Projects | Exposure (project-months) | Swaps per 100 project-months |
| --- | --- | ---: | ---: | ---: | ---: |
| 2022 | AI | 79 | 39 | 9647.4 | 0.819 |
| 2022 | non-AI | 67 | 37 | 15390.0 | 0.435 |
| 2023 | AI | 61 | 36 | 9665.4 | 0.631 |
| 2023 | non-AI | 85 | 48 | 15064.9 | 0.564 |
| 2024 | AI | 30 | 20 | 9691.9 | 0.310 |
| 2024 | non-AI | 48 | 20 | 13920.1 | 0.345 |
| 2025–cutoff | AI | 62 | 39 | 17371.0 | 0.357 |
| 2025–cutoff | non-AI | 39 | 28 | 20291.4 | 0.192 |

In 2022, projects that later show an AI signal already swapped at 0.819 per 100 project-months, against 0.435 for projects with no AI signal. In 2023 the rates are 0.631 and 0.564. In 2024 the AI rate is 0.310 and the non-AI rate is 0.345. In 2025 through the cut-off the AI rate is 0.357 and the non-AI rate is 0.192.

## The 14 ai_after swaps

Interim. These are the 14 same-commit main-rule ai_after swaps in the snapshot above, from the 1,375 eligible projects. Later finishes are not in this list.
“AI author” means the commit has an AI co-author trailer or an AI agent as its author.

| Project | Commit | Removed | Added | AI author |
| --- | --- | --- | --- | --- |
| xetorthio/jedis | [`1d1b268f9b`](https://github.com/xetorthio/jedis/commit/1d1b268f9be5b093f6684bc814d2fdab376a1ee3) | junit:junit | org.mockito:mockito-junit-jupiter | No |
| xetorthio/jedis | [`b04e64bf45`](https://github.com/xetorthio/jedis/commit/b04e64bf45e23c06e9d3b638ccc5a2142f7ee638) | org.slf4j:slf4j-simple | ch.qos.logback:logback-classic | Yes. Co-authored-by Copilot. The author is a person. |
| testingbot/Testingbot-Tunnel | [`b29131094d`](https://github.com/testingbot/Testingbot-Tunnel/commit/b29131094dca040294ef4643ae3b5993171b5d09) | net.sf.json-lib:json-lib | com.fasterxml.jackson.core:jackson-databind | No |
| ta4j/ta4j | [`c29781e045`](https://github.com/ta4j/ta4j/commit/c29781e0453b9ec116ae9cab4a22fa8c6866b08a) | ch.qos.logback:logback-classic | org.apache.logging.log4j:log4j-api | No |
| ta4j/ta4j | [`c29781e045`](https://github.com/ta4j/ta4j/commit/c29781e0453b9ec116ae9cab4a22fa8c6866b08a) | ch.qos.logback:logback-classic | org.apache.logging.log4j:log4j-core | No |
| osalvador/ReplicaDB | [`c376068c32`](https://github.com/osalvador/ReplicaDB/commit/c376068c326f3ff30a23f86d7081091491c82b79) | org.slf4j:slf4j-log4j12 | org.apache.logging.log4j:log4j-slf4j-impl | No |
| Adyen/adyen-java-api-library | [`40c802aff6`](https://github.com/Adyen/adyen-java-api-library/commit/40c802aff6066430fe61e118465a0d376fb7b0ae) | junit:junit | org.mockito:mockito-junit-jupiter | No |
| undera/jmeter-plugins | [`cb7a711182`](https://github.com/undera/jmeter-plugins/commit/cb7a71118278a2521d09b09c44b43ca1649a81bc) | org.powermock:powermock-api-mockito | org.mockito:mockito-core | No |
| undera/jmeter-plugins | [`cb7a711182`](https://github.com/undera/jmeter-plugins/commit/cb7a71118278a2521d09b09c44b43ca1649a81bc) | org.powermock:powermock-module-junit4 | org.mockito:mockito-core | No |
| phax/ph-commons | [`41c5ac9225`](https://github.com/phax/ph-commons/commit/41c5ac9225c801852e7edc37140b15fd9e4f99f7) | com.sun.xml.bind:jaxb-impl | org.glassfish.jaxb:jaxb-runtime | No |
| apache/airavata | [`f250f6dde8`](https://github.com/apache/airavata/commit/f250f6dde8e5f37eb857b5bf3117b556ee2e4b90) | org.apache.commons:commons-dbcp2 | com.zaxxer:HikariCP | Yes. Co-authored-by Claude. The author is a person. |
| geosolutions-it/geostore | [`6b07cfec9e`](https://github.com/geosolutions-it/geostore/commit/6b07cfec9e615fd46db8a22fd6aa4ff4685770a8) | com.sun.xml.bind:jaxb-impl | org.glassfish.jaxb:jaxb-runtime | No |
| apache/skywalking | [`277f19bcce`](https://github.com/apache/skywalking/commit/277f19bcce913c7aed66c13178d7b29f252ed729) | log4j:log4j | ch.qos.logback:logback-core | No |
| dekorateio/dekorate | [`47fd389536`](https://github.com/dekorateio/dekorate/commit/47fd3895362261b2d51cf13ef784b9e8876f1b45) | com.fasterxml.jackson.dataformat:jackson-dataformat-yaml | org.yaml:snakeyaml | No |

Two of the 14 swaps come from a commit with an AI co-author. None of the 14 has an AI agent as the commit author. The other 12 have neither.

## Projection and P2

Interim, and not yet the finished projection. The seeded sample is still running. Its ordered prefix is stopped at `wildfly/wildfly`, with 807 eligible projects before that gap, so the run has not reached its 2,000-project close and has not written the P2 samples.
The projection and the unreviewed P2 draw wait until that run finishes.
