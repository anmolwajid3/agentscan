# How the hand labels were made

One person read the packets on 8 November 2026 (Europe/Kyiv) and filled checks 3, 4, and 5 (rater A). Check 4 was labeled from the packets before the script labels were opened. A second rater has not labeled check 5. No maintainer has been emailed. The letters are in `letters.md`.

## Check 2

19 of 20 flagged projects have a co-author line, an agent author, or a tool mention on or after the signal date. That half of the bar passes. The timing half does not: 14 of 19 observable start dates are within 92 days, which is 74%, under the 80% bar. Three gaps are long because a co-author line appears months or years before the instruction file (527, 867, and 2887 days). The file is a late marker. The pre-written response applies: date adoption from the co-author line, or call the file projects AI-configured rather than AI-using.

None of the 20 unflagged projects had a strict hidden-use hit after one false hit was removed. That hit was a commit about a UI cursor position. It is not Cursor the editor.

## Check 3

12 of 30 records could be placed. 3 were written first. 9 were written after. 18 had no discussion to compare, so they stay "can't tell". Most records cannot be placed, so the timing question does not pass. The script's code commit agreed in 28 of 30. Both misses were broad paths (`node/node.go`, and a later pile of test files) rather than the commit that introduced the decision.

## Check 4

The first 30 (seed 20261108) agreed on 24 of 30 (80%). Those rows are kept in `check4_development_sample.csv` and are not the reported score. The misses that named another decision were "deprecated by ADR-N", "deprecated as of ADR-N", and "rejected, see ADR-N". The rules now treat those phrases as a replacement. "Deprecated (no superseding ADR)" is not a replacement. A bare year, as in "deprecated by 2021", is not one either.

The reported score is a fresh sample of 30 (seed 20261110) that shares no file with the first 30. The script agreed on 29 of 30 (97%). The miss is `SAP/cloud-sdk-js` `0002-cli-scaffold.md`: the text says the CLI is deprecated and to use the sample projects instead. The hand label is replaced. The script says no-longer-needed, because the pointer is not an ADR.

The fresh sample has 9 replaced, 4 no-longer-needed, 1 rejected-before-use, and 16 cleanup-or-rename. The measured repositories only contain 9 rejected-before-use transitions and 9 no-longer-needed transitions, and the first sample had already taken 8 of the rejected ones. The fresh sample therefore includes every remaining case of those two labels, then fills the rest with cleanup. On the 14 cases that are not cleanup, agreement is 13 of 14.

## Check 5 and 6

Rater A took about 81 minutes for 15 reversals, roughly 5 minutes each. Kappa waits on rater B (`data/manual/check5_rater_b.csv` and `guides/classification_guide.md`). Check 6 waits on replies to the ten letters.
