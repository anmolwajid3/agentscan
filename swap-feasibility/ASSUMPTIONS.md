# Assumptions

- The 1,194 rules are every row of `source/rules_typed.csv` (`fromLib`, `toLib`, `type`). The main count uses the 802 rows whose type does not start with `rename`. The 392 `rename:*` rows are counted separately. Reason: that file is the only list in the replication package with 1,194 rows, and the rename rows are a different kind of change.
- The rule list dates from about 2020 and may miss swaps to libraries that became common later. Reason: the replication package is He et al. 2021, and its crawl timestamps end around January 2020.
- A rule id is the row number in `rules_typed.csv`. Reason: the file has no id column.
- Adoption date is the ADR pilot's earliest strong signal. Reason: the brief says to reuse that rule and not rewrite it.
- A plain commit-message mention does not set the adoption date. Reason: that is the validated rule.
- A library is removed only when no `pom.xml` on the first-parent tree still declares it, and added only when none declared it before that commit. Reason: the brief says to read every module. A dependency that remains in any module was not removed. The tree is rebuilt from the pom diffs, including renames. One maven commit was checked against `git ls-tree`: 2,061 pom files, the same set.
- Plugin dependencies are not library dependencies. Reason: they build the project rather than ship inside it.
- `${project.groupId}`, `${project.version}`, `${project.parent.groupId}`, and other properties are resolved from the same pom and from parent poms found by a relative path in this repository. A property that is still unresolved stays unparsed. Reason: these are the common Maven placeholders, and full Maven resolution would download parents that are not in the repository.
- Every path named `pom.xml` counts, including test fixtures and examples. Reason: the brief does not exclude them, and dropping them would be a guess.
- The 30-day result is dated on the later of the two commits and is not mixed into the same-commit counts. Reason: the brief says to report the two modes separately.
- Exposure for `ai_before` runs from the first commit to the adoption date. Exposure for `ai_after` runs from adoption to the earlier of the last commit and the cut-off. Exposure for controls runs from 1 January 2025 to that same end. Reason: the brief names the control window and says to keep the last commit date so a quiet project does not stay under observation.
- Fork and archive status come from the GitHub API at screening time, using `GITHUB_TOKEN`. A repository that is not archived now was not archived on 31 December 2023. A repository that is archived now has an unknown archive date, so it is not counted as eligible. Reason: the API gives a boolean, not the archive date, and a missing date must not become "not archived".
- The fork flag in the 2020 project list is not reused as the 2023 fork flag. Reason: it is a different date. The trial asks GitHub.
