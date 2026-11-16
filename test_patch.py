import json, math, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
chars = json.loads((ROOT/'characters.json').read_text(encoding='utf-8'))
ratings = json.loads((ROOT/'character_ratings.json').read_text(encoding='utf-8'))
class PatchTests(unittest.TestCase):
 def test_roster(self):
  self.assertEqual(len(chars),125)
  self.assertEqual(len({c['id'] for c in chars}),125)
  self.assertEqual(len({c['name'] for c in chars}),125)
 def test_new_characters(self):
  names={c['name'] for c in chars}
  for n in ['Kyros','Ashura Doji','Gecko Moria','Vergo','Urouge']: self.assertIn(n,names)
 def test_manga_updates(self):
  p=ratings['characters']
  self.assertEqual(p['Monkey D. Luffy']['power'],96)
  self.assertEqual(p['Charlotte Katakuri']['power'],89)
  self.assertEqual(p['Charlotte Katakuri']['haki_score'],89)
  self.assertEqual([p['Charlotte Katakuri']['haki_breakdown'][k]['score'] for k in ['observation','armament','conqueror']],[98,89,80])
  self.assertEqual(p['Ethanbaron V. Nusjuro']['haki_score'],92)
  self.assertEqual(p['Gecko Moria']['power'],89)
  self.assertIn('Prime',p['Gecko Moria']['version_label'])
  self.assertEqual([p['Ethanbaron V. Nusjuro']['haki_breakdown'][k]['score'] for k in ['observation','armament','conqueror']],[92,95,89])
  self.assertEqual(p['Ethanbaron V. Nusjuro']['haki_breakdown']['conqueror']['status'],'starke Indizien')
 def test_unknown_haki_not_zero(self):
  for n in ['Kyros','Gecko Moria','Urouge']:
   p=ratings['characters'][n]
   self.assertIsNone(p['haki_score'])
   self.assertEqual(p['haki_status'],'nicht bestätigt')
 def test_all_pairs_and_draw_counts(self):
  rows=ratings['matchup_results']
  self.assertEqual(len(rows),125*124//2)
  keys=[tuple(sorted((r['a'],r['b']))) for r in rows]
  self.assertEqual(len(set(keys)),len(rows))
  self.assertTrue(all(r['a_wins_simulated']+r['b_wins_simulated']==15000 for r in rows))
  self.assertTrue(all(0.01<=r['a_win_probability']<=99.99 for r in rows))
 def test_shanks_usopp_is_not_a_coinflip(self):
  row=next(r for r in ratings['matchup_results'] if {r['a'],r['b']}=={'Shanks','Usopp'})
  shanks=row['a_win_probability'] if row['a']=='Shanks' else 100-row['a_win_probability']
  self.assertGreater(shanks,99.8)
 def test_shanks_mihawk_stays_competitive(self):
  row=next(r for r in ratings['matchup_results'] if {r['a'],r['b']}=={'Shanks','Dracule Mihawk'})
  p=row['a_win_probability'] if row['a']=='Shanks' else 100-row['a_win_probability']
  self.assertGreater(p,35); self.assertLess(p,65)
if __name__=='__main__': unittest.main(verbosity=2)
