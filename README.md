# Repository

Two pieces of work live here.

The ADR feasibility pilot is in [`adr-feasibility/`](adr-feasibility/). It runs the six checks for the study of architecture decision records and AI coding tools, and it stores the sampling frame, the measured repositories, the scorecard, and the labeling packets.

The rest of this repository is the FORMA study screening described below.

# FORMA study screening

Eleven studies for the related work of the FORMA paper. Each one can change a paragraph. The question is whether a designated verifier can check a cross-agent requirement from the evidence it is allowed to see.

The workbook is [`forma-screening/FORMA-screening.xlsx`](forma-screening/FORMA-screening.xlsx).

| Sheet | What it is |
| --- | --- |
| Studies | Eleven rows. The ID is the order the studies would be used in the paper, not a rank. Each row has the FORMA element it informs, why it is here, what it does not do, and where it goes in the draft. |
| Screening log | What happened to every row of the other 18-row sheet, the three studies added here, and the papers that were considered and left out. |
| Search record | The query, the date, and the corrections to venues and authors. |

The PDFs are in [`papers/`](papers/). `papers/Claude/` uses the other sheet’s numbers, `papers/Cursor/` uses this sheet’s numbers. A file ending in `-D` is in both lists. The same study keeps its own number in each folder, so Claude `S01-D` is Cursor `S02-D`.

The search was run on **3 November 2026 (Europe/Kyiv)**, limited to work from **2022 onward**.

```text
("LLM agents" OR "LLM-based agents" OR "large language model agents"
 OR "agentic AI" OR "agentic systems" OR "multi-agent LLM"
 OR "agent-to-agent")
AND
(architecture OR verification OR assurance OR "runtime enforcement"
 OR "trust management" OR "evidence sharing" OR "information flow"
 OR "access control" OR reliability)
```
