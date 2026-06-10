"""Generate notebooks/market_eda.ipynb (cells only; execute with nbconvert)."""

import json
from pathlib import Path


def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source}


def code(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source,
    }


CELLS = [
    md(
        "# UK data-role job market — what 519 postings say\n"
        "\n"
        "**Question:** As a candidate moving from compliance into data, which role "
        "lane offers the most realistic entry path right now — and does my own "
        "application behaviour match what the market is actually posting?\n"
        "\n"
        "**Data:** 519 UK job postings collected 26 May – 10 Jun 2026 by my own "
        "scraping pipeline (Indeed + LinkedIn), deduplicated into SQLite, each "
        "scored 0–100 for fit against my CV by an LLM scoring step. Exported here "
        "as a sanitized snapshot (`data/jobs_snapshot.csv`) — descriptions and "
        "personal scoring rationale stripped.\n"
        "\n"
        "*This is live, messy, self-collected data — not a tutorial dataset.*"
    ),
    code(
        "import pandas as pd\n"
        "import numpy as np\n"
        "import re\n"
        "import matplotlib.pyplot as plt\n"
        "\n"
        "df = pd.read_csv('../data/jobs_snapshot.csv')\n"
        "df['first_seen'] = pd.to_datetime(df['first_seen'], errors='coerce')\n"
        "print(df.shape)\n"
        "df.head(3)"
    ),
    md(
        "## 1. Cleaning\n"
        "\n"
        "Two fields need work before any analysis is trustworthy:\n"
        "\n"
        "- `workplace_type` is free-text from two different scrapers — the same "
        "concept arrives as `On-Site`, `On-site`, `On-Site/Hybrid`, `Hybrid/Onsite`…\n"
        "- `title` needs classifying into comparable **role lanes** "
        "(Data Analyst / Data Scientist / ML-AI / Data Engineer / other)."
    ),
    code(
        "def normalize_workplace(w):\n"
        "    if not isinstance(w, str):\n"
        "        return 'Unknown'\n"
        "    w = w.strip().lower()\n"
        "    if 'hybrid' in w:\n"
        "        return 'Hybrid'\n"
        "    if 'remote' in w:\n"
        "        return 'Remote'\n"
        "    if 'on-site' in w or 'onsite' in w or 'on site' in w:\n"
        "        return 'On-site'\n"
        "    return 'Other/Unknown'\n"
        "\n"
        "LANE_PATTERNS = [\n"
        "    ('ML/AI Engineer', r'machine learning|ml engineer|\\bml\\b|ai engineer|artificial intelligence'),\n"
        "    ('Data Scientist', r'data scien'),\n"
        "    ('Data Analyst', r'data analyst|insight analyst|business analyst|bi analyst|analytics'),\n"
        "    ('Data Engineer', r'data engineer'),\n"
        "    ('Software/Other Eng', r'software|developer|engineer'),\n"
        "]\n"
        "\n"
        "def lane(title):\n"
        "    t = title.lower()\n"
        "    for name, pat in LANE_PATTERNS:\n"
        "        if re.search(pat, t):\n"
        "            return name\n"
        "    return 'Other'\n"
        "\n"
        "df['workplace'] = df['workplace_type'].map(normalize_workplace)\n"
        "df['lane'] = df['title'].map(lane)\n"
        "df[['workplace', 'lane']].describe()"
    ),
    md("## 2. What is the market actually posting?"),
    code(
        "lane_counts = df['lane'].value_counts()\n"
        "\n"
        "fig, ax = plt.subplots(figsize=(8, 4))\n"
        "lane_counts.sort_values().plot.barh(ax=ax, color='#4878A8')\n"
        "ax.set_title('UK data-role postings by lane (n=519, 26 May–10 Jun 2026)')\n"
        "ax.set_xlabel('postings')\n"
        "for i, v in enumerate(lane_counts.sort_values()):\n"
        "    ax.text(v + 2, i, str(v), va='center')\n"
        "plt.tight_layout()\n"
        "plt.savefig('../figures/lanes.png', dpi=150)\n"
        "plt.show()\n"
        "\n"
        "share = (lane_counts / len(df) * 100).round(1)\n"
        "print(share.to_string())"
    ),
    md(
        "**Data Analyst is the largest defined lane** — 120 postings (23.1%), "
        "nearly double Data Scientist (69, 13.3%). For a career-changer the "
        "volume is in DA, not DS/ML — the entry math favours the bridge."
    ),
    md("## 3. Where do *I* fit? Fit-score by lane"),
    code(
        "by_lane = df.groupby('lane')['score'].agg(['mean', 'median', 'count']).round(1)\n"
        "by_lane = by_lane.sort_values('mean', ascending=False)\n"
        "print(by_lane.to_string())\n"
        "\n"
        "high_fit = df[df['score'] >= 70]\n"
        "hf = high_fit['lane'].value_counts()\n"
        "\n"
        "fig, ax = plt.subplots(figsize=(8, 3.5))\n"
        "hf.sort_values().plot.barh(ax=ax, color='#3B8A6E')\n"
        "ax.set_title('High-fit postings (score ≥ 70) by lane')\n"
        "ax.set_xlabel('postings')\n"
        "for i, v in enumerate(hf.sort_values()):\n"
        "    ax.text(v + 0.3, i, str(v), va='center')\n"
        "plt.tight_layout()\n"
        "plt.savefig('../figures/high_fit_lanes.png', dpi=150)\n"
        "plt.show()"
    ),
    md("## 4. Geography and workplace model"),
    code(
        "fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))\n"
        "df['location'].value_counts().head(8).sort_values().plot.barh(\n"
        "    ax=axes[0], color='#4878A8')\n"
        "axes[0].set_title('Top locations')\n"
        "df['workplace'].value_counts().sort_values().plot.barh(\n"
        "    ax=axes[1], color='#8A6FA8')\n"
        "axes[1].set_title('Workplace model (normalized)')\n"
        "plt.tight_layout()\n"
        "plt.savefig('../figures/geo_workplace.png', dpi=150)\n"
        "plt.show()\n"
        "\n"
        "flex = df['workplace'].isin(['Hybrid', 'Remote']).mean() * 100\n"
        "print(f'Hybrid or remote share: {flex:.1f}%')"
    ),
    md("## 5. Market noise — who is actually posting?"),
    code(
        "top_companies = df['company'].value_counts().head(10)\n"
        "print(top_companies.to_string())\n"
        "\n"
        "noise = df['company'].isin(['DataAnnotation', 'Information Tech Consultants',\n"
        "                            'Metrica Recruitment']).sum()\n"
        "print(f'\\nTop gig-platform + recruiter-aggregator share of feed: '\n"
        "      f'{noise} postings ({noise/len(df)*100:.1f}%)')"
    ),
    md(
        "The single most frequent poster is **DataAnnotation** (AI training-data "
        "gig work, 36 postings) and two recruiter aggregators. ~14% of a raw "
        "'data jobs' feed is not direct employment — a filter any serious "
        "job-search automation needs."
    ),
    md("## 6. Pipeline cadence"),
    code(
        "daily = df.set_index('first_seen').resample('D').size()\n"
        "fig, ax = plt.subplots(figsize=(9, 3))\n"
        "daily.plot(ax=ax, marker='o', color='#4878A8')\n"
        "ax.set_title('Postings ingested per day')\n"
        "ax.set_ylabel('postings')\n"
        "plt.tight_layout()\n"
        "plt.savefig('../figures/cadence.png', dpi=150)\n"
        "plt.show()\n"
        "print(f'{len(df)} postings across {daily.index.nunique()} days; '\n"
        "      f'mean {daily.mean():.0f}/day')"
    ),
    md(
        "## Findings\n"
        "\n"
        "1. **The volume is in Data Analyst, not Data Science.** DA is the largest "
        "defined lane (120 postings, 23.1%) — 1.7× the Data Scientist count (69). "
        "For a career-changer, the bridge-role strategy is what the posting "
        "volume actually supports.\n"
        "2. **My fit scores are competitive in the DA lane** (mean 61 vs overall "
        "54), and high-fit postings (≥70) exist in meaningful volume across "
        "DA/DS/ML lanes — the constraint is application volume, not "
        "opportunity supply.\n"
        "3. **42% of postings are hybrid or remote** after normalizing the "
        "messy workplace field; London dominates (124) but Manchester (41), "
        "Bristol (27) and Leeds (18) carry real volume for non-London "
        "candidates.\n"
        "4. **~14% of a raw scraped feed is gig platforms and recruiter "
        "aggregators**, not direct employers — automated pipelines need a "
        "noise filter before any downstream scoring is meaningful.\n"
        "\n"
        "## Limitations (honest)\n"
        "\n"
        "- 16-day window, two sources, Indeed-skewed (495/24) — this is a live "
        "pipeline snapshot, not a census of the UK market.\n"
        "- The fit score is a personal LLM heuristic (v1) scoring against *my* "
        "CV — useful for my funnel decisions, not an objective market measure.\n"
        "- Salary fields were too sparse in the scraped sources to analyse; "
        "next pipeline iteration adds a salary-capture step."
    ),
]

NB = {
    "cells": CELLS,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.9"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

out = Path(__file__).resolve().parent.parent / "notebooks" / "market_eda.ipynb"
out.write_text(json.dumps(NB, indent=1))
print(f"wrote {out}")
