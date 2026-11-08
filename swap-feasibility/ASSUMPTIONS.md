# Assumptions

- The 1,194 rules are every row of `source/rules_typed.csv` (`fromLib`, `toLib`, `type`), including 802 rows typed `undecided`. Reason: that file is the only list in the replication package with 1,194 rows. `rules.xlsx` has 1,401 pairs and `cache/mig_graph.json` has 123 edges.
- A rule id is the row number in `rules_typed.csv`. Reason: the file has no id column.
- Adoption date is the ADR pilot's earliest strong signal. Reason: the brief says to reuse that rule and not rewrite it.
- A plain commit-message mention does not set the adoption date. Reason: that is the validated rule.
- A library is removed only when no `pom.xml` on the first-parent tree still declares it, and added only when none declared it before that commit. Reason: the brief says to read every module. A dependency that remains in any module was not removed. The tree is rebuilt from the pom diffs, including renames. One maven commit was checked against `git ls-tree`: 2,061 pom files, the same set.
- Plugin dependencies are not library dependencies. Reason: they build the project rather than ship inside it.
- A `${property}` that cannot be resolved inside the same file makes that dependency unparsed. Reason: the brief says an unparsed dependency must not be dropped silently and must not be guessed.
- Every path named `pom.xml` counts, including test fixtures and examples. Reason: the brief does not exclude them, and dropping them would be a guess.
- The 30-day result is dated on the later of the two commits and is not mixed into the same-commit counts. Reason: the brief says to report the two modes separately.
- Exposure for `ai_before` runs from the first commit to the adoption date. Exposure for `ai_after` runs from adoption to the earlier of the last commit and the cut-off. Exposure for controls runs from 1 January 2025 to that same end. Reason: the brief names the control window and says to keep the last commit date so a quiet project does not stay under observation.
- A repository that is archived now has archive status NA. Reason: the GitHub API does not give the date it was archived, and a missing date must not become "not archived".
- The fork flag in the 2020 project list is not reused as the 2023 fork flag. Reason: it is a different date. The trial asks GitHub.
