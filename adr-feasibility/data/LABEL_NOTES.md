# How the hand labels were made

One person read the packets on 8 November 2026 (Europe/Kyiv) and filled checks 3, 4, and 5 (rater A). Check 4 was labeled from the packets before the script labels were opened. A second rater has not labeled check 5. No maintainer has been emailed. The letters are in `letters.md`.

## Check 1 recount

The adoption date was already the earliest of the instruction file, an AI co-author line, and an agent author. Recounting with that date does not move the pass bar: 67 projects still have a signal and at least 5 earlier ADRs, 273 have at least 5 ADRs and no signal, and 133 superseded records sit in those windows.

Those 133 split into 32 written before adoption and 101 in projects with no signal. Two further superseded records in eligible AI projects were written after adoption. They were not inside the 133. No superseded record lacked a date.

## Check 2

The first 20 (seed 20261108, kept in `check2_development_sample.csv`) confirmed use in 19 of 20. The date half failed, 14 of 19 within 92 days. The long gaps were commit-message mentions dated years before the strong signal, including a Cloud Foundry component named Copilot. Those mentions are not the adoption date.

The reported sample is a new 20 flagged projects and a new 20 unflagged projects, seed 20261111, excluding those 40 repositories. The adoption date is the earliest strong signal. The gap is the distance from that date to the earliest co-author or agent author. 19 of 20 show use on or after the adoption date. 17 of 18 projects that have a co-author or agent-author date are within 92 days. The one longer gap is Sylius/Sylius: `AGENTS.md` on 12 June 2025, first co-author on 2 October 2026, 478 days. Two projects have no co-author and no agent author, so their gap is blank rather than zero. One of those two still has a later strict mention, so use is confirmed. The other only adds the instruction file.

A hidden trace means a strict tool mention, co-author, or agent author in a project with no strong signal. The fresh 20 unflagged projects have none. That is not proof that unflagged projects never use AI. The earlier "cursor position" commit is not a hidden trace.

## Check 3

12 of 30 records could be placed. 3 were written first. 9 were written after. 18 had no discussion to compare, so they stay "can't tell". Most records cannot be placed, so the timing question does not pass. The script's code commit agreed in 28 of 30. Both misses were broad paths (`node/node.go`, and a later pile of test files) rather than the commit that introduced the decision.

## Check 4

The first 30 (seed 20261108) agreed on 24 of 30 (80%). Those rows are kept in `check4_development_sample.csv` and are not the reported score. The misses that named another decision were "deprecated by ADR-N", "deprecated as of ADR-N", and "rejected, see ADR-N". The rules now treat those phrases as a replacement. "Deprecated (no superseding ADR)" is not a replacement. A bare year, as in "deprecated by 2021", is not one either.

The reported score is a fresh sample of 30 (seed 20261110) that shares no file with the first 30. The script agreed on 29 of 30 (97%). The miss is `SAP/cloud-sdk-js` `0002-cli-scaffold.md`: the text says the CLI is deprecated and to use the sample projects instead. The hand label is replaced. The script says no-longer-needed, because the pointer is not an ADR.

The fresh sample has 9 replaced, 4 no-longer-needed, 1 rejected-before-use, and 16 cleanup-or-rename. The measured repositories only contain 9 rejected-before-use transitions and 9 no-longer-needed transitions, and the first sample had already taken 8 of the rejected ones. The fresh sample therefore includes every remaining case of those two labels, then fills the rest with cleanup. On the 14 cases that are not cleanup, agreement is 13 of 14.

## Check 5 and 6

Rater A took about 81 minutes for 15 reversals, roughly 5 minutes each. Kappa waits on rater B (`data/manual/check5_rater_b.csv` and `guides/classification_guide.md`).

Check 6A and 6B were not built. The inputs they require are listed in `check6/INPUTS.md`. The hardness labels cover 15 reversals, not 30, and there is no list of the commits that carried out each reversal.
