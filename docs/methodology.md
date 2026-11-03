# Methodology and data dictionary

This analysis describes a fixed convenience sample collected from 26 May to 10 June 2026. It does not estimate the total UK market or identify currently open jobs.

## Public input fields

| Field | Meaning and limits |
|---|---|
| id | Internal row identifier; unique does not mean unique vacancy |
| source | Collection source label, mainly Indeed with a smaller LinkedIn sample |
| title, company | Recorded text, not independently employer-verified |
| location | Raw label; city, region and remote labels are mixed |
| workplace_type | Raw field that mixes work arrangement, hours and contract labels |
| score | Historical personal LLM score, 0-100; blank remains unknown |
| status | Pipeline state; this snapshot has no verified application outcome history |
| first_seen | Collection timestamp; source values have no timezone |
| posted | Source posting date where available; not filled from first_seen |

Full descriptions, private CV material and scoring explanations are not public inputs. Salary, canonical source IDs, search queries and scoring versions are not available. The original CSV is preserved byte-for-byte.

## Quality rules

The reader requires exactly the public column allowlist. It rejects duplicate internal IDs, missing identities/titles/companies, malformed timestamps and non-finite or out-of-range scores. Collection timestamps must be timezone-naive, matching this snapshot; offset-aware inputs require explicit normalisation before analysis. Parsed timestamps provide a canonical sort key. Missing posting dates, scores and locations are reported rather than guessed. CSV exports escape formula-leading strings; private database reads use read-only mode and close their connections. An invalid export cannot replace an existing output file.

Repeated-record candidates share normalised source, title, company and location. Their CSV lines are exported for review. This is deliberately a flag, not a deletion rule. Different adverts can share those fields; cross-source duplicates can also escape this rule. The sensitivity scenario keeps the earliest observed representative per key and reports the changed lane counts, without presenting it as a corrected truth set.

## Classifications

Title rules are ordered and visible in `src/analysis.py`: ML/AI, Data Scientist, Data Engineer (including Analytics Engineer), Data Analyst, other engineering, then Other. Broad terms such as business analyst and analytics remain imperfect proxies. Regression examples check implementation behaviour, not real-world accuracy. An independently labelled sample is still needed.

One change from the original rules affects this snapshot: `Data Engineer (Analytics)` at CSV line 13 is now assigned to Data Engineer before the broad analytics rule is considered. DA therefore has 119 rows rather than 120, and Data Engineer has 23 rather than 22. No source row was changed or removed.

Seniority is a separate title-only signal. Mixed junior/senior titles remain mixed. Absence of a senior word does not establish an entry-level vacancy.

Explicit Hybrid and Remote labels are counted separately from mixed arrangements. Part-Time and Temporary do not establish a workplace arrangement; their original values remain available. Location, sponsorship and attendance must be checked against the actual advert.

## Interpretation and remaining work

Counts use rows, not unique vacancies. Source shares, missingness, threshold sensitivity and repeated-key sensitivity are in `reports/generated/metrics.json`. Model scores are descriptive historical values. The 60/70/80 thresholds are sensitivity views, not validated hiring cut-offs. Source bias is not fixed by adding a confidence interval to this convenience sample.

Before using the work for hiring recommendations, I would need stable advert identifiers, source collection metadata, full-ad eligibility review and an independently reviewed label set. Evaluating the fit score would also require a documented model/prompt/CV version and an outcome dataset, with a suitable held-out evaluation rather than tuning and testing on the same examples.

## Data rights and privacy

The MIT licence covers the code, not third-party rights in collected job data. Source-specific collection and redistribution permissions have not been established by this project. Removing descriptions and personal rationale reduces exposure but does not settle that question. Do not add private databases, credentials, CVs or client records to the repository. Verify source terms and permissions before collecting or redistributing further data; otherwise use a synthetic fixture for public demonstrations.
