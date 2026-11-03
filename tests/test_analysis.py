import csv
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from src.analysis import (REQUIRED, DataQualityError, normalise, read_snapshot,
                          repeated_groups, role_lane, safe_cell, seniority_signal, summary, workplace)
from src.analyse import run
from src.export_snapshot import derive_posted, export


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'input.csv'
        self.row = dict(id='1', source='indeed', title='Data Analyst', company='Example',
                        location='Leeds', workplace_type='Hybrid', score='70', status='new',
                        first_seen='2026-05-26 12:00:00', posted='')

    def write(self, rows, fields=REQUIRED):
        with self.path.open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader();writer.writerows(rows)

    def test_missing_posted_is_flagged_not_invented(self):
        self.write([self.row]);rows = read_snapshot(self.path)
        metrics = summary(rows, self.path)
        self.assertEqual(metrics['missing_posted_rows'], 1)
        self.assertEqual(rows[0]['posted'], '')

    def test_duplicate_ids_fail(self):
        self.write([self.row, self.row])
        with self.assertRaises(DataQualityError):read_snapshot(self.path)

    def test_additional_private_column_fails_allowlist(self):
        self.write([dict(self.row, resume='private')], (*REQUIRED, 'resume'))
        with self.assertRaises(DataQualityError):read_snapshot(self.path)

    def test_missing_required_column_fails(self):
        self.write([{k:v for k,v in self.row.items() if k != 'source'}], tuple(k for k in REQUIRED if k != 'source'))
        with self.assertRaises(DataQualityError):read_snapshot(self.path)

    def test_invalid_score_fails(self):
        for value in ['-1', '101', 'NaN', 'inf', 'invalid']:
            with self.subTest(value=value):
                self.write([dict(self.row, score=value)])
                with self.assertRaises(DataQualityError):read_snapshot(self.path)

    def test_missing_score_is_unknown_not_zero(self):
        self.write([dict(self.row, score='')]);m = summary(read_snapshot(self.path), self.path)
        self.assertEqual(m['missing_score_rows'], 1)
        self.assertEqual(m['score_threshold_counts']['70'], 0)
        self.assertEqual(m['score_means_by_lane'], {})

    def test_empty_and_invalid_fields_fail(self):
        for field,value in [('title',''), ('first_seen','not-a-date'), ('posted','2026-99-01')]:
            with self.subTest(field=field):
                self.write([dict(self.row, **{field:value})])
                with self.assertRaises(DataQualityError):read_snapshot(self.path)

    def test_empty_snapshot_fails(self):
        self.write([])
        with self.assertRaises(DataQualityError):read_snapshot(self.path)

    def test_bad_field_count_fails(self):
        self.write([self.row]);self.path.write_text(self.path.read_text().rstrip()+',extra\n')
        with self.assertRaises(DataQualityError):read_snapshot(self.path)

    def test_repeated_keys_are_flagged_without_deleting_rows(self):
        self.write([self.row, dict(self.row,id='2',company=' EXAMPLE ')])
        rows = read_snapshot(self.path);m = summary(rows,self.path)
        self.assertEqual(len(rows),2)
        self.assertEqual(repeated_groups(rows)[0]['csv_lines'],[2,3])
        self.assertEqual(m['repeat_key_sensitivity']['representative_rows'],1)
        self.assertEqual(m['row_count'],2)

    def test_collection_gaps_are_retained(self):
        self.write([self.row,dict(self.row,id='2',first_seen='2026-05-28 12:00:00')])
        self.assertEqual(summary(read_snapshot(self.path),self.path)['ingestion_by_day']['2026-05-27'],0)

    def test_offset_aware_collection_time_requires_explicit_normalisation(self):
        self.write([dict(self.row,first_seen='2026-05-26T12:00:00+01:00')])
        with self.assertRaises(DataQualityError):read_snapshot(self.path)

    def test_timestamp_sort_key_is_canonical(self):
        self.write([self.row,dict(self.row,id='2',first_seen='2026-05-26T11:00:00')])
        rows=read_snapshot(self.path)
        self.assertLess(rows[1]['first_seen_sort'],rows[0]['first_seen_sort'])

    def test_mixed_workplace_is_not_assumed_hybrid(self):
        self.assertEqual(workplace('On-Site/Hybrid'),'Mixed hybrid/on-site')
        self.assertEqual(workplace('Hybrid/Onsite'),'Mixed hybrid/on-site')
        self.assertEqual(workplace('remote / onsite'),'Mixed remote/other')
        self.assertEqual(workplace('Part-Time'),'Unknown')
        self.assertEqual(workplace('Temporary'),'Unknown')
        self.assertEqual(workplace('On site'),'On-site')

    def test_taxonomy_precedence_is_explicit(self):
        self.assertEqual(role_lane('Analytics Engineer'),'Data Engineer')
        self.assertEqual(role_lane('Senior Data Scientist'),'Data Scientist')
        self.assertEqual(role_lane('Unknown occupation'),'Other')

    def test_title_seniority_does_not_imply_eligibility(self):
        self.assertEqual(seniority_signal('Data Analyst (Junior & Senior opportunities)'),'Mixed')
        self.assertEqual(seniority_signal('Data Analyst'),'Unknown')

    def test_untrusted_spreadsheet_cells_are_escaped(self):
        for value in ['=CMD()', '+SUM(A1)', '-1+1', '@SUM(A1)', '  =CMD()', '\tformula']:
            self.assertTrue(safe_cell(value).startswith("'"))
        self.assertEqual(safe_cell('Data Analyst'),'Data Analyst')

    def test_normalisation(self):
        self.assertEqual(normalise('  DATA  Analyst '),'data analyst')

    def test_metrics_and_reports_are_deterministic(self):
        self.write([self.row]);a,b = self.root/'a',self.root/'b'
        run(self.path,a);run(self.path,b)
        for file in a.iterdir():self.assertEqual(file.read_bytes(),(b/file.name).read_bytes())
        self.assertEqual(json.loads((a/'metrics.json').read_text())['row_count'],1)

    def test_invalid_input_does_not_create_reports(self):
        self.write([dict(self.row,score='wrong')]);out=self.root/'output'
        with self.assertRaises(DataQualityError):run(self.path,out)
        self.assertFalse(out.exists())

    def test_empty_score_chart_exists_and_replaces_stale_chart(self):
        figures=self.root/'figures';output=self.root/'reports'
        self.write([self.row]);run(self.path,output,figures)
        prior=(figures/'high_fit_lanes.png').read_bytes()
        self.write([dict(self.row,score='')]);run(self.path,output,figures)
        empty=(figures/'high_fit_lanes.png').read_bytes()
        self.assertGreater(len(empty),1000)
        self.assertNotEqual(prior,empty)

    def test_export_missing_database_does_not_create_it(self):
        database=self.root/'absent.db'
        with self.assertRaises(sqlite3.OperationalError):export(database,self.root/'export.csv')
        self.assertFalse(database.exists())

    def test_malformed_posted_json_becomes_missing(self):
        for value in [None, '', 'broken', '[]', 'null']:
            self.assertIsNone(derive_posted(value))

    def test_export_allowlist_and_atomic_validation(self):
        db=self.root/'input.db';out=self.root/'export.csv'
        with sqlite3.connect(db) as connection:
            connection.execute('CREATE TABLE jobs (id,source,title,company,location,workplace_type,score,status,first_seen,raw_json,resume)')
            connection.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                               ('1','indeed','=formula','Example','Leeds','Remote',70,'new','2026-05-26 12:00:00','{}','private'))
        export(db,out)
        with out.open() as handle:
            reader=csv.DictReader(handle);row=next(reader)
        self.assertNotIn('resume',row)
        self.assertTrue(row['title'].startswith("'="))
        original=out.read_bytes()
        with sqlite3.connect(db) as connection:connection.execute('UPDATE jobs SET score=999')
        with self.assertRaises(DataQualityError):export(db,out)
        self.assertEqual(out.read_bytes(),original)
        self.assertFalse(list(self.root.glob('tmp*.csv')))


if __name__ == '__main__':unittest.main()
