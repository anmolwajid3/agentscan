# Check 6 inputs

Inspected 8 November 2026. The packets and trouble counts were not built. The brief says to stop when an input the check needs is not in the project, and not to invent a substitute.

## What is on disk

| Needed | File that exists | Columns |
| --- | --- | --- |
| Hand labels for hardness | `data/manual/check5_rater_a.csv` | `case_id`, `decision_type`, `hard`, `d1`, `d2`, `d3`, `d4`, `d5`, `minutes`, `note`. 15 rows. `hard` is `yes` or `no`. |
| Second rater | `data/manual/check5_rater_b.csv` | Same columns. Header only. |
| Reversal sample linked to those labels | `data/check5_sample.csv` and `data/check6_sample.csv` | `case_id`, `repo`, `path`, `title`, `status`, `first_commit`, `date`, `old_state`, `new_state`, `script_label`, `script_rule`, `script_reason`, `script_commit`, `author`, `email`, `commit_url`, `adr_url`. 15 rows in check 5. The check 6 sheet is the same reversals. `path` is the old ADR only. |
| Per-repository measurements | `data/repos/*.json` | Each ADR has `adr_id`, `path`, `first_commit`, `status`, `replacement` (a text pointer such as "ADR-045", not a checked path), and `implementation` (`sha`, `date`, `subject`, `reason`, `paths`). Each status change has `path`, `commit`, `date`, `old_state`, `new_state`, `replacement`, `message`. |

## What is missing

1. No reversal list has both the old ADR path and a resolved new ADR path. The replacement field is a phrase copied from the status line.
2. No file lists the commits that carried out the reversal. `implementation` is the Check 3 guess at the commit that first put an ADR into code. In the measured set it is often `sha: null` and `reason: no-code-commit-found`. The 28 of 30 agreement was mostly agreement that no code commit could be identified. The status-change `commit` is the commit that edited the ADR text.
3. The hardness labels cover 15 reversals, not about 30. The remaining 15 have not been labelled. They were not filled in here.
4. Clones are not kept. Two leftover directories were under `/tmp/adr-clones`. `GITHUB_TOKEN` and `GH_TOKEN` are not set, so issue and pull-request text cannot be collected under the brief's token rule.

## What this blocks

Check 6A needs the linked issues, pull requests, and release notes for each reversal, then a blinded packet. Check 6B needs the files changed by the implementing commits. Neither input exists as specified, so neither check was run, including the three-reversal trial.
