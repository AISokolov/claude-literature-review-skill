---
name: literature-review
description: Research assistant for academic literature reviews in any discipline, driven by a personal research profile (topic, research streams, search terms). Finds and verifies peer-reviewed papers via OpenAlex/Semantic Scholar/Crossref and discipline databases, extracts findings with page references from legal full texts, runs a human Accept/Reject review queue, optionally appends accepted papers to the user's Google Sheet, and writes evidence-based research-gap, summary and methodology reports. Use for /literature-review, research profile setup, finding papers, analyzing a DOI/URL, citation tracking, research gaps, or literature summaries.
argument-hint: "[setup | profile | update topic|streams|terms | find <topic> | find <N> papers | analyze <DOI/URL> | related <DOI/URL> | review | sync | research-gaps | summarize | methodology | status]"
---

# Literature Review Assistant

Skill directory: `~/.claude/skills/literature-review/` (call it `$SKILL`).
State helper: `python "$SKILL/scripts/state.py" <command>` (run without args for help).
User data lives in `$SKILL/data/`: the research profile, review history, cached PDFs and reports. It is never committed to git.

Read these on demand, not all up front:
- `data/research-profile.json`: the user's research profile. **Load it at the start of every invocation.**
- `references/profile-setup.md`: first-run setup, profile commands, profile schema.
- `references/search-strategy.md`: API endpoints, discipline-specific sources, query building, citation tracking.
- `references/extraction.md`: what to extract, evidence rules, the paper card format.
- `references/sheet-sync.md`: the optional Google Sheets append procedure.
- `references/gap-analysis.md`: gap, summary and methodology report formats.

## Step 0: load the research profile (every invocation)

Run `state.py profile-check`.
- **`missing profile` or missing required fields:** run setup from `references/profile-setup.md` before anything else, unless the request is only `status`.
- **Profile OK:** read `data/research-profile.json` and use it as the research context. Don't ask setup questions again.

All of the following derive from the profile: topic, research question, `project_context`, streams, terms, years, preferred sources, relevance rubric and sheet. Never assume a discipline the profile doesn't state.

## Non-negotiable rules

1. **Never fabricate.** Every paper must resolve via DOI (Crossref, DataCite or OpenAlex) or a publisher page you actually fetched. Every finding, limitation or quote must come from text you actually read. If you didn't read it, write `Not reported` or `Not accessible`.
2. **Never auto-decide.** Only the user's explicit Accept/Reject (via the AskUserQuestion prompt or a plain chat instruction naming the paper) changes a paper's status.
3. **Only accepted papers go to the sheet**, only by appending a new row, and only via `references/sheet-sync.md`. Never edit, reorder, reformat or delete existing rows or headers without explicit permission for that specific change.
4. **Label provenance.** Mark verbatim text as quotes with a page or section; mark everything else as AI summary. Separate author-stated limitations from AI-inferred ones.
5. **Approval status ≠ sync status.** Always report both.
6. **Profile changes never touch history.** Updating the profile must not delete or alter papers, decisions, sync state, search logs or reports.

## Commands (natural language is fine: map the request to the nearest one)

| Request | Do |
|---|---|
| `setup` | Create or reconfigure the profile (`references/profile-setup.md`). |
| `profile` | Show the current profile in readable form. |
| `update topic` / `update streams` / `update terms` / `update <field>` | Edit only that field, confirm, save (`references/profile-setup.md`). |
| *(no args)* | Status line, then a search across all streams (default 5 papers), then review. |
| `find <topic>` | Targeted search → review. |
| `find <N> papers` | Search until N new, relevant, verified candidates are found (or sources are exhausted: say so) → review. |
| `analyze <DOI/URL>` | Resolve and extract that paper → review. |
| `related <DOI/URL>` | Backward references + forward citations + related works → rank → review. |
| `review` | Resume the pending queue. |
| `sync` | Retry every `accepted` + `sync_pending` paper. |
| `reconsider <title/DOI>` | `state.py decide <key> reconsider`, then review it. |
| `status` | `state.py stats` plus a one-line search coverage summary. |
| `research-gaps` / `summarize` / `methodology` | See `references/gap-analysis.md`. |

## Discovery workflow

1. **Status + dedupe baseline.** Run `state.py stats`. If the profile has a sheet, refresh the sheet index (step 1 of `references/sheet-sync.md`) once per session before the first search.
2. **Search** using `references/search-strategy.md`, with queries built from the profile. Log every query with `state.py log-search`.
3. **Pre-filter.** Write the raw candidates (`[{"doi":..,"title":..}]`) to a temp JSON and run `state.py filter`. Drop everything it reports as known. Previously rejected papers stay out unless the user asks for them.
4. **Screen** by title, abstract and venue against the profile, using its `relevance_rubric` (or the default rubric in `references/extraction.md`). Keep only papers that plausibly score ≥ 6/10. Respect `year_range`. Allow older work only if `allow_older_foundational` is true and the paper is clearly foundational; say why.
5. **Verify** metadata via Crossref `/works/{doi}`, or DataCite `/dois/{doi}` if Crossref returns 404. Title, authors, year, venue and DOI must agree. Drop or flag anything that doesn't resolve.
6. **Full text.** Find a legal open-access copy (see `references/search-strategy.md` §Full text). Download it to `$SKILL/data/pdfs/<doi with / replaced by _>.pdf`, check it's a real PDF, then read it with the Read tool (use `pages` for long PDFs). Never bypass paywalls or bot checks. Set availability to `Full text`, `Abstract only` or `Metadata only`.
7. **Extract** per `references/extraction.md`. If the profile has a sheet, fill `sheet.<key>` for each configured column. Save to a temp JSON and run `state.py add <file>`. The paper is now `pending`.
8. Continue with the review loop.

For several candidates, you may parallelize steps 6–7 with subagents (one per paper). Give each one `references/extraction.md` and the relevant profile fields, and require JSON-only output. You assemble the cards and run the review yourself.

## Review loop

For each `pending` paper (`state.py list --status pending`, highest relevance first):

1. Print the **paper card** (format in `references/extraction.md`) as normal chat output.
2. Ask with **AskUserQuestion**: header `Decision`, question `"Accept or reject: <short title>?"`, options:
   - `Accept`: approve (and append to the sheet, if one is configured)
   - `Reject`: exclude from the database and future searches
   - `Skip for now`: keep it pending
   - The user can also type free text, e.g. "accept but note X", or "stop".
3. Apply it: `state.py decide <key> accept|reject|skip --note "<user note>"`.
4. On **Accept**, if the profile has a confirmed sheet mapping, immediately run `references/sheet-sync.md` for that paper. Then run `state.py sync-ok` or `state.py sync-fail`. A sync failure never reverts the approval. Without a sheet, accepted papers stay in the local library only, and the `sync` status stays `sync_pending` until a sheet is configured.
5. Show a one-line tally after each decision: `Pending 3 · Accepted 5 · Rejected 2 · Synced 4 · Awaiting sync 1`.
6. Stop when the queue is empty or the user says stop. Pending papers persist across sessions.

## Output hygiene

- Keep paper cards readable: short headings, no walls of JSON.
- Reports go to `state.py next-report <name>` paths (versioned, never overwritten). Give the user the path and a short summary in chat.
- At the end of a run, report what was searched, how many candidates were screened, how many were dropped and why (duplicate, off-topic, unverifiable, no legal full text), and how many were queued.
