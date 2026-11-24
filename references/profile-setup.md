# Research profile: setup and management

The profile lives at `$SKILL/data/research-profile.json` (git-ignored). Its schema is shown by `$SKILL/research-profile.example.json`. `state.py profile-check` reports a missing file or missing required fields.

## First-run setup (or `setup`)

Ask conversationally, a few questions at a time. Use AskUserQuestion where the answer is a choice; use plain chat for free text.

**Required**
1. **Topic:** title or general subject. Ask whether it is `confirmed` or `preliminary`. Preliminary topics are fine; store alternative wordings in `topic.alternatives`.
2. **Research streams:** 2–6 main research areas, each with a one-line description.
3. **Search terms:** keywords and phrases.

If the user has no streams or terms yet, **propose** them from the topic, question and discipline (e.g., 3–5 streams, 10–20 terms including synonyms and field-specific jargon), then ask the user to confirm or edit. Never save suggestions without confirmation.

**Optional:** ask once; the user may skip any of these.
- Central research question.
- Academic discipline.
- `project_context`: a system, artifact, population or case the research is about.
- Preferred year range (default: last ~15 years, with older foundational work allowed).
- Preferred journals, conferences and databases.
- Google Sheets URL and target worksheet (tab).

**Derived by you (don't ask; show for confirmation)**
- `openalex_filters.subfield_ids`: look up the discipline with `https://api.openalex.org/subfields?search=<discipline>&select=id,display_name,field`. Pick 1–3 matching subfield IDs (numeric part only). Leave empty for very interdisciplinary topics.
- `relevance_rubric`: four bands (9–10, 7–8, 5–6, 0–4) phrased in terms of this research question and its streams.
- `preferred_sources.databases`: suggest discipline databases from `search-strategy.md` if the user named none.

**Google Sheet (only if the user gave one)**
1. Resolve the URL to a spreadsheet ID. If the user only gave a name, search Drive and confirm when several files share a name. Record any same-named files that must not be written in `do_not_write`.
2. Read the sheet: tabs (`get_spreadsheet` with `sheets.properties`), header row, a few data rows, formulas and rich-text links in the first column.
3. Propose a `columns` mapping: for each header, a `key` (snake_case), a writing `instruction` that matches the style of the existing rows (bullets vs prose, length), and an optional `link` (`{"text": "Source", "target": "pdf_then_doi" | "doi"}`) if existing rows link a word to the paper.
4. Ask about every ambiguous column (e.g., is "Future work" the authors' own future work or a suggested follow-up?). Set `mapping_confirmed: true` only after the user confirms.
5. Never create a new spreadsheet or change existing columns.

**Save:** write `data/research-profile.json`, run `state.py profile-check`, show a short summary, and offer to start the first search.

## Profile commands

- **`profile`:** show the topic (and its status), question, discipline, streams, term count (list terms on request), years, sources, and whether a sheet is configured (name and tab; don't print the ID unless asked).
- **`update topic` / `update streams` / `update terms` / `update <field>`:** show the current value, take the change (or propose one on request), confirm, and write **only that field**. For streams and terms, support add, remove and replace. After a topic or stream change, offer to regenerate the relevance rubric.
- **`update sheet`:** redo the Google Sheet steps above.
- **Topic confirmed later:** set `topic.status` to `confirmed` and keep earlier wordings in `alternatives`.

Updating the profile never touches `library.json`, `search_log.json`, `sheet_index.json`, `pdfs/` or `reports/`. Earlier relevance scores stay as they were. If the topic changed substantially, mention that pending papers were scored against the old profile.
