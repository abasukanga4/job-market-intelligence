"""Network-free validation and descriptive summaries; rows are not vacancies."""
import csv
import hashlib
import math
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

REQUIRED = ('id', 'source', 'title', 'company', 'location', 'workplace_type',
            'score', 'status', 'first_seen', 'posted')
PATTERNS = (
    ('ML/AI Engineer', r'machine learning|ml engineer|\bml\b|ai engineer|artificial intelligence'),
    ('Data Scientist', r'data scien'),
    ('Data Engineer', r'data engineer|analytics engineer'),
    ('Data Analyst', r'data analyst|insight analyst|business analyst|bi analyst|analytics'),
    ('Software/Other Eng', r'software|developer|engineer'),
)


class DataQualityError(ValueError):
    """Input errors must not silently become confident analytical results."""


def normalise(value):
    return re.sub(r'\s+', ' ', value.strip()).casefold()


def role_lane(title):
    return next((name for name, pattern in PATTERNS if re.search(pattern, title, re.I)), 'Other')


def workplace(value):
    text = normalise(value)
    onsite = bool(re.search(r'on[- ]?site', text))
    if 'hybrid' in text and onsite:
        return 'Mixed hybrid/on-site'
    if 'remote' in text and (onsite or 'hybrid' in text):
        return 'Mixed remote/other'
    if 'hybrid' in text:
        return 'Hybrid'
    if 'remote' in text:
        return 'Remote'
    return 'On-site' if onsite else 'Unknown'


def seniority_signal(title):
    junior = bool(re.search(r'\b(junior|graduate|apprentice|entry[- ]level)\b', title, re.I))
    senior = bool(re.search(r'\b(senior|lead|principal|head|manager|director)\b', title, re.I))
    return 'Mixed' if junior and senior else 'Senior signal' if senior else 'Junior signal' if junior else 'Unknown'


def read_snapshot(path):
    with Path(path).open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        if set(fields) != set(REQUIRED) or len(fields) != len(REQUIRED):
            raise DataQualityError('Snapshot schema differs from the public-column allowlist')
        rows, seen = [], set()
        for line, raw in enumerate(reader, 2):
            if None in raw or any(v is None for v in raw.values()):
                raise DataQualityError(f'CSV line {line}: incorrect field count')
            row = {k: v.strip() for k, v in raw.items()}
            if any(not row[k] for k in ('id', 'source', 'title', 'company', 'first_seen')):
                raise DataQualityError(f'CSV line {line}: missing identity/title/company/date')
            if row['id'] in seen:
                raise DataQualityError(f'CSV line {line}: duplicate internal ID')
            seen.add(row['id'])
            try:
                first = datetime.fromisoformat(row['first_seen'])
                if first.tzinfo is not None:
                    raise ValueError('Expected timezone-naive source timestamps; normalise offset-aware input explicitly')
                if row['posted']:
                    datetime.fromisoformat(row['posted'])
                score = float(row['score']) if row['score'] else None
                if score is not None and (not math.isfinite(score) or not 0 <= score <= 100):
                    raise ValueError('invalid score')
            except ValueError as exc:
                raise DataQualityError(f'CSV line {line}: invalid timestamp or score') from exc
            row.update(score_value=score, csv_line=line, first_seen_day=first.date().isoformat(),
                       first_seen_sort=first.isoformat(),
                       lane=role_lane(row['title']), workplace=workplace(row['workplace_type']),
                       seniority_signal=seniority_signal(row['title']))
            rows.append(row)
    if not rows:
        raise DataQualityError('Empty snapshot')
    return rows


def repeated_groups(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(normalise(row[k]) for k in ('source', 'title', 'company', 'location'))].append(row)
    return [dict(source=k[0], title=k[1], company=k[2], location=k[3],
                 csv_lines=[r['csv_line'] for r in values], row_count=len(values))
            for k, values in sorted(groups.items()) if len(values) > 1]


def summary(rows, snapshot_path):
    count = len(rows)
    groups = repeated_groups(rows)
    lanes = Counter(r['lane'] for r in rows)
    scored = [r for r in rows if r['score_value'] is not None]
    arrange = Counter(r['workplace'] for r in rows)
    days = Counter(r['first_seen_day'] for r in rows)
    start, end = min(days), max(days)
    current, daily = datetime.fromisoformat(start).date(), {}
    while current.isoformat() <= end:
        daily[current.isoformat()] = days[current.isoformat()]
        current += timedelta(days=1)
    representative = {}
    for row in sorted(rows, key=lambda r: (r['first_seen_sort'], r['csv_line'])):
        representative.setdefault(tuple(normalise(row[k]) for k in ('source', 'title', 'company', 'location')), row)
    explicit = arrange['Hybrid'] + arrange['Remote']
    ambiguous = sum(v for k, v in arrange.items() if k.startswith('Mixed'))
    return {
        'snapshot_sha256': hashlib.sha256(Path(snapshot_path).read_bytes()).hexdigest(),
        'row_count': count, 'unique_internal_ids': len({r['id'] for r in rows}),
        'collection_start': start, 'collection_end': end, 'calendar_days': len(daily),
        'days_with_ingestion': len(days), 'ingestion_by_day': daily,
        'source_counts': dict(sorted(Counter(r['source'] for r in rows).items())),
        'lane_counts': dict(sorted(lanes.items())), 'workplace_counts': dict(sorted(arrange.items())),
        'explicit_hybrid_remote_rows': explicit,
        'explicit_hybrid_remote_percent': round(100 * explicit / count, 2),
        'ambiguous_arrangement_rows': ambiguous,
        'broad_flexible_including_mixed_percent': round(100 * (explicit + ambiguous) / count, 2),
        'missing_posted_rows': sum(not r['posted'] for r in rows),
        'missing_posted_percent': round(100 * sum(not r['posted'] for r in rows) / count, 2),
        'missing_score_rows': count - len(scored),
        'missing_location_rows': sum(not r['location'] for r in rows), 'scored_rows': len(scored),
        'score_means_by_lane': {k: round(statistics.mean(r['score_value'] for r in scored if r['lane'] == k), 2)
                                for k in sorted(lanes) if any(r['lane'] == k for r in scored)},
        'score_threshold_counts': {str(t): sum(r['score_value'] >= t for r in scored) for t in (60, 70, 80)},
        'model_scored_70_by_lane': dict(sorted(Counter(r['lane'] for r in scored if r['score_value'] >= 70).items())),
        'seniority_title_signals': dict(sorted(Counter(r['seniority_signal'] for r in rows).items())),
        'data_analyst_senior_or_mixed_title_rows': sum(r['lane'] == 'Data Analyst' and r['seniority_signal'] in ('Senior signal', 'Mixed') for r in rows),
        'potential_repeated_groups': len(groups),
        'rows_beyond_first_in_potential_groups': sum(g['row_count'] - 1 for g in groups),
        'repeat_key_sensitivity': {'representative_rows': len(representative),
                                 'lane_counts': dict(sorted(Counter(r['lane'] for r in representative.values()).items())),
                                 'interpretation': 'First observed representative per composite key; not verified unique vacancies'},
        'poster_type_status': 'Not verified. Recruiting agencies are not automatically invalid adverts.',
        'score_status': 'Historical personal LLM heuristic; model/prompt/CV version and hiring calibration unavailable.',
        'eligibility_status': 'Not assessed: descriptions, required years, work rights and commute evidence absent.',
        'taxonomy_status': 'Title rules have synthetic regression cases; no empirical gold-label validation.',
        'timestamp_timezone': 'Input validated as timezone-naive; original timezone remains unknown.',
        'data_limit': 'Convenience sample from a private collection pipeline, not a census or current vacancy list.',
    }


def safe_cell(value):
    text = str(value)
    dangerous = text.startswith(('\t', '\r', '\n')) or text.lstrip().startswith(('=', '+', '-', '@'))
    return "'" + text if dangerous else text


def write_groups(path, groups):
    with Path(path).open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=['source', 'title', 'company', 'location', 'csv_lines', 'row_count'])
        writer.writeheader()
        for group in groups:
            writer.writerow({k: safe_cell(';'.join(map(str, v)) if isinstance(v, list) else v)
                             for k, v in group.items()})
