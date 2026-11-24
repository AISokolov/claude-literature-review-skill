# Search strategy

Call the APIs with `curl -s -m 30` from Bash and parse with `python -c` (or `jq` if available). URL-encode queries. On Windows, set `PYTHONIOENCODING=utf-8` when printing titles.
Optional API keys are read from the environment if set: `OPENALEX_API_KEY`, `S2_API_KEY`, `IEEE_API_KEY`, `CORE_API_KEY`. Without them, the APIs are rate-limited: on HTTP 429, back off and retry once, then switch source and tell the user.

## Building queries from the profile
- Use the topic, research question, stream names and descriptions, and `terms`.
- Combine terms **within** a stream (synonyms joined by OR) and **across** streams (AND), e.g. `<stream-1 term> AND <stream-3 term>`. Cross-stream queries find the most specific work.
- Every default run should cover at least two streams unless the user named a topic.
- Use exact phrases for multi-word technical terms. In OpenAlex, put the phrase in quotes inside `title_and_abstract.search:`.
- Apply `year_range` as filters. Use `openalex_filters.subfield_ids` to cut off-field noise: without it, ambiguous words (e.g., "cell", "network", "model", "resistance") pull in unrelated fields. Drop the filter for queries that deliberately reach into a neighbouring field.
- **Citation tracking** from papers already accepted or already in the sheet is usually more precise than keyword search. Do it early.

## Universal sources

### OpenAlex (primary: broad, free, includes OA links)
- **Search:** `https://api.openalex.org/works?search=<q>&filter=publication_year:>{from-1},primary_topic.subfield.id:<id1>|<id2>,type:article|conference-paper|review&per_page=25&select=id,doi,title,publication_year,authorships,primary_location,best_oa_location,cited_by_count,abstract_inverted_index,related_works`
- **Phrase search:** `filter=title_and_abstract.search:"<phrase>"` (field-level filter: `primary_topic.field.id:<id>`)
- **Single work:** `https://api.openalex.org/works/https://doi.org/<doi>`
- **Forward citations:** `https://api.openalex.org/works?filter=cites:<openalex_id>&per_page=50&sort=cited_by_count:desc`
- **Backward references:** the `referenced_works` field; batch-fetch with `filter=openalex_id:W1|W2|...`
- **Related works:** the `related_works` field.
- **Abstract:** rebuild from `abstract_inverted_index` (place each word at its positions).
- **Venue:** `primary_location.source.display_name`. **OA PDF and license:** `best_oa_location.pdf_url` and `.license`.
- **Discipline lookup:** `https://api.openalex.org/subfields?search=<discipline>`
- **Work types:** use OpenAlex's own type names, e.g. `conference-paper`, not Crossref's `proceedings-article`.
- If `OPENALEX_API_KEY` is set, append `&api_key=$OPENALEX_API_KEY`.

### Semantic Scholar (semantic relevance, citations, OA PDFs)
- **Search:** `https://api.semanticscholar.org/graph/v1/paper/search?query=<q>&year=<from>-&fieldsOfStudy=<fields>&limit=20&fields=title,year,venue,externalIds,abstract,openAccessPdf,citationCount`
- **Paper:** `/graph/v1/paper/DOI:<doi>?fields=...`
- **Citations / references:** `/graph/v1/paper/DOI:<doi>/citations` and `/references`
- **Recommendations:** `https://api.semanticscholar.org/recommendations/v1/papers/forpaper/DOI:<doi>?fields=title,externalIds,year`
- Send the header `-H "x-api-key: $S2_API_KEY"` if set. Without a key, expect 429s; wait a few seconds between calls. Abstracts of some publishers are elided.

### Crossref / DataCite (metadata verification: source of truth)
- `https://api.crossref.org/works/<doi>` gives title, author, container-title, issued, page.
- **Title lookup:** `https://api.crossref.org/works?query.bibliographic=<title>&rows=3`. Accept a match only if the normalized titles match and the year is within ±1.
- If Crossref returns 404 (some proceedings and repositories register with DataCite): `https://api.datacite.org/dois/<doi>`.

## Discipline-specific sources (use those relevant to the profile)

| Discipline | Source | Endpoint / note |
|---|---|---|
| Biomedicine, health, life sciences | Europe PMC (OA full text, no key) | `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=<q>&format=json&resultType=core` |
| | PubMed | Use the PubMed connector if connected, else E-utilities `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=<q>&retmode=json` |
| Computer science, physics, mathematics | arXiv (preprints: flag as not peer-reviewed) | `http://export.arxiv.org/api/query?search_query=all:<q>&max_results=20` (Atom XML) |
| | DBLP (CS venue and author lookup) | `https://dblp.org/search/publ/api?q=<q>&format=json` |
| Engineering, electronics | IEEE Xplore (needs `IEEE_API_KEY`) | `https://ieeexploreapi.ieee.org/api/v1/search/articles?querytext=<q>&start_year=<from>&apikey=$IEEE_API_KEY` |
| Education | ERIC | `https://api.ies.ed.gov/eric/?search=<q>&format=json&rows=20` |
| Economics, social sciences | RePEc/IDEAS, SSRN | No stable public API; use OpenAlex with the right subfield, plus the web-fetch agent for landing pages. |
| Any (OA full text) | CORE (needs `CORE_API_KEY`) | `https://api.core.ac.uk/v3/search/works?q=<q>` |

Publisher platforms (ACM DL, IEEE Xplore, ScienceDirect, Springer, Wiley, T&F) often block scripted downloads with bot checks. Never bypass them: use Crossref/OpenAlex for metadata and look for a legal copy elsewhere. If the user has institutional access, they can download PDFs themselves and give you the file paths.

## Full text (legal sources only), in order
1. OpenAlex `best_oa_location.pdf_url` and other `locations[].pdf_url`
2. Semantic Scholar `openAccessPdf.url`
3. Europe PMC / PubMed Central (biomedicine), arXiv
4. Institutional repositories, e.g. HAL: `https://api.archives-ouvertes.fr/search/?q=doiId_s:"<doi>"&fl=uri_s,fileMain_s`
5. The author's own publication page (fetch it and look for a PDF link)
6. A PDF the user supplies

Download with:
`curl -sL -m 60 -A "literature-review-skill" -o "$SKILL/data/pdfs/<doi with / replaced by _>.pdf" "<url>"`
Use a distinct filename per attempt, or check before the next attempt: a failed retry must not overwrite a good file. The file must start with `%PDF-` (`head -c 5`). If it's HTML (paywall, login or bot check), discard it and mark the paper `Abstract only`. To remove a file, use a literal path, never a shell variable.

## Coverage tracking
Log every query: `state.py log-search --source openalex --query "..." --count N --stream <n|0 for citation tracking>`. Gap reports cite this log. A search that returns nothing is evidence about the *search*, not proof of a research gap.
