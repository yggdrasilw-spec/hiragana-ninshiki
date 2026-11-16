"""Critical source restrictions: avoid cross-reading and cross-sense leakage."""
import importlib.util, sys, unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
spec=importlib.util.spec_from_file_location('gaps',root/'scripts/build-shiritori-vocabulary-gaps.py')
gaps=importlib.util.module_from_spec(spec);spec.loader.exec_module(gaps)

class Restrictions(unittest.TestCase):
    def setUp(self):
        self.kana=dict(text='あめ',tags=[],appliesToKanji=['雨'])
        self.form=dict(text='雨',tags=[])
        self.sense=dict(partOfSpeech=['n'],misc=[],dialect=[],appliesToKana=['あめ'],
                        appliesToKanji=['雨'],gloss=[dict(text='rain')])
    def test_reading_to_spelling_restriction(self):
        self.assertFalse(gaps.eligible_senses(dict(sense=[self.sense]),self.kana,dict(text='飴',tags=[])))
    def test_sense_to_reading_restriction(self):
        self.sense['appliesToKana']=['う']
        self.assertFalse(gaps.eligible_senses(dict(sense=[self.sense]),self.kana,self.form))
    def test_difficulty_is_not_rejection(self):
        self.sense['misc']=['arch','rare']
        self.assertEqual(len(gaps.eligible_senses(dict(sense=[self.sense]),self.kana,self.form)),1)
    def test_old_kana_is_not_current_pronunciation(self):
        self.kana['tags']=['ok']
        self.assertFalse(gaps.eligible_senses(dict(sense=[self.sense]),self.kana,self.form))
    def test_inappropriate_sense_is_not_admitted_by_safe_sibling(self):
        bad={**self.sense,'misc':['vulg'],'gloss':[dict(text='inappropriate')]}
        result=gaps.eligible_senses(dict(sense=[bad,self.sense]),self.kana,self.form)
        self.assertEqual([s['number'] for s in result],[2])
    def test_kana_normalization(self):
        self.assertEqual(gaps.hira('ｶﾞｯﾊﾟ'),'がっぱ')

if __name__=='__main__':unittest.main()
