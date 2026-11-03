# FORMA study screening

Fourteen studies for the FORMA paper, on whether a designated verifier can check a cross-agent requirement from the evidence it is allowed to see.

The studies, PDFs, and the workbook are in [`forma-screening/`](forma-screening/).

| Item | What it is |
| --- | --- |
| `forma-screening/FORMA-screening.xlsx` | One row per study: ID, title, authors, year, venue, DOI or URL, publication status, PDF status, and a short reason for inclusion. A second sheet records the search and why the set was cut to these fourteen. |
| `forma-screening/S01.pdf` … `S14.pdf` | Full text. The file name is the ID in the workbook. |

`S01` is the first row, not a ranking. Rows run by year, newest first, then by first author. No theme labels have been assigned.

## Search

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

Google Scholar blocked automated queries from this environment. The same Boolean query was run on arXiv and OpenAlex, and the first five Scholar pages were screened from a browser export. That pass kept a much larger set. This folder keeps the fourteen studies closest to architectural verifiability: evidence available to a named verifier, the trust assumptions behind that evidence, information flow and isolation, runtime verification and enforcement, and failures of multi-agent LLM systems.

Three of the fourteen are already cited in the draft: AgentLeak, AgentSpec, and “Why Do Multi-Agent LLM Systems Fail?”. Protocol documents and the draft’s attack and fault benchmarks were not repeated. The search-record sheet names them.
