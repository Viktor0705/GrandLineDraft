from __future__ import annotations

import gzip
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_gzip_json(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def pair_key(row):
    return tuple(sorted((row["a"], row["b"])))


def test_two_universes_have_independent_complete_rosters_and_matchups():
    one_piece = read_json(BASE / "characters.json")
    naruto = read_json(BASE / "naruto" / "characters.json")
    op_rows = read_gzip_json(BASE / "matchup_results.json.gz")
    naruto_rows = read_gzip_json(BASE / "naruto" / "matchup_results.json.gz")
    assert len(one_piece) == 140
    assert len(naruto) == 94
    assert len(op_rows) == 140 * 139 // 2
    assert len(naruto_rows) == 94 * 93 // 2
    assert len({pair_key(row) for row in op_rows}) == len(op_rows)
    assert len({pair_key(row) for row in naruto_rows}) == len(naruto_rows)
    assert all(row["simulations_per_pair"] == 15000 for row in op_rows + naruto_rows)


def test_universe_ids_do_not_overlap():
    op_ids = {int(item["id"]) for item in read_json(BASE / "characters.json")}
    naruto_ids = {int(item["id"]) for item in read_json(BASE / "naruto" / "characters.json")}
    assert len(op_ids) == 140
    assert len(naruto_ids) == 94
    assert op_ids.isdisjoint(naruto_ids)


def test_naruto_cutoff_excludes_boruto():
    characters = read_json(BASE / "naruto" / "characters.json")
    ratings = read_json(BASE / "naruto" / "character_ratings.json")
    assert "The Last" in ratings["anime_cutoff"]
    assert "Boruto" in ratings["anime_cutoff"]
    assert all("boruto" not in json.dumps(item, ensure_ascii=False).casefold() for item in characters)
    assert all("boruto" not in name.casefold() for name in ratings["characters"])


def test_user_requested_naruto_anchor_values_are_preserved():
    data = read_json(BASE / "naruto" / "character_ratings.json")["characters"]
    expected = {
        "Kaguya Ōtsutsuki": (100, 100, 100),
        "Hagoromo Ōtsutsuki": (100, 100, 100),
        "Madara Uchiha (Jūbi-Jinchūriki)": (98, 100, 100),
        "Naruto Uzumaki (The Last)": (97, 98, 97),
        "Sasuke Uchiha (The Last)": (97, 95, 98),
        "Hamura Ōtsutsuki": (96, 99, 50),
        "Obito Uchiha (Jūbi-Jinchūriki)": (95, 99, 95),
        "Ashura Ōtsutsuki": (95, 98, 98),
        "Indra Ōtsutsuki": (94, 97, 96),
        "Toneri Ōtsutsuki": (94, 98, 97),
        "Kakashi Hatake (DMS)": (94, 96, 98),
        "Might Guy (Acht Tore)": (93, 84, 97),
        "Hashirama Senju (Prime)": (92, 97, 91),
        "Nagato (Prime)": (90, 98, 100),
        "Pain (Sechs Pfade)": (88, 96, 97),
    }
    for name, values in expected.items():
        item = data[name]
        assert (item["power"], item["chakra_score"], item["abilities"]) == values
    assert data["Hamura Ōtsutsuki"]["abilities_unknown"] is True


def test_naruto_fivefold_has_five_distinct_categories():
    ratings = read_json(BASE / "naruto" / "character_ratings.json")["characters"]
    required = {"ninjutsu", "chakra", "taijutsu", "speed", "battle_iq"}
    assert len(ratings) == 94
    for character in ratings.values():
        stats = character["ranking_stats"]
        assert required.issubset(stats)
        for key in required:
            value = stats[key]
            assert value is None or 0 <= value <= 100


def test_naruto_matchups_include_core_counterplay_examples():
    rows = read_gzip_json(BASE / "naruto" / "matchup_results.json.gz")
    by_pair = {pair_key(row): row for row in rows}
    names = [
        ("Naruto Uzumaki (The Last)", "Toneri Ōtsutsuki"),
        ("Might Guy (Acht Tore)", "Madara Uchiha (Jūbi-Jinchūriki)"),
        ("Pain (Sechs Pfade)", "Jiraiya (Sennin-Modus)"),
    ]
    for a, b in names:
        row = by_pair[tuple(sorted((a, b)))]
        assert row["simulations_per_pair"] == 15000
        assert row["a_win_probability"] + (100 - row["a_win_probability"]) == 100
        assert row["reason"]


def test_app_switch_is_keyed_to_visible_universe_selector():
    app = (BASE / "app.py").read_text(encoding="utf-8")
    assert 'key="anime_universe_selector", on_change=on_anime_universe_change' in app
    callback = app[app.index("def on_anime_universe_change") : app.index("# ---- Sidebar", app.index("def on_anime_universe_change"))]
    assert 'st.session_state.get("anime_universe_selector", "One Piece")' in callback
    assert 'st.session_state["anime_universe"] = selected' in callback
    assert '"naruto": "naruto"' not in callback  # mapping is centralized at the selectbox, not duplicated incorrectly
    assert '"Naruto Shippuden · The Last (ohne Boruto)": "naruto"' in app
    assert 'st.session_state["anime_universe"] = ACTIVE_UNIVERSE' in callback
    assert 'MATCHUPS_FILE = DATA_DIR / "matchup_results.json.gz"' in app


def test_naruto_classic_mode_uses_chakra_and_skill_weights_without_haki_or_bounty():
    ratings = read_json(BASE / "naruto" / "character_ratings.json")
    assert ratings["weights"] == {"power": 0.68, "haki": 0.16, "abilities": 0.16, "versatility": 0.0}
    app = (BASE / "app.py").read_text(encoding="utf-8")
    assert 'RESOURCE_LABEL = "Chakra" if IS_NARUTO else "Haki"' in app
    assert 'live_record = None if IS_NARUTO else live_bounty_for(name)' in app
    assert '"Chakra", "chakra",' in app
    assert "Ninjutsu, Chakra, Taijutsu, Geschwindigkeit und Battle IQ" in app


def test_kaguya_and_hagoromo_are_full_100_ceiling_anchors():
    ratings = read_json(BASE / "naruto" / "character_ratings.json")["characters"]
    for name in ("Kaguya Ōtsutsuki", "Hagoromo Ōtsutsuki"):
        p = ratings[name]
        assert (p["power"], p["chakra_score"], p["abilities"]) == (100, 100, 100)
        assert all(p["ranking_stats"][k] == 100 for k in ("ninjutsu", "chakra", "taijutsu", "speed", "battle_iq"))
        assert all(p["combat_stats"][k] == 100 for k in ("offense", "defense", "speed", "endurance", "battle_iq", "chakra_control"))
        assert "haki_mastery" not in p["combat_stats"]


def test_naruto_browser_has_its_own_categories_and_no_one_piece_filters():
    app = (BASE / "app.py").read_text(encoding="utf-8")
    start = app.index("def render_naruto_roster_browser")
    end = app.index("def render_roster_browser", start)
    body = app[start:end]
    assert '"Chakra", "Ninjutsu", "Taijutsu", "Geschwindigkeit", "Battle IQ"' in body
    assert "TEUFELSFRUCHT" not in body.upper()
    assert "KOPFGELD" not in body.upper()
    assert "HAKI" not in body.upper()


def test_naruto_local_portrait_file_patterns_accept_four_digit_ids():
    app = (BASE / "app.py").read_text(encoding="utf-8")
    start = app.index("def local_portrait_items")
    end = app.index("def ", start + 5)
    body = app[start:end]
    assert r"manual_character_(\d{3,})" in body
    assert r"linked_character_(\d{3,})" in body
    assert r"character_(\d{3,})_" in body


def test_naruto_ai_and_unknown_abilities_are_labeled_correctly():
    app = (BASE / "app.py").read_text(encoding="utf-8")
    assert '("Shinobi-KI" if IS_NARUTO else "Grand Line KI")' in app
    assert 'ability_small = "FÄHIG. N. B." if ch_profile.get("abilities_unknown")' in app
    assert 'chakra_text = f"{int(chakra_raw)}/100" if isinstance(chakra_raw, (int, float)) else "unbekannt"' in app


def test_fivefold_widget_has_naruto_specific_category_icons():
    widget = (BASE / "fivefold_component" / "index.html").read_text(encoding="utf-8")
    for label in ("Ninjutsu", "Chakra", "Taijutsu"):
        assert f"'{label}':{{icon:" in widget


def test_all_135_original_one_piece_characters_and_ids_are_preserved():
    legacy = read_json(BASE / "tests" / "legacy_one_piece_roster_5_0_4.json")
    current = read_json(BASE / "characters.json")
    current_by_name = {item["name"]: int(item["id"]) for item in current}
    assert len(legacy) == 135
    for item in legacy:
        assert current_by_name.get(item["name"]) == int(item["id"])
    assert {item["name"] for item in current} - {item["name"] for item in legacy} == {
        "Kyros", "Ashura Doji", "Gecko Moria (Prime)", "Vergo", "Kanjuro"
    }


def test_kaguya_hagoromo_include_all_requested_top_end_attributes():
    ratings = read_json(BASE / "naruto" / "character_ratings.json")["characters"]
    for name in ("Kaguya Ōtsutsuki", "Hagoromo Ōtsutsuki"):
        p = ratings[name]
        assert p["versatility"] == 100
        assert p["intelligence"] == 100
        assert p["abilities"] == 100
        assert p["power"] == 100
        assert p["chakra_score"] == 100
        assert all(p["combat_stats"][k] == 100 for k in ("offense", "defense", "speed", "endurance", "battle_iq", "chakra_control"))


def test_remaining_user_stated_naruto_anchors_are_present():
    ratings = read_json(BASE / "naruto" / "character_ratings.json")["characters"]
    expected = {
        "Hiruzen Sarutobi (Prime)": (91, 94, 96),
        "Tobirama Senju (Prime)": (91, 95, 97),
        "Nagato (Prime)": (90, 98, 100),
        "Minato Namikaze (KCM · Edo)": (90, 96, 97),
        "Itachi Uchiha (Edo Tensei)": (90, 94, 98),
        "Kabuto Yakushi (Sennin-Modus)": (89, 94, 97),
        "Pain (Sechs Pfade)": (88, 96, 97),
    }
    for name, values in expected.items():
        p = ratings[name]
        assert (p["power"], p["chakra_score"], p["abilities"]) == values
