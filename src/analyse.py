"""Run local descriptive analysis; no scraping, scoring or employer contact."""
import argparse
import json
from pathlib import Path
from .analysis import read_snapshot, repeated_groups, summary, write_groups


def plot(rows, metrics, directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from collections import Counter
    directory.mkdir(parents=True, exist_ok=True)
    dates = metrics['collection_start'] + ' to ' + metrics['collection_end']

    def bars(values, title, name, colour='#4878A8'):
        items = sorted(values.items(), key=lambda x: (x[1], x[0]))
        maximum = max((v for _, v in items), default=0)
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.barh([k for k, _ in items], [v for _, v in items], color=colour)
        for i, (_, value) in enumerate(items):
            ax.text(value + maximum * .015, i, str(value), va='center')
        ax.set_xlim(0, max(1, maximum * 1.14))
        if not items:
            ax.text(.5, .5, 'No rows meet this threshold', transform=ax.transAxes,
                    ha='center', va='center')
            ax.set_yticks([])
        ax.set_title(title + '\n' + dates, fontsize=11)
        ax.set_xlabel('Snapshot rows')
        fig.tight_layout();fig.savefig(directory / name, dpi=150);plt.close(fig)

    bars(metrics['lane_counts'], 'Rule-based title categories (not verified entry-level vacancies)', 'lanes.png')
    bars(metrics['model_scored_70_by_lane'], 'Historical model scores >=70 (uncalibrated)', 'high_fit_lanes.png', '#3B8A6E')
    bars(metrics['workplace_counts'], 'Workplace labels: mixed arrangements kept separate', 'geo_workplace.png', '#8A6FA8')
    bars(dict(Counter(r['location'] for r in rows).most_common(8)),
         'Raw location labels (not commute or work-rights eligibility)', 'locations.png')
    bars({'Missing posted date': metrics['missing_posted_rows'],
          'Rows beyond first in repeated keys': metrics['rows_beyond_first_in_potential_groups'],
          'Ambiguous work arrangement': metrics['ambiguous_arrangement_rows']},
         'Data-quality flags (may overlap; repeats are not proven duplicates)', 'quality.png', '#A9683B')
    fig, ax = plt.subplots(figsize=(10, 3.5))
    daily = metrics['ingestion_by_day']
    ax.plot(list(daily), list(daily.values()), marker='o')
    ax.tick_params(axis='x', rotation=45)
    ax.set_title('Rows first seen by collection day; spikes may be ingestion batches', fontsize=11)
    ax.set_ylabel('Snapshot rows');ax.set_ylim(bottom=0)
    fig.tight_layout();fig.savefig(directory / 'cadence.png', dpi=150);plt.close(fig)


def run(input_path, output_dir, figures_dir=None):
    input_path, output_dir = Path(input_path), Path(output_dir)
    if output_dir.resolve() == input_path.resolve().parent:
        raise ValueError('Keep generated reports separate from the source snapshot')
    rows = read_snapshot(input_path)
    metrics = summary(rows, input_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'metrics.json').write_text(json.dumps(metrics, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    write_groups(output_dir / 'potential_repeated_groups.csv', repeated_groups(rows))
    (output_dir / 'quality-summary.md').write_text(
        '# Snapshot quality summary\n\n'
        f"- Source rows: {metrics['row_count']}.\n"
        f"- Missing posted dates: {metrics['missing_posted_rows']} ({metrics['missing_posted_percent']}%).\n"
        f"- Potential repeated groups: {metrics['potential_repeated_groups']}; rows beyond first: {metrics['rows_beyond_first_in_potential_groups']}. Not proven duplicate vacancies.\n"
        f"- Explicit hybrid/remote: {metrics['explicit_hybrid_remote_rows']} ({metrics['explicit_hybrid_remote_percent']}%). Mixed arrangements: {metrics['ambiguous_arrangement_rows']}.\n"
        f"- Collection days with rows: {metrics['days_with_ingestion']}/{metrics['calendar_days']}. No publication-rate inference.\n\n"
        'Scores are uncalibrated historical model outputs. Eligibility and source redistribution permissions are not established by this analysis.\n', encoding='utf-8')
    if figures_dir:
        plot(rows, metrics, Path(figures_dir))
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('data/jobs_snapshot.csv'))
    parser.add_argument('--out', type=Path, default=Path('reports/generated'))
    parser.add_argument('--figures', type=Path)
    args = parser.parse_args()
    metrics = run(args.input, args.out, args.figures)
    print(json.dumps({'rows': metrics['row_count'], 'output': str(args.out)}))


if __name__ == '__main__':
    main()
