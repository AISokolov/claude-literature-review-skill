# Reports: research gaps, summary, methodology

## Evidence base
- Use **accepted** papers only (`state.py list --status accepted`, then `state.py show <key>`). If a sheet is configured, also use the papers already in the sheet (read all mapped columns). Pending, rejected or search-only papers may be mentioned only as "unvalidated leads" in a separate section.
- When a claim needs a page reference and the cached PDF exists, re-open it (`$DATA/<pdf_local>`) to confirm the reference. Don't rely on memory.
- Start every report with a **coverage section**: date, profile topic (and its status), number of approved papers, papers per stream, the queries run (from `$DATA/search_log.json`), and a caveat that rejected, inaccessible or abstract-only papers limit the conclusions.

## Versioning
Get the path with `state.py next-report research-gaps` (or `summary`, `methodology`). Never overwrite an earlier version. In a new version, open with "Changes since vN": new papers considered, and gaps strengthened, weakened or withdrawn. If the profile changed since the last version, say how.

## Adapting to the discipline
Derive design vocabulary, typical methods, variables and metrics from the profile's discipline **and** from the methods the approved papers actually use. Don't import conventions from other fields. Examples of what "design" can mean:
- **Experimental and quasi-experimental** (lab, field, clinical trial): IVs/DVs, conditions, sample size, measures.
- **Observational and correlational** (cohort, survey, archival, econometric): exposures/predictors, outcomes, confounders, identification strategy.
- **Qualitative** (interviews, ethnography, case study, document analysis): sampling, data sources, analysis approach, credibility criteria.
- **Computational or design research** (simulation, system building, benchmarks): artifacts, datasets, baselines, evaluation criteria.
- **Secondary** (systematic review, meta-analysis): inclusion criteria, databases, synthesis method.

## research-gaps report
Compare across the profile's streams. Look for:
- underexplored questions
- contradictory findings
- methodological limitations
- missing conditions, populations or contexts
- thin empirical evidence
- unexplored combinations of concepts
- opportunities for novel studies

For each gap:
```
### G<n>. <short name>  —  Confidence: High | Medium | Low  —  Type: Well-supported gap | Preliminary hypothesis
**Description:**
**Supporting evidence:** <paper> — what it shows/omits (p./§) …  (≥ 2 papers for "well-supported")
**Counterevidence:** <papers that partly address it, or "none found among approved papers">
**Why existing work is insufficient:**
**Relevance to the research question / project:**
**Suggested research question:**
**Suggested study design:** <in the discipline's own terms, e.g. 3×2 within-subjects N≈24; matched cohort; 15 semi-structured interviews>
**Key variables / constructs:** …
**Recommended measures or evaluation criteria:** <grounded in instruments the approved papers used, where possible>
```
Never call something a gap just because a search returned nothing. Absence of results is only "not found under queries X, Y". It can support a *preliminary hypothesis*, not a well-supported gap.

## summarize report
Common findings (with the papers that agree), contradictions (who vs. whom, and plausible reasons such as population, setting or measurement), recurring limitations, and the current answer to the research question with its confidence.

## methodology report
A table of approved papers: design, sample, setting, variables or constructs, instruments, analysis. Then the most common designs and measures in this literature, what each can and cannot establish, and 1–3 concrete study designs suited to the profile's research question. Ground every recommended choice in specific papers.
