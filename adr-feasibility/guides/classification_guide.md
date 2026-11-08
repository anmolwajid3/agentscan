# Classification guide

Use this guide for checks 4, 5, and 6. Label on your own. Do not discuss a case with the other rater until both of you have written your labels down.

The five scores come from the signals named in the study plan: migration, people outside the project, how widely the change spreads, how long the transition lasts, and how much coordination or checking is visible. The separate Claude document that first listed them was not in the export, so the definitions below are the ones this pilot uses. Both raters must use these definitions and not a private scale.

## Decision type

Pick one.

| Type | Use it when the decision is mainly about |
| --- | --- |
| data-storage | where data lives, the schema, the database, a log, or a queue of stored facts |
| interface | an API, a CLI, a UI contract, or public types other code calls |
| integration | how this system talks to another system, including protocol and outside authentication |
| deployment | runtime, hosting, CI, or environments |
| code-structure | modules, layering, language, framework, or structure inside one process |
| other | security policy, licensing, team process, or a mix that does not fit |

If two types fit, pick the one that made the reversal hard. A database change that also renames a module is data-storage.

## Hard dimension

Answer yes or no.

Yes if any one of these is true:

- existing data had to be moved or converted (a new empty table is not enough)
- users or other systems had to change
- the transition was long: more than one release, or the record names a deprecation window

No if the reversal is code inside this project, with no stored data, no outside caller, and no waiting period.

## Five scores

Each score is 0, 1, or 2. Score what the repository shows, not what might have happened off GitHub.

| Score | 0 | 1 | 2 |
| --- | --- | --- | --- |
| D1 Data | no data impact | schema or format change for new data only | existing data migrated or converted |
| D2 Outside parties | nobody outside this codebase | internal callers only | external users or other systems must change |
| D3 Spread | one module or package | several modules in this repository | several services or repositories |
| D4 Transition | cut over in one change | a compatibility shim or deprecation in a single release | more than one release, or a long parallel run |
| D5 Checking | nothing visible beyond the edit | a review discussion or a version bump | security or legal review, several teams, or a long check afterwards |

The hard dimension is yes when D1 is 2, or D2 is 2, or D4 is 2. The scores can still disagree with a quick reading, which is why both are recorded.

## Cheap, moderate, expensive

This scale is secondary. The pass bar for check 5 uses decision type and the yes/no hard dimension.

- cheap: hard is no, and D1 + D2 + D3 + D4 + D5 is 3 or less
- expensive: hard is yes, and the sum is 6 or more
- moderate: every other case

## Endings (check 4)

| Label | Use it when |
| --- | --- |
| replaced | a new decision takes this one's place. A pointer such as "superseded by ADR-0012" is the usual sign |
| no-longer-needed | the decision was dropped, deprecated, or left obsolete, and nothing replaced it |
| rejected-before-use | it was still a proposal, and the team turned it down |
| cleanup-or-rename | the file was moved, renumbered, or reworded, and the decision did not change |

A status that was accepted and is later rejected, with no replacement, is no-longer-needed. Rejected from proposed is rejected-before-use.

## Minutes

Write how many minutes the case took, including reading the record. That number is how the full study's effort gets estimated.
