# FORMA study screening

Screened studies on the architecture, verification, evidence, trust, and reliability of LLM and agentic systems, collected for the FORMA paper.

The studies, PDFs, and the screening workbook are in [`forma-screening/`](forma-screening/).

| Item | What it is |
| --- | --- |
| `forma-screening/FORMA-screening.xlsx` | One row per study: ID, title, authors, year, venue, DOI or URL, publication status, PDF status, and a short reason for inclusion. A second sheet records the search date, the query, and the filters. |
| `forma-screening/S01.pdf` … | Full text, when an open PDF could be retrieved. The file name is the ID in the workbook. |

`S01`–`S1335` run in year order, newest first, then by first author and title. `S01` is the first row, not a ranking. `S1336`–`S1351` were added later from the first five Google Scholar pages and were not renumbered into that sort.

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

Google Scholar blocked automated queries from this environment (HTTP 403 and 429, including from a normal Chrome window). The same Boolean query was run on the arXiv API and on OpenAlex. On 3 November 2026 the first five Scholar result pages were supplied from a browser and reconciled with the workbook: existing IDs were kept, 16 relevant studies were appended as `S1336`–`S1351`, and four domain or off-target hits were left out. The search-record sheet states the counts, the OpenAlex page cap, and the screening rules.

## How to review

Open `forma-screening/FORMA-screening.xlsx`. Filter or sort there. Where the PDF status is `unavailable`, the DOI or URL is still in the row. Where the status is `preprint PDF; published version unavailable`, the file is the open preprint and the bibliographic fields point at the published version.

No theme labels have been assigned. The reason column only says why the study was kept.
