"""Build the notebook from the same analysis functions used by the CLI."""
from pathlib import Path
import nbformat


def build():
    md = nbformat.v4.new_markdown_cell
    code = nbformat.v4.new_code_cell
    cells = [
        md('# What a small job-posting sample can tell me\n\n'
           'This is a case study of records collected from 26 May to 10 June 2026, not a current list of jobs. '
           'I wanted to understand the mix of roles in my feed. Before using the counts to guide a search, '
           'I need to check what the data can actually support.'),
        code("from pathlib import Path\nimport sys\nimport pandas as pd\nfrom IPython.display import display, Markdown, Image\n"
             "ROOT = next(p for p in (Path.cwd(), Path.cwd().parent) if (p / 'data/jobs_snapshot.csv').exists())\n"
             "sys.path.insert(0, str(ROOT))\nfrom src.analyse import run\n"
             "m = run(ROOT / 'data/jobs_snapshot.csv', ROOT / 'reports/generated', ROOT / 'figures')\n"
             "df = pd.read_csv(ROOT / 'data/jobs_snapshot.csv')\ndisplay(df.head(3))"),
        md('## Start with the quality checks\n\n'
           'A unique internal ID does not prove a unique vacancy. Repeated titles at the same company and location '
           'might be reposts, collection duplicates or separate openings. I keep every source row and export the groups for review.'),
        code("display(Markdown(f\"The snapshot contains **{m['row_count']} rows**. Posting dates are missing for **{m['missing_posted_rows']} ({m['missing_posted_percent']}%)**. There are **{m['potential_repeated_groups']} repeated composite-key groups**, with **{m['rows_beyond_first_in_potential_groups']} rows beyond the first**. These are candidates for investigation, not confirmed duplicate vacancies.\"))\n"
             "display(Image(filename=str(ROOT / 'figures/quality.png')))"),
        md('## Which titles appear in the feed?\n\n'
           'The labels below come from documented title rules. They do not check the full advert or establish seniority, '
           'required experience or work rights. The tests cover examples and edge cases; they are not an independent accuracy study.'),
        code("display(pd.Series(m['lane_counts'], name='Snapshot rows').sort_values(ascending=False))\n"
             "display(Image(filename=str(ROOT / 'figures/lanes.png')))\n"
             "display(Markdown(f\"The Other category contains **{m['lane_counts'].get('Other', 0)} rows**. Under a first-record-per-composite-key sensitivity scenario, **{m['repeat_key_sensitivity']['representative_rows']} rows** remain. This scenario tests how counts might change; it is not a verified deduplication.\"))"),
        md('## Work arrangements and location\n\n'
           'The original workplace field mixes arrangements with labels such as Part-Time and Temporary. '
           'Mixed hybrid/on-site descriptions stay separate. A hybrid label does not say whether I can manage the office attendance, '
           'and a remote label does not establish UK eligibility.'),
        code("display(Markdown(f\"Explicit hybrid or remote labels account for **{m['explicit_hybrid_remote_rows']} rows ({m['explicit_hybrid_remote_percent']}%)**. Another **{m['ambiguous_arrangement_rows']} rows** have mixed arrangements. Counting the mixed labels as flexible would raise the share to **{m['broad_flexible_including_mixed_percent']}%**, so the definition matters.\"))\n"
             "display(Image(filename=str(ROOT / 'figures/geo_workplace.png')))\n"
             "display(Image(filename=str(ROOT / 'figures/locations.png')))"),
        md('## What do the old model scores mean?\n\n'
           'These scores came from a private LLM step comparing adverts with my CV. The public snapshot does not retain '
           'the model, prompt, CV version or requirement evidence. I can describe the scores, but cannot calibrate them '
           'against hiring outcomes. A score of 70 is an analysis threshold, not a 70% interview chance.'),
        code("display(pd.Series(m['score_threshold_counts'], name='Rows meeting threshold'))\n"
             "display(pd.Series(m['score_means_by_lane'], name='Mean historical score'))\n"
             "display(Image(filename=str(ROOT / 'figures/high_fit_lanes.png')))") ,
        md('## Collection cadence\n\n'
           'This chart measures when the pipeline first saw a row. It does not measure when an employer posted a vacancy. '
           'A large batch or a collection gap could reflect the collector rather than changes in demand.'),
        code("display(Image(filename=str(ROOT / 'figures/cadence.png')))\n"
             "display(Markdown(f\"Rows were collected on **{m['days_with_ingestion']} of {m['calendar_days']} calendar days**. Source counts: **{m['source_counts']}**. The source mix and missing dates limit market-wide or freshness claims.\"))"),
        md('## Conclusions\n\n'
           'Data Analyst is a useful lane to investigate in this sample, but the counts do not prove it is the easiest route into work. '
           'The historical model scores do not establish that capability-fit is solved or that sending more applications is the main bottleneck.\n\n'
           'My next step would be to review actual adverts against an explicit eligibility rubric, resolve repeated-record candidates, '
           'and track applications and interviews. I would compare results across role groups before changing the search strategy. '
           'Recruiter adverts should be assessed, not discarded simply because an agency posted them.\n\n'
           'See `reports/market-memo.md` for the short decision note and `docs/methodology.md` for definitions and remaining limits.'),
    ]
    notebook = nbformat.v4.new_notebook(cells=cells, metadata={
        'kernelspec': {'display_name': 'Job Market Python', 'language': 'python', 'name': 'job-market-python'},
        'language_info': {'name': 'python', 'version': '3.12'},
    })
    path = Path(__file__).resolve().parents[1] / 'notebooks/market_eda.ipynb'
    nbformat.write(notebook, path)
    return path


if __name__ == '__main__':
    print(build())
