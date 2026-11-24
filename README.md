# literature-review: a Claude Code skill for academic literature reviews

A [Claude Code](https://claude.com/claude-code) skill that helps you find, verify, read and review academic literature for a thesis or research project, in any discipline.

- **Discovery:** keyword, phrase and citation-tracking searches over OpenAlex, Semantic Scholar and Crossref, plus discipline databases (Europe PMC, PubMed, arXiv, DBLP, ERIC, IEEE Xplore, CORE).
- **Verification:** every paper is checked against Crossref or DataCite. Nothing is invented: missing sections are marked `Not reported` or `Not accessible`.
- **Full-text analysis:** only from legal open-access copies (or PDFs you supply), with page and section references. AI summaries are kept apart from author statements, and stated limitations apart from inferred ones.
- **Human-in-the-loop review:** each paper is shown as a card with **Accept / Reject / Skip** buttons. Nothing is approved automatically.
- **Optional Google Sheets sync:** accepted papers are appended to *your existing* literature spreadsheet using *your* columns. Rows are never overwritten, and retries never create duplicates.
- **Duplicate prevention and persistent history:** rejected papers stay out of future searches; decisions survive between sessions.
- **Evidence-based reports:** research gaps, literature summaries and methodology overviews, versioned and never overwritten.

Everything adapts to a **research profile** (topic, research streams, search terms), set up interactively the first time you run the skill.

## Requirements

| | Needed for | Notes |
|---|---|---|
| Claude Code (CLI, desktop or IDE extension) | everything | |
| Python 3.8+ | `scripts/state.py` (local state) | standard library only, no `pip install` |
| `curl` | API calls and PDF downloads | built into Windows 10+, macOS and Linux |
| Google Sheets connector | *optional*: syncing accepted papers to a sheet | claude.ai → Settings → Connectors → Google Sheets (add Google Drive to find sheets by name). In the CLI, check it with `/mcp`. |
| `OPENALEX_API_KEY` | *optional*: higher OpenAlex limits | free at <https://openalex.org/settings/api> |
| `S2_API_KEY` | *optional*: reliable Semantic Scholar access | free at <https://www.semanticscholar.org/product/api> (unkeyed requests are often rate-limited) |
| `IEEE_API_KEY`, `CORE_API_KEY` | *optional*: IEEE Xplore / CORE search | |

## Installation

Clone the repository into your personal skills folder:

```bash
# macOS / Linux
git clone https://github.com/AISokolov/claude-literature-review-skill.git ~/.claude/skills/literature-review
```
```powershell
# Windows (PowerShell)
git clone https://github.com/AISokolov/claude-literature-review-skill.git "$HOME\.claude\skills\literature-review"
```

That's it: the skill is available in every Claude Code session, from any folder. To update later, run `git pull` in that folder. Your personal data in `data/` is git-ignored and is never touched by an update.

To set API keys, add them to your shell environment (for example `setx S2_API_KEY "..."` on Windows, or `export S2_API_KEY=...` in your shell profile), then start a new session.

## First run

```
/literature-review
```

With no profile yet, the skill runs setup and asks for:

- **Required:** thesis topic (a preliminary topic is fine), research streams, search terms. If you don't have streams or terms yet, it suggests some from your topic for you to confirm or edit.
- **Optional:** research question, discipline, year range, preferred journals, conferences and databases, and a Google Sheets URL plus worksheet.

If you give a spreadsheet, the skill reads its header row and existing rows, proposes how each column should be filled (matching your current writing style), and asks about anything ambiguous. It never creates a new spreadsheet or changes your columns.

The profile is saved to `data/research-profile.json` and loaded automatically from then on. See [`research-profile.example.json`](research-profile.example.json) for a complete example from another field.

## Usage

Commands are natural language: these are examples, not strict syntax.

| Command | What it does |
|---|---|
| `/literature-review` | Search across all streams and present new papers for review |
| `/literature-review find <topic>` | Targeted search |
| `/literature-review find 10 papers` | Find N new, verified, relevant papers |
| `/literature-review analyze <DOI or URL>` | Analyze one paper and queue it for review |
| `/literature-review related <DOI or URL>` | Citation tracking plus related works |
| `/literature-review review` | Resume the pending review queue |
| `/literature-review sync` | Retry Google Sheets sync for accepted papers |
| `/literature-review reconsider <title or DOI>` | Bring back a rejected paper |
| `/literature-review status` | Pending, accepted, rejected and synced counts |
| `/literature-review research-gaps` | Evidence-based gap report from accepted papers |
| `/literature-review summarize` | Common findings, contradictions, limitations |
| `/literature-review methodology` | Methods used in the literature, plus study designs suited to your question |
| `/literature-review setup` | Create or redo the research profile |
| `/literature-review profile` | Show the current profile |
| `/literature-review update topic` / `streams` / `terms` | Edit one part of the profile |

Updating the profile never deletes papers, review decisions or reports.

## Where your data lives

All personal data stays local in `data/`, which is excluded from git:

```
data/
  research-profile.json   your profile (topic, streams, terms, sheet ID and column mapping)
  library.json            every paper surfaced: pending / accepted / rejected, sheet sync status
  sheet_index.json        DOIs/titles already in your sheet (for duplicate checks)
  search_log.json         queries run (search coverage for gap reports)
  pdfs/                   cached open-access PDFs
  reports/                research-gaps-v001.md, summary-v001.md, …
```

To move to another computer, copy `data/` along with the skill.

## How it works

```
SKILL.md                         workflow, commands, non-negotiable rules
references/profile-setup.md      first-run setup and profile commands
references/search-strategy.md    APIs, discipline sources, query building, legal full-text sources
references/extraction.md         evidence rules, record format, paper card
references/sheet-sync.md         duplicate-safe, append-only Google Sheets procedure
references/gap-analysis.md       gap / summary / methodology report formats
scripts/state.py                 local JSON state (review queue, decisions, sync status, dedupe)
research-profile.example.json    example profile
```

There's no server, database or web app: Claude Code does the research, and a small Python script keeps the local state consistent.

## Limitations

- Paywalled papers are never bypassed. Without a legal open-access copy, a paper is marked `Abstract only` or `Metadata only`, and its conclusions or limitations are not inferred. You can download PDFs through your own institutional access and give Claude the file path.
- Some publisher sites (ACM DL, IEEE, ScienceDirect, …) block scripted downloads; the skill skips them.
- Free API tiers are rate-limited; API keys help.
- Abstracts of closed-access papers are summarized rather than reproduced, out of respect for copyright.
- AI summaries can contain errors: check important claims against the cited page.

## License

[MIT](LICENSE)
