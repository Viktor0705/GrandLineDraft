from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
APP = (BASE / "app.py").read_text(encoding="utf-8")


def test_online_guest_is_auto_switched_to_host_anime_before_join():
    join = APP[APP.index("def online_join_room") : APP.index("def online_poll_impl")]
    assert 'room_universe = state.get("anime_universe", "one_piece")' in join
    assert 'return _prepare_online_join_universe_switch(room_universe, clean, guest_name)' in join
    assert "Bitte wechsle zuerst im Menü das Anime-Universum" not in join


def test_pending_anime_selector_is_applied_before_sidebar_widget():
    top = APP[:APP.index("ACTIVE_UNIVERSE =")]
    assert 'st.session_state.pop("_pending_anime_universe_selector", None)' in top
    assert 'st.session_state["anime_universe_selector"] = _pending_selector_label' in top


def test_pending_online_join_completes_after_new_universe_initializes():
    init = APP[APP.index("restore_persistent_game_state()") : APP.index("players = st.session_state.players")]
    assert 'st.session_state.pop("_pending_online_join", None)' in init
    assert 'online_join_room(' in init
    assert init.index("rank_init_game()") < init.index('st.session_state.pop("_pending_online_join", None)')


def test_online_join_switch_preserves_guest_local_save_and_invalidates_universe_caches():
    fn = APP[APP.index("def _prepare_online_join_universe_switch") : APP.index("def online_join_room")]
    assert "persist_game_state()" in fn
    assert 'st.session_state["anime_universe"] = room_universe' in fn
    assert '"get_characters"' in fn
    assert '"get_matchup_rows"' in fn


def test_online_payload_keeps_universe_id_and_rejects_cross_universe_poll_apply():
    assert '"anime_universe"' in APP[APP.index("GAME_STATE_KEYS =") : APP.index("ONLINE_ROOM_TABLE")]
    apply = APP[APP.index("def apply_online_state") : APP.index("def online_fetch_room") ]
    assert 'state.get("anime_universe", "one_piece") != ACTIVE_UNIVERSE' in apply


def test_online_join_stages_naruto_selection_and_delays_real_join_until_rerun():
    import ast
    import re

    class SessionState(dict):
        pass

    class StreamlitStub:
        def __init__(self):
            self.session_state = SessionState({
                "anime_universe": "one_piece",
                "players": {"A": {"name": "Guest"}},
                "pool_search": "Shanks",
            })

    st = StreamlitStub()
    source_tree = ast.parse(APP)
    wanted = {"_prepare_online_join_universe_switch", "online_join_room"}
    nodes = [node for node in source_tree.body if isinstance(node, ast.FunctionDef) and node.name in wanted]
    env = {
        "st": st,
        "re": re,
        "GAME_STATE_KEYS": ["anime_universe", "players", "remaining", "online_room_code", "online_role"],
        "_PENDING_ANIME_LABELS": {
            "one_piece": "One Piece",
            "naruto": "Naruto Shippuden · The Last (ohne Boruto)",
        },
        "ACTIVE_UNIVERSE": "one_piece",
        "supabase_config": lambda: {"url": "https://example.supabase.co", "key": "server-only"},
        "online_fetch_room": lambda code: {
            "status": "waiting",
            "guest_name": None,
            "payload": {"state": {
                "anime_universe": "naruto",
                "players": {"A": {"name": "Host"}, "B": {"name": "Wartet auf Mitspieler"}},
            }},
        },
        "persist_game_state": lambda: True,
    }
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "online_join_test", "exec"), env)

    ok, message = env["online_join_room"]("AB12CD34", "Guest")

    assert ok is True
    assert "automatisch umgestellt" in message
    assert st.session_state["anime_universe"] == "naruto"
    assert st.session_state["_pending_online_join"]["code"] == "AB12CD34"
    assert st.session_state["_pending_online_join"]["guest_name"] == "Guest"
    assert st.session_state["_pending_anime_universe_selector"] == "Naruto Shippuden · The Last (ohne Boruto)"
    assert "players" not in st.session_state  # old One Piece in-memory game was cleared
