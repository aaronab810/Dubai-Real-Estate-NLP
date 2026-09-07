"""Verify that default discovery cannot silently append uncleaned Reddit rows."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd

NOTEBOOK = json.loads((Path(__file__).resolve().parents[1] / 'notebooks/Topic_discovery_for_SMDI.ipynb').read_text(encoding='utf-8'))
def src(i): return ''.join(NOTEBOOK['cells'][i]['source'])

class CleanCorpusInputTests(unittest.TestCase):
    def test_default_reads_final_parquet_and_skips_all_raw_append_cells(self):
        fixture = pd.DataFrame({'platform':['reddit','twitter'], 'id':['a','b']})
        ns = {'pd':pd, 'os':os}
        with patch('os.makedirs'), patch('os.path.exists',return_value=True), \
             patch('pandas.read_parquet',return_value=fixture) as parquet, \
             patch('pandas.read_csv',side_effect=AssertionError('Unexpected raw CSV read')), \
             contextlib.redirect_stdout(io.StringIO()):
            exec(src(5),ns)
            for i in range(6,26): exec(src(i),ns)
        self.assertFalse(ns['LEGACY_APPEND_REDDIT'])
        self.assertTrue(parquet.call_args.args[0].endswith('master_processed_analysis_clean.parquet'))
        self.assertEqual(len(ns['social']),2)
        self.assertNotIn('reddit_new',ns)

    def test_csv_fallback_is_final_clean_export(self):
        ns = {'pd':pd,'os':os,'LEGACY_APPEND_REDDIT':False,
              'SOCIAL_PARQUET':'master_processed_analysis_clean.parquet',
              'SOCIAL_CSV':'master_processed_analysis_clean.csv'}
        with patch('os.path.exists',return_value=False), \
             patch('pandas.read_csv',return_value=pd.DataFrame({'platform':['reddit'],'id':['x']})) as read, \
             contextlib.redirect_stdout(io.StringIO()):
            exec(src(6),ns)
        self.assertEqual(read.call_args.args[0],'master_processed_analysis_clean.csv')

    def test_duplicate_record_ids_fail_before_training(self):
        ns = {'pd':pd,'os':os,'LEGACY_APPEND_REDDIT':False,'SOCIAL_PARQUET':'final.parquet'}
        fixture = pd.DataFrame({'platform':['reddit','reddit'],'id':['x','x']})
        with patch('os.path.exists',return_value=True), patch('pandas.read_parquet',return_value=fixture):
            with self.assertRaisesRegex(ValueError,'Duplicate platform'):
                exec(src(6),ns)

if __name__ == '__main__': unittest.main()
