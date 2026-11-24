# Extraction rules and paper card

## Evidence rules
- Base every field on text you actually read. Note the source: `p. 7`, `§5.2 Discussion`, or `abstract` when that's all you had.
- **Copyright:** show a paper's abstract verbatim only if the paper is openly licensed (e.g., CC BY, which you can check in OpenAlex `best_oa_location.license`). Otherwise give a faithful summary labelled "Abstract (AI summary)" plus the DOI link. Quotes: at most one per card, under 15 words, in quotation marks, with a page reference. Don't store long verbatim passages in `library.json`.
- Everything that isn't a quote is an **AI summary** and must be labelled that way on the card.
- **Limitations:** split them into `stated` (the authors say so, with page/section) and `inferred` (your critique, labelled as inferred).
- **Missing section:** write `Not reported`. **Unread section** (paywall, abstract only): write `Not accessible`. Never fill these in from the abstract.
- **Availability:** `Full text` (you read the PDF or HTML body), `Abstract only`, or `Metadata only`.
- **Units and conventions:** state each paper's measurement conventions whenever papers might differ (e.g., a percentage scale that runs in opposite directions, different questionnaire versions, effect-size types). Harmonize them in cross-paper reports.
- **Preprints and grey literature:** flag them as not peer-reviewed.

## Relevance score (0–10)
Use `relevance_rubric` from the profile. If it's absent, use:
- **9–10:** directly addresses the research question with strong evidence.
- **7–8:** strong evidence for one stream that clearly transfers to the research question.
- **5–6:** adjacent context, or mainly a methods or theory source.
- **0–4:** tangential; don't queue it unless asked.

Always explain the score in terms of the profile's research question (and `project_context`, if set). Name which condition, measure, population or finding transfers.

## Record JSON (passed to `state.py add`)
```json
{
  "title": "", "authors": ["Last, F."], "year": 2020, "venue": "", "doi": "10.xxxx/...",
  "url": "https://doi.org/...", "pdf_url": "", "pdf_local": "pdfs/....pdf  (relative to $DATA)",
  "availability": "Full text | Abstract only | Metadata only",
  "peer_reviewed": true,
  "foundational_justification": "only if older than year_range.from",
  "units": "measurement conventions, if relevant",
  "abstract": "AI summary, or verbatim if openly licensed",
  "conclusion":   {"summary": "", "ref": "p. 9"},
  "limitations":  {"stated": [{"text": "", "ref": "§6"}], "inferred": [""]},
  "future_work":  {"summary": "", "ref": "", "status": "reported | Not reported | Not accessible"},
  "methodology": "", "main_findings": [""],
  "relevance_score": 8, "relevance_explanation": "", "streams": [1, 3],
  "sheet": { "<column key>": "<cell text>" },
  "verified": {"crossref": true, "notes": ""}
}
```
`streams` are 1-based indices into the profile's `streams`. `sheet` holds one entry per column `key` in the profile's `sheet.columns` (omit it if no sheet is configured). Write each cell exactly as it will appear, following that column's `instruction`, so the user reviews exactly what will be appended. A column with a `link` (e.g. the title column) needs no cell text: it is built from `title` + link during sync.

## Paper card (printed in chat before each decision)

```
━━━ [3 of 7 pending] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<Title>
<Authors> (<Year>) · <Venue>
DOI: https://doi.org/<doi> · PDF: <url or "none found">
Availability: Full text | Abstract only | Metadata only   [Preprint, if applicable]
Relevance: 8/10 · Streams: <names>
[Older than the year range: <justification>]   [Units: <convention>]

Why it matters (AI summary)
  <2–3 sentences tied to the research question / project context>

Abstract (original | AI summary)
Main findings (AI summary, with refs)
Conclusion (AI summary, with ref)
Limitations
  Stated by authors: …   Inferred by AI: …
Future work (authors): … | Not reported | Not accessible
Methodology: <design, sample, data, analysis>

→ Will be appended to the sheet as:   (only if a sheet is configured)
  <header>: <first ~80 chars>  …for the most informative columns
```
Keep the card under about 60 lines. If the user asks, show the full sheet text before they decide.
