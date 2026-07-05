# UK Data-Role Job Market Intelligence

**Question:** Which data-role lane offers a career-changer the most realistic entry path in the UK right now — and does my own application behaviour match what the market actually posts?

**Data:** 519 UK job postings, collected 26 May – 10 Jun 2026 by a scraping pipeline I built while job-hunting (Indeed + LinkedIn → deduplicated SQLite → LLM fit-scoring against my CV → ranked daily digest). This repo contains a sanitized snapshot — descriptions and personal scoring rationale stripped.

**Approach:**
- Normalize messy free-text fields (workplace model arrives as `On-Site` / `On-site` / `Hybrid/Onsite`…) and classify titles into comparable role lanes
- Exploratory analysis: lane volume, fit-score distributions, geography, feed noise, ingest cadence
- Written market memo with the decision the data drove

**Findings:**
- **Data Analyst is the largest defined lane — 120 postings (23%), 1.7× Data Scientist (69).** The entry-path volume is in DA, not DS/ML.
- **121 postings (23%) scored high-fit (≥70) against my CV in just 16 days** — opportunity supply is not the constraint; application volume is.
- **42% of postings are hybrid or remote** after normalization; London leads (124) but Manchester, Bristol and Leeds carry real volume.
- **~14% of a raw scraped feed is gig platforms and recruiter aggregators**, not direct employers — automated job-search tooling needs a noise filter before scoring means anything.

**Tools:** Python (pandas, matplotlib) · SQLite/SQL · LLM-assisted scoring pipeline

[EDA notebook](notebooks/market_eda.ipynb) · [1-page market memo](reports/market-memo.md) · [snapshot export script](src/export_snapshot.py)

---

## Repository structure

```
data/jobs_snapshot.csv     sanitized posting snapshot (519 rows)
notebooks/market_eda.ipynb cleaning + EDA, executed with outputs
figures/                   charts rendered by the notebook
reports/market-memo.md     1-page insight memo
src/export_snapshot.py     pipeline-DB → public snapshot export
src/build_notebook.py      notebook generator (reproducibility)
```

## Reproduce

```bash
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute notebooks/market_eda.ipynb --output market_eda_executed.ipynb
```

## Provenance & honesty notes

- The collection pipeline (scraper, dedup, scoring, Gmail digest) runs privately as part of a larger automation project; this repo publishes the analysis layer over its output.
- 16-day window, two sources, Indeed-skewed (495/24): a live pipeline snapshot, not a census of the UK market.
- The fit score is a personal LLM heuristic scoring postings against *my* CV — useful for funnel decisions, not an objective market measure.
