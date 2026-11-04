from pathlib import Path
import re

BASE = Path(__file__).resolve().parents[1]
APP = (BASE / "app.py").read_text(encoding="utf-8")
WHEEL = (BASE / "fivefold_component" / "index.html").read_text(encoding="utf-8")
SQL = (BASE / "cloud_portraits_schema.sql").read_text(encoding="utf-8").lower()

def test_private_cloud_portrait_bucket_and_rls():
    assert "gld-character-portraits" in SQL
    assert "public=false" in SQL.replace(" ", "").replace("\n", "")
    assert "enable row level security" in SQL
    assert "revoke all" in SQL
    assert "to service_role" in SQL

def test_cloud_image_functions_and_zip_import_exist():
    assert "def upload_cloud_portraits" in APP
    assert "def portrait_archive_items" in APP
    assert "cloud_portrait_archive_upload" in APP
    assert "cloud_portraits_schema.sql" in APP

def test_direct_link_calls_cloud_upload():
    start = APP.index("def install_portrait_from_url")
    end = APP.index("def image_as_jpeg", start)
    fn = APP[start:end]
    assert "upload_cloud_portraits" in fn
    assert "direct_link" in fn

def test_online_spin_uses_shared_start_time():
    assert "classic_spin_started_at = time.time() + 2.50" in APP
    assert "rank_spin_started_at = time.time() + 2.50" in APP
    assert "start_at=st.session_state.get(\"classic_spin_started_at\")" in APP
    assert "start_at=st.session_state.get(\"rank_spin_started_at\")" in APP
    assert "startAtSeconds=Number(a.start_at||0)" in WHEEL

def test_remote_spin_preferred_during_poll():
    assert "remote_is_spin" in APP
    assert "not remote_is_spin" in APP
    assert "active_variant = remote_state.get(\"draft_variant\", \"classic\")" in APP

def test_polling_only_fetches_metadata_each_tick():
    assert "st.fragment(run_every=1.0)(online_poll_impl)" in APP
    assert "online_fetch_room_meta(code)" in APP

def test_no_service_secret_in_client_component():
    assert "service_role_key" not in WHEEL
    assert "sb_secret_" not in WHEEL

def test_portrait_archive_parser_has_limits_and_no_extractall():
    assert "info.file_size > 12 * 1024 * 1024" in APP
    assert "total_size > 150 * 1024 * 1024" in APP
    assert "extractall(" not in APP


def test_wheel_animation_keeps_dom_and_catches_up_to_shared_epoch():
    assert "Preserve the active DOM node on ordinary Streamlit rerenders" in WHEEL
    assert "animationDelay=elapsedMs>0" in WHEEL
    assert "will-change:transform" in WHEEL
