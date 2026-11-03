"""Render the human-written README and memo using the computed metrics."""
import json
from pathlib import Path


def write(root):
    root = Path(root)
    m = json.loads((root / 'reports/generated/metrics.json').read_text())
    n, da, ds = m['row_count'], m['lane_counts'].get('Data Analyst', 0), m['lane_counts'].get('Data Scientist', 0)
    readme = f'''# UK job-posting snapshot: analysis and quality checks

I collected this sample while looking for work. I wanted to understand which roles appeared in my feed and whether the data was reliable enough to guide my search. The analysis starts with quality checks, then looks at the patterns the sample can support.

**Scope:** {n} records first seen from {m['collection_start']} to {m['collection_end']}. This is a dated case study, not a current vacancy list or a representative survey of the UK market.

![Data-quality checks](figures/quality.png)

## Key findings

- Data Analyst has {da} classified rows, compared with {ds} for Data Scientist. Other has {m['lane_counts'].get('Other', 0)} rows, so it is important not to call DA the largest category overall.
- {m['missing_posted_rows']} posting dates are missing ({m['missing_posted_percent']}%). First seen is a collection timestamp, not a substitute for the posting date.
- {m['potential_repeated_groups']} groups repeat the same source, title, company and location. There are {m['rows_beyond_first_in_potential_groups']} rows beyond the first in those groups. These might be duplicates, reposts or separate openings; I have not silently removed them.
- {m['explicit_hybrid_remote_rows']} rows explicitly say hybrid or remote ({m['explicit_hybrid_remote_percent']}%). Another {m['ambiguous_arrangement_rows']} have mixed arrangements. Treating those as flexible produces {m['broad_flexible_including_mixed_percent']}%, which explains why the earlier figure was too broad for a practical job search.
- {m['score_threshold_counts']['70']} rows have historical model scores of at least 70. That describes an uncalibrated scoring system, not the number of jobs I could realistically obtain.

## What I conclude

DA is worth investigating, but these data do not establish the easiest entry route, the cause of unsuccessful applications or the right application volume. I would check actual requirements and practical arrangements, then track interview outcomes before changing strategy. Agency adverts are not automatically invalid.

The useful result is a clearer description of the feed and a list of checks needed before using it to make decisions.

## Reproduce locally

Use Python 3.12. The lock file pins package versions and hashes, with platform markers for macOS and Linux. Run from the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements.lock
python -m unittest discover -s tests -v
python -m src.analyse --figures figures
python -m src.write_report
python -m src.build_notebook
python -m ipykernel install --sys-prefix --name job-market-python
python -m nbconvert --to notebook --execute notebooks/market_eda.ipynb --inplace --ExecutePreprocessor.kernel_name=job-market-python --ExecutePreprocessor.timeout=180
```

The analysis uses the supplied CSV. It does not scrape, call an LLM, send messages or require private credentials. To resolve dependencies again, use `uv pip compile requirements.in --python-version 3.12 --universal --generate-hashes --output-file requirements.lock` and review the changes.

## Explore the work

- [Executed notebook](notebooks/market_eda.ipynb)
- [Short decision memo](reports/market-memo.md)
- [Computed metrics](reports/generated/metrics.json)
- [Quality summary](reports/generated/quality-summary.md)
- [Potential repeated records](reports/generated/potential_repeated_groups.csv)
- [Methodology and data dictionary](docs/methodology.md)
- [Validation tests](tests/test_analysis.py)

`src/analysis.py` holds the validation and transformation rules. `src/analyse.py` writes reports and charts. The notebook uses the same functions; README and memo numbers come from the same metrics file. A GitHub Actions workflow runs the tests and notebook on Python 3.12. Local verification is separate from a successful hosted CI run.

## Source and limits

The private collection pipeline is outside this repository. The public snapshot contains metadata and historical personal fit scores, not full descriptions, CV text or scoring rationales. Source counts are {m['source_counts']}; the sample is strongly Indeed-skewed.

Stable source advert IDs, collection queries, scorer versions, work-rights evidence and hiring outcomes are unavailable here. No deduplication, taxonomy accuracy or interview-prediction claim is made. The code has an MIT licence; it does not grant rights over third-party job data. The metadata is retained for this case study, with redistribution permissions unverified. See the methodology before reusing it.
'''
    memo = f'''# Decision memo: what this sample supports

## The question

Which kinds of data roles appeared in my collected feed, and is there enough evidence to change my application strategy?

## What I found

The snapshot has {n} records collected over {m['calendar_days']} calendar days in May-June 2026. Title rules classify {da} as Data Analyst and {ds} as Data Scientist. That makes DA worth examining, but it does not establish entry-level eligibility. The Other category has {m['lane_counts'].get('Other', 0)} records and the source mix is {m['source_counts']}.

Data quality changes how I interpret those counts. Posting dates are missing for {m['missing_posted_rows']} records. There are {m['potential_repeated_groups']} repeated source/title/company/location groups. Keeping the first row from each key would leave {m['repeat_key_sensitivity']['representative_rows']} rows, but that is only a sensitivity scenario: it could discard separate genuine openings.

Only {m['explicit_hybrid_remote_rows']} records have an unambiguous hybrid or remote label. A further {m['ambiguous_arrangement_rows']} have mixed labels. Neither group establishes that the location or work rights suit me.

## What I cannot conclude

The {m['score_threshold_counts']['70']} historical scores of at least 70 are not verified suitable vacancies. The model, prompt and CV version are not recorded in the public data, and no interview outcomes are available to evaluate the scores. I cannot use them to show that application volume is the bottleneck, or that my capabilities already meet the adverts.

Recruiter adverts also need checking individually. Counting posts from a few named firms does not measure the number of invalid opportunities in the feed.

## The decision

I would test a DA-focused shortlist as a hypothesis, not commit to a fixed increase in applications on these figures alone. First I would review full adverts, distinguish essential from desirable requirements, check location and work rights, and investigate repeated records. Then I would track applications and interview outcomes across comparable role groups.

The immediate improvement is better screening and measurement. This snapshot does not identify a single cause of unsuccessful applications.
'''
    (root / 'README.md').write_text(readme, encoding='utf-8')
    (root / 'reports/market-memo.md').write_text(memo, encoding='utf-8')


if __name__ == '__main__':
    write(Path(__file__).resolve().parents[1])
