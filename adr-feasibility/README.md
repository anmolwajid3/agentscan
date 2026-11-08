# ADR feasibility pilot

Six checks for the study of architecture decision records (ADRs) and AI coding tools. The question is whether GitHub data can support the study at all. Each check has a pass bar that was written into the scripts before the counts were read.

| Check | Question | Pass bar |
| --- | --- | --- |
| 1 | Do enough projects exist? | 50 with an AI signal and at least 5 earlier ADRs, 50 without a signal and at least 5 ADRs, and 100 superseded decisions in those windows |
| 2 | Does the AI signal mean real use? | 16 of 20 flagged projects show use, and the signal date is usually within 92 days of the first observable use |
| 3 | Does the ADR date show when the decision was made? | Most of 30 records can be placed as written-first or written-after, and the script's code commit is right in at least 8 of 10 judged cases |
| 4 | Can the script tell endings apart? | Agreement with a hand label on at least 85% of about 30 status changes |
| 5 | Do two people label the same way? | Cohen's kappa at least 0.6 for decision type and for the yes/no hard dimension |
| 6 | Do the labels match the people who did the work? | Maintainer replies agree in most of the cases that get an answer |

Checks 5 and 6 cannot be finished by one person. The packets, the classification guide, and the unsent letters are in this folder. Kappa is computed only after a second rater fills `data/manual/check5_rater_b.csv`. Maintainer replies go in `data/manual/check6_replies.csv`. Nothing is emailed from this tool.

## Run it

Python 3.11 or newer. No third-party packages.

```bash
cd adr-feasibility
python -m adr_pilot discover
python -m adr_pilot collect --workers 3 --slice pilot
python -m adr_pilot report
```

`discover` builds `data/sampling_frame.csv` from two sources:

- The Buchgeher et al. (2023) census of 921 GitHub ADR repositories, crawled in January 2022. The dataset is cloned from `software-competence-center-hagenberg/ADR-Study-Dataset`.
- Sourcegraph's public index of GitHub, queried for ADR folders (`docs/adr`, `doc/adr`, `docs/decisions`, `architecture/decisions`, and the same paths with archived repositories included).

GitHub's own code search requires a token. If `GITHUB_TOKEN` or `GH_TOKEN` is set, `discover` also runs a code search and adds whatever that returns. Without a token the live search is the Sourcegraph index, which is a search of public GitHub, not a private corpus.

`collect` clones each candidate with `git clone --filter=blob:none` (default branch, blobs fetched only for ADR and signal files), measures it, and deletes the clone. It skips repositories that already have a JSON file in `data/repos/`, so a stopped run can be continued. Projects that are no longer on GitHub are recorded as unavailable and are not dropped from the frame for being inactive. That is the survivorship rule: eligibility uses only history before the AI signal, and a quiet project still counts.

`report` writes `data/SCORECARD.md`, the sample sheets, and the reading packets.

## What counts

An official AI signal is the earliest of:

- `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, or `copilot-instructions.md` outside vendored directories
- a co-author trailer whose name or email is an AI tool, not a person who happens to be named Claude
- a commit authored by an AI coding agent

An ADR counts toward the "at least 5" bar only when its first commit is before that signal. A project whose signal arrives before any ADR is AI-native. It is counted, and it does not fill the quota of 50 projects with a before period.

Superseded means the status block says the decision was superseded or replaced. A template line that merely lists the words "proposed, accepted, rejected, deprecated, superseded" does not count.

## Hand labels

1. Read `guides/classification_guide.md`.
2. Read `data/packets/check3/` and fill `data/manual/check3_labels.csv`. `timing` is `written-first`, `written-after`, or `cant-tell`. `implementation_correct` is `yes` or `no`.
3. Read `data/packets/check4/` and fill `data/manual/check4_labels.csv`. Do this before opening `data/check4_script_labels.csv`.
4. Give `data/packets/check5/` and the guide to a second person. You fill `check5_rater_a.csv`. They fill `check5_rater_b.csv`. Labels are `data-storage`, `interface`, `integration`, `deployment`, `code-structure`, or `other`. `hard` is `yes` or `no`. Scores `d1` to `d5` are 0, 1, or 2.
5. Send the letters in `data/letters.md` yourself. Record answers in `check2_replies.csv` and `check6_replies.csv`.
6. Run `python -m adr_pilot report` again.

## Tests

```bash
python -m unittest discover -s tests
```
