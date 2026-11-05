"""Integrity tests for Grand Line Draft 5.0 bundle."""
from __future__ import annotations
import json
import gzip
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


class CharacterDataIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.characters = json.loads((BASE / "characters.json").read_text(encoding="utf-8"))
        cls.data = json.loads((BASE / "character_ratings.json").read_text(encoding="utf-8"))
        with gzip.open(BASE / "matchup_results.json.gz", "rt", encoding="utf-8") as handle:
            cls.matchups = json.load(handle)
        cls.ratings = cls.data["characters"]

    def test_character_ids_and_names_are_unique(self):
        self.assertEqual(len(self.characters), 135)
        self.assertEqual(len({c["id"] for c in self.characters}), len(self.characters))
        self.assertEqual(len({c["name"] for c in self.characters}), len(self.characters))
        self.assertEqual(len(self.ratings), 135)
        self.assertEqual(set(c["name"] for c in self.characters), set(self.ratings))

    def test_every_character_has_fivefold_values_and_rationales(self):
        expected = {"devil_fruit", "haki", "strength", "speed", "battle_iq"}
        for character in self.characters:
            profile = self.ratings[character["name"]]
            ranking = profile["ranking_stats"]
            self.assertTrue(expected.issubset(ranking), character["name"])
            for key in expected - {"haki"}:
                value = ranking[key]
                self.assertIsInstance(value, (int, float), f"{character['name']} / {key}")
                self.assertGreaterEqual(value, 0, f"{character['name']} / {key}")
                self.assertLessEqual(value, 100, f"{character['name']} / {key}")
                self.assertTrue(ranking.get("rationale", {}).get(key), f"Missing rationale: {character['name']} / {key}")
            haki = ranking["haki"]
            self.assertTrue(haki is None or (isinstance(haki, (int, float)) and 0 <= haki <= 100), character["name"])
            self.assertTrue(ranking.get("rationale", {}).get("haki"), f"Missing Haki rationale: {character['name']}")

    def test_whitebeard_has_confirmed_quake_fruit(self):
        profile = self.ratings["Edward Newgate"]
        self.assertEqual(profile["ranking_stats"]["devil_fruit"], 100)
        self.assertIn("Gura Gura no Mi", profile["devil_fruit_name"])
        self.assertEqual(profile["devil_fruit_status"], "bestätigt")

    def test_well_known_fruit_users_are_not_zeroed(self):
        known_users = [
            "Monkey D. Luffy", "Tony Tony Chopper", "Nico Robin", "Brook", "Portgas D. Ace",
            "Sabo", "Edward Newgate", "Marshall D. Teach", "Buggy", "Crocodile",
            "Donquixote Doflamingo", "Boa Hancock", "Bartholomew Kuma", "Perona",
            "Bentham (Bon Clay)", "Enel", "Caesar Clown", "Charlotte Linlin",
            "Charlotte Katakuri", "Charlotte Cracker", "Charlotte Perospero", "Kaido",
            "X Drake", "Jewelry Bonney", "Capone Bege", "Bartolomeo", "Kozuki Momonosuke",
            "Marco", "Bellamy", "Rob Lucci", "Kaku", "Magellan", "Smoker", "Sengoku",
            "Sakazuki (Akainu)", "Kuzan (Aokiji)", "Borsalino (Kizaru)", "Issho (Fujitora)",
            "Aramaki (Ryokugyu)", "Emporio Ivankov", "Dr. Vegapunk", "Shiryu", "Van Augur",
            "Jesus Burgess", "Donquixote Rosinante", "Charlotte Pudding", "Blueno", "Shiki",
            "Charlotte Smoothie", "Charlotte Oven", "Charlotte Daifuku", "Jozu", "S-Hawk",
            "S-Snake", "S-Bear", "S-Shark", "Shepherd Sommers", "Rimoshifu Killingham",
        ]
        for name in known_users:
            self.assertGreater(self.ratings[name]["ranking_stats"]["devil_fruit"], 0, name)

    def test_unknown_haki_is_not_falsely_quantified(self):
        unknown = [n for n, p in self.ratings.items() if p.get("haki_score") is None]
        self.assertGreater(len(unknown), 0)
        for name in unknown:
            profile = self.ratings[name]
            self.assertIsNone(profile.get("haki_score"), name)
            self.assertIn("unbekannt", str(profile.get("haki_status", "")).lower(), name)
            self.assertIsNone(profile["ranking_stats"]["haki"], name)

    def test_user_power_anchors(self):
        expected = {
            "Imu":100, "Joy Boy":100, "Rocks D. Xebec":99,
            "Gol D. Roger":98, "Edward Newgate":98, "Monkey D. Garp":98,
            "Shanks":97, "Dracule Mihawk":97, "Kaido":96, "Monkey D. Luffy":95,
            "Charlotte Katakuri":89, "Queen":85, "Donquixote Doflamingo":83,
        }
        for name, power in expected.items():
            self.assertEqual(self.ratings[name]["power"], power, name)

    def test_matchup_matrix_complete_and_simulated(self):
        matchups = self.matchups
        self.assertEqual(len(matchups), 135 * 134 // 2)
        self.assertEqual(len({tuple(sorted((m["a"], m["b"]))) for m in matchups}), len(matchups))
        for item in matchups:
            self.assertEqual(item["simulations_per_pair"], 15000)
            self.assertEqual(item["a_wins_simulated"] + item["b_wins_simulated"], 15000)
            self.assertAlmostEqual(item["a_win_probability"] + (100-item["a_win_probability"]), 100.0)
            self.assertTrue(item.get("reason"))

    def test_disputed_matchup_directions_are_consistent(self):
        index = {tuple(sorted((m["a"],m["b"]))):m for m in self.matchups}
        def chance(a,b):
            row=index[tuple(sorted((a,b)))]
            return row["a_win_probability"] if row["a"]==a else 100-row["a_win_probability"]
        self.assertTrue(48 <= chance("Shanks","Dracule Mihawk") <= 52)
        self.assertGreater(chance("Kaido","Monkey D. Luffy"),50)
        self.assertGreater(chance("Queen","Donquixote Doflamingo"),50)
        self.assertGreater(chance("Charlotte Katakuri","Boa Hancock"),50)

    def test_new_15_character_profiles_are_present(self):
        expected = {"Charlotte Smoothie","Charlotte Oven","Charlotte Daifuku","Charlotte Snack","Urouge","Edward Weevil","Vista","Jozu","S-Hawk","S-Snake","S-Bear","S-Shark","Limejuice","Shepherd Sommers","Rimoshifu Killingham"}
        actual={c["name"] for c in self.characters}
        self.assertTrue(expected.issubset(actual))
        ids=[c["id"] for c in self.characters]
        self.assertEqual(len(ids),len(set(ids)))

    def test_manga_cutoff_and_simulation_count(self):
        method=self.data["matchup_method"]
        self.assertEqual(method["simulations_per_pair"],15000)
        self.assertEqual(method["unique_pairs"],9045)
        self.assertEqual(method["total_simulated_fights"],135675000)
        self.assertEqual(self.data["review_summary"]["date"],"2026-11-05")

    def test_katakuri_haki_recalibration(self):
        kat=self.data["characters"]["Charlotte Katakuri"]
        self.assertEqual(kat["haki_score"],89)
        self.assertEqual(kat["ranking_stats"]["haki"],89)
        self.assertEqual(kat["haki_breakdown"]["observation"]["score"],98)
        self.assertEqual(kat["haki_breakdown"]["armament"]["score"],89)
        self.assertEqual(kat["haki_breakdown"]["conqueror"]["score"],80)
        self.assertEqual(kat["power"],89)
        self.assertEqual(len([m for m in self.matchups if "Charlotte Katakuri" in (m["a"],m["b"])]),134)


if __name__ == "__main__":
    unittest.main()
