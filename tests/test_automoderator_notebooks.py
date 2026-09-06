"""Regression checks for notebook filtering and positional embedding alignment.

Run: python -m unittest discover -s tests -v
Requires pandas and numpy. No Colab, Drive writes, or model downloads.
"""
import ast
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TOPIC = json.loads((ROOT/'notebooks/Topic_discovery_for_SMDI.ipynb').read_text(encoding='utf-8'))
MERGE = json.loads((ROOT/'notebooks/twitter_reddit_merge.ipynb').read_text(encoding='utf-8'))
def src(n, i): return ''.join(n['cells'][i]['source'])
def helper(n, i):
    node = next(x for x in ast.parse(src(n,i)).body
                if isinstance(x,ast.FunctionDef) and x.name=='known_automoderator_mask')
    ns = {}
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<notebook helper>','exec'),ns)
    return ns['known_automoderator_mask']

class AutoModeratorTests(unittest.TestCase):
    def test_exact_account_matching_and_platform_scope(self):
        d = pd.DataFrame({'platform':['reddit']*7+['twitter'],
                          'username':['AutoModerator',' automoderator ','u/AutoModerator',
                                      '/u/AutoModerator','automation_expert','AutoModeratorFan',None,'AutoModerator']})
        expected = [True,True,True,True,False,False,False,False]
        for n,i in [(TOPIC,28),(TOPIC,44),(MERGE,56)]:
            self.assertEqual(helper(n,i)(d).tolist(),expected)

    def test_missing_identity_columns_fail_explicitly(self):
        with self.assertRaises(ValueError):
            helper(TOPIC,28)(pd.DataFrame({'clean_text':['example']}))

    def test_filter_does_not_mutate_input_or_drop_human_mentions(self):
        d = pd.DataFrame({'platform':['reddit'],'username':['human'],
                          'clean_text':['AutoModerator removed my property question.']})
        before=d.copy(deep=True)
        self.assertFalse(helper(TOPIC,28)(d).any())
        pd.testing.assert_frame_equal(d,before)

    def run_resume(self,d,e,info):
        with tempfile.TemporaryDirectory() as tmp:
            ns={'SAVE_DIR':tmp}
            with patch('numpy.load',return_value=e), patch('pandas.read_pickle',return_value=d), \
                 patch('pandas.read_csv',return_value=info), contextlib.redirect_stdout(io.StringIO()):
                exec(src(TOPIC,44),ns)
            excluded=pd.read_csv(Path(tmp)/'quality_audit/automoderator_excluded_resume.csv')
            return ns,excluded

    def test_resume_masks_embeddings_by_position_and_recounts_topics(self):
        d=pd.DataFrame({'id':['a','bot1','b','bot2','outlier'],
                        'platform':['reddit']*5,
                        'username':['human','AutoModerator','other','AutoModerator','third'],
                        'topic':[1,1,2,8,-1]},index=[9,5,42,0,13])
        e=np.arange(15).reshape(5,3)
        info=pd.DataFrame({'Topic':[-1,1,2,8],'Count':[1,2,1,1]})
        ns,excluded=self.run_resume(d,e,info)
        self.assertEqual(ns['social'].id.tolist(),['a','b','outlier'])
        np.testing.assert_array_equal(ns['embeddings'],e[[0,2,4]])
        self.assertEqual(dict(zip(ns['topic_info'].Topic,ns['topic_info'].Count)),{-1:1,1:1,2:1})
        self.assertEqual(excluded.id.tolist(),['bot1','bot2'])
        ns2,excluded2=self.run_resume(ns['social'],ns['embeddings'],ns['topic_info'])
        np.testing.assert_array_equal(ns2['embeddings'],ns['embeddings'])
        self.assertEqual(len(excluded2),0)

    def test_resume_rejects_misaligned_cache(self):
        d=pd.DataFrame({'platform':['reddit'],'username':['human'],'topic':[0]})
        with self.assertRaises(ValueError):
            self.run_resume(d,np.zeros((2,3)),pd.DataFrame({'Topic':[0],'Count':[1]}))

    def test_downstream_cells_cannot_reload_unfiltered_cache(self):
        for i in [45,53]:
            self.assertNotIn('np.load(',src(TOPIC,i))
        self.assertIn('ne(-1)',src(TOPIC,53))
        self.assertIn('REVIEWED_SMDI_MAPPING',src(TOPIC,63))
        with self.assertRaises(ValueError):
            exec(src(TOPIC,62),{})

    def test_final_preprocessing_removes_even_first_bot_notice(self):
        # Execute the actual final removal expression, not a mirrored predicate.
        node=next(x for x in ast.parse(src(MERGE,56)).body
                  if isinstance(x,ast.Assign) and any(
                      isinstance(t,ast.Subscript) and isinstance(t.slice,ast.Constant)
                      and t.slice.value=='removed_by_author_aware_policy' for t in x.targets))
        d=pd.DataFrame({'is_known_automoderator':[True,False,False],
                        'is_extra_low_info_contact_variant':[False]*3,
                        'is_same_author_exact_text_repeat':[False,False,True],
                        'is_same_author_highconf_near_duplicate_repeat':[False]*3})
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<final policy>','exec'),{'df':d})
        self.assertEqual(d.removed_by_author_aware_policy.tolist(),[True,False,True])

    def test_changed_cells_compile_and_stale_topic_outputs_are_clear(self):
        for n,indices in [(TOPIC,[28,39,44,45,53,54,61,62,63]),(MERGE,[56])]:
            for i in indices:
                compile(src(n,i),f'cell_{i}','exec')
        self.assertTrue(all(not c.get('outputs') and c.get('execution_count') is None
                            for c in TOPIC['cells'] if c['cell_type']=='code'))

if __name__=='__main__': unittest.main()
