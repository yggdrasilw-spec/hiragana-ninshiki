"""Semantic regressions for dictionary restrictions and candidate filtering."""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('audit', Path(__file__).resolve().parent.parent / 'scripts/audit-shiritori-dictionary.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def entry():
    return {'id': '1', 'kanji': [{'text': '上手', 'common': True, 'tags': []},
                                {'text': '巧い', 'common': True, 'tags': []}],
            'kana': [{'text': 'じょうず', 'common': True, 'tags': [], 'appliesToKanji': ['上手']},
                     {'text': 'うまい', 'common': True, 'tags': [], 'appliesToKanji': ['巧い']}],
            'sense': [{'partOfSpeech': ['n'], 'appliesToKana': ['じょうず'],
                       'appliesToKanji': ['上手'], 'misc': [], 'dialect': [],
                       'gloss': [{'text': 'DO NOT COPY THIS GLOSS'}]},
                      {'partOfSpeech': ['adj-i'], 'appliesToKana': ['うまい'],
                       'appliesToKanji': ['巧い'], 'misc': [], 'dialect': []}]}


class DictionaryTests(unittest.TestCase):
    def test_restrictions_and_gloss_exclusion(self):
        report, candidates = audit.audit({'words': [entry()]}, [])
        self.assertEqual([(c['reading'], c['word']) for c in candidates], [('じょうず', '上手')])
        self.assertNotIn('DO NOT COPY', str((report, candidates)))
        report, _ = audit.audit({'words': [entry()]}, [{'reading': 'うまい', 'word': '上手'}])
        self.assertEqual(report['matchedRows'], 0)
        self.assertEqual(report['readingMismatches'][0]['dictionaryReadings'], ['じょうず'])

    def test_existing_kana_word_and_same_entry_alternatives(self):
        report, candidates = audit.audit({'words': [entry()]}, [{'reading': 'じょうず', 'word': 'じょうず'}])
        self.assertEqual(report['matchedRows'], 1)
        # Matching a kana spelling should also cover the same entry's kanji.
        self.assertEqual(candidates, [])

    def test_marked_senses_and_n_ending(self):
        data = entry()
        data['sense'][0]['misc'] = ['vulg']
        self.assertEqual(audit.audit({'words': [data]}, [])[1], [])
        data['sense'][0]['misc'] = []
        data['kana'][0]['text'] = 'じょうずん'
        data['sense'][0]['appliesToKana'] = ['じょうずん']
        self.assertEqual(audit.audit({'words': [data]}, [])[1], [])


if __name__ == '__main__':
    unittest.main()
