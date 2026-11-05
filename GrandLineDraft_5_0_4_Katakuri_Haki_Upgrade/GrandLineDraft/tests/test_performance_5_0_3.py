from pathlib import Path
import gzip
import json

BASE = Path(__file__).resolve().parents[1]


def test_matchups_are_split_from_startup_rating_payload():
    ratings = json.loads((BASE / "character_ratings.json").read_text(encoding="utf-8"))
    assert "matchup_results" not in ratings
    assert (BASE / "matchup_results.json.gz").stat().st_size < 800_000
    with gzip.open(BASE / "matchup_results.json.gz", "rt", encoding="utf-8") as handle:
        rows = json.load(handle)
    assert len(rows) == 135 * 134 // 2 == 9045


def test_profiles_and_portrait_prefetch_are_cached_in_code():
    app = (BASE / "app.py").read_text(encoding="utf-8")
    assert "def _build_character_profile_cached" in app
    assert "def _ranking_profile_cached" in app
    assert "def get_character_search_index" in app
    assert "def _cloud_portrait_batch" in app
    assert "def character_portrait_thumbnail" in app


def test_saves_only_once_at_end_of_full_render():
    app = (BASE / "app.py").read_text(encoding="utf-8")
    assert "The single end-of-run save below handles persistence once" in app
    assert "time.time() + 2.50" in app
