import csv
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def test_killer_b_power_level_is_88_and_chakra_is_kept_separate():
    ratings = json.loads((BASE / "naruto" / "character_ratings.json").read_text(encoding="utf-8"))
    bee = ratings["characters"]["Killer B"]
    assert bee["power"] == 88
    assert bee["chakra_score"] == 98
    assert bee["abilities"] == 94


def test_killer_b_export_uses_the_same_88_power_level():
    with (BASE / "naruto" / "POWER_MATRIX_NARUTO_RANKINGS.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))
    bee = next(row for row in rows if row["Charakter"] == "Killer B")
    assert int(bee["Power Level"]) == 88
