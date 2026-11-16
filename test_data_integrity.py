"""Integrity tests for Grand Line Draft 5.1 bundle."""
from __future__ import annotations
import json, gzip, unittest
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]

class CharacterDataIntegrityTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.characters=json.loads((BASE/'characters.json').read_text(encoding='utf-8'))
  cls.data=json.loads((BASE/'character_ratings.json').read_text(encoding='utf-8'))
  with gzip.open(BASE/'matchup_results.json.gz','rt',encoding='utf-8') as f: cls.matchups=json.load(f)
  cls.ratings=cls.data['characters']
  cls.index={tuple(sorted((m['a'],m['b']))):m for m in cls.matchups}
 def chance(self,a,b):
  row=self.index[tuple(sorted((a,b)))]
  return row['a_win_probability'] if row['a']==a else 100-row['a_win_probability']
 def test_character_ids_and_names_unique(self):
  self.assertEqual(len(self.characters),140)
  self.assertEqual(len({c['id'] for c in self.characters}),140)
  self.assertEqual(len({c['name'] for c in self.characters}),140)
  self.assertEqual(len(self.ratings),140)
  self.assertEqual({c['name'] for c in self.characters},set(self.ratings))
 def test_fivefold_profiles_complete(self):
  expected={'devil_fruit','haki','strength','speed','battle_iq'}
  for c in self.characters:
   r=self.ratings[c['name']]['ranking_stats']
   self.assertTrue(expected.issubset(r),c['name'])
   for k in expected-{'haki'}:
    self.assertIsInstance(r[k],(int,float),f'{c["name"]}/{k}')
    self.assertTrue(0<=r[k]<=100)
    self.assertTrue(r.get('rationale',{}).get(k))
   self.assertTrue(r['haki'] is None or 0<=r['haki']<=100)
   self.assertTrue(r.get('rationale',{}).get('haki'))
 def test_old_135_characters_preserved(self):
  expected={'Monkey D. Luffy','Shanks','Charlotte Katakuri','Ethanbaron V. Nusjuro','Kaido','Imu','Joy Boy'}
  self.assertTrue(expected.issubset(self.ratings))
  self.assertEqual(self.ratings['Charlotte Katakuri']['haki_score'],89)
  self.assertEqual(self.ratings['Charlotte Katakuri']['haki_breakdown']['conqueror']['score'],80)
 def test_five_new_characters(self):
  expected={'Gecko Moria','Kyros','Ashura Doji','Vergo','Kawamatsu'}
  self.assertTrue(expected.issubset(self.ratings))
  self.assertEqual(self.ratings['Gecko Moria']['power'],89)
  self.assertEqual(self.ratings['Gecko Moria']['haki_score'],None)
  self.assertEqual(self.ratings['Ashura Doji']['haki_score'],85)
  self.assertEqual(self.ratings['Vergo']['haki_score'],90)
  self.assertEqual(self.ratings['Kawamatsu']['haki_score'],86)
 def test_latest_manga_changes(self):
  self.assertEqual(self.ratings['Monkey D. Luffy']['power'],96)
  self.assertIn('Kapitel 1198',self.ratings['Monkey D. Luffy']['version_label'])
  n=self.ratings['Ethanbaron V. Nusjuro']
  self.assertEqual(n['haki_score'],93)
  self.assertEqual(n['ranking_stats']['haki'],93)
  self.assertEqual(n['haki_breakdown']['observation']['score'],91)
  self.assertEqual(n['haki_breakdown']['armament']['score'],93)
  self.assertEqual(n['haki_breakdown']['conqueror']['score'],94)
 def test_matchup_matrix_complete(self):
  self.assertEqual(len(self.matchups),140*139//2)
  self.assertEqual(len(self.index),9730)
  for m in self.matchups:
   self.assertEqual(m['simulations_per_pair'],15000)
   self.assertEqual(m['a_wins_simulated']+m['b_wins_simulated'],15000)
   self.assertGreater(m['a_win_probability'],0)
   self.assertLess(m['a_win_probability'],100)
   self.assertTrue(m.get('reason'))
 def test_disputed_matchup_directions_are_sane(self):
  self.assertGreater(self.chance('Shanks','Usopp'),99.0)
  self.assertGreater(self.chance('Shanks','Nami'),99.0)
  self.assertTrue(48<=self.chance('Shanks','Dracule Mihawk')<=52)
  self.assertGreater(self.chance('Kaido','Monkey D. Luffy'),50)
  self.assertGreater(self.chance('Queen','Donquixote Doflamingo'),50)
  self.assertGreater(self.chance('Charlotte Katakuri','Boa Hancock'),50)
  self.assertGreater(self.chance('Kaido','Gecko Moria'),65)
 def test_matrix_metadata(self):
  m=self.data['matchup_method']
  self.assertEqual(m['unique_pairs'],9730)
  self.assertEqual(m['simulations_per_pair'],15000)
  self.assertEqual(m['total_simulated_fights'],145950000)
  self.assertEqual(self.data['review_summary']['characters_total'],140)
  self.assertEqual(self.data['review_summary']['manga_cutoff'],'Kapitel 1198, 09.11.2026 (Deutschland)')

if __name__=='__main__': unittest.main()
