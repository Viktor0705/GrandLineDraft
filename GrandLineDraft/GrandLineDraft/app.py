from __future__ import annotations

import hashlib
import base64
import gzip
import threading
from itertools import permutations
import html
import io
import json
import math
import random
import re
import secrets
import time
import os
import zipfile
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

import requests
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
CHARACTERS_FILE = BASE_DIR / "characters.json"
RATINGS_FILE = BASE_DIR / "character_ratings.json"
PORTRAIT_DIR = BASE_DIR / "portraits"
SAVE_DIR = BASE_DIR / "saves"
AUTOSAVE_FILE = SAVE_DIR / "autosave.json"
PORTRAIT_LINKS_FILE = BASE_DIR / "portrait_links.json"
START_BUDGET = 20
TEAM_SIZE = 5
MIN_PRICE = 1
MAX_RETURNS = 3
RETURN_PENALTY = 1
API_BASE = "https://onepieceapi.com/api/characters"
FANDOM_API = "https://onepiece.fandom.com/api.php"
USER_AGENT = "GrandLineDraft/5.0.3 (fan game; performance edition)"
PORTRAIT_DIR.mkdir(exist_ok=True)

# Keep-alive HTTP sessions are local to each Streamlit worker thread. This avoids
# opening a fresh TCP/TLS connection for every small Supabase poll or image request.
_HTTP_LOCAL = threading.local()

def http_session() -> requests.Session:
    session = getattr(_HTTP_LOCAL, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        _HTTP_LOCAL.session = session
    return session

st.set_page_config(
    page_title="Grand Line Draft 5.0.3 | Performance Edition",
    page_icon="🏴‍☠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Local custom component: animation and drag-and-drop run in the browser rather
# than blocking Python or repeatedly rebuilding the whole Streamlit page.
FIVEFOLD_WIDGET = components.declare_component(
    "grandline_fivefold_widget", path=str(BASE_DIR / "fivefold_component")
)

# ---- Styling ---------------------------------------------------------------
st.markdown(r"""
<style>
/* Local system fonts only: no external font request during startup. */
:root { --gold:#e8bd64; --gold2:#b98732; --ink:#07111b; --panel:#101d2b; --panel2:#152638; --muted:#92a5b9; --white:#eef4fa; --red:#e65e5e; --line:rgba(210,226,243,.12); }
html, body, [class*="css"] { font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; }
.stApp { background: radial-gradient(ellipse at 50% -10%, #19334a 0%, #0a1724 44%, #060c14 100%); color:var(--white); }
[data-testid="stHeader"] { background:transparent; }
.block-container { padding-top:1.15rem; padding-bottom:3rem; max-width:1540px; }
#MainMenu, footer {visibility:hidden;}
[data-testid="stSidebar"] { background:linear-gradient(180deg,#0b1723,#08111b); border-right:1px solid var(--line); }
[data-testid="stSidebar"] * { color:var(--white); }
.stMarkdown p { color: #d7e0e9; }
h1,h2,h3 { color:var(--white)!important; font-family:'Arial Narrow','Roboto Condensed',system-ui,sans-serif!important; letter-spacing:.045em; }
h1 { font-size: clamp(2.6rem, 4.5vw, 4rem)!important; line-height:.95!important; font-weight:900!important; margin-bottom:.1rem!important; }
h2 { font-size:2rem!important; font-weight:800!important; }
h3 { font-size:1.35rem!important; font-weight:800!important; }
.eyebrow { color:var(--gold); text-transform:uppercase; letter-spacing:.2em; font-size:.72rem; font-weight:800; }
.hero-sub { color:#a9bacb; margin-top:.4rem; font-size:.95rem; }
.gold { color:var(--gold); }
.hero-mark { display:inline-flex; align-items:center; justify-content:center; width:58px; height:58px; border-radius:17px; margin-right:14px; background:linear-gradient(145deg,#f0ce81,#9e6d20); box-shadow:0 10px 35px rgba(213,157,55,.17); color:#08111a; font-size:2rem; }
.brand-row { display:flex; align-items:center; gap:14px; }
.brand-mini { color:#91a3b6; font-size:.72rem; letter-spacing:.16em; font-weight:800; text-transform:uppercase; }
.stat-strip { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin:1.1rem 0 1.3rem; }
.stat { background:rgba(16,29,43,.84); border:1px solid var(--line); padding:13px 16px; border-radius:14px; }
.stat-label { color:#91a4b8; font-weight:700; letter-spacing:.12em; text-transform:uppercase; font-size:.66rem; }
.stat-value { font-family:'Arial Narrow','Roboto Condensed',system-ui,sans-serif; font-size:1.8rem; font-weight:800; color:var(--white); margin-top:2px; }
.stat-value span { color:var(--gold); }
.panel-label { color:var(--gold); font-size:.7rem; font-weight:800; letter-spacing:.18em; text-transform:uppercase; }
.player-heading { display:flex; align-items:center; justify-content:space-between; gap:8px; }
.player-name { font-family:'Arial Narrow','Roboto Condensed',system-ui,sans-serif; font-size:1.8rem; line-height:1; font-weight:900; letter-spacing:.04em; }
.player-tag { font-size:.68rem; padding:5px 8px; border:1px solid var(--line); color:#b9c8d5; border-radius:99px; white-space:nowrap; }
.player-money { font-family:'Arial Narrow','Roboto Condensed',system-ui,sans-serif; font-size:2.3rem; font-weight:900; color:var(--gold); line-height:1.1; }
.player-meta { color:#8fa2b5; font-size:.75rem; }
.slot-title { font-size:.66rem; color:#92a5b9; text-transform:uppercase; letter-spacing:.13em; font-weight:800; }
.slot-empty { display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:102px; border:1px dashed rgba(167,190,212,.2); border-radius:11px; color:#63788e; background:rgba(255,255,255,.015); text-align:center; font-size:.7rem; padding:5px; }
.slot-empty b { font-family:'Arial Narrow','Roboto Condensed',system-ui,sans-serif; font-size:1.3rem; color:#64798e; }
div[data-testid="stVerticalBlockBorderWrapper"] { background:linear-gradient(165deg,rgba(19,35,51,.88),rgba(8,17,27,.92)); border-color:var(--line)!important; border-radius:18px!important; }
div.stButton > button { border-radius:11px; border:1px solid rgba(232,189,100,.4); font-weight:800; min-height:2.6rem; transition:all .18s ease; }
div.stButton > button[kind="primary"] { background:linear-gradient(135deg,#efcb7a,#c1903c); color:#0a1420; border:1px solid #f5d891; box-shadow:0 8px 20px rgba(195,145,59,.16); }
div.stButton > button[kind="primary"]:hover { background:linear-gradient(135deg,#ffe2a0,#d29a3a); transform:translateY(-1px); color:#06101a; border-color:#ffe4aa; }
div.stButton > button[kind="secondary"] { background:#142536; color:#e5edf5; border-color:var(--line); }
div.stButton > button[kind="secondary"]:hover { border-color:var(--gold); color:var(--gold); }
[data-testid="stImage"] img { border-radius:12px; }
[data-testid="stProgressBar"] > div { background:#24384b; border-radius:99px; }
[data-testid="stProgressBar"] > div > div { background:linear-gradient(90deg,#bd8734,#f5d58a); border-radius:99px; }
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div { background:#0c1824; border-color:rgba(210,226,243,.17); border-radius:10px; }
label, [data-testid="stWidgetLabel"] p { color:#a8b9c9!important; font-size:.82rem!important; }
hr { border-color:var(--line)!important; }
.small-muted { color:#91a5b7; font-size:.78rem; }
.character-name { font-family:'Arial Narrow','Roboto Condensed',system-ui,sans-serif; font-size:1.8rem; line-height:1.05; font-weight:900; color:#fff; }
.character-sub { color:#9db0c2; font-size:.79rem; margin-top:.25rem; }
.price-pill { display:inline-block; color:#121a22; font-size:.78rem; font-weight:900; background:var(--gold); border-radius:99px; padding:5px 10px; }
.round-banner { border:1px solid rgba(232,189,100,.28); background:linear-gradient(90deg,rgba(232,189,100,.09),rgba(232,189,100,.025)); border-radius:13px; padding:12px 14px; }
.status-dot { display:inline-block; width:7px; height:7px; border-radius:50%; background:#79d7a5; margin-right:7px; box-shadow:0 0 0 4px rgba(121,215,165,.08); }
.wheel-shell { display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; padding:8px 0 16px; }
.wheel { position:relative; width:min(250px,70vw); aspect-ratio:1; border-radius:50%; border:7px solid #e9c574; box-shadow:0 0 0 8px rgba(232,189,100,.08), 0 15px 45px rgba(0,0,0,.32), inset 0 0 0 3px rgba(4,12,20,.8); background:conic-gradient(from 0deg,#223a4b 0 30deg,#b9893e 30deg 60deg,#172b3b 60deg 90deg,#dcba6e 90deg 120deg,#223a4b 120deg 150deg,#b9893e 150deg 180deg,#172b3b 180deg 210deg,#dcba6e 210deg 240deg,#223a4b 240deg 270deg,#b9893e 270deg 300deg,#172b3b 300deg 330deg,#dcba6e 330deg 360deg); transition:transform .075s linear; display:flex; align-items:center; justify-content:center; }
.wheel:before { content:''; position:absolute; inset:21px; border-radius:50%; border:1px dashed rgba(255,255,255,.38); }
.wheel-hub { z-index:1; border-radius:50%; width:92px; height:92px; background:linear-gradient(140deg,#f0d28e,#a36d21); border:5px solid #101d2b; display:flex; align-items:center; justify-content:center; color:#101720; font-size:2rem; box-shadow:0 4px 18px rgba(0,0,0,.4); }
.wheel-pointer { color:#f5d992; font-size:1.9rem; margin-bottom:-12px; z-index:2; text-shadow:0 2px 6px #000; }
.wheel-caption { color:#8fa4b8; font-size:.72rem; letter-spacing:.18em; text-transform:uppercase; font-weight:800; margin-top:14px; }
.result-wrap { border:1px solid rgba(232,189,100,.34); border-radius:18px; background:radial-gradient(circle at 50% 0%,rgba(232,189,100,.11),transparent 45%),rgba(7,15,24,.55); padding:17px; text-align:center; }
.auction-price { font-family:'Arial Narrow','Roboto Condensed',system-ui,sans-serif; font-size:3.2rem; line-height:1; font-weight:900; color:var(--gold); }
.auction-turn { color:#d3dfeb; font-size:.82rem; }
.winner-row { border-radius:11px; border:1px solid rgba(121,215,165,.25); background:rgba(121,215,165,.07); padding:12px; color:#b7f2d0; font-weight:700; }
.history-row { display:flex; gap:10px; align-items:center; padding:9px 0; border-bottom:1px solid rgba(210,226,243,.08); }
.history-no { color:#8296aa; font-family:'Arial Narrow','Roboto Condensed',system-ui,sans-serif; font-size:1.2rem; font-weight:800; min-width:28px; }
.history-main { flex:1; color:#e0e9f1; font-size:.83rem; }
.history-price { color:var(--gold); font-weight:900; font-size:.9rem; white-space:nowrap; }
.footer-note { color:#71869b; font-size:.72rem; text-align:center; padding-top:15px; }
.crew-score { font-family:'Arial Narrow','Roboto Condensed',system-ui,sans-serif; font-size:2.35rem; font-weight:900; line-height:1.0; color:var(--gold); }
.crew-score-label { color:#90a5b9; letter-spacing:.14em; text-transform:uppercase; font-size:.65rem; font-weight:800; }
.team-total-card { border:1px solid rgba(232,189,100,.42); background:linear-gradient(140deg,rgba(232,189,100,.13),rgba(12,24,36,.72)); border-radius:15px; padding:14px 16px; margin:12px 0 14px; }
.team-total-label { color:#b9c8d7; text-transform:uppercase; letter-spacing:.15em; font-weight:800; font-size:.67rem; }
.team-total-value { display:flex; align-items:baseline; flex-wrap:wrap; gap:7px; color:var(--gold); font-family:'Arial Narrow','Roboto Condensed',system-ui,sans-serif; font-size:clamp(2rem,4vw,3rem); font-weight:900; line-height:1.08; margin-top:4px; font-variant-numeric:tabular-nums; }
.team-total-value span { color:#dce5ed; font-family:'Inter',sans-serif; font-size:.78rem; font-weight:800; letter-spacing:.04em; }
.team-total-meta { color:#91a5b8; font-size:.74rem; margin-top:4px; }
div[data-testid="stMetric"] { min-width:0; }
div[data-testid="stMetricLabel"] { min-height:1.5rem; }
div[data-testid="stMetricLabel"] p { white-space:normal!important; line-height:1.2!important; overflow-wrap:anywhere!important; }
div[data-testid="stMetricValue"] { white-space:normal!important; overflow-wrap:anywhere!important; line-height:1.15!important; font-variant-numeric:tabular-nums; }
div[data-testid="stMetricValue"] > div { font-size:clamp(1.05rem,2.2vw,1.65rem)!important; line-height:1.15!important; white-space:normal!important; overflow-wrap:anywhere!important; }
.analysis-note { border:1px solid rgba(232,189,100,.18); border-radius:12px; background:rgba(232,189,100,.045); padding:12px 14px; color:#d7e0e9; font-size:.82rem; }
.analysis-chip { display:inline-block; border-radius:99px; padding:4px 8px; font-size:.68rem; font-weight:800; background:rgba(232,189,100,.12); color:#f1ce84; border:1px solid rgba(232,189,100,.18); margin:2px 4px 2px 0; }
@media (max-width:800px) { .stat-strip{grid-template-columns:repeat(2,minmax(0,1fr));} .player-name{font-size:1.5rem;} }
.draft-card-banner { border:1px solid rgba(232,189,100,.35); border-radius:15px; padding:13px 15px; background:radial-gradient(circle at 0% 0%,rgba(232,189,100,.13),transparent 48%),linear-gradient(135deg,rgba(14,31,46,.9),rgba(7,15,24,.92)); margin:10px 0 13px; }
.draft-card-kicker { font-size:.65rem; color:#e8bd64; font-weight:900; letter-spacing:.19em; text-transform:uppercase; }
.draft-card-name { font-family:'Arial Narrow','Roboto Condensed',system-ui,sans-serif; font-size:clamp(1.9rem,3vw,2.7rem); font-weight:900; color:#f6f8fb; line-height:1; margin-top:5px; }
.draft-card-sub { color:#9fb2c4; font-size:.78rem; margin-top:6px; }
.score-pills { display:flex; flex-wrap:wrap; gap:6px; margin-top:10px; }
.score-pill { display:inline-flex; align-items:center; gap:5px; border:1px solid rgba(232,189,100,.25); background:rgba(232,189,100,.075); color:#f1d18b; border-radius:8px; padding:5px 8px; font-size:.7rem; font-weight:800; }
.combat-grid { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:7px; margin:8px 0; }
.combat-stat { border:1px solid rgba(210,226,243,.1); background:rgba(255,255,255,.025); border-radius:10px; padding:9px; min-width:0; }
.combat-stat-label { text-transform:uppercase; letter-spacing:.08em; font-size:.58rem; font-weight:800; color:#91a5b8; }
.combat-stat-value { font-family:'Arial Narrow','Roboto Condensed',system-ui,sans-serif; font-size:1.45rem; font-weight:900; color:#f2ca77; margin-top:2px; }
.evidence-line { border-left:2px solid #b98732; padding:7px 10px; color:#cbd7e2; font-size:.79rem; background:rgba(232,189,100,.035); margin:6px 0; }
@media(max-width:800px) {.combat-grid{grid-template-columns:repeat(2,minmax(0,1fr));}}
</style>
""", unsafe_allow_html=True)


# ---- Format and data --------------------------------------------------------
def money(value: float) -> str:
    return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower().replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("ß", "ss"))


def safe_text(value: Any) -> str:
    return html.escape(str(value), quote=True)


def search_text(value: Any) -> str:
    """Convert optional character metadata to searchable text without failing on None."""
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(search_text(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return " ".join(search_text(item) for item in value)
    return str(value)


@st.cache_data(show_spinner=False)
def get_characters() -> list[dict[str, Any]]:
    with CHARACTERS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def get_rating_data() -> dict[str, Any]:
    try:
        return json.loads(RATINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "weights": {"power": .68, "haki": .14, "abilities": .14, "versatility": .04},
            "characters": {},
            "sources": {},
        }


MATCHUPS_FILE = BASE_DIR / "matchup_results.json.gz"

@st.cache_data(show_spinner=False, max_entries=1)
def get_matchup_rows() -> list[dict[str, Any]]:
    """Load the large pairwise table only when a finished-team matchup is requested."""
    if MATCHUPS_FILE.is_file():
        try:
            with gzip.open(MATCHUPS_FILE, "rt", encoding="utf-8") as handle:
                rows = json.load(handle)
            return rows if isinstance(rows, list) else []
        except (OSError, EOFError, gzip.BadGzipFile, json.JSONDecodeError):
            return []
    # Backwards compatibility with 5.0.0/5.0.1 projects where rows lived in the main JSON.
    rows = get_rating_data().get("matchup_results", [])
    return rows if isinstance(rows, list) else []


def bounty_label(amount: int | None, state: str = "unbekannt") -> str:
    if amount is None:
        return "Unbekannt"
    if amount <= 0:
        return "Kein bestätigtes Kopfgeld"
    shown = f"{amount:,}".replace(",", ".") + " ฿"
    if state == "historisch":
        return shown + " · historisch"
    if state == "cross_guild":
        return shown + " · Cross Guild"
    return shown


BOUNTY_ALIASES = {
    "Roronoa Zoro": ["Lorenor Zorro", "Zoro"],
    "Jinbe": ["Jinbei"], "Dracule Mihawk": ["Mihawk"],
    "Trafalgar D. Water Law": ["Trafalgar Law", "Trafalgar (D. Water) Law"],
    "Marshall D. Teach": ["Blackbeard"], "Edward Newgate": ["Whitebeard"],
    "Charlotte Linlin": ["Big Mom"], "Kaido": ["Kaidou"],
    "Donquixote Doflamingo": ["Don Quichotte de Flamingo", "Doflamingo"],
    "Sakazuki (Akainu)": ["Sakazuki", "Akainu"], "Kuzan (Aokiji)": ["Kuzan", "Aokiji"],
    "Borsalino (Kizaru)": ["Borsalino", "Kizaru"], "Issho (Fujitora)": ["Issho", "Fujitora"],
    "Aramaki (Ryokugyu)": ["Aramaki", "Ryokugyu"], "Tony Tony Chopper": ["Chopper"],
    "Capone Bege": ["Capone"], "Don Chinjao": ["Chinjao"], "Boa Sandersonia": ["Sandersonia"],
    "Boa Marigold": ["Marigold"], "Monkey D. Dragon": ["Dragon"], "Emporio Ivankov": ["Ivankov"],
    "Vinsmoke Reiju": ["Reiju"], "Dr. Vegapunk": ["Vegapunk"], "Vinsmoke Judge": ["Judge"],
    "Donquixote Rosinante": ["Rosinante", "Corazon"], "Gol D. Roger": ["Roger"],
    "Silvers Rayleigh": ["Rayleigh"], "Jewelry Bonney": ["Bonney"],
    "Bartholomew Kuma": ["Kuma"], "Portgas D. Ace": ["Portgas Ace"], "Rob Lucci": ["Lucci"],
    "Who's-Who": ["Who's Who"], "Nefertari Vivi": ["Vivi"],
}


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_live_bounty_data() -> tuple[dict[str, dict[str, Any]], str]:
    """Only fetch public data when the user presses the refresh button."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    result: dict[str, dict[str, Any]] = {}
    try:
        for page in range(1, 16):
            response = session.get(API_BASE, params={"limit": 100, "page": page}, timeout=6)
            response.raise_for_status()
            payload = response.json()
            records = payload.get("data", payload.get("results", [])) if isinstance(payload, dict) else payload
            if not isinstance(records, list) or not records:
                break
            for row in records:
                if not isinstance(row, dict):
                    continue
                raw_name = row.get("name", "")
                if isinstance(raw_name, dict):
                    raw_name = raw_name.get("en") or raw_name.get("romaji") or raw_name.get("jp") or ""
                key = normalize(str(raw_name))
                if not key:
                    continue
                bounty_rows = row.get("bounties") or []
                active = [b for b in bounty_rows if isinstance(b, dict) and b.get("is_active") and isinstance(b.get("amount"), (int, float)) and b.get("amount", 0) > 0]
                if active:
                    chosen = max(active, key=lambda b: int(b.get("amount", 0)))
                    result[key] = {"amount": int(chosen["amount"]), "state": "aktiv", "source": "One Piece API"}
            if len(records) < 100:
                break
        if result:
            stamp = datetime.now(timezone.utc).astimezone().strftime("%d.%m.%Y, %H:%M")
            return result, stamp
        return {}, "Keine aktiven Kopfgelder aus der API erhalten. Offline-Daten bleiben erhalten."
    except (requests.RequestException, ValueError, TypeError) as exc:
        return {}, f"Online-Abruf fehlgeschlagen ({type(exc).__name__}). Offline-Daten bleiben erhalten."


def live_bounty_for(name: str) -> dict[str, Any] | None:
    live = st.session_state.get("live_bounties", {})
    for candidate in [name, *BOUNTY_ALIASES.get(name, [])]:
        record = live.get(normalize(candidate))
        if record:
            return record
    return None


def power_tier(value: float) -> str:
    """Readable fan-tier label; it is not an official One Piece classification."""
    if value >= 99:
        return "MYTHOS-TIER"
    if value >= 97:
        return "LEGENDEN-TIER"
    if value >= 94:
        return "KAISER-/SPITZEN-TIER"
    if value >= 90:
        return "OBERKLASSE"
    if value >= 85:
        return "KOMMANDANTEN-TIER"
    if value >= 75:
        return "ELITE"
    if value >= 60:
        return "KAMPFERFAHREN"
    if value >= 40:
        return "SPEZIALIST"
    return "BEGRENZTE KAMPFFEATS"


@st.cache_data(show_spinner=False, max_entries=512)
def _build_character_profile_cached(
    character_name: str,
    rating_entry: dict[str, Any],
    weights: dict[str, Any],
    live_record: dict[str, Any] | None,
) -> dict[str, Any]:
    """Pure profile derivation cached by the character's static data and optional bounty override."""
    profile = {
        "power": 50, "abilities": 50, "intelligence": 50, "intelligence_bonus": 0.0,
        "haki_score": None, "haki_status": "nicht bestätigt", "haki_types": [],
        "haki_note": "Für diese Figur ist keine bestätigte Haki-Anwendung hinterlegt; sie wird nicht mit 0 bewertet.",
        "versatility": 50, "status": 50,
        "bounty": None, "bounty_state": "unbekannt", "confidence": "Niedrig",
        "rationale": "Für diese Figur liegt noch keine detaillierte Einzelbewertung vor.",
        "ability_summary": "Noch keine individuelle Fähigkeitsbeschreibung hinterlegt.",
        "combat_stats": {"offense": 50, "defense": 50, "speed": 50, "endurance": 50, "battle_iq": 50, "haki_mastery": 0},
        "weaknesses": "Kein besonderer Konter hinterlegt.",
        **(rating_entry if isinstance(rating_entry, dict) else {}),
    }
    if not isinstance(profile.get("haki_types"), list):
        profile["haki_types"] = []
    if not isinstance(profile.get("haki_breakdown"), dict):
        profile["haki_breakdown"] = {}
    if profile.get("haki_status") != "bestätigt" or not isinstance(profile.get("haki_score"), (int, float)):
        profile["haki_score"] = None
        if not profile.get("haki_status"):
            profile["haki_status"] = "nicht bestätigt"
    if live_record:
        profile["bounty"] = live_record.get("amount")
        if profile.get("bounty_state") != "cross_guild":
            profile["bounty_state"] = "aktiv"
        profile["bounty_source"] = "live"
    else:
        profile["bounty_source"] = "offline"
    bounty = profile.get("bounty")
    bounty_score = 50.0 if bounty is None else min(100.0, 100 * math.log1p(max(0, bounty) / 1_000_000) / math.log1p(5_564.8))
    personal_weights = {k: float(weights.get(k, 0)) for k in ("power", "haki", "abilities", "versatility")}
    present = {
        "power": float(profile.get("power", 50)),
        "abilities": float(profile.get("abilities", 50)),
        "versatility": float(profile.get("versatility", 50)),
    }
    if profile.get("haki_score") is not None:
        present["haki"] = float(profile["haki_score"])
    else:
        personal_weights["haki"] = 0.0
        total_other = sum(personal_weights.values())
        if total_other:
            personal_weights = {k: v / total_other for k, v in personal_weights.items()}
    score_base = sum(present.get(k, 0.0) * personal_weights.get(k, 0.0) for k in personal_weights)
    intel = max(0.0, min(100.0, float(profile.get("intelligence", 50))))
    profile["intelligence_bonus"] = round(max(0.0, min(.45, (intel - 50.0) / 50.0 * .45)), 3)
    score = score_base + float(profile.get("intelligence_bonus", 0.0))
    profile["bounty_score"] = round(bounty_score, 1)
    profile["weighted_base_score"] = round(score_base, 3)
    profile["score"] = round(max(0, min(100, score)), 1)
    profile["individual_weights"] = personal_weights
    return profile


def character_profile(character: dict[str, Any]) -> dict[str, Any]:
    name = str(character.get("name", ""))
    rating_entry = get_rating_data().get("characters", {}).get(name, {})
    weights = get_rating_data().get("weights", {"power": .68, "haki": .14, "abilities": .14, "versatility": .04})
    live_record = live_bounty_for(name)
    return _build_character_profile_cached(name, rating_entry, weights, live_record)


# Chemistry values are fan-model estimates of how well two characters would work together.
# Pairs not listed are inferred conservatively from crew affiliation, not assumed perfect.
def _pair_key(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((normalize(a), normalize(b))))


@st.cache_data(show_spinner=False)
def get_matchup_index() -> dict[tuple[str, str], dict[str, Any]]:
    """Build a constant-time lookup for the supplied v5.0 pairwise simulations."""
    rows = get_matchup_rows()
    index: dict[tuple[str, str], dict[str, Any]] = {}
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            name_a, name_b = row.get("a"), row.get("b")
            if name_a and name_b and normalize(str(name_a)) != normalize(str(name_b)):
                index[_pair_key(str(name_a), str(name_b))] = row
    return index


CHEMISTRY_PAIRS = {
    _pair_key("Monkey D. Luffy", "Roronoa Zoro"): 88,
    _pair_key("Monkey D. Luffy", "Nami"): 83,
    _pair_key("Monkey D. Luffy", "Sanji"): 82,
    _pair_key("Monkey D. Luffy", "Usopp"): 86,
    _pair_key("Monkey D. Luffy", "Nico Robin"): 78,
    _pair_key("Monkey D. Luffy", "Trafalgar D. Water Law"): 79,
    _pair_key("Nami", "Usopp"): 83,
    _pair_key("Nico Robin", "Franky"): 77,
    _pair_key("Roronoa Zoro", "Sanji"): 57,
    _pair_key("Shanks", "Benn Beckman"): 88,
    _pair_key("Gol D. Roger", "Silvers Rayleigh"): 89,
    _pair_key("Edward Newgate", "Marco"): 84,
    _pair_key("Marshall D. Teach", "Van Augur"): 76,
    _pair_key("Kaido", "King"): 78,
    _pair_key("King", "Queen"): 61,
    _pair_key("Queen", "Jack"): 62,
    _pair_key("Charlotte Linlin", "Charlotte Katakuri"): 76,
    _pair_key("Charlotte Katakuri", "Charlotte Pudding"): 77,
    _pair_key("Law", "Bepo"): 90,
    _pair_key("Trafalgar D. Water Law", "Bepo"): 90,
    _pair_key("Bepo", "Shachi"): 85,
    _pair_key("Bepo", "Penguin"): 85,
    _pair_key("Shachi", "Penguin"): 84,
    _pair_key("Nekomamushi", "Inuarashi"): 92,
    _pair_key("Carrot", "Pedro"): 84,
    _pair_key("Chopper", "Dr. Kureha"): 82,
    _pair_key("Dr. Kureha", "Dr. Hiriluk"): 81,
    _pair_key("Iceburg", "Paulie"): 78,
    _pair_key("Koby", "Monkey D. Garp"): 86,
    _pair_key("Crocodile", "Dracule Mihawk"): 59,
    _pair_key("Buggy", "Crocodile"): 43,
    _pair_key("Buggy", "Dracule Mihawk"): 43,
    _pair_key("Crocodile", "Monkey D. Luffy"): 34,
    _pair_key("King", "Kingbaum"): 48,
}


def faction_group(character: dict[str, Any]) -> str:
    faction = str(character.get("faction", "")).lower()
    groups = [
        ("Strohhut", "strawhats"), ("Bestien-Piraten", "beast_pirates"), ("Big-Mom-Piraten", "big_mom"),
        ("Heart-Piraten", "heart_pirates"), ("Marine", "marines"), ("Cipher Pol", "cipher_pol"),
        ("Revolutionäre", "revolutionaries"), ("Cross Guild", "cross_guild"), ("Mink", "minks"),
        ("Wano", "wano"), ("Roger-Piraten", "roger_pirates"), ("Whitebeard-Piraten", "whitebeard"),
    ]
    for token, group in groups:
        if token.lower() in faction:
            return group
    return faction


def pair_chemistry(a: dict[str, Any], b: dict[str, Any]) -> float:
    explicit = CHEMISTRY_PAIRS.get(_pair_key(a.get("name", ""), b.get("name", "")))
    if explicit is not None:
        return float(explicit)
    fa, fb = faction_group(a), faction_group(b)
    if fa and fa == fb:
        return 65.0
    if fa and fb and ({fa, fb} <= {"strawhats", "minks", "wano", "heart_pirates"}):
        return 57.0
    return 48.0


def analyze_team(team: list[dict[str, Any]]) -> dict[str, Any]:
    profiles = [character_profile(ch) | {"name": ch.get("name", ""), "price": ch.get("price", 0), "character": ch} for ch in team]
    if not profiles:
        return {"profiles": [], "score": None, "chemistry": 50.0, "confidence": "Noch offen", "bounty_total": 0, "known_bounties": 0, "spent": 0,
                "haki_avg": None, "haki_count": 0, "haki_unknown_count": 0, "haki_names": [], "weighted_contributions": {}, "effective_weights": {}}
    average = lambda key: sum(float(p.get(key, 50)) for p in profiles) / len(profiles)
    pairs = [pair_chemistry(profiles[i]["character"], profiles[j]["character"]) for i in range(len(profiles)) for j in range(i + 1, len(profiles))]
    chemistry = sum(pairs) / len(pairs) if pairs else 50.0

    ratings = get_rating_data()
    configured = ratings.get("weights", {"power": .68, "haki": .14, "abilities": .14, "versatility": .04})
    avg_values = {
        "power": average("power"),
        "abilities": average("abilities"),
        "versatility": average("versatility"),
    }
    confirmed_haki = [p for p in profiles if p.get("haki_status") == "bestätigt" and isinstance(p.get("haki_score"), (int, float))]
    haki_avg = sum(float(p["haki_score"]) for p in confirmed_haki) / len(confirmed_haki) if confirmed_haki else None
    haki_unknown_count = len(profiles) - len(confirmed_haki)

    # If at least one Haki profile is confirmed, use the configured 14% Haki component
    # as the average of confirmed Haki users only. Unknowns are not zeroes and do
    # not enter that average/denominator. If none is confirmed, omit Haki and
    # renormalize the other criteria to avoid penalizing lack of data.
    effective_weights = {k: float(configured.get(k, 0.0)) for k in ("power", "haki", "abilities", "versatility")}
    if confirmed_haki:
        effective_weights["haki"] = float(configured.get("haki", .14))
    else:
        effective_weights["haki"] = 0.0
        other_total = sum(effective_weights[k] for k in ("power", "abilities", "versatility"))
        if other_total:
            for k in ("power", "abilities", "versatility"):
                effective_weights[k] /= other_total
    values_for_weights = {
        "power": avg_values["power"],
        "abilities": avg_values["abilities"],
        "versatility": avg_values["versatility"],
    }
    if haki_avg is not None:
        values_for_weights["haki"] = haki_avg
    weighted_contributions = {k: values_for_weights.get(k, 0.0) * effective_weights.get(k, 0.0) for k in effective_weights}
    base_score = sum(weighted_contributions.values())

    avg_intelligence = average("intelligence")
    intelligence_bonus = max(0.0, min(.45, (avg_intelligence - 50.0) / 50.0 * .45))
    # Team chemistry is neutral at 50, gives up to +2 and can penalize bad synergy by up to -2.
    chemistry_bonus = max(-2.0, min(2.0, (chemistry - 50.0) * .04))
    score = max(0.0, min(100.0, base_score + intelligence_bonus + chemistry_bonus))

    conf_nums = {"Hoch": 3, "Mittel": 2, "Niedrig": 1}
    conf = sum(conf_nums.get(p.get("confidence", "Niedrig"), 1) for p in profiles) / len(profiles)
    confidence = "Hoch" if conf >= 2.55 else "Mittel" if conf >= 1.75 else "Niedrig"
    known = [p["bounty"] for p in profiles if isinstance(p.get("bounty"), (int, float))]
    return {
        "profiles": profiles, "score": round(score, 1), "base_score": round(base_score, 2),
        "chemistry": round(chemistry, 1), "weighted_contributions": weighted_contributions,
        "effective_weights": effective_weights,
        "avg_power": round(avg_values["power"], 1), "avg_abilities": round(avg_values["abilities"], 1),
        "avg_versatility": round(avg_values["versatility"], 1), "avg_intelligence": round(avg_intelligence, 1),
        "haki_avg": round(haki_avg, 1) if haki_avg is not None else None,
        "haki_count": len(confirmed_haki), "haki_unknown_count": haki_unknown_count,
        "haki_names": [p["name"] for p in confirmed_haki],
        "intelligence_bonus": round(intelligence_bonus, 2),
        "confidence": confidence,
        "bounty_total": sum(known), "known_bounties": len(known), "spent": sum(float(p.get("price", 0)) for p in profiles),
        "pair_scores": pairs, "chemistry_bonus": round(chemistry_bonus, 2),
    }


def role_for_slot(index: int) -> str:
    return f"SLOT {index + 1}"


# ---- Persistent game state / portable backup -------------------------------
GAME_STATE_KEYS = [
    "game_mode", "mode_selector", "name_input_a", "name_input_b", "players", "remaining", "used",
    "history", "return_history", "returns_used", "phase", "round_no", "current_char", "spin_owner",
    "next_spinner", "auction", "last_winner", "game_seed", "draft_variant", "rank_game_mode", "rank_mode_selector",
    "rank_players", "rank_remaining", "rank_used", "rank_history", "rank_return_history", "rank_returns_used",
    "rank_phase", "rank_round_no", "rank_current_char", "rank_pending_draw_character", "rank_spin_id",
    "rank_spin_owner", "rank_next_spinner", "rank_auction",
    "rank_last_winner", "rank_pending_player", "rank_pending_character_id", "rank_game_seed",
    "classic_match_history", "classic_next_start_player", "classic_start_player", "classic_result_recorded",
    "rank_match_history", "rank_next_start_player", "rank_start_player", "rank_result_recorded",
    "online_room_code", "online_role", "online_revision", "online_last_hash", "online_status",
    "classic_pending_draw_character", "classic_spin_id", "classic_spin_started_at",
    "rank_spin_started_at",
]


ONLINE_ROOM_TABLE = "gld_online_rooms"
PORTRAIT_BUCKET = "gld-character-portraits"
PORTRAIT_TABLE = "gld_character_portraits"
ONLINE_LOCAL_ONLY_KEYS = {"mode_selector", "rank_mode_selector", "name_input_a", "name_input_b", "online_room_code", "online_role", "online_revision", "online_last_hash", "online_status"}


def supabase_config() -> dict[str, str] | None:
    """Read Supabase secrets on the server; never expose the service key to the browser."""
    try:
        section = st.secrets.get("supabase", {})
    except Exception:
        section = {}
    url = str(os.environ.get("SUPABASE_URL") or section.get("url", "")).strip().rstrip("/")
    key = str(os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or section.get("service_role_key", "")).strip()
    return {"url": url, "key": key} if url.startswith("https://") and key else None


def supabase_rest(
    method: str,
    params: dict[str, Any] | None = None,
    payload: Any = None,
    *,
    table: str = ONLINE_ROOM_TABLE,
    prefer: str = "return=representation",
) -> Any:
    """Small server-side PostgREST helper. Secrets never leave the Streamlit server."""
    config = supabase_config()
    if not config:
        raise RuntimeError("Supabase ist nicht konfiguriert. Lege die serverseitigen Supabase-Secrets an.")
    headers = {
        "apikey": config["key"], "Authorization": f"Bearer {config['key']}",
        "Content-Type": "application/json", "Accept": "application/json", "Prefer": prefer,
    }
    response = http_session().request(
        method.upper(), f"{config['url']}/rest/v1/{table}",
        headers=headers, params=params or {}, json=payload, timeout=(3.5, 8),
    )
    response.raise_for_status()
    if not response.content:
        return []
    try:
        return response.json()
    except ValueError:
        return []


def online_shared_state() -> dict[str, Any]:
    return {k: st.session_state.get(k) for k in GAME_STATE_KEYS if k in st.session_state and k not in ONLINE_LOCAL_ONLY_KEYS}


def online_state_hash(state: dict[str, Any] | None = None) -> str:
    payload = state if state is not None else online_shared_state()
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def apply_online_state(state: dict[str, Any]) -> None:
    """Apply shared game keys only; widget keys and local connection identity remain local."""
    if not isinstance(state, dict):
        return
    for key, value in state.items():
        if key in GAME_STATE_KEYS and key not in ONLINE_LOCAL_ONLY_KEYS:
            st.session_state[key] = value


def online_fetch_room(code: str) -> dict[str, Any] | None:
    rows = supabase_rest("GET", {"room_code": f"eq.{code.upper()}", "select": "*", "limit": "1"})
    if not isinstance(rows, list) or not rows:
        return None
    row = rows[0]
    expires_at = row.get("expires_at")
    if expires_at:
        try:
            expiry = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
            if expiry <= datetime.now(timezone.utc):
                return None
        except ValueError:
            pass
    return row


def online_fetch_room_meta(code: str) -> dict[str, Any] | None:
    """Fetch only small lobby metadata on each poll; download the large game payload only on change."""
    fields = "room_code,revision,status,host_name,guest_name,variant,updated_at,expires_at"
    rows = supabase_rest("GET", {"room_code": f"eq.{code.upper()}", "select": fields, "limit": "1"})
    if not isinstance(rows, list) or not rows:
        return None
    row = rows[0]
    expires_at = row.get("expires_at")
    if expires_at:
        try:
            expiry = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
            if expiry <= datetime.now(timezone.utc):
                return None
        except ValueError:
            pass
    return row


def online_force_pull() -> tuple[bool, str]:
    """Explicitly discard unsynced local room changes and load the latest remote revision."""
    code = st.session_state.get("online_room_code")
    if not code:
        return False, "Es ist keine Online-Lobby verbunden."
    try:
        row = online_fetch_room(code)
        if not row:
            return False, "Raum fehlt oder ist abgelaufen. Der lokale Spielstand bleibt bestehen."
        envelope = row.get("payload") or {}
        state = envelope.get("state", {}) if isinstance(envelope, dict) else {}
        if not isinstance(state, dict):
            return False, "Der gespeicherte Online-Spielstand ist ungültig."
        apply_online_state(state)
        st.session_state.online_revision = int(row.get("revision", 0))
        st.session_state.online_last_hash = online_state_hash(state)
        st.session_state.online_status = "Neueste Online-Version geladen"
        return True, "Neueste Online-Version übernommen. Nicht synchronisierte lokale Änderungen wurden verworfen."
    except Exception as exc:
        return False, f"Online-Spielstand konnte nicht geladen werden ({type(exc).__name__})."


def online_sync_local_state() -> None:
    code = st.session_state.get("online_room_code")
    role = st.session_state.get("online_role")
    if not code or role not in {"A", "B"}:
        return
    state = online_shared_state()
    digest = online_state_hash(state)
    if digest == st.session_state.get("online_last_hash"):
        return
    revision = int(st.session_state.get("online_revision", 0))
    try:
        rows = supabase_rest("PATCH", {"room_code": f"eq.{code}", "revision": f"eq.{revision}", "select": "room_code,revision"}, {
            "payload": {"state": state}, "revision": revision + 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        if isinstance(rows, list) and rows:
            st.session_state.online_revision = int(rows[0].get("revision", revision + 1))
            st.session_state.online_last_hash = digest
            st.session_state.online_status = "Synchronisiert"
        else:
            st.session_state.online_status = "Synchronisationskonflikt – neueste Raumversion wird abgefragt"
    except Exception as exc:
        st.session_state.online_status = f"Offline gespeichert · Online-Sync fehlgeschlagen ({type(exc).__name__})"


def online_create_room(variant: str) -> tuple[bool, str]:
    if not supabase_config():
        return False, "Online-Modus nicht eingerichtet. Bitte Supabase-Projekt und secrets.toml konfigurieren."
    st.session_state.game_mode = "online"
    st.session_state.rank_game_mode = "online"
    st.session_state.draft_variant = variant
    reset_game(); rank_reset_game()
    code = secrets.token_hex(4).upper()
    state = online_shared_state()
    row = {
        "room_code": code, "revision": 0, "variant": variant,
        "host_name": st.session_state.players["A"]["name"], "guest_name": None,
        "status": "waiting", "payload": {"state": state},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        result = supabase_rest("POST", payload=row)
        if not isinstance(result, list) or not result:
            return False, "Raum konnte nicht angelegt werden. Supabase-Antwort war leer."
        st.session_state.online_room_code = code
        st.session_state.online_role = "A"
        st.session_state.online_revision = 0
        st.session_state.online_last_hash = online_state_hash(state)
        st.session_state.online_status = "Wartet auf Mitspieler"
        persist_game_state()
        return True, f"Raum {code} erstellt. Teile den Code mit deinem Mitspieler."
    except Exception as exc:
        return False, f"Raum konnte nicht erstellt werden: {type(exc).__name__}: {exc}"


def online_join_room(code: str, guest_name: str) -> tuple[bool, str]:
    clean = re.sub(r"[^A-Z0-9]", "", (code or "").upper())[:8]
    if len(clean) != 8:
        return False, "Bitte einen gültigen 8-stelligen Raumcode eingeben."
    if not supabase_config():
        return False, "Online-Modus nicht eingerichtet. Bitte Supabase-Projekt und secrets.toml konfigurieren."
    try:
        row = online_fetch_room(clean)
        if not row:
            return False, "Raum nicht gefunden. Prüfe den Code."
        if row.get("status") != "waiting" or row.get("guest_name"):
            return False, "Dieser Raum ist bereits belegt oder nicht mehr offen."
        envelope = row.get("payload") or {}
        state = envelope.get("state", {}) if isinstance(envelope, dict) else {}
        if not isinstance(state, dict) or not isinstance(state.get("players"), dict):
            return False, "Der gespeicherte Raumzustand ist ungültig."
        variant = row.get("variant", "classic")
        state["game_mode"] = "online"; state["rank_game_mode"] = "online"; state["draft_variant"] = variant
        state["players"]["B"]["name"] = guest_name.strip() or "Spieler B"
        if isinstance(state.get("rank_players"), dict) and "B" in state["rank_players"]:
            state["rank_players"]["B"]["name"] = guest_name.strip() or "Spieler B"
        revision = int(row.get("revision", 0))
        result = supabase_rest("PATCH", {"room_code": f"eq.{clean}", "revision": f"eq.{revision}", "status": "eq.waiting", "select": "room_code,revision"}, {
            "guest_name": guest_name.strip() or "Spieler B", "status": "active",
            "payload": {"state": state}, "revision": revision + 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        if not isinstance(result, list) or not result:
            return False, "Der Raum wurde gerade von jemand anderem belegt. Bitte neuen Raumcode verwenden."
        apply_online_state(state)
        st.session_state.online_room_code = clean
        st.session_state.online_role = "B"
        st.session_state.online_revision = revision + 1
        st.session_state.online_last_hash = online_state_hash(state)
        st.session_state.online_status = "Verbunden als Spieler B"
        persist_game_state()
        return True, f"Raum {clean} beigetreten. Du spielst als {guest_name.strip() or 'Spieler B'}."
    except Exception as exc:
        return False, f"Beitritt fehlgeschlagen: {type(exc).__name__}: {exc}"


def online_poll_impl() -> None:
    code = st.session_state.get("online_room_code")
    role = st.session_state.get("online_role")
    if not code or role not in {"A", "B"}:
        st.caption("Noch keiner Online-Lobby beigetreten.")
        return
    try:
        # Most polls transfer only a few metadata fields, not the full character pool.
        meta = online_fetch_room_meta(code)
        if not meta:
            st.error("Online-Raum nicht gefunden oder abgelaufen. Lokaler Spielstand bleibt erhalten.")
            return
        revision = int(meta.get("revision", 0))
        current_revision = int(st.session_state.get("online_revision", 0))
        if revision > current_revision:
            # Fetch the large payload only when the revision actually changed.
            row = online_fetch_room(code)
            if row:
                local_hash = online_state_hash()
                last_hash = st.session_state.get("online_last_hash")
                envelope = row.get("payload") or {}
                remote_state = envelope.get("state", {}) if isinstance(envelope, dict) else {}
                # A spin is a transient shared event, not a local edit. The non-spinning
                # player must adopt it immediately or their browser never renders the wheel.
                remote_spin_owner = None
                remote_is_spin = False
                if isinstance(remote_state, dict):
                    active_variant = remote_state.get("draft_variant", "classic")
                    if active_variant == "ranking":
                        remote_is_spin = remote_state.get("rank_phase") == "spinning"
                        remote_spin_owner = remote_state.get("rank_spin_owner") if remote_is_spin else None
                    else:
                        remote_is_spin = remote_state.get("phase") == "spinning"
                        remote_spin_owner = remote_state.get("spin_owner") if remote_is_spin else None
                    remote_is_spin = remote_is_spin and remote_spin_owner in {"A", "B"} and remote_spin_owner != role
                if local_hash != last_hash and not remote_is_spin:
                    st.warning("Es gibt lokale Änderungen und eine neuere Raumversion. Bitte synchronisieren oder die neueste Version laden.")
                else:
                    apply_online_state(remote_state)
                    st.session_state.online_revision = int(row.get("revision", revision))
                    st.session_state.online_last_hash = online_state_hash(remote_state)
                    st.session_state.online_status = "Gemeinsame Rad-Animation empfangen" if remote_is_spin else "Neue Aktion des Mitspielers übernommen"
                    st.rerun()
        guest = meta.get("guest_name") or "wartet …"
        status = meta.get("status", "waiting")
        st.caption(f"Raum **{code}** · Spieler {role} · Gegenüber: **{guest if role == 'A' else meta.get('host_name','Host')}** · Status: **{status}** · Revision {revision}")
        if st.session_state.get("online_status"):
            st.caption(st.session_state.online_status)
    except Exception as exc:
        st.caption(f"Online-Verbindung derzeit nicht erreichbar ({type(exc).__name__}). Der lokale Spielstand bleibt erhalten.")


if hasattr(st, "fragment"):
    render_online_poll_fragment = st.fragment(run_every=1.0)(online_poll_impl)
else:
    render_online_poll_fragment = online_poll_impl


def online_can_control(player_key: str, variant: str | None = None) -> bool:
    mode_key = "rank_game_mode" if variant == "ranking" else "game_mode"
    if st.session_state.get(mode_key, "friend") != "online":
        return True
    return bool(st.session_state.get("online_room_code") and st.session_state.get("online_role") == player_key)


def current_game_state() -> dict[str, Any]:
    state = {key: st.session_state.get(key) for key in GAME_STATE_KEYS if key in st.session_state}
    return {"app": "Grand Line Draft 5.0", "schema_version": 3,
            "saved_at": datetime.now().astimezone().isoformat(timespec="seconds"), "state": state}


def persist_game_state() -> bool:
    """Persist only changed local state; still perform the lightweight online diff check."""
    if "players" not in st.session_state:
        return False
    try:
        state = current_game_state()
        state_digest = online_state_hash(state.get("state", {}))
        if state_digest != st.session_state.get("_last_local_autosave_hash"):
            SAVE_DIR.mkdir(parents=True, exist_ok=True)
            payload = json.dumps(state, ensure_ascii=False, indent=2)
            fd, tmp_name = tempfile.mkstemp(prefix="autosave_", suffix=".tmp", dir=str(SAVE_DIR))
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(payload)
                Path(tmp_name).replace(AUTOSAVE_FILE)
            finally:
                Path(tmp_name).unlink(missing_ok=True)
            st.session_state["_last_local_autosave_hash"] = state_digest
        online_sync_local_state()
        return True
    except (OSError, TypeError, ValueError):
        return False


def restore_persistent_game_state() -> bool:
    """Restore only recognized game keys from a local, app-generated save."""
    if "players" in st.session_state or not AUTOSAVE_FILE.exists():
        return False
    try:
        payload = json.loads(AUTOSAVE_FILE.read_text(encoding="utf-8"))
        state = payload.get("state", {}) if isinstance(payload, dict) else {}
        if not isinstance(state, dict) or not isinstance(state.get("players"), dict):
            return False
        for key in GAME_STATE_KEYS:
            if key in state:
                st.session_state[key] = state[key]
        return True
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return False


def migrate_saved_character_pool() -> None:
    """Keep active saves intact while appending newly added character IDs to each unclaimed pool."""
    roster = get_characters()
    roster_by_id = {int(c["id"]): c for c in roster}
    for variant in ("classic", "ranking"):
        remaining_key = "remaining" if variant == "classic" else "rank_remaining"
        used_key = "used" if variant == "classic" else "rank_used"
        players_key = "players" if variant == "classic" else "rank_players"
        current_key = "current_char" if variant == "classic" else "rank_current_char"
        if remaining_key not in st.session_state:
            continue
        seen = {int(c["id"]) for c in st.session_state.get(remaining_key, []) if isinstance(c, dict) and c.get("id") is not None}
        seen.update(int(c["id"]) for c in st.session_state.get(used_key, []) if isinstance(c, dict) and c.get("id") is not None)
        current = st.session_state.get(current_key)
        if isinstance(current, dict) and current.get("id") is not None:
            seen.add(int(current["id"]))
        players = st.session_state.get(players_key, {})
        for player in players.values() if isinstance(players, dict) else []:
            for c in player.get("team", []):
                if isinstance(c, dict) and c.get("id") is not None:
                    seen.add(int(c["id"]))
        auction_key = "auction" if variant == "classic" else "rank_auction"
        auction = st.session_state.get(auction_key)
        if isinstance(auction, dict):
            c = auction.get("character")
            if isinstance(c, dict) and c.get("id") is not None:
                seen.add(int(c["id"]))
        if variant == "ranking":
            pending = st.session_state.get("rank_pending_draw_character")
            if isinstance(pending, dict) and pending.get("id") is not None:
                seen.add(int(pending["id"]))
        for cid, character in roster_by_id.items():
            if cid not in seen:
                st.session_state[remaining_key].append(character.copy())


def import_game_state(payload: dict[str, Any]) -> tuple[bool, str]:
    state = payload.get("state") if isinstance(payload, dict) else None
    if not isinstance(state, dict) or not isinstance(state.get("players"), dict):
        return False, "Die Datei ist kein unterstützter Grand Line Draft-Spielstand. Bitte einen Grand Line Draft 3.5-, 3.6- oder 5.0-Export verwenden."
    try:
        players = state["players"]
        if set(players.keys()) != {"A", "B"}:
            return False, "Spielstand abgelehnt: Spielerstruktur ist ungültig."
        for key in ("A", "B"):
            player = players[key]
            if not isinstance(player, dict) or not isinstance(player.get("team"), list):
                return False, "Spielstand abgelehnt: Teamdaten sind ungültig."
            if len(player["team"]) > TEAM_SIZE:
                return False, "Spielstand abgelehnt: Teamgröße überschreitet die Spielregeln."
        for key in GAME_STATE_KEYS:
            if key in state:
                st.session_state[key] = state[key]
        # Reset transient widgets to avoid stale slider/bid keys overriding a loaded game.
        for key in list(st.session_state.keys()):
            if isinstance(key, str) and (key.startswith("bid_") or key.startswith("raise_") or key.startswith("pass_") or key.startswith("opening_bid_") or key == "spin_wheel"):
                st.session_state.pop(key, None)
        persist_game_state()
        return True, "Spielstand geladen und lokal gespeichert."
    except (TypeError, ValueError, OSError) as exc:
        return False, f"Spielstand konnte nicht geladen werden ({type(exc).__name__})."


def make_portable_backup() -> bytes:
    """Package app, ratings, autosave and cached/manual portraits into one portable ZIP."""
    persist_game_state()
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        wanted = ["app.py", "characters.json", "character_ratings.json", "matchup_results.json.gz", "portrait_links.json", "requirements.txt", "README.md", "CHANGELOG_5_0.md", "ONLINE_SETUP.md", "online_schema.sql", "cloud_portraits_schema.sql", "POWER_MATRIX_V5_REVIEW.md", "Start_GrandLineDraft.bat", "CHANGELOG_5_0_2.md"]
        for filename in wanted:
            item = BASE_DIR / filename
            if item.exists():
                archive.write(item, f"GrandLineDraft/{filename}")
        component_file = BASE_DIR / "fivefold_component" / "index.html"
        if component_file.exists():
            archive.write(component_file, "GrandLineDraft/fivefold_component/index.html")
        config = BASE_DIR / ".streamlit" / "config.toml"
        if config.exists():
            archive.write(config, "GrandLineDraft/.streamlit/config.toml")
        if AUTOSAVE_FILE.exists():
            archive.write(AUTOSAVE_FILE, "GrandLineDraft/saves/autosave.json")
        if PORTRAIT_DIR.exists():
            for item in PORTRAIT_DIR.rglob("*"):
                if item.is_file() and item.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                    archive.write(item, f"GrandLineDraft/portraits/{item.relative_to(PORTRAIT_DIR).as_posix()}")
    return out.getvalue()


# ---- Character portrait handling -------------------------------------------
def portrait_path(character: dict[str, Any]) -> Path:
    # The suffix invalidates caches created before exact page mappings were fixed.
    identity = f"{character.get('name','')}|{character.get('wiki_slug','')}".encode("utf-8")
    suffix = hashlib.sha256(identity).hexdigest()[:8]
    return PORTRAIT_DIR / f"character_{int(character['id']):03d}_{suffix}.jpg"


def manual_portrait_path(character: dict[str, Any]) -> Path:
    """Persistent user-supplied portrait; takes precedence over online/cache images."""
    return PORTRAIT_DIR / f"manual_character_{int(character['id']):03d}.jpg"


def linked_portrait_path(character: dict[str, Any]) -> Path:
    """A verified image downloaded from a user-provided direct image URL."""
    return PORTRAIT_DIR / f"linked_character_{int(character['id']):03d}.jpg"


def load_portrait_link_overrides() -> dict[str, Any]:
    try:
        payload = json.loads(PORTRAIT_LINKS_FILE.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def save_portrait_link_overrides(payload: dict[str, Any]) -> None:
    PORTRAIT_LINKS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def install_portrait_from_url(character: dict[str, Any], url: str) -> tuple[bool, str]:
    """Download, validate, optimize, and persist a direct image URL on explicit user action."""
    raw_url = (url or "").strip()
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        return False, "Bitte eine gültige direkte http(s)-Bild-URL ohne Zugangsdaten eintragen."
    try:
        with requests.get(
            raw_url,
            timeout=(3.5, 7),
            allow_redirects=True,
            stream=True,
            headers={"User-Agent": USER_AGENT, "Accept": "image/avif,image/webp,image/png,image/jpeg,image/*;q=0.8"},
        ) as response:
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > 12 * 1024 * 1024:
                return False, "Das Bild ist größer als 12 MB. Bitte eine kleinere Bilddatei verwenden."
            chunks = []
            total = 0
            for chunk in response.iter_content(128 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > 12 * 1024 * 1024:
                    return False, "Das Bild ist größer als 12 MB. Bitte eine kleinere Bilddatei verwenden."
                chunks.append(chunk)
            content = b"".join(chunks)
        normalized_image = image_as_jpeg(content)
        if not normalized_image:
            detail = "Der Link lieferte keine lesbare Bilddatei" if "image" not in content_type else "Das Bild ist beschädigt oder zu klein"
            return False, f"{detail}. Bitte einen direkten Link zu einer JPG-, PNG- oder WEBP-Datei verwenden."
        PORTRAIT_DIR.mkdir(parents=True, exist_ok=True)
        destination = linked_portrait_path(character)
        temporary = destination.with_suffix(".tmp")
        temporary.write_bytes(normalized_image)
        temporary.replace(destination)
        # The latest chosen source wins. Clear an old manual image to avoid ambiguity.
        manual_portrait_path(character).unlink(missing_ok=True)
        overrides = st.session_state.get("portrait_link_overrides")
        if not isinstance(overrides, dict):
            overrides = load_portrait_link_overrides()
        overrides[str(character["id"])] = {
            "name": character["name"],
            "url": raw_url,
            "saved_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        save_portrait_link_overrides(overrides)
        st.session_state["portrait_link_overrides"] = overrides
        st.session_state.setdefault("portrait_status", {})[character["name"]] = "Eigenes Bild · aus Link gespeichert"
        _cached_portrait_bytes.clear()
        cloud_count, cloud_errors = upload_cloud_portraits([{
            "id": int(character["id"]), "name": character["name"],
            "bytes": normalized_image, "source": "direct_link",
        }])
        if cloud_count:
            return True, "Bild erfolgreich gespeichert und mit allen Geräten über Supabase Storage synchronisiert."
        if cloud_errors:
            return True, "Bild lokal gespeichert. Cloud-Synchronisierung noch nicht möglich: " + cloud_errors[0]
        return True, "Bild lokal gespeichert. Für geräteübergreifende Synchronisierung zuerst cloud_portraits_schema.sql ausführen."
    except (requests.RequestException, OSError, ValueError) as exc:
        return False, f"Bild konnte nicht geladen werden ({type(exc).__name__}). Prüfe, ob die URL öffentlich erreichbar ist."


def image_as_jpeg(content: bytes) -> bytes | None:
    try:
        image = Image.open(io.BytesIO(content))
        image.verify()
        image = Image.open(io.BytesIO(content)).convert("RGB")
        if image.width < 80 or image.height < 80:
            return None
        image.thumbnail((620, 800))
        out = io.BytesIO()
        image.save(out, format="JPEG", quality=88, optimize=True)
        return out.getvalue()
    except Exception:
        return None


def _wiki_page_title_matches(returned_title: str, requested_title: str) -> bool:
    returned_base = returned_title.split("(", 1)[0].strip()
    requested_base = requested_title.replace("_", " ").split("(", 1)[0].strip()
    return normalize(returned_title) == normalize(requested_title.replace("_", " ")) or normalize(returned_base) == normalize(requested_base)


# ---- Supabase Storage: shared character portrait library --------------------
def _supabase_storage_headers(config: dict[str, str], content_type: str | None = None) -> dict[str, str]:
    headers = {"apikey": config["key"], "Authorization": f"Bearer {config['key']}"}
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def cloud_portrait_object_path(character_id: int) -> str:
    return f"characters/{int(character_id):03d}.jpg"


def _upload_cloud_portrait_object(config: dict[str, str], character_id: int, image_bytes: bytes) -> tuple[int, str, int, str | None]:
    object_path = cloud_portrait_object_path(character_id)
    url = f"{config['url']}/storage/v1/object/{PORTRAIT_BUCKET}/{quote(object_path, safe='/')}"
    headers = _supabase_storage_headers(config, "image/jpeg")
    headers["x-upsert"] = "true"
    response = http_session().post(url, headers=headers, data=image_bytes, timeout=(5, 30))
    response.raise_for_status()
    return int(character_id), object_path, len(image_bytes), None


def upload_cloud_portraits(items: list[dict[str, Any]]) -> tuple[int, list[str]]:
    """Upload optimized JPEGs to the private bucket, then upsert their metadata in one DB request."""
    config = supabase_config()
    if not config:
        return 0, ["Supabase ist nicht konfiguriert."]
    if not items:
        return 0, []
    errors: list[str] = []
    successful: list[tuple[dict[str, Any], str, int]] = []
    def worker(item: dict[str, Any]):
        return item, _upload_cloud_portrait_object(config, int(item["id"]), item["bytes"])
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(worker, item) for item in items]
        for future in as_completed(futures):
            try:
                item, uploaded = future.result()
                _cid, object_path, size, _ = uploaded
                successful.append((item, object_path, size))
            except Exception as exc:
                errors.append(f"{type(exc).__name__}: Bild konnte nicht hochgeladen werden.")
    if successful:
        now = datetime.now(timezone.utc).isoformat()
        metadata = [{
            "character_id": int(item["id"]), "character_name": str(item["name"]),
            "storage_path": object_path, "content_type": "image/jpeg", "file_size": size,
            "source": str(item.get("source", "upload")), "updated_at": now,
        } for item, object_path, size in successful]
        try:
            supabase_rest(
                "POST", {"on_conflict": "character_id"}, metadata,
                table=PORTRAIT_TABLE, prefer="resolution=merge-duplicates,return=minimal",
            )
        except Exception as exc:
            errors.append(f"Bilddateien wurden übertragen, aber die Bildtabelle konnte nicht aktualisiert werden ({type(exc).__name__}). Bitte cloud_portraits_schema.sql prüfen.")
            return 0, errors
        _cloud_portrait_index.clear()
        _cloud_portrait_bytes.clear()
        _cloud_portrait_batch.clear()
    return len(successful), errors


@st.cache_data(show_spinner=False, ttl=45)
def _cloud_portrait_index(url: str, key: str) -> dict[str, dict[str, Any]]:
    """Cache the small metadata index; a missing table is cached as empty instead of hammering the API."""
    headers = _supabase_storage_headers({"url": url, "key": key}, "application/json")
    try:
        response = http_session().get(
            f"{url}/rest/v1/{PORTRAIT_TABLE}",
            headers=headers, params={"select": "character_id,character_name,storage_path,updated_at,source", "limit": "500"},
            timeout=(3.5, 8),
        )
        response.raise_for_status()
        payload = response.json()
        return {str(row["character_id"]): row for row in payload if isinstance(row, dict) and row.get("character_id") is not None}
    except (requests.RequestException, ValueError, TypeError):
        return {}


@st.cache_data(show_spinner=False, ttl=3600, max_entries=256)
def _cloud_portrait_bytes(url: str, key: str, storage_path: str, updated_at: str) -> bytes | None:
    headers = _supabase_storage_headers({"url": url, "key": key})
    response = http_session().get(
        f"{url}/storage/v1/object/{PORTRAIT_BUCKET}/{quote(storage_path, safe='/')}",
        headers=headers, timeout=(4, 12),
    )
    response.raise_for_status()
    content = image_as_jpeg(response.content)
    return content


@st.cache_data(show_spinner=False, ttl=3600, max_entries=24)
def _cloud_portrait_batch(url: str, key: str, items: tuple[tuple[str, str, str], ...]) -> dict[str, bytes]:
    """Fetch only the currently visible portraits in parallel; bytes are cached as one batch."""
    if not items:
        return {}
    headers = _supabase_storage_headers({"url": url, "key": key})
    def fetch(item: tuple[str, str, str]):
        character_id, storage_path, _updated_at = item
        try:
            response = http_session().get(
                f"{url}/storage/v1/object/{PORTRAIT_BUCKET}/{quote(storage_path, safe='/')}",
                headers=headers, timeout=(3.5, 10),
            )
            response.raise_for_status()
            image_bytes = image_as_jpeg(response.content)
            return character_id, image_bytes
        except (requests.RequestException, ValueError, OSError):
            return character_id, None
    result: dict[str, bytes] = {}
    with ThreadPoolExecutor(max_workers=min(8, len(items))) as executor:
        futures = [executor.submit(fetch, item) for item in items]
        for future in as_completed(futures):
            character_id, image_bytes = future.result()
            if image_bytes:
                result[character_id] = image_bytes
    return result


def cloud_portraits_for_characters(characters: list[dict[str, Any]]) -> dict[str, bytes]:
    """Prefetch cloud portraits for a visible set concurrently; skips newer local overrides."""
    config = supabase_config()
    if not config or not characters:
        return {}
    try:
        index = _cloud_portrait_index(config["url"], config["key"])
        items: list[tuple[str, str, str]] = []
        for character in characters:
            cid = str(int(character["id"]))
            meta = index.get(cid)
            if not meta:
                continue
            local_custom = next((p for p in (linked_portrait_path(character), manual_portrait_path(character)) if p.is_file()), None)
            if local_custom:
                try:
                    local_mtime = local_custom.stat().st_mtime
                    cloud_time = datetime.fromisoformat(str(meta.get("updated_at", "")).replace("Z", "+00:00")).timestamp() if meta.get("updated_at") else 0
                    if local_mtime > cloud_time + 1:
                        continue
                except (OSError, ValueError, TypeError):
                    pass
            items.append((cid, str(meta.get("storage_path", "")), str(meta.get("updated_at", ""))))
        return _cloud_portrait_batch(config["url"], config["key"], tuple(items)) if items else {}
    except Exception:
        return {}


@st.cache_data(show_spinner=False, max_entries=512)
def _portrait_thumbnail(image_bytes: bytes, max_width: int = 300, max_height: int = 380) -> bytes:
    """Create compact card thumbnails, retaining the full-resolution portrait for detail views."""
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=76, optimize=True, progressive=True)
        return output.getvalue()
    except Exception:
        return image_bytes


def character_portrait_thumbnail(character: dict[str, Any], cloud_batch: dict[str, bytes] | None = None) -> bytes:
    return _portrait_thumbnail(character_portrait(character, cloud_batch), 300, 380)


def cloud_portrait_for_character(character: dict[str, Any]) -> bytes | None:
    config = supabase_config()
    if not config:
        return None
    try:
        index = _cloud_portrait_index(config["url"], config["key"])
        meta = index.get(str(int(character["id"])))
        if not meta:
            return None
        return _cloud_portrait_bytes(config["url"], config["key"], str(meta["storage_path"]), str(meta.get("updated_at", "")))
    except Exception:
        # Cloud images are an enhancement; a network/schema problem must not break game rendering.
        return None


@st.cache_data(show_spinner=False, ttl=60)
def cloud_portrait_schema_ready() -> tuple[bool, str]:
    try:
        rows = supabase_rest("GET", {"select": "character_id", "limit": "1"}, table=PORTRAIT_TABLE)
        return True, "Cloud-Bildertabelle erreichbar."
    except Exception as exc:
        return False, f"Cloud-Bildertabelle noch nicht bereit ({type(exc).__name__}). Bitte cloud_portraits_schema.sql ausführen."


def delete_cloud_portrait(character_id: int) -> tuple[bool, str]:
    config = supabase_config()
    if not config:
        return False, "Supabase ist nicht konfiguriert."
    path = cloud_portrait_object_path(character_id)
    headers = _supabase_storage_headers(config, "application/json")
    try:
        response = requests.delete(
            f"{config['url']}/storage/v1/object/{PORTRAIT_BUCKET}",
            headers=headers, json={"prefixes": [path]}, timeout=(4, 12),
        )
        if response.status_code not in (200, 404):
            response.raise_for_status()
        supabase_rest("DELETE", {"character_id": f"eq.{int(character_id)}"}, table=PORTRAIT_TABLE, prefer="return=minimal")
        _cloud_portrait_index.clear(); _cloud_portrait_bytes.clear(); _cloud_portrait_batch.clear()
        return True, "Cloud-Porträt entfernt."
    except Exception as exc:
        return False, f"Cloud-Bild konnte nicht entfernt werden ({type(exc).__name__})."


def portrait_archive_items(zip_bytes: bytes) -> tuple[list[dict[str, Any]], list[str]]:
    """Read a user ZIP without extracting paths; accept this app's portrait filename conventions."""
    roster = {int(c["id"]): c for c in get_characters()}
    chosen: dict[int, tuple[int, dict[str, Any]]] = {}
    warnings: list[str] = []
    total_size = 0
    pattern = re.compile(r"^(manual_character|linked_character|character)_(\d{3})(?:_[a-f0-9]{8})?\.(?:jpg|jpeg|png|webp)$", re.I)
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
            files = [info for info in archive.infolist() if not info.is_dir()]
            if len(files) > 300:
                return [], ["Das ZIP enthält mehr als 300 Dateien; bitte nur den portraits-Ordner packen."]
            for info in files:
                name = info.filename.replace("\\", "/")
                basename = name.rsplit("/", 1)[-1]
                # Only accept files under a portraits path or files at the ZIP root.
                if "/" in name and "portraits/" not in name.lower():
                    continue
                match = pattern.match(basename)
                if not match:
                    continue
                char_id = int(match.group(2))
                if char_id not in roster:
                    continue
                if info.file_size > 12 * 1024 * 1024:
                    warnings.append(f"{basename}: größer als 12 MB, übersprungen.")
                    continue
                total_size += info.file_size
                if total_size > 150 * 1024 * 1024:
                    return [], ["Das ZIP ist größer als 150 MB entpackte Bilddaten. Bitte in kleinere Archive aufteilen."]
                raw = archive.read(info)
                normalized = image_as_jpeg(raw)
                if not normalized:
                    warnings.append(f"{basename}: kein gültiges Bild, übersprungen.")
                    continue
                prefix = match.group(1).lower()
                priority = 3 if prefix == "manual_character" else (2 if prefix == "linked_character" else 1)
                item = {"id": char_id, "name": roster[char_id]["name"], "bytes": normalized, "source": "zip_import"}
                old = chosen.get(char_id)
                if old is None or priority > old[0]:
                    chosen[char_id] = (priority, item)
    except (zipfile.BadZipFile, OSError, ValueError) as exc:
        return [], [f"Das Bilderarchiv konnte nicht gelesen werden ({type(exc).__name__})."]
    return [row[1] for row in chosen.values()], warnings


def local_portrait_items() -> list[dict[str, Any]]:
    roster = {int(c["id"]): c for c in get_characters()}
    patterns = [
        (re.compile(r"^manual_character_(\d{3})\.jpg$", re.I), "manual_upload"),
        (re.compile(r"^linked_character_(\d{3})\.jpg$", re.I), "direct_link"),
        (re.compile(r"^character_(\d{3})_[a-f0-9]{8}\.jpg$", re.I), "local_portrait"),
    ]
    picked: dict[int, tuple[int, dict[str, Any]]] = {}
    for path in PORTRAIT_DIR.glob("*.jpg"):
        for pattern, source in patterns:
            match = pattern.match(path.name)
            if not match:
                continue
            char_id = int(match.group(1))
            if char_id not in roster:
                continue
            try:
                raw = path.read_bytes()
            except OSError:
                continue
            normalized = image_as_jpeg(raw)
            if not normalized:
                continue
            priority = 3 if source == "manual_upload" else (2 if source == "direct_link" else 1)
            old = picked.get(char_id)
            if old is None or priority >= old[0]:
                picked[char_id] = (priority, {"id": char_id, "name": roster[char_id]["name"], "bytes": normalized, "source": source})
            break
    return [row[1] for row in picked.values()]


@st.cache_data(show_spinner=False, ttl=86400)
def fetch_portrait_remote(name: str, wiki_slug: str, direct_url: str = "") -> tuple[bytes | None, str]:
    """Fetch only exact-page portraits; substring matching is intentionally forbidden."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json,image/avif,image/webp,image/*,*/*;q=0.8"})

    def download(url: str, source: str) -> tuple[bytes | None, str]:
        try:
            response = session.get(url, timeout=6, allow_redirects=True)
            if response.ok and "image" in response.headers.get("content-type", "").lower():
                img = image_as_jpeg(response.content)
                if img:
                    return img, source
        except (requests.RequestException, ValueError):
            pass
        return None, ""

    if direct_url:
        image, source = download(direct_url, "offizielle One-Piece-Seite")
        if image:
            return image, source

    # Preferred source: exact MediaWiki page thumbnail, preventing King/Kingbaum crossover.
    requested_title = wiki_slug.replace("_", " ")
    try:
        response = session.get(FANDOM_API, params={
            "action": "query", "format": "json", "prop": "pageimages", "piprop": "thumbnail",
            "pithumbsize": 620, "titles": requested_title,
        }, timeout=5)
        if response.ok:
            pages = response.json().get("query", {}).get("pages", {})
            for page in pages.values():
                title = str(page.get("title", ""))
                img_url = page.get("thumbnail", {}).get("source")
                if img_url and title and _wiki_page_title_matches(title, requested_title):
                    image, source = download(img_url, f"One Piece Wiki · {title}")
                    if image:
                        return image, source
    except (requests.RequestException, ValueError, TypeError):
        pass

    # Optional API fallback accepts exact normalized names only; never `wanted in result`.
    try:
        response = session.get(API_BASE, params={"q": name, "limit": 20, "page": 1}, timeout=5)
        if response.ok:
            payload = response.json()
            records = payload.get("data", payload.get("results", [])) if isinstance(payload, dict) else payload
            if isinstance(records, list):
                for record in records:
                    if not isinstance(record, dict):
                        continue
                    raw_name = record.get("name", "")
                    if isinstance(raw_name, dict):
                        raw_name = raw_name.get("en") or raw_name.get("romaji") or raw_name.get("jp") or ""
                    if normalize(str(raw_name)) != normalize(name):
                        continue
                    image_url = record.get("image_url") or record.get("image")
                    if isinstance(image_url, str) and image_url.startswith("http"):
                        image, source = download(image_url, "One Piece API · exakter Name")
                        if image:
                            return image, source
    except (requests.RequestException, ValueError, TypeError):
        pass
    return None, "Kein echtes Porträt erreichbar"


def placeholder_portrait(character: dict[str, Any]) -> bytes:
    name = character["name"]
    faction = character.get("faction", "One Piece")
    width, height = 520, 650
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    c1 = (12 + digest[0] % 29, 27 + digest[1] % 34, 40 + digest[2] % 42)
    c2 = (90 + digest[3] % 70, 61 + digest[4] % 65, 27 + digest[5] % 45)
    im = Image.new("RGB", (width, height), c1)
    draw = ImageDraw.Draw(im)
    draw.polygon([(0, 0), (width, 0), (0, height)], fill=c2)
    for r in (90, 140, 190, 245):
        draw.ellipse((width//2-r, 150-r, width//2+r, 150+r), outline=(220, 184, 102), width=2)
    try:
        big = ImageFont.truetype("DejaVuSans-Bold.ttf", 54)
        mid = ImageFont.truetype("DejaVuSans-Bold.ttf", 25)
        small = ImageFont.truetype("DejaVuSans.ttf", 18)
    except Exception:
        big = mid = small = ImageFont.load_default()
    parts = [x for x in re.split(r"\s+", re.sub(r"[()]", " ", name)) if x]
    initials = "".join(p[0] for p in parts[:2]).upper() or "OP"
    bbox = draw.textbbox((0, 0), initials, font=big)
    draw.text(((width-(bbox[2]-bbox[0]))/2, 220), initials, font=big, fill=(245, 215, 144))
    label = name if len(name) <= 24 else name[:22] + "…"
    bbox = draw.textbbox((0, 0), label, font=mid)
    draw.text(((width-(bbox[2]-bbox[0]))/2, 370), label, font=mid, fill=(238, 244, 250))
    faction_label = faction if len(faction) < 28 else faction[:26] + "…"
    bbox = draw.textbbox((0, 0), faction_label, font=small)
    draw.text(((width-(bbox[2]-bbox[0]))/2, 420), faction_label, font=small, fill=(225, 190, 110))
    for label, y in [("GRAND LINE DRAFT", 545), ("ERSATZPORTRÄT · OFFLINE", 590)]:
        bbox = draw.textbbox((0, 0), label, font=small)
        draw.text(((width-(bbox[2]-bbox[0]))/2, y), label, font=small, fill=(151, 170, 187))
    out = io.BytesIO()
    im.save(out, format="JPEG", quality=87)
    return out.getvalue()


@st.cache_data(show_spinner=False, max_entries=512)
def _cached_portrait_bytes(path_text: str, modified_ns: int, name: str, faction: str) -> bytes:
    """Read local images quickly; placeholders are cached too. No network work here."""
    path = Path(path_text)
    try:
        if path.is_file():
            return path.read_bytes()
    except OSError:
        pass
    return placeholder_portrait({"name": name, "faction": faction})


def character_portrait(character: dict[str, Any], cloud_batch: dict[str, bytes] | None = None) -> bytes:
    """Prefer the shared cloud override, then a newer local custom file, then the local base portrait."""
    overrides = st.session_state.get("portrait_link_overrides", {})
    link_meta = overrides.get(str(character["id"]), {}) if isinstance(overrides, dict) else {}
    local_custom_options = [
        (linked_portrait_path(character), "Eigenes Bild · aus Link gespeichert"),
        (manual_portrait_path(character), "Eigenes Bild · manuell hinzugefügt"),
    ]
    local_custom = next(((path, label) for path, label in local_custom_options if path.is_file()), None)
    cloud_meta = None
    config = supabase_config()
    if config:
        try:
            cloud_meta = _cloud_portrait_index(config["url"], config["key"]).get(str(int(character["id"])))
        except Exception:
            cloud_meta = None
    cloud_preferred = bool(cloud_meta)
    if local_custom and cloud_meta:
        try:
            local_mtime = local_custom[0].stat().st_mtime
            cloud_timestamp = datetime.fromisoformat(str(cloud_meta.get("updated_at", "")).replace("Z", "+00:00")).timestamp() if cloud_meta.get("updated_at") else 0
            if local_mtime > cloud_timestamp + 1:
                cloud_preferred = False
        except (OSError, ValueError, TypeError):
            pass
    status = st.session_state.setdefault("portrait_status", {})
    if cloud_preferred and cloud_meta and config:
        try:
            prefetched = (cloud_batch or {}).get(str(int(character["id"])))
            cloud_image = prefetched or _cloud_portrait_bytes(config["url"], config["key"], str(cloud_meta["storage_path"]), str(cloud_meta.get("updated_at", "")))
            if cloud_image:
                status[character["name"]] = "Cloud-Porträt · Supabase Storage"
                return cloud_image
        except Exception:
            pass
    if local_custom:
        path, source = local_custom
        try:
            modified_ns = path.stat().st_mtime_ns
        except OSError:
            modified_ns = 0
        if link_meta.get("url") and path == linked_portrait_path(character):
            status[character["name"]] = f"Eigenes Bild · Link: {link_meta['url']}"
        else:
            status[character["name"]] = source
        return _cached_portrait_bytes(str(path), modified_ns, character["name"], character.get("faction", "One Piece"))
    if cloud_meta and config:
        try:
            prefetched = (cloud_batch or {}).get(str(int(character["id"])))
            cloud_image = prefetched or _cloud_portrait_bytes(config["url"], config["key"], str(cloud_meta["storage_path"]), str(cloud_meta.get("updated_at", "")))
            if cloud_image:
                status[character["name"]] = "Cloud-Porträt · Supabase Storage"
                return cloud_image
        except Exception:
            pass
    base_path = portrait_path(character)
    try:
        modified_ns = base_path.stat().st_mtime_ns if base_path.is_file() else 0
    except OSError:
        modified_ns = 0
    status.setdefault(character["name"], "Lokal gespeichertes Porträt" if base_path.is_file() else "Ersatzporträt · kein lokales Bild vorhanden")
    return _cached_portrait_bytes(str(base_path), modified_ns, character["name"], character.get("faction", "One Piece"))



def audit_all_portraits(progress_callback=None) -> dict[str, str]:
    """Check all character page mappings, download valid images, and cache them locally."""
    chars = get_characters()
    fetch_portrait_remote.clear()
    results: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_map = {}
        for ch in chars:
            manual_path = manual_portrait_path(ch)
            linked_path = linked_portrait_path(ch)
            path = portrait_path(ch)
            if linked_path.exists():
                results[ch["name"]] = "Eigenes Bild · aus Link gespeichert"
            elif manual_path.exists():
                results[ch["name"]] = "Eigenes Bild · manuell hinzugefügt"
            elif path.exists():
                results[ch["name"]] = "Lokal gespeichert"
            else:
                future_map[executor.submit(fetch_portrait_remote, ch["name"], ch.get("wiki_slug", ch["name"].replace(" ", "_")), ch.get("image_url", ""))] = ch
        if progress_callback:
            progress_callback(len(results) / max(1, len(chars)))
        for future in as_completed(future_map):
            ch = future_map[future]
            try:
                image, source = future.result()
            except Exception:
                image, source = None, "Prüfung fehlgeschlagen"
            if image:
                try:
                    portrait_path(ch).write_bytes(image)
                    results[ch["name"]] = source
                except OSError:
                    results[ch["name"]] = source + " · lokales Speichern fehlgeschlagen"
            else:
                results[ch["name"]] = "Kein echtes Bild gefunden – Ersatzporträt wird verwendet"
            if progress_callback:
                progress_callback(len(results) / max(1, len(chars)))
    st.session_state.portrait_status = results
    return results


# ---- Rules and game state ---------------------------------------------------
def is_ai_mode() -> bool:
    return st.session_state.get("game_mode", "friend") == "single"


def is_ai_player(player_key: str) -> bool:
    return is_ai_mode() and player_key == "B"


def other(player: str) -> str:
    return "B" if player == "A" else "A"


def team_slots(player: str) -> int:
    return TEAM_SIZE - len(st.session_state.players[player]["team"])


def max_bid(player: str) -> int:
    p = st.session_state.players[player]
    if team_slots(player) <= 0:
        return 0
    reserve_after_buying = max(0, team_slots(player) - 1) * MIN_PRICE
    return max(0, int(p["budget"] - reserve_after_buying + 1e-9))


def can_return_card(player_key: str, current_draw: bool = False) -> bool:
    p = st.session_state.players[player_key]
    count = st.session_state.returns_used.get(player_key, 0)
    if count >= MAX_RETURNS:
        return False
    # Returning a won character opens one additional team slot; the fee cannot break minimum reserves.
    target_slots = team_slots(player_key) if current_draw else team_slots(player_key) + 1
    return p["budget"] - RETURN_PENALTY >= target_slots * MIN_PRICE


def commit_return(player_key: str, character: dict[str, Any], reason: str) -> None:
    """Commit a return after the caller has validated the budget and return allowance."""
    player = st.session_state.players[player_key]
    player["budget"] = round(player["budget"] - RETURN_PENALTY, 2)
    st.session_state.returns_used[player_key] += 1
    st.session_state.remaining.append(character.copy())
    st.session_state.remaining.sort(key=lambda x: x["id"])
    st.session_state.used = [x for x in st.session_state.used if x["id"] != character["id"]]
    st.session_state.return_history.append({"player": player["name"], "player_key": player_key, "character": character["name"], "fee": RETURN_PENALTY, "reason": reason, "round": st.session_state.round_no})


def apply_return(player_key: str, character: dict[str, Any], reason: str) -> bool:
    if not can_return_card(player_key, current_draw=(reason == "gezogene Karte")):
        return False
    commit_return(player_key, character, reason)
    return True


def return_owned_character(player_key: str, team_index: int) -> None:
    if not can_return_card(player_key, current_draw=False):
        st.error(f"Rückgabe nicht möglich: maximal {MAX_RETURNS} Rückgaben und {money(RETURN_PENALTY)} Strafe je Rückgabe. Das Mindestbudget muss erhalten bleiben.")
        return
    team = st.session_state.players[player_key]["team"]
    if team_index < 0 or team_index >= len(team):
        return
    character = team.pop(team_index)
    commit_return(player_key, character, "gewonnene Karte")
    if st.session_state.phase == "finished":
        st.session_state.phase = "ready"
    persist_game_state(); st.rerun()


def reset_game() -> None:
    for key in ["players", "remaining", "used", "history", "return_history", "returns_used", "phase", "round_no", "current_char", "spin_owner", "next_spinner", "auction", "last_winner", "game_seed", "classic_pending_draw_character", "classic_spin_id", "classic_spin_started_at"]:
        st.session_state.pop(key, None)
    init_game()


def init_game() -> None:
    if "players" in st.session_state:
        return
    characters = get_characters()
    ids = [c.get("id") for c in characters]
    names = [normalize(str(c.get("name", ""))) for c in characters]
    if len(characters) != 135 or len(ids) != len(set(ids)) or len(names) != len(set(names)):
        st.error("Die Charakterdatenbank muss 135 Figuren mit eindeutigen IDs und Namen enthalten. Bitte characters.json prüfen.")
        st.stop()
    mode = st.session_state.get("game_mode", "friend")
    player_a = st.session_state.get("name_input_a", "Spieler 1").strip() or "Spieler 1"
    player_b = "Grand Line KI" if mode == "single" else ("Wartet auf Mitspieler" if mode == "online" else (st.session_state.get("name_input_b", "Spieler 2").strip() or "Spieler 2"))
    st.session_state.players = {
        "A": {"name": player_a, "budget": float(START_BUDGET), "team": []},
        "B": {"name": player_b, "budget": float(START_BUDGET), "team": []},
    }
    st.session_state.remaining = [c.copy() for c in characters]
    st.session_state.used = []
    st.session_state.history = []
    st.session_state.return_history = []
    st.session_state.returns_used = {"A": 0, "B": 0}
    st.session_state.phase = "ready"
    st.session_state.round_no = 0
    st.session_state.current_char = None
    starter = st.session_state.get("classic_next_start_player", "A")
    starter = starter if starter in {"A", "B"} else "A"
    st.session_state.spin_owner = starter
    st.session_state.next_spinner = starter
    st.session_state.classic_start_player = starter
    st.session_state.classic_result_recorded = None
    st.session_state.auction = None
    st.session_state.last_winner = None
    st.session_state.game_seed = random.randrange(10**8)


def active_spinner() -> str:
    preferred = st.session_state.next_spinner
    if team_slots(preferred) > 0:
        return preferred
    return other(preferred)


def draw_character(placeholder=None) -> None:
    """Choose the result on the server, then animate it client-side on both online devices."""
    remaining = st.session_state.remaining
    if not remaining:
        return
    spinner = active_spinner()
    if not online_can_control(spinner, "classic"):
        st.warning("Du kannst erst ziehen, wenn du in der Online-Partie an der Reihe bist.")
        return
    final = remaining[secrets.randbelow(len(remaining))]
    st.session_state.spin_owner = spinner
    st.session_state.classic_pending_draw_character = final.copy()
    st.session_state.classic_spin_id = f"{st.session_state.game_seed}-{st.session_state.round_no + 1}-{final['id']}-{secrets.token_hex(3)}"
    st.session_state.classic_spin_started_at = time.time() + 2.50
    st.session_state.phase = "spinning"
    persist_game_state()
    st.rerun()


def complete_classic_spin() -> None:
    """Commit a classic draw only on the controlling player's session after both clients had time to animate."""
    if st.session_state.get("phase") != "spinning":
        return
    spinner = st.session_state.get("spin_owner", "A")
    if not online_can_control(spinner, "classic"):
        return
    final = st.session_state.get("classic_pending_draw_character")
    if not isinstance(final, dict):
        st.session_state.phase = "ready"
        st.session_state.classic_spin_id = None
        st.session_state.classic_pending_draw_character = None
        st.session_state.classic_spin_started_at = None
        persist_game_state(); st.rerun()
    remaining = st.session_state.remaining
    if not any(c.get("id") == final.get("id") for c in remaining):
        st.session_state.phase = "ready"
        st.session_state.classic_spin_id = None
        st.session_state.classic_pending_draw_character = None
        st.session_state.classic_spin_started_at = None
        persist_game_state(); st.rerun()
    st.session_state.remaining = [c for c in remaining if c.get("id") != final.get("id")]
    st.session_state.used.append(final.copy())
    st.session_state.current_char = final.copy()
    st.session_state.classic_pending_draw_character = None
    st.session_state.classic_spin_id = None
    st.session_state.classic_spin_started_at = None
    st.session_state.round_no += 1
    st.session_state.phase = "drawn"
    persist_game_state(); st.rerun()


def ai_max_willing_bid(character: dict[str, Any]) -> int:
    profile = character_profile(character)
    willingness = int(round(2 + profile["score"] / 15))
    team = st.session_state.players["B"]["team"]
    if team:
        synergy = sum(pair_chemistry(character, owned) for owned in team) / len(team)
        if synergy >= 70:
            willingness += 1
        elif synergy <= 42:
            willingness -= 1
    return max(1, min(willingness, max_bid("B")))


def begin_auction(opening_bid: int) -> None:
    spinner = st.session_state.spin_owner
    if not online_can_control(spinner, "classic"):
        st.warning("Nur der zuständige Online-Spieler kann die Auktion eröffnen.")
        return
    opponent = other(spinner)
    character = st.session_state.current_char
    if character is None:
        return
    if team_slots(opponent) <= 0:
        settle_auction(spinner, int(opening_bid), direct=True)
        return
    st.session_state.auction = {
        "character": character,
        "opening_player": spinner,
        "current_bid": int(opening_bid),
        "highest_bidder": spinner,
        "current_turn": opponent,
    }
    st.session_state.phase = "auction"
    persist_game_state(); st.rerun()


def maybe_ai_return_weak_character() -> None:
    """The AI only returns a clearly weaker pick if the roster has a large outlier."""
    if not is_ai_mode() or st.session_state.returns_used["B"] >= MAX_RETURNS:
        return
    p = st.session_state.players["B"]
    if len(p["team"]) < 3 or p["budget"] < RETURN_PENALTY + team_slots("B") + 1:
        return
    scored = [(character_profile(ch)["score"], idx, ch) for idx, ch in enumerate(p["team"])]
    scored.sort(key=lambda item: item[0])
    weakest, idx, ch = scored[0]
    second = scored[1][0]
    if second - weakest >= 25 and can_return_card("B", current_draw=False):
        p["team"].pop(idx)
        commit_return("B", ch, "KI tauscht einen klaren Schwachpunkt")


def settle_auction(winner: str, price: int, direct: bool = False) -> None:
    auction = st.session_state.auction or {}
    actor = auction.get("current_turn") if auction else st.session_state.get("spin_owner", "A")
    if not online_can_control(actor or "A", "classic"):
        st.warning("Diese Online-Aktion gehört dem anderen Spieler.")
        return
    character = st.session_state.current_char
    if st.session_state.auction:
        character = st.session_state.auction["character"]
    if character is None:
        return
    player = st.session_state.players[winner]
    if price > player["budget"] or team_slots(winner) <= 0:
        st.error("Das Gebot ist nicht gültig. Bitte prüfe Budget und Teamplätze.")
        return
    player["budget"] = round(player["budget"] - price, 2)
    player["team"].append({**character, "price": price, "round": st.session_state.round_no})
    st.session_state.history.append({
        "round": st.session_state.round_no, "character": character["name"], "faction": character["faction"],
        "winner": player["name"], "winner_key": winner, "price": int(price), "spinner": st.session_state.spin_owner, "direct": direct,
    })
    st.session_state.last_winner = {"player": winner, "character": character["name"], "price": int(price)}
    if winner == "B":
        maybe_ai_return_weak_character()
    st.session_state.next_spinner = other(st.session_state.spin_owner)
    st.session_state.current_char = None
    st.session_state.auction = None
    if len(st.session_state.players["A"]["team"]) == TEAM_SIZE and len(st.session_state.players["B"]["team"]) == TEAM_SIZE:
        st.session_state.phase = "finished"
    else:
        st.session_state.phase = "ready"
    persist_game_state(); st.rerun()


def process_ai_automatic_actions() -> None:
    """Run autonomous AI turns before rendering interactive controls."""
    if not is_ai_mode():
        return
    if st.session_state.phase == "drawn" and st.session_state.spin_owner == "B":
        ch = st.session_state.current_char
        cap = max_bid("B")
        if not ch or cap < MIN_PRICE:
            return
        opener = min(cap, max(1, int(round(character_profile(ch)["score"] / 32))))
        begin_auction(opener)
    if st.session_state.phase == "auction" and st.session_state.auction and st.session_state.auction["current_turn"] == "B":
        auction = st.session_state.auction
        character = auction["character"]
        current = int(auction["current_bid"])
        ceiling = min(ai_max_willing_bid(character), max_bid("B"))
        if team_slots("B") > 0 and current < ceiling:
            score = character_profile(character)["score"]
            step = 2 if score >= 85 and current <= 4 else 1
            proposal = min(ceiling, current + step)
            if proposal > current:
                auction["current_bid"] = proposal
                auction["highest_bidder"] = "B"
                auction["current_turn"] = "A"
                st.session_state.auction = auction
                persist_game_state(); st.rerun()
        settle_auction(auction["highest_bidder"], current)


def html_stat(label: str, value: str) -> str:
    return f'<div class="stat"><div class="stat-label">{label}</div><div class="stat-value">{value}</div></div>'


def render_player(player_key: str) -> None:
    player = st.session_state.players[player_key]
    is_ai = is_ai_player(player_key)
    cloud_batch = cloud_portraits_for_characters(player.get("team", []))
    label = "PLAYER 01" if player_key == "A" else "PLAYER 02"
    accent = "Dein Schiff" if player_key == "A" else ("KI-Rivale" if is_ai else "Freund-Modus")
    with st.container(border=True):
        st.markdown(f'<div class="panel-label">{label}</div><div class="player-heading"><div class="player-name">{safe_text(player["name"].upper())}</div><div class="player-tag">{safe_text(accent)}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="player-money">{money(player["budget"])}</div><div class="player-meta">Restbudget · Start: {money(START_BUDGET)} · Rückgaben: {st.session_state.returns_used[player_key]}/{MAX_RETURNS}</div>', unsafe_allow_html=True)
        st.progress(len(player["team"]) / TEAM_SIZE, text=f"TEAM {len(player['team'])}/{TEAM_SIZE}")
        for row_start in (0, 3):
            cols = st.columns(3 if row_start == 0 else 2, gap="small")
            indices = list(range(row_start, min(row_start + (3 if row_start == 0 else 2), TEAM_SIZE)))
            for col, idx in zip(cols, indices):
                with col:
                    if idx < len(player["team"]):
                        ch = player["team"][idx]
                        st.image(character_portrait_thumbnail(ch, cloud_batch), width=118)
                        slot_role = role_for_slot(idx)
                        ch_profile = character_profile(ch)
                        haki_small = f"HAKI {int(ch_profile['haki_score'])}/100" if ch_profile.get("haki_score") is not None else "HAKI N. B."
                        st.markdown(f'<div class="player-tag" style="display:inline-block;margin:3px 0 6px">{slot_role}</div><div style="font-weight:800;font-size:.78rem;line-height:1.15;min-height:31px">{safe_text(ch["name"])}</div><div style="font-size:.68rem;color:#e8bd64;font-weight:800">POWER {ch_profile["power"]}/100</div><div style="font-size:.66rem;color:#c4d0dc;font-weight:700">{haki_small} · FÄHIG. {int(ch_profile.get("abilities", 50))}/100</div><div style="font-size:.72rem;color:#e8bd64;font-weight:800">{money(ch["price"])}</div>' , unsafe_allow_html=True)
                        if st.session_state.phase in ("ready", "finished") and not is_ai and can_return_card(player_key, current_draw=False):
                            if st.button("↩ Rückgabe · 1 €", key=f"return_{player_key}_{ch['id']}", use_container_width=True, help=f"Maximal {MAX_RETURNS} Rückgaben je Spieler."):
                                return_owned_character(player_key, idx)
                    else:
                        st.markdown(f'<div class="slot-empty"><b>＋</b><span>{role_for_slot(idx)}</span></div>', unsafe_allow_html=True)
        if team_slots(player_key) == 0:
            st.markdown('<div class="winner-row">✓ Team komplett</div>', unsafe_allow_html=True)



def bounty_card_label(amount: int | None, state: str = "unbekannt") -> str:
    """Compact amount sized for a three-column character card; full bounty remains in the detail caption."""
    if amount is None:
        return "Unbekannt"
    if amount >= 1_000_000_000:
        value = f"{amount / 1_000_000_000:.2f}".rstrip("0").rstrip(".").replace(".", ",")
        return f"{value} Mrd. ฿"
    if amount >= 1_000_000:
        value = f"{amount / 1_000_000:.1f}".rstrip("0").rstrip(".").replace(".", ",")
        return f"{value} Mio. ฿"
    if amount >= 1_000:
        value = f"{amount / 1_000:.1f}".rstrip("0").rstrip(".").replace(".", ",")
        return f"{value} Tsd. ฿"
    return f"{amount} ฿"


def render_character_analysis(character: dict[str, Any]) -> None:
    profile = character_profile(character)
    # Card always exposes the four draft-defining details requested: Power, bounty, Haki and abilities.
    st.markdown(
        f'<div class="draft-card-banner"><div class="draft-card-kicker">PEAK FORM · MANGA BIS KAPITEL 1197</div>'
        f'<div class="draft-card-name">{safe_text(character.get("name", "Unbekannt"))}</div>'
        f'<div class="draft-card-sub">{safe_text(character.get("faction", ""))} · {safe_text(character.get("role", ""))}</div>'
        f'<div class="score-pills"><span class="score-pill">POWER {int(profile["power"])}/100</span>'
        f'<span class="score-pill">KOPFGELD {safe_text(bounty_card_label(profile.get("bounty"), profile.get("bounty_state", "unbekannt")))}</span>'
        f'<span class="score-pill">HAKI {str(int(profile["haki_score"])) + "/100" if profile.get("haki_score") is not None else "NICHT BESTÄTIGT"}</span>'
        f'<span class="score-pill">FÄHIGKEITEN {int(profile.get("abilities", 50))}/100</span></div></div>',
        unsafe_allow_html=True,
    )
    fruit_name = profile.get("devil_fruit_name")
    fruit_status = profile.get("devil_fruit_status", "nicht bestätigt")
    if fruit_name:
        st.markdown(
            f'<div class="evidence-line"><b>Teufelsfrucht / Kraftform:</b> {safe_text(fruit_name)} '
            f'<span style="color:#9db0c2">· {safe_text(fruit_status)}</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="evidence-line"><b>Teufelsfrucht:</b> Keine eigene Teufelsfrucht eindeutig bestätigt. '
            'Ein Fivefold-Wert von 0 bedeutet hier „keine belegte eigene Frucht“, nicht Kampfstärke 0.</div>',
            unsafe_allow_html=True,
        )
    # Two spacious rows keep values such as "50 / 100" and compact bounties from clipping.
    row_one = st.columns(2, gap="medium")
    row_one[0].metric("Power Level", f"{int(profile['power'])} / 100")
    row_one[1].metric("Kopfgeld", bounty_card_label(profile.get("bounty"), profile.get("bounty_state", "unbekannt")))
    row_two = st.columns(2, gap="medium")
    if profile.get("haki_score") is not None:
        row_two[0].metric("Haki-Fähigkeit", f"{int(profile['haki_score'])} / 100")
    else:
        row_two[0].metric("Haki-Fähigkeit", "Unbekannt" if profile.get("haki_types") else "Nicht bestätigt")
    row_two[1].metric("Fähigkeiten", f"{int(profile.get('abilities', 50))} / 100")
    st.progress(float(profile["power"]) / 100, text=f"Power Level · {power_tier(profile['power'])}")
    if profile.get("haki_score") is not None:
        st.progress(float(profile["haki_score"]) / 100, text=f"Haki-Meisterschaft · {int(profile['haki_score'])}/100 · {', '.join(profile.get('haki_types', [])) or 'Art nicht näher aufgeschlüsselt'}")
        if profile.get("haki_note"):
            st.caption(f"Haki-Einordnung: {profile['haki_note']}")
    else:
        if profile.get("haki_types"):
            st.caption(f"Haki-Typ belegt ({', '.join(profile.get('haki_types', []))}), aber die individuelle Meisterschaft ist nicht belastbar quantifizierbar. Kein künstlicher 0-Wert.")
        else:
            st.caption("Haki: im verwendeten Manga-Dossier nicht ausreichend bestätigt. Diese Figur wird aus dem Haki-Durchschnitt ausgeschlossen und nicht künstlich mit 0 bewertet.")
        if profile.get("haki_note"):
            st.caption(f"Haki-Einordnung: {profile['haki_note']}")
    haki_breakdown = profile.get("haki_breakdown", {})
    if haki_breakdown:
        with st.expander("⚡ Haki im Detail · Observation, Armament und Königshaki", expanded=False):
            haki_cols = st.columns(3, gap="small")
            for col, (part_key, label) in zip(haki_cols, [("observation", "Observationshaki"), ("armament", "Rüstungshaki"), ("conqueror", "Königshaki")]):
                detail = haki_breakdown.get(part_key, {})
                with col:
                    value = detail.get("score")
                    st.metric(label, f"{value}/100" if value is not None else "Nicht bestätigt")
                    if detail.get("status") == "bestätigt":
                        st.caption("Typ bestätigt · Zahl ist Modellschätzung")
                    elif "Typ bestätigt" in str(detail.get("status", "")) or "bestätigt; Meisterschaft" in str(detail.get("status", "")) or "Ausbruch bestätigt" in str(detail.get("status", "")):
                        st.caption("Typ belegt · Stärke unbekannt")
                    else:
                        st.caption("Nicht bestätigt / unbekannt")
                    st.write(detail.get("rationale", "Keine getrennte Einordnung hinterlegt."))
            st.caption("Die Teilwerte sind Fan-Modellschätzungen auf Basis der jeweils belegten Anwendungen. Nicht bestätigte Haki-Arten werden als unbekannt angezeigt, nicht als 0/100. Die Teilwerte sind keine offiziellen Manga-Statistiken.")
    st.progress(float(profile.get("abilities", 50)) / 100, text=f"Fähigkeiten/Nutzwert · {int(profile.get('abilities', 50))}/100")
    st.caption("Der Fähigkeitenwert bewertet nicht nur rohe Stärke, sondern auch Reichweite, Kontrolle, Spezialeffekte, Verteidigung, Mobilität und taktischen Nutzwert.")
    st.markdown("**Fähigkeiten & Kampfidentität**")
    st.markdown(f'<div class="evidence-line">{safe_text(profile.get("ability_summary", "Keine individuelle Fähigkeitsbeschreibung hinterlegt."))}</div>', unsafe_allow_html=True)
    stats = profile.get("combat_stats", {})
    with st.expander("🧭 Kampfprofil · Angriff, Defensive, Tempo und Ausdauer", expanded=False):
        labels = [("Angriff", "offense"), ("Defensive", "defense"), ("Tempo", "speed"), ("Ausdauer", "endurance"), ("Kampftaktik", "battle_iq")]
        st.markdown('<div class="combat-grid">' + ''.join(
            f'<div class="combat-stat"><div class="combat-stat-label">{label}</div><div class="combat-stat-value">{int(stats.get(key, 50))}</div></div>'
            for label, key in labels) + '</div>', unsafe_allow_html=True)
        st.caption("Diese fünf Teilwerte sind transparente Fan-Modellschätzungen für den Matchmaker, keine offiziellen Manga-Zahlen.")
        st.markdown("**Konterfenster / Grenzen**")
        st.write(profile.get("weaknesses", "Kein besonderer Konter hinterlegt."))
        if profile.get("evidence_basis"):
            st.caption(profile["evidence_basis"])
    specialties = profile.get("specialty_stats", {})
    if specialties:
        with st.expander("🎯 Spezialisierte Vergleichswerte", expanded=False):
            specialty_cols = st.columns(max(1, len(specialties)), gap="small")
            specialty_labels = {"swordsmanship": "Schwertkunst", "haki_edge": "Haki-Spitzenwert"}
            for col, (key, value) in zip(specialty_cols, specialties.items()):
                with col:
                    st.metric(specialty_labels.get(key, key.replace("_", " ").title()), f"{int(value)}/100")
            st.caption("Spezialisierte Vergleichswerte werden nur als zusätzliche Profilinformation gezeigt und ändern die klassische Teamformel nicht separat.")
    if profile.get("version_label"):
        st.caption(f"Bewertungsform: {profile['version_label']} · Evidenzsicherheit: {profile.get('confidence', 'Niedrig')}")
    st.caption(profile.get("rationale", "Fan-Schätzung auf Basis der bis Manga-Kapitel 1197 bekannten Story-Feats."))
    if profile.get("bounty_state") == "cross_guild":
        st.caption("Einordnung: Dieses Kopfgeld stammt von der Cross Guild, die Marineangehörige zu Zielen erklärt. Es ist kein von der Weltregierung gegen einen Piraten verhängtes Kopfgeld.")
    if profile.get("bounty_source") == "live":
        st.caption("Das Kopfgeld wurde beim letzten manuellen Online-Abruf bestätigt. Power Level und Fähigkeiten bleiben Fan-Einschätzungen.")


def render_roster_browser() -> None:
    """Searchable, filterable character explorer shared by both game modes."""
    characters = get_characters()
    # Each profile is derived once per explorer render and reused by filtering,
    # sorting, cards and details. This avoids duplicate scoring work on every click.
    character_by_id = {int(c["id"]): c for c in characters}
    profiles_all = {int(c["id"]): character_profile(c) for c in characters}
    rank_profiles_all = {int(c["id"]): ranking_profile(c) for c in characters}
    search_index = get_character_search_index()
    options = ["Alle Fraktionen"] + sorted({c["faction"] for c in characters})
    role_options = ["Alle Rollen"] + sorted({c.get("role", "Unbekannt") for c in characters})
    fcol, rolecol, scol, sortcol = st.columns([1, 1, 1.25, 1.25])
    with fcol:
        faction_filter = st.selectbox("Fraktion / Crew", options, key="pool_filter")
    with rolecol:
        role_filter = st.selectbox("Rolle", role_options, key="pool_role_filter")
    with scol:
        search = st.text_input("Charakter suchen", placeholder="Name, Crew oder Fähigkeit …", key="pool_search")
    with sortcol:
        sort_by = st.selectbox("Sortierung", [
            "Power Level · stärkste zuerst", "Power Level · schwächste zuerst", "Name A–Z",
            "Haki · höchste zuerst", "Teufelsfrucht · höchste zuerst", "Stärke · höchste zuerst",
            "Geschwindigkeit · höchste zuerst", "Battle IQ · höchste zuerst"
        ], key="pool_sort")
    range_col, type_col = st.columns([1, 1.4])
    with range_col:
        power_range = st.slider("Power-Level-Bereich", 0, 100, (0, 100), key="pool_power_range")
    with type_col:
        evidence_filter = st.selectbox("Frucht / Haki", [
            "Alle", "Teufelsfrucht-Wert > 0", "Keine bestätigte eigene Teufelsfrucht",
            "Observationshaki bestätigt", "Rüstungshaki bestätigt", "Königshaki bestätigt",
            "Haki nicht bestätigt"
        ], key="pool_evidence_filter")

    active_variant = st.session_state.get("draft_variant", "classic")
    if active_variant == "ranking":
        remaining_ids = {c["id"] for c in st.session_state.get("rank_remaining", [])}
        active_char = st.session_state.get("rank_current_char")
        active_id = active_char.get("id") if active_char else None
        owned_ids = {c["id"] for key in ("A", "B") for c in st.session_state.get("rank_players", {}).get(key, {}).get("team", [])}
    else:
        remaining_ids = {c["id"] for c in st.session_state.remaining}
        active_id = st.session_state.current_char["id"] if st.session_state.current_char else None
        owned_ids = {c["id"] for key in ("A", "B") for c in st.session_state.players[key]["team"]}

    q = search.lower().strip()
    filtered = []
    for character in characters:
        if faction_filter != "Alle Fraktionen" and character["faction"] != faction_filter:
            continue
        if role_filter != "Alle Rollen" and character.get("role", "Unbekannt") != role_filter:
            continue
        profile = profiles_all[int(character["id"])]
        rs = rank_profiles_all[int(character["id"])]
        if not (power_range[0] <= int(profile["power"]) <= power_range[1]):
            continue
        searchable = search_index.get(int(character["id"]), "")
        if q and q not in searchable:
            continue
        haki_types = set(profile.get("haki_types") or [])
        if evidence_filter == "Teufelsfrucht-Wert > 0" and rs["devil_fruit"] <= 0:
            continue
        if evidence_filter == "Keine bestätigte eigene Teufelsfrucht" and rs["devil_fruit"] > 0:
            continue
        if evidence_filter == "Observationshaki bestätigt" and not ("Observationshaki" in haki_types or "Observationshaki (Mantra)" in haki_types):
            continue
        if evidence_filter == "Rüstungshaki bestätigt" and "Rüstungshaki" not in haki_types:
            continue
        if evidence_filter == "Königshaki bestätigt" and "Königshaki" not in haki_types:
            continue
        if evidence_filter == "Haki nicht bestätigt" and profile.get("haki_status") == "bestätigt":
            continue
        filtered.append(character)

    profiles = profiles_all
    rank_profiles = rank_profiles_all
    sort_map = {
        "Haki · höchste zuerst": lambda c: (rank_profiles[c["id"]].get("haki_unknown", False), -rank_profiles[c["id"]]["haki"], str(c.get("name") or "").casefold()),
        "Teufelsfrucht · höchste zuerst": lambda c: (-rank_profiles[c["id"]]["devil_fruit"], c["name"].casefold()),
        "Stärke · höchste zuerst": lambda c: (-rank_profiles[c["id"]]["strength"], c["name"].casefold()),
        "Geschwindigkeit · höchste zuerst": lambda c: (-rank_profiles[c["id"]]["speed"], c["name"].casefold()),
        "Battle IQ · höchste zuerst": lambda c: (-rank_profiles[c["id"]]["battle_iq"], c["name"].casefold()),
    }
    if sort_by == "Power Level · stärkste zuerst":
        filtered.sort(key=lambda c: (-profiles[c["id"]]["power"], c["name"].casefold()))
    elif sort_by == "Power Level · schwächste zuerst":
        filtered.sort(key=lambda c: (profiles[c["id"]]["power"], c["name"].casefold()))
    elif sort_by == "Name A–Z":
        filtered.sort(key=lambda c: c["name"].casefold())
    else:
        filtered.sort(key=sort_map[sort_by])

    page_size = 20
    pages = max(1, math.ceil(len(filtered) / page_size))
    page_key = "pool_page"
    if st.session_state.get(page_key, 1) > pages:
        st.session_state[page_key] = pages
    page = st.selectbox("Ergebnisseite", list(range(1, pages + 1)), format_func=lambda p: f"Seite {p}/{pages}", key=page_key)
    subset = filtered[(page - 1) * page_size: page * page_size]
    st.caption(f"{len(filtered)} Figuren gefunden · {len(remaining_ids)} im aktiven Lostopf. Such- und Filteränderungen setzen den laufenden Draft nicht zurück.")
    cols = st.columns(4, gap="small")
    status = st.session_state.setdefault("portrait_status", {})
    selected_pool_id = st.session_state.get("pool_selected_character_id")
    cloud_batch = cloud_portraits_for_characters(subset)
    for i, ch in enumerate(subset):
        with cols[i % 4]:
            st.image(character_portrait_thumbnail(ch, cloud_batch), width=155)
            if ch["id"] in remaining_ids:
                state_label, color = "IM LOSTOPF", "#8dddb0"
            elif ch["id"] == active_id:
                state_label, color = "AKTUELL GEZOGEN", "#e8bd64"
            elif ch["id"] in owned_ids:
                state_label, color = "VERGEBEN", "#e8bd64"
            else:
                state_label, color = "AUSSERHALB DES POOLS", "#a7b7c6"
            profile, rprofile = profiles[ch["id"]], rank_profiles[ch["id"]]
            selected_style = "border:1px solid rgba(232,189,100,.75);box-shadow:0 0 0 1px rgba(232,189,100,.14);" if int(ch["id"]) == selected_pool_id else "border:1px solid rgba(210,226,243,.1);"
            st.markdown(
                f'<div style="{selected_style}background:rgba(255,255,255,.025);border-radius:10px;padding:9px;margin-bottom:8px">'
                f'<div style="font-weight:800;font-size:.84rem">{safe_text(ch["name"])}</div>'
                f'<div style="font-size:.7rem;color:#98adbf;margin:3px 0">{safe_text(ch["faction"])} · {safe_text(ch["role"])}</div>'
                f'<div style="font-size:.7rem;color:#e8bd64;font-weight:800">POWER {profile["power"]} · FRUCHT {rprofile["devil_fruit"]} · HAKI {rprofile["haki_display"]}</div>'
                f'<div style="font-size:.67rem;color:#cbd7e2;margin-top:3px">Kopfgeld: {safe_text(bounty_card_label(profile.get("bounty"), profile.get("bounty_state", "unbekannt")))}</div>'
                f'<div style="font-size:.63rem;letter-spacing:.08em;font-weight:800;color:{color};margin-top:5px">{state_label}</div></div>', unsafe_allow_html=True)
            if st.button("👁 Werte ansehen", key=f"pool_open_profile_{int(ch['id'])}", use_container_width=True, help=f"Öffnet Haki, Fähigkeiten, Power Level, Kopfgeld und die vollständige Bewertung von {ch['name']}."):
                st.session_state["pool_selected_character_id"] = int(ch["id"])
            if status.get(ch["name"], "").startswith("Ersatzporträt"):
                st.caption("Ersatzbild · Quelle prüfen")

    # Details are opened by a click on any character card. The selection persists
    # across pagination/filter changes and is independent of the active draft.
    selected_id = st.session_state.get("pool_selected_character_id")
    selected = character_by_id.get(int(selected_id)) if selected_id is not None else None
    if selected:
        st.markdown("---")
        st.markdown('<div class="panel-label">CHARAKTER-EXPLORER</div><h2>Vollständiges Charakterprofil</h2><div class="small-muted">Power Level, Kopfgeld, Haki, Fähigkeiten und Fivefold-Werte – unabhängig vom aktuellen Draft.</div>', unsafe_allow_html=True)
        with st.container(border=True):
            photo_col, identity_col = st.columns([0.7, 2.3], gap="medium")
            with photo_col:
                selected_cloud = cloud_portraits_for_characters([selected])
                st.image(character_portrait(selected, selected_cloud), use_container_width=True)
            with identity_col:
                st.markdown(f'<div class="character-name">{safe_text(selected["name"])}</div><div class="character-sub">{safe_text(selected.get("faction", ""))} · {safe_text(selected.get("role", ""))}</div>', unsafe_allow_html=True)
                if st.button("Ausgewähltes Profil schließen", key=f"pool_close_profile_{int(selected['id'])}"):
                    st.session_state.pop("pool_selected_character_id", None)
                    st.rerun()
            render_character_analysis(selected)
            detail_rank = rank_profiles_all[int(selected["id"])]
            st.markdown("### Fivefold Ranking · fünf getrennte Kategorien")
            stat_cols = st.columns(5, gap="small")
            for col, (label, key, _desc) in zip(stat_cols, RANKING_CATEGORIES):
                with col:
                    st.metric(label, detail_rank[f"{key}_display"])
            with st.expander("Warum hat der Charakter diese Fivefold-Werte?", expanded=False):
                for label, key, _desc in RANKING_CATEGORIES:
                    st.markdown(f"**{label}: {detail_rank[f'{key}_display']}** · {detail_rank[f'{key}_evidence']}")
                    st.write(detail_rank[f"{key}_rationale"])
    else:
        st.info("Klicke bei einem beliebigen Charakter auf **Werte ansehen**, um sein komplettes Profil zu öffnen.")


# Pairwise battle counters. Positive advantage belongs to the named favourite.
# Values are model modifiers, not canonically quantified powers.
MATCHUP_RULES = [
    {"a": "Monkey D. Luffy", "b": "Enel", "favored": "Monkey D. Luffy", "bonus": 20,
     "reason": "Klarer Frucht-Konter: Ruffys Gummikörper leitet Enels Blitz nicht. Enels Mantra, Reichweite und erhitzte Waffen bleiben echte Gefahren; der Bonus ist deshalb groß, aber nicht automatisch ein Sieg."},
    {"a": "Sanji", "b": "Nami", "favored": "Nami", "bonus": 22,
     "reason": "Kanonischer Verhaltens-Konter: Sanji greift Frauen nicht an. Das ist kein höherer Power-Level Namis, aber eine starke Einschränkung für Sanjis direkte Kampfführung."},
    {"a": "Sanji", "b": "Nico Robin", "favored": "Nico Robin", "bonus": 22,
     "reason": "Kanonischer Verhaltens-Konter: Sanji würde Robin nicht angreifen; Robins Greif-/Kontrollfähigkeiten verschärfen den taktischen Nachteil."},
    {"a": "Sanji", "b": "Boa Hancock", "favored": "Boa Hancock", "bonus": 22,
     "reason": "Sanji weigert sich, Frauen zu verletzen; Hancocks Versteinerungsfähigkeit kann zusätzlich gefährlich sein. Das ist ein Matchup-Sonderfall, kein Ranking allgemeiner Kampfkraft."},
    {"a": "Sanji", "b": "Black Maria", "favored": "Black Maria", "bonus": 22,
     "reason": "Sanji verweigerte im Manga den direkten Kampf gegen Black Maria, weil er keine Frau schlägt. Der Vorteil entsteht aus seiner Einschränkung, nicht aus einer höheren allgemeinen Stufe."},
    {"a": "Sanji", "b": "Stussy", "favored": "Stussy", "bonus": 22,
     "reason": "Verhaltensbedingter Konter: Sanji würde eine Frau nicht direkt angreifen. Der Modellbonus beschreibt diese Einschränkung statt rohe Stärke."},
    {"a": "Sanji", "b": "Gunko", "favored": "Gunko", "bonus": 22,
     "reason": "Verhaltensbedingter Konter: Sanji schlägt keine Frauen. Gunko kann deshalb in einem direkten Matchup stärker profitieren als ihr reiner Power-Level vermuten lässt."},
    {"a": "Usopp", "b": "Perona", "favored": "Usopp", "bonus": 10,
     "reason": "Bekannter Konter: Usopps extrem negatives Selbstbild machte ihn gegenüber Peronas Negative-Hollow-Effekt ungewöhnlich resistent."},
    {"a": "Joy Boy", "b": "Imu", "favored": "Joy Boy", "bonus": 3,
     "reason": "Kleiner, spekulativer Lore-Hinweis: Joy Boys gespeichertes Königshaki brachte Imu sichtbar aus dem Gleichgewicht und stoppte Gorosei-Effekte. Es gibt keinen vollständigen direkten Kampf; der Bonus ist bewusst klein."},
    {"a": "Portgas D. Ace", "b": "Sakazuki (Akainu)", "favored": "Sakazuki (Akainu)", "bonus": 14,
     "reason": "Kanonischer Elementnachteil: Magma überwältigte Aces Feuer im direkten Zusammenstoß. Das ist ein echter Fruchtvorteil und unabhängig vom generellen Power Level."},
    {"a": "Monkey D. Luffy", "b": "Crocodile", "favored": "Monkey D. Luffy", "bonus": 5,
     "reason": "Wasser/Flüssigkeit und später Blut ermöglichten Ruffy, Crocodiles Sandkörper zu treffen. Der Vorteil hängt von der verfügbaren Umgebung ab."},
    {"a": "Shanks", "b": "Eustass Kid", "favored": "Shanks", "bonus": 12,
     "reason": "Manga-Feat: Shanks erkannte mit Zukunftssicht Kids gefährliche Vorbereitung und beendete den Angriff in einem Schlag. Kontext und Crew-Unterstützung verhindern, dass dies als universeller Abstand für jedes Duell gelesen wird."},
    {"a": "Buggy", "b": "Dracule Mihawk", "favored": "Buggy", "bonus": 5,
     "reason": "Buggys Bara-Bara-Frucht bietet einen speziellen Schutz gegen gewöhnliche Schnittangriffe. Starkes Haki, stumpfe Gewalt oder andere Angriffsformen umgehen diesen Vorteil teilweise."},
]


def matchup_effect(character_a: dict[str, Any], character_b: dict[str, Any]) -> tuple[float, str]:
    name_a = normalize(character_a.get("name", ""))
    name_b = normalize(character_b.get("name", ""))
    female_names = {normalize(n) for n in ["Nami", "Nico Robin", "Boa Hancock", "Black Maria", "Stussy", "Gunko", "Jewelry Bonney", "Charlotte Linlin", "Charlotte Cracker", "Charlotte Perospero", "Perona", "Tashigi", "Nefertari Vivi", "Charlotte Pudding", "Carrot", "Tsuru", "Dr. Kureha"]}
    if name_a == normalize("Sanji") and name_b in female_names:
        return -22.0, "Kanonische Einschränkung: Sanji verweigert den Angriff auf Frauen; der Matchup-Bonus steht für diese Verhaltensschwäche, nicht für mehr rohe Kampfkraft."
    if name_b == normalize("Sanji") and name_a in female_names:
        return 22.0, "Kanonische Einschränkung: Sanji verweigert den Angriff auf Frauen; der Matchup-Bonus steht für diese Verhaltensschwäche, nicht für mehr rohe Kampfkraft."
    for rule in MATCHUP_RULES:
        ra, rb = normalize(rule["a"]), normalize(rule["b"])
        if {name_a, name_b} == {ra, rb}:
            modifier = float(rule["bonus"])
            if name_a != normalize(rule["favored"]):
                modifier *= -1
            return modifier, rule["reason"]
    return 0.0, "Kein besonderer kanonischer Konter hinterlegt; das Modell vergleicht vor allem Kampfkraft, Fähigkeiten und Intelligenz."


def duel_rating(character: dict[str, Any]) -> float:
    profile = character_profile(character)
    stats = profile.get("combat_stats", {})
    weights = {
        "power": 0.55, "haki": 0.10, "abilities": 0.12, "versatility": 0.03,
        "offense": 0.05, "defense": 0.05, "speed": 0.04, "endurance": 0.04, "battle_iq": 0.02,
    }
    values = {
        "power": float(profile.get("power", 50)),
        "abilities": float(profile.get("abilities", 50)),
        "versatility": float(profile.get("versatility", 50)),
        "offense": float(stats.get("offense", 50)),
        "defense": float(stats.get("defense", 50)),
        "speed": float(stats.get("speed", 50)),
        "endurance": float(stats.get("endurance", 50)),
        "battle_iq": float(stats.get("battle_iq", profile.get("intelligence", 50))),
    }
    if isinstance(profile.get("haki_score"), (int, float)) and profile.get("haki_status") == "bestätigt":
        values["haki"] = float(profile["haki_score"])
    else:
        weights.pop("haki")
    weight_sum = sum(weights.values())
    base = sum(values.get(key, 0.0) * weight for key, weight in weights.items()) / weight_sum
    # Small tactical/crew-read bonus; neither bounty nor social status influences duels.
    base += float(profile.get("intelligence_bonus", 0.0)) * 0.25
    return min(100.0, max(0.0, base))

def duel_result(character_a: dict[str, Any], character_b: dict[str, Any]) -> dict[str, Any]:
    """Return a duel prediction using the v5.0 all-pairs simulations when available.

    Probabilities in the matrix are oriented to its stored `a` and `b`. This
    function always reorients them to the caller's character_a/character_b order.
    The older local formula remains a defensive fallback for characters not in the
    matrix; current roster pairs all resolve through the complete matrix.
    """
    name_a = str(character_a.get("name", ""))
    name_b = str(character_b.get("name", ""))
    rating_a, rating_b = duel_rating(character_a), duel_rating(character_b)
    matchup = get_matchup_index().get(_pair_key(name_a, name_b))

    if matchup:
        stored_a = normalize(str(matchup.get("a", "")))
        direct_orientation = stored_a == normalize(name_a)
        try:
            stored_probability = float(matchup.get("a_win_probability", matchup.get("win_probability", 50.0)))
        except (TypeError, ValueError):
            denominator = max(1, int(matchup.get("simulations_per_pair", 250) or 250))
            stored_probability = 100.0 * float(matchup.get("a_wins_simulated", denominator / 2)) / denominator
        p_a = stored_probability if direct_orientation else 100.0 - stored_probability
        # Preserve the app's established non-certainty floor/ceiling. These are
        # model simulations, not canonically guaranteed fight outcomes.
        p_a = max(2.0, min(98.0, p_a))
        try:
            row_modifier = float(matchup.get("matchup_modifier", 0.0) or 0.0)
        except (TypeError, ValueError):
            row_modifier = 0.0
        modifier = row_modifier if direct_orientation else -row_modifier
        simulations = int(matchup.get("simulations_per_pair", 250) or 250)
        try:
            row_a_wins = int(matchup.get("a_wins_simulated", 0) or 0)
            row_b_wins = int(matchup.get("b_wins_simulated", 0) or 0)
            wins_a = row_a_wins if direct_orientation else row_b_wins
            wins_b = row_b_wins if direct_orientation else row_a_wins
        except (TypeError, ValueError):
            wins_a = round(p_a * simulations / 100.0)
            wins_b = simulations - wins_a
        confidence = str(matchup.get("confidence", "Unbekannt"))
        special_factors = matchup.get("special_factors", [])
        if not isinstance(special_factors, list):
            special_factors = [str(special_factors)] if special_factors else []
        reason = str(matchup.get("reason") or "V4.4-Matchup-Prognose aus den vorab berechneten Ergebnisziehungen.")
        # The probability and the displayed margin stay mathematically consistent.
        p_unit = max(0.02, min(0.98, p_a / 100.0))
        margin = 10.0 * math.log(p_unit / (1.0 - p_unit))
        source = "Power Matrix v5.0 · 15.000 Ergebnisziehungen"
    else:
        # Backward-compatible fallback for any future character absent from v4.4.
        modifier, reason = matchup_effect(character_a, character_b)
        margin = rating_a - rating_b + modifier
        p_a = 100.0 / (1.0 + math.exp(max(-12, min(12, -margin / 10.0))))
        p_a = max(2.0, min(98.0, p_a))
        simulations, confidence, wins_a, wins_b = 0, "Fallback", 0, 0
        special_factors = []
        source = "Lokale Fallback-Formel"

    if p_a >= 55:
        leader = name_a
    elif p_a <= 45:
        leader = name_b
    else:
        leader = "Enges Duell"
    return {
        "a": character_a, "b": character_b,
        "rating_a": round(rating_a, 1), "rating_b": round(rating_b, 1),
        "modifier": modifier, "margin": margin, "p_a": p_a, "leader": leader,
        "reason": reason, "special_factors": special_factors,
        "simulations": simulations, "a_wins_simulated": wins_a,
        "b_wins_simulated": wins_b, "confidence": confidence,
        "prediction_source": source,
    }


def calculate_matchmaking(team_a: list[dict[str, Any]], team_b: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pair team members to create the closest projected duels using v5.0 odds."""
    count = min(len(team_a), len(team_b), TEAM_SIZE)
    if count <= 0:
        return []
    a_team = team_a[:count]
    b_team = team_b[:count]

    # Only 25 pair predictions are needed for two five-character teams. Reuse
    # them across the at-most 120 possible assignments to avoid repeated work.
    pair_results = {
        (a_char.get("name", ""), b_char.get("name", "")): duel_result(a_char, b_char)
        for a_char in a_team for b_char in b_team
    }
    best_order = None
    best_value = -float("inf")
    for order in permutations(b_team, count):
        objective = 0.0
        for a_char, b_char in zip(a_team, order):
            predicted_probability = float(pair_results[(a_char.get("name", ""), b_char.get("name", ""))]["p_a"])
            # Prefer close fights around 50:50, using the actual v5.0 pairwise
            # estimate rather than a second, inconsistent formula.
            objective += -abs(predicted_probability - 50.0)
        if objective > best_value:
            best_value, best_order = objective, order

    chosen_order = best_order or b_team
    results = [pair_results[(a_char.get("name", ""), b_char.get("name", ""))]
               for a_char, b_char in zip(a_team, chosen_order)]
    for index, duel in enumerate(results):
        duel["number"] = index + 1
        duel["role_a"] = role_for_slot(next((i for i, c in enumerate(team_a) if c.get("id") == duel["a"].get("id")), index))
        duel["role_b"] = role_for_slot(next((i for i, c in enumerate(team_b) if c.get("id") == duel["b"].get("id")), index))
    return results


def battle_text(name_a: str, a: dict[str, Any], name_b: str, b: dict[str, Any], matchups: list[dict[str, Any]] | None = None) -> str:
    if not a["profiles"] or not b["profiles"]:
        return "Noch sind nicht beide Crews vollständig genug aufgestellt, um einen sinnvollen Kampftext zu formulieren."
    overall_delta = float(a["score"] - b["score"])
    if matchups:
        average_duel_margin = sum(float(item.get("margin", 0)) for item in matchups) / len(matchups)
        overall_delta = overall_delta * 0.35 + average_duel_margin * 0.65
    if overall_delta >= 0:
        winner_name, winner, loser_name, loser = name_a, a, name_b, b
    else:
        winner_name, winner, loser_name, loser = name_b, b, name_a, a
    if abs(overall_delta) < 3:
        intro = f"{name_a} und {name_b} liefern sich ein enges Gefecht: {winner_name} hat rechnerisch nur einen kleinen Vorteil."
    elif winner["chemistry"] > loser["chemistry"] + 8:
        intro = f"{winner_name} wirkt als Crew eingespielter und kann durch die bessere Teamchemie koordinierter angreifen."
    else:
        intro = f"{winner_name} hat nach Power Level, bestätigtem Haki und Team-Boni die stärkere modellierte Kampfbilanz."
    if winner["avg_power"] > loser["avg_power"] + 10:
        detail = " Im direkten Schlagabtausch dürfte die höhere rohe Kampfkraft den Unterschied machen."
    elif winner["chemistry"] > loser["chemistry"] + 10:
        detail = " Durch abgestimmte Kombinationen und gegenseitige Unterstützung kann die Crew einzelne stärkere Gegner ausspielen."
    else:
        detail = " Der Ausgang hängt stark von den konkreten Duellen, Haki, Teufelsfrüchten und der Kampfsituation ab."
    counter_notes = []
    for duel in matchups or []:
        if abs(duel.get("modifier", 0)) >= 15:
            favored = duel["a"]["name"] if duel["modifier"] > 0 else duel["b"]["name"]
            counter_notes.append(f"{favored} hat im Duell gegen {duel['b']['name'] if duel['modifier'] > 0 else duel['a']['name']} einen speziellen Matchup-Vorteil")
    if counter_notes:
        detail += " Der Matchmaker sieht zudem: " + "; außerdem ".join(counter_notes[:2]) + "."
    return intro + detail + f" Das Modell sieht {winner_name} leicht vorne, schließt eine Überraschung durch {loser_name} aber nicht aus."



# ---- Fivefold Ranking mode --------------------------------------------------
RANKING_CATEGORIES = [
    ("Teufelsfrucht", "devil_fruit", "Fruchtpotenzial, Beherrschung, Erwachen, Reichweite und besondere Effekte"),
    ("Haki", "haki", "Bestätigte Haki-Meisterschaft; unbestätigte Werte sind ausdrücklich als Schätzung markiert"),
    ("Stärke", "strength", "Direkte Durchschlagskraft, physische Kraft, Defensive und Durchhaltevermögen"),
    ("Geschwindigkeit", "speed", "Bewegungstempo, Reaktionen, Beschleunigung und Kampfmobilität"),
    ("Battle IQ", "battle_iq", "Taktische Entscheidungen im Kampf, Anpassung und Nutzung von Schwächen"),
]
RANK_CATEGORY_LABELS = [item[0] for item in RANKING_CATEGORIES]
RANK_CATEGORY_KEYS = {label: key for label, key, _ in RANKING_CATEGORIES}


@st.cache_data(show_spinner=False, max_entries=512)
def _ranking_profile_cached(character_name: str, values: dict[str, Any]) -> dict[str, Any]:
    """Cached pure Fivefold profile; unknown Haki remains visible as '?' and neutral only in the mean."""
    result: dict[str, Any] = {}
    unknown_count = 0
    for label, key, description in RANKING_CATEGORIES:
        raw = values.get(key, None if key == "haki" else 0)
        evidence = values.get("evidence", {}).get(key, "Modell-Schätzung")
        rationale = values.get("rationale", {}).get(key, description)
        unknown = raw is None or (key == "haki" and any(token in str(evidence).lower() for token in ("unbekannt", "nicht quantifizierbar", "nicht ausreichend")))
        if unknown:
            score = 50 if key == "haki" else 0
            display = "?" if key == "haki" else f"{score}/100"
            unknown_count += 1
        else:
            try:
                score = int(max(0, min(100, round(float(raw)))))
            except (TypeError, ValueError):
                score = 50 if key == "haki" else 0
                unknown = key == "haki"
            display = "?" if unknown and key == "haki" else f"{score}/100"
        result[key] = score
        result[f"{key}_unknown"] = bool(unknown)
        result[f"{key}_display"] = display
        result[f"{key}_evidence"] = str(evidence)
        result[f"{key}_rationale"] = str(rationale)
    result["average"] = round(sum(result[key] for _, key, _ in RANKING_CATEGORIES) / len(RANKING_CATEGORIES), 1)
    result["unknown_count"] = unknown_count
    result["average_note"] = "Unbekannte Haki-Meisterschaft wird ausschließlich für den Fivefold-Gleichgewichtsschnitt intern neutral mit 50 angesetzt und als ? angezeigt." if result.get("haki_unknown") else "Alle fünf Kategorien besitzen einen Zahlenwert."
    return result


def ranking_profile(character: dict[str, Any]) -> dict[str, Any]:
    rating = get_rating_data().get("characters", {}).get(character.get("name", ""), {})
    values = rating.get("ranking_stats", {}) if isinstance(rating, dict) else {}
    return _ranking_profile_cached(str(character.get("name", "")), values if isinstance(values, dict) else {})


@st.cache_data(show_spinner=False, max_entries=1)
def get_character_search_index() -> dict[int, str]:
    """Build the full-text index once; roster keystrokes then use simple substring checks."""
    ratings = get_rating_data().get("characters", {})
    result: dict[int, str] = {}
    for character in get_characters():
        rating = ratings.get(character.get("name", ""), {})
        ranking = rating.get("ranking_stats", {}) if isinstance(rating, dict) else {}
        searchable = [
            character.get("name"), character.get("role"), character.get("faction"),
            rating.get("ability_summary") if isinstance(rating, dict) else "",
            rating.get("haki_note") if isinstance(rating, dict) else "",
            rating.get("devil_fruit_name") if isinstance(rating, dict) else "",
            ranking.get("devil_fruit_rationale"), ranking.get("haki_rationale"),
            ranking.get("strength_rationale"), ranking.get("speed_rationale"),
            ranking.get("battle_iq_rationale"), ranking.get("evidence"),
            rating.get("haki_types") if isinstance(rating, dict) else [],
        ]
        result[int(character["id"])] = " ".join(search_text(value) for value in searchable).casefold()
    return result



def rank_is_ai_mode() -> bool:
    return st.session_state.get("rank_game_mode", "friend") == "single"


def rank_is_ai_player(player_key: str) -> bool:
    return rank_is_ai_mode() and player_key == "B"


def rank_other(player_key: str) -> str:
    return "B" if player_key == "A" else "A"


def rank_slots(player_key: str) -> int:
    return max(0, TEAM_SIZE - len(st.session_state.rank_players[player_key]["team"]))


def rank_free_categories(player_key: str) -> list[str]:
    used = {item.get("category") for item in st.session_state.rank_players[player_key]["team"] if item.get("category")}
    return [label for label in RANK_CATEGORY_LABELS if label not in used]


def rank_max_bid(player_key: str) -> int:
    player = st.session_state.rank_players[player_key]
    slots = rank_slots(player_key)
    if slots <= 0:
        return 0
    reserve_after_buying = max(0, slots - 1) * MIN_PRICE
    return max(0, int(float(player["budget"]) - reserve_after_buying + 1e-9))


def rank_can_return(player_key: str, current_draw: bool = False) -> bool:
    player = st.session_state.rank_players[player_key]
    if st.session_state.rank_returns_used.get(player_key, 0) >= MAX_RETURNS:
        return False
    slots = rank_slots(player_key)
    target_slots = slots if current_draw else slots + 1
    return float(player["budget"]) - RETURN_PENALTY >= target_slots * MIN_PRICE


def rank_init_game(force: bool = False) -> None:
    if "rank_players" in st.session_state and not force:
        return
    characters = get_characters()
    mode = st.session_state.get("rank_game_mode", "friend")
    name_a = st.session_state.get("name_input_a", "Spieler 1").strip() or "Spieler 1"
    name_b = "Grand Line KI" if mode == "single" else ("Wartet auf Mitspieler" if mode == "online" else (st.session_state.get("name_input_b", "Spieler 2").strip() or "Spieler 2"))
    st.session_state.rank_players = {
        "A": {"name": name_a, "budget": float(START_BUDGET), "team": []},
        "B": {"name": name_b, "budget": float(START_BUDGET), "team": []},
    }
    st.session_state.rank_remaining = [c.copy() for c in characters]
    st.session_state.rank_used = []
    st.session_state.rank_history = []
    st.session_state.rank_return_history = []
    st.session_state.rank_returns_used = {"A": 0, "B": 0}
    st.session_state.rank_phase = "ready"
    st.session_state.rank_round_no = 0
    st.session_state.rank_current_char = None
    st.session_state.rank_pending_draw_character = None
    st.session_state.rank_spin_id = None
    st.session_state.rank_spin_started_at = None
    starter = st.session_state.get("rank_next_start_player", "A")
    starter = starter if starter in {"A", "B"} else "A"
    st.session_state.rank_spin_owner = starter
    st.session_state.rank_next_spinner = starter
    st.session_state.rank_start_player = starter
    st.session_state.rank_result_recorded = None
    st.session_state.rank_auction = None
    st.session_state.rank_last_winner = None
    st.session_state.rank_pending_player = None
    st.session_state.rank_pending_character_id = None
    st.session_state.rank_game_seed = random.randrange(10**8)


def rank_reset_game() -> None:
    for key in [
        "rank_players", "rank_remaining", "rank_used", "rank_history", "rank_return_history", "rank_returns_used",
        "rank_phase", "rank_round_no", "rank_current_char", "rank_spin_owner", "rank_next_spinner", "rank_auction",
        "rank_pending_draw_character", "rank_spin_id", "rank_spin_started_at",
        "rank_last_winner", "rank_pending_player", "rank_pending_character_id", "rank_game_seed",
    ]:
        st.session_state.pop(key, None)
    rank_init_game(force=True)


def rank_active_spinner() -> str:
    preferred = st.session_state.rank_next_spinner
    if rank_slots(preferred) > 0:
        return preferred
    return rank_other(preferred)


def rank_draw_character() -> None:
    """Select a secret result, then let the browser animate before revealing it."""
    remaining = st.session_state.rank_remaining
    spinner = rank_active_spinner()
    if not online_can_control(spinner, "ranking"):
        st.warning("Du kannst erst ziehen, wenn du in der Online-Partie an der Reihe bist.")
        return
    if not remaining or rank_slots("A") <= 0 and rank_slots("B") <= 0:
        st.session_state.rank_phase = "finished"
        return
    if rank_slots(spinner) <= 0:
        spinner = rank_other(spinner)
    if rank_slots(spinner) <= 0:
        st.session_state.rank_phase = "finished"
        return
    final = remaining[secrets.randbelow(len(remaining))]
    st.session_state.rank_spin_owner = spinner
    st.session_state.rank_pending_draw_character = final.copy()
    st.session_state.rank_spin_id = f"{st.session_state.rank_game_seed}-{st.session_state.rank_round_no + 1}-{final['id']}-{secrets.token_hex(3)}"
    st.session_state.rank_spin_started_at = time.time() + 2.50
    st.session_state.rank_phase = "spinning"
    persist_game_state()
    st.rerun()


def rank_complete_spin() -> None:
    """Commit only on the active spinner session; both browsers run the same animation."""
    if st.session_state.get("rank_phase") != "spinning":
        return
    if not online_can_control(st.session_state.get("rank_spin_owner", "A"), "ranking"):
        return
    final = st.session_state.get("rank_pending_draw_character")
    if not isinstance(final, dict):
        st.session_state.rank_phase = "ready"
        st.session_state.rank_spin_id = None
        persist_game_state()
        st.rerun()
    remaining = st.session_state.rank_remaining
    if not any(c.get("id") == final.get("id") for c in remaining):
        st.session_state.rank_pending_draw_character = None
        st.session_state.rank_phase = "ready"
        st.session_state.rank_spin_id = None
        persist_game_state()
        st.rerun()
    st.session_state.rank_round_no += 1
    st.session_state.rank_remaining = [c for c in remaining if c["id"] != final["id"]]
    st.session_state.rank_used.append(final.copy())
    st.session_state.rank_current_char = final.copy()
    st.session_state.rank_pending_draw_character = None
    st.session_state.rank_spin_id = None
    st.session_state.rank_spin_started_at = None
    st.session_state.rank_phase = "drawn"
    persist_game_state()
    st.rerun()


def rank_commit_return(player_key: str, character: dict[str, Any], reason: str) -> None:
    player = st.session_state.rank_players[player_key]
    player["budget"] = round(float(player["budget"]) - RETURN_PENALTY, 2)
    st.session_state.rank_returns_used[player_key] += 1
    st.session_state.rank_remaining.append({k: v for k, v in character.items() if k not in {"price", "round", "category"}})
    st.session_state.rank_remaining.sort(key=lambda x: x["id"])
    st.session_state.rank_used = [x for x in st.session_state.rank_used if x["id"] != character["id"]]
    st.session_state.rank_return_history.append({
        "player": player["name"], "player_key": player_key, "character": character["name"],
        "fee": RETURN_PENALTY, "reason": reason, "round": st.session_state.rank_round_no,
    })


def rank_return_current_draw(player_key: str) -> None:
    character = st.session_state.rank_current_char
    if character is None or not rank_can_return(player_key, current_draw=True):
        st.error("Rückgabe nicht möglich: Drei Rückgaben je Spieler; jede kostet 1 € und Mindestbudget für offene Kategorien bleibt reserviert.")
        return
    rank_commit_return(player_key, character, "gezogene Karte")
    st.session_state.rank_current_char = None
    st.session_state.rank_auction = None
    st.session_state.rank_phase = "ready"
    st.session_state.rank_next_spinner = rank_other(st.session_state.rank_spin_owner)
    persist_game_state()
    st.rerun()


def rank_begin_auction(opening_bid: int) -> None:
    character = st.session_state.rank_current_char
    spinner = st.session_state.rank_spin_owner
    if not online_can_control(spinner, "ranking"):
        st.warning("Nur der zuständige Online-Spieler kann die Auktion eröffnen.")
        return
    opponent = rank_other(spinner)
    if character is None:
        return
    cap = rank_max_bid(spinner)
    if opening_bid < MIN_PRICE or opening_bid > cap:
        st.error("Das Startgebot liegt außerhalb des verfügbaren Budgets.")
        return
    if rank_slots(opponent) <= 0 or rank_max_bid(opponent) < opening_bid + 1:
        rank_settle_auction(spinner, int(opening_bid), direct=True)
        return
    st.session_state.rank_auction = {
        "character": character.copy(), "opening_player": spinner, "current_bid": int(opening_bid),
        "highest_bidder": spinner, "current_turn": opponent,
    }
    st.session_state.rank_phase = "auction"
    persist_game_state()
    st.rerun()


def rank_settle_auction(winner: str, price: int, direct: bool = False) -> None:
    auction = st.session_state.rank_auction or {}
    actor = auction.get("current_turn") if auction else st.session_state.get("rank_spin_owner", "A")
    if not online_can_control(actor or "A", "ranking"):
        st.warning("Diese Online-Aktion gehört dem anderen Spieler.")
        return
    character = auction.get("character") or st.session_state.rank_current_char
    if character is None:
        return
    player = st.session_state.rank_players[winner]
    if price > float(player["budget"]) or rank_slots(winner) <= 0 or price < MIN_PRICE:
        st.error("Das Gebot ist ungültig. Budget und freie Kategorien prüfen.")
        return
    player["budget"] = round(float(player["budget"]) - price, 2)
    acquired = {**character, "price": int(price), "round": st.session_state.rank_round_no, "category": None}
    player["team"].append(acquired)
    st.session_state.rank_history.append({
        "round": st.session_state.rank_round_no, "character": character["name"], "faction": character.get("faction", "Unbekannt"),
        "winner": player["name"], "winner_key": winner, "price": int(price), "spinner": st.session_state.rank_spin_owner,
        "direct": direct, "category": None,
    })
    st.session_state.rank_last_winner = {"player": winner, "character": character["name"], "price": int(price)}
    st.session_state.rank_pending_player = winner
    st.session_state.rank_pending_character_id = character["id"]
    st.session_state.rank_current_char = None
    st.session_state.rank_auction = None
    st.session_state.rank_phase = "assign"
    st.session_state.rank_next_spinner = rank_other(st.session_state.rank_spin_owner)
    persist_game_state()
    st.rerun()


def rank_assign_category(player_key: str, category: str) -> None:
    if not online_can_control(player_key, "ranking"):
        st.warning("Nur der Gewinner kann die eigene Fivefold-Kategorie zuordnen.")
        return
    if category not in rank_free_categories(player_key):
        st.error("Diese Kategorie ist bereits besetzt. Wähle einen freien Teamplatz.")
        return
    character_id = st.session_state.rank_pending_character_id
    team = st.session_state.rank_players[player_key]["team"]
    target = next((item for item in team if item.get("id") == character_id and not item.get("category")), None)
    if target is None:
        st.error("Die ausstehende Charakterzuordnung konnte nicht gefunden werden.")
        return
    target["category"] = category
    for item in reversed(st.session_state.rank_history):
        if item.get("character") == target.get("name") and item.get("winner_key") == player_key and item.get("category") is None:
            item["category"] = category
            break
    st.session_state.rank_pending_player = None
    st.session_state.rank_pending_character_id = None
    st.session_state.rank_phase = "finished" if rank_slots("A") == 0 and rank_slots("B") == 0 else "ready"
    persist_game_state()
    st.rerun()


def rank_return_owned_character(player_key: str, team_index: int) -> None:
    if st.session_state.rank_phase not in {"ready", "finished"}:
        st.warning("Eine bereits zugeordnete Karte kann nur zwischen Zügen oder nach Abschluss zurückgegeben werden.")
        return
    if not rank_can_return(player_key, current_draw=False):
        st.error(f"Rückgabe nicht möglich: maximal {MAX_RETURNS} Rückgaben für je {money(RETURN_PENALTY)} Strafe; Mindestbudget muss erhalten bleiben.")
        return
    team = st.session_state.rank_players[player_key]["team"]
    if not 0 <= team_index < len(team):
        return
    character = team.pop(team_index)
    rank_commit_return(player_key, character, "gewonnene Karte")
    if st.session_state.rank_phase == "finished":
        st.session_state.rank_phase = "ready"
    persist_game_state()
    st.rerun()


def rank_ai_willing_bid(character: dict[str, Any]) -> int:
    profile = ranking_profile(character)
    team = st.session_state.rank_players["B"]["team"]
    score = profile["average"]
    if team:
        team_score = rank_team_average(team)
        if team_score is not None and score > team_score + 6:
            score += 4
        elif team_score is not None and score < team_score - 12:
            score -= 4
    return max(1, min(int(round(2 + score / 15)), rank_max_bid("B")))


def rank_team_average(team: list[dict[str, Any]]) -> float | None:
    scores = []
    for item in team:
        category = item.get("category")
        if category in RANK_CATEGORY_KEYS:
            scores.append(ranking_profile(item)[RANK_CATEGORY_KEYS[category]])
    return round(sum(scores) / len(scores), 2) if scores else None


def rank_probability(team_a: list[dict[str, Any]], team_b: list[dict[str, Any]]) -> dict[str, Any] | None:
    score_a, score_b = rank_team_average(team_a), rank_team_average(team_b)
    if score_a is None or score_b is None:
        return None
    delta = score_a - score_b
    # Same capped logistic curve as the classic duel probability model (10-point scale).
    p_a = 100.0 / (1.0 + math.exp(max(-12.0, min(12.0, -delta / 10.0))))
    p_a = max(2.0, min(98.0, p_a))
    return {"score_a": score_a, "score_b": score_b, "delta": delta, "p_a": p_a, "p_b": 100.0 - p_a}


def rank_process_ai_automatic_actions() -> None:
    if st.session_state.get("draft_variant", "classic") != "ranking" or not rank_is_ai_mode() or "rank_players" not in st.session_state:
        return
    phase = st.session_state.rank_phase
    if phase == "ready" and rank_active_spinner() == "B" and st.session_state.rank_remaining:
        rank_draw_character()
    if phase == "drawn" and st.session_state.rank_spin_owner == "B":
        char = st.session_state.rank_current_char
        cap = rank_max_bid("B")
        if char and cap >= MIN_PRICE:
            opener = min(cap, max(1, int(round(ranking_profile(char)["average"] / 32))))
            rank_begin_auction(opener)
        return
    if phase == "auction" and st.session_state.rank_auction and st.session_state.rank_auction.get("current_turn") == "B":
        auction = st.session_state.rank_auction
        char = auction["character"]
        current = int(auction["current_bid"])
        ceiling = rank_ai_willing_bid(char)
        if rank_slots("B") > 0 and current < ceiling:
            proposal = min(ceiling, current + (2 if ranking_profile(char)["average"] >= 90 and current <= 4 else 1))
            if proposal > current:
                auction["current_bid"] = proposal
                auction["highest_bidder"] = "B"
                auction["current_turn"] = "A"
                st.session_state.rank_auction = auction
                persist_game_state()
                st.rerun()
        rank_settle_auction(auction["highest_bidder"], current)
    if phase == "assign" and st.session_state.rank_pending_player == "B":
        team_item = next((item for item in st.session_state.rank_players["B"]["team"] if item.get("id") == st.session_state.rank_pending_character_id), None)
        if team_item:
            free = rank_free_categories("B")
            best_category = max(free, key=lambda label: ranking_profile(team_item)[RANK_CATEGORY_KEYS[label]])
            rank_assign_category("B", best_category)


def rank_render_player(player_key: str) -> None:
    player = st.session_state.rank_players[player_key]
    cloud_batch = cloud_portraits_for_characters(player.get("team", []))
    average = rank_team_average(player["team"])
    reveal_average = False  # Reveal the averages only in the final panel below the draft.
    color = "#e8bd64" if player_key == "A" else "#77c8ed"
    if reveal_average and average is not None:
        avg_label = f"{average:.1f}<span>/ 100</span>"
        avg_title = "Enddurchschnitt"
    elif st.session_state.get("rank_phase") == "finished":
        avg_label = "<span>Siehe Endergebnis unten</span>"
        avg_title = "Finalwert enthüllt"
    else:
        avg_label = "<span>Wird am Ende aufgedeckt</span>"
        avg_title = "Wertung verborgen"
    st.markdown(f"""<div class="team-total-card"><div class="player-heading"><div class="player-name" style="color:{color}">{safe_text(player['name'])}</div><div class="player-tag">SPIELER {player_key}</div></div><div class="player-money">{money(player['budget'])}</div><div class="player-meta">Restbudget · Rückgaben {st.session_state.rank_returns_used[player_key]}/{MAX_RETURNS} · {len(player['team'])}/5 Karten</div><div class="team-total-label" style="margin-top:9px">{avg_title}</div><div class="team-total-value">{avg_label}</div></div>""", unsafe_allow_html=True)
    by_category = {item.get("category"): (idx, item) for idx, item in enumerate(player["team"]) if item.get("category")}
    for category, key, _desc in RANKING_CATEGORIES:
        st.markdown(f'<div class="slot-title" style="margin:12px 0 5px">{safe_text(category)}</div>', unsafe_allow_html=True)
        if category in by_category:
            index, item = by_category[category]
            score = ranking_profile(item)[key]
            cols = st.columns([1, 2.0])
            with cols[0]:
                st.image(character_portrait_thumbnail(item, cloud_batch), width=118)
            with cols[1]:
                st.markdown(f'**{safe_text(item["name"])}**')
                display_score = ranking_profile(item)[f'{key}_display']
                st.markdown(f'<div class="crew-score">{safe_text(display_score.split("/")[0])}<span style="font-size:.7rem;color:#9aafc3"> {"" if display_score == "?" else "/ 100"}</span></div>', unsafe_allow_html=True)
                if ranking_profile(item)[f'{key}_unknown']:
                    st.caption("Haki-Meisterschaft unbekannt · neutral 50 nur für den Enddurchschnitt")
                st.caption(f"Preis: {money(item.get('price', 0))}")
                if st.session_state.rank_phase in {"ready", "finished"} and rank_can_return(player_key, current_draw=False):
                    if st.button(f"↩ Zurückgeben · 1 €", key=f"rank_return_owned_{player_key}_{item['id']}_{item.get('round',0)}", use_container_width=True):
                        rank_return_owned_character(player_key, index)
        else:
            st.markdown(f'<div class="slot-empty"><b>—</b><span>Platz frei</span></div>', unsafe_allow_html=True)


def rank_show_character_values(character: dict[str, Any]) -> None:
    profile = ranking_profile(character)
    st.image(character_portrait(character), use_container_width=True)
    base_profile = character_profile(character)
    fruit_name = base_profile.get("devil_fruit_name", "Keine bestätigte eigene Teufelsfrucht")
    fruit_status = base_profile.get("devil_fruit_status", "nicht bestätigt")
    st.markdown(f'<div class="draft-card-banner"><div class="draft-card-kicker">PEAK MANGA FORM · RANKING-KARTE</div><div class="draft-card-name">{safe_text(character["name"])}</div><div class="draft-card-sub">{safe_text(character.get("faction", "Unbekannte Fraktion"))} · Power Level {base_profile["power"]}/100 · Kopfgeld {bounty_label(base_profile.get("bounty"), base_profile.get("bounty_state", "unbekannt"))}</div><div class="draft-card-sub"><b>Teufelsfrucht / Kraftform:</b> {safe_text(fruit_name)} · {safe_text(fruit_status)}</div><div class="score-pills">' + ''.join(f'<span class="score-pill">{safe_text(label)} <b>{safe_text(profile[key + "_display"])}</b></span>' for label, key, _ in RANKING_CATEGORIES) + '</div></div>', unsafe_allow_html=True)
    with st.expander("Einordnung der fünf Kategorien und Evidenz", expanded=False):
        for label, key, desc in RANKING_CATEGORIES:
            st.markdown(f"**{label}: {safe_text(profile[f'{key}_display'])}** · {safe_text(profile[f'{key}_evidence'])}")
            st.write(profile[f"{key}_rationale"])


def rank_render_mode() -> None:
    players = st.session_state.rank_players
    st.markdown('<div class="brand-row"><div class="hero-mark">⚖</div><div><div class="eyebrow">SEPARATER SPIELMODUS · 5 DISZIPLINEN</div><h1>FIVEFOLD <span class="gold">RANKING</span></h1><div class="hero-sub">Ziehe eine Figur, gewinne die Auktion und ordne sie einer noch freien Kategorie zu. Fünf unterschiedliche Kategorien entscheiden über den Durchschnitt.</div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="analysis-note"><b>Regeln:</b> 20 € Budget pro Spieler · gleiche Auktionslogik wie im klassischen Modus · 1 € Strafe pro Rückgabe · maximal 3 Rückgaben je Spieler. Jeder Spieler belegt jede Kategorie genau einmal: Teufelsfrucht, Haki, Stärke, Geschwindigkeit und Battle IQ. Der Endwert ist der arithmetische Mittelwert der fünf Kategorie-Werte (je 20 %); dieselbe logistische Wahrscheinlichkeitskurve wie beim klassischen Duellmodell zeigt die geschätzte Gewinnchance. Unbekannte Haki-Meisterschaft wird in der Karte als ? gezeigt und für den Fivefold-Schnitt intern nur neutral mit 50 angesetzt.</div>', unsafe_allow_html=True)
    top1, top2, top3, top4 = st.columns(4)
    top1.metric("Charaktere im Pool", f"{len(st.session_state.rank_remaining)} / {len(get_characters())}")
    top2.metric("Karten gewonnen", f"{len(st.session_state.rank_history)}")
    top3.metric("Kategorien je Spieler", "5 × 1")
    top4.metric("Aktuelle Runde", str(st.session_state.rank_round_no + (1 if st.session_state.rank_phase == 'ready' else 0)))

    left, center, right = st.columns([1.06, 1.5, 1.06], gap="medium")
    with left:
        rank_render_player("A")
    with right:
        rank_render_player("B")
    with center:
        with st.container(border=True):
            st.markdown('<div class="panel-label">FIVEFOLD DRAFT DECK</div>', unsafe_allow_html=True)
            phase = st.session_state.rank_phase
            if phase == "finished":
                st.markdown('<div class="result-wrap"><div class="eyebrow">FÜNF DISZIPLINEN BESETZT</div><h2>Ranking abgeschlossen</h2><p class="small-muted">Alle Kategorien zählen genau gleich. Es gibt keine Zusatzpunkte durch Kopfgeld, Titel oder die Reihenfolge der Plätze.</p></div>', unsafe_allow_html=True)
                if st.session_state.get("rank_result_recorded") is None:
                    st.markdown("**Spielergebnis speichern** · Wähle das tatsächliche Ergebnis. Die Modellwahrscheinlichkeit bleibt eine Prognose, kein automatisch festgelegter Sieger.")
                    result_cols = st.columns(3)
                    with result_cols[0]:
                        if st.button(f"{players['A']['name']} gewinnt", key="rank_result_a", use_container_width=True):
                            record_completed_match("ranking", "A")
                    with result_cols[1]:
                        if st.button(f"{players['B']['name']} gewinnt", key="rank_result_b", use_container_width=True):
                            record_completed_match("ranking", "B")
                    with result_cols[2]:
                        if st.button("Unentschieden", key="rank_result_tie", use_container_width=True):
                            record_completed_match("ranking", "tie")
                else:
                    outcome = st.session_state.rank_result_recorded
                    result_label = "Unentschieden" if outcome == "tie" else f"{players[outcome]['name']} als Sieger gespeichert"
                    st.success(f"Ergebnis gespeichert: {result_label}.")
                    st.caption(f"Nächster Startspieler: {players[st.session_state.get('rank_next_start_player', 'A')]['name']} · Bei Unentschieden bleibt der Startspieler der letzten Runde erhalten.")
                    if st.button("Neue Fivefold-Runde starten", key="rank_new_game_finish", type="primary", use_container_width=True):
                        rank_reset_game(); persist_game_state(); st.rerun()
            elif phase == "ready":
                spinner = rank_active_spinner()
                st.markdown(f'<div class="round-banner"><span class="status-dot"></span><b>Runde {st.session_state.rank_round_no + 1}</b> · {safe_text(players[spinner]["name"])} zieht die nächste Figur</div>', unsafe_allow_html=True)
                st.markdown('<div class="round-banner" style="text-align:center;margin:13px 0"><div style="font-size:2rem">🎡</div><b>Bereit für den nächsten Spin?</b><div class="small-muted">Das Rad startet sichtbar und enthüllt die Karte erst nach der Animation.</div></div>', unsafe_allow_html=True)
                if rank_is_ai_player(spinner):
                    st.info("Die KI zieht automatisch …")
                    if st.session_state.rank_remaining:
                        rank_draw_character()
                elif st.button("🎡 NÄCHSTE KARTE ZIEHEN", key="rank_spin_card", type="primary", use_container_width=True, disabled=(not st.session_state.rank_remaining or not online_can_control(spinner, "ranking"))):
                    rank_draw_character()
                if st.session_state.rank_last_winner:
                    last = st.session_state.rank_last_winner
                    st.caption(f"Letzter Zuschlag: {last['character']} → {players[last['player']]['name']} für {money(last['price'])}.")
            elif phase == "spinning":
                spinner = st.session_state.rank_spin_owner
                spin_id = st.session_state.get("rank_spin_id") or f"fallback-{st.session_state.rank_round_no + 1}"
                spin_result = FIVEFOLD_WIDGET(
                    mode="wheel",
                    spin_id=spin_id,
                    player=players[spinner]["name"],
                    round=st.session_state.rank_round_no + 1,
                    variant="ranking", animation_ms=3200, broadcast_delay_ms=1200,
                    start_at=st.session_state.get("rank_spin_started_at"),
                    key=f"rank_wheel_{spin_id}",
                    default=None,
                )
                if (isinstance(spin_result, dict) and spin_result.get("event") == "spin_complete"
                        and spin_result.get("spin_id") == spin_id
                        and online_can_control(spinner, "ranking")):
                    rank_complete_spin()
            elif phase == "drawn":
                character = st.session_state.rank_current_char
                spinner = st.session_state.rank_spin_owner
                opponent = rank_other(spinner)
                st.markdown(f'<div class="round-banner"><b>Gezogen von {safe_text(players[spinner]["name"])}</b> · Karte #{st.session_state.rank_round_no}</div>', unsafe_allow_html=True)
                rank_show_character_values(character)
                cap = rank_max_bid(spinner)
                options = list(range(MIN_PRICE, cap + 1))
                if rank_is_ai_player(spinner):
                    st.info("Die KI eröffnet die Auktion …")
                    rank_begin_auction(min(cap, max(1, int(round(ranking_profile(character)["average"] / 32)))))
                elif options:
                    opening = st.select_slider("Startgebot", options=options, value=min(2, max(options)), format_func=lambda x: money(x), key=f"rank_opening_{st.session_state.rank_game_seed}_{st.session_state.rank_round_no}")
                    st.caption(f"Maximalgebot: {money(cap)} · mindestens 1 € pro noch offenem Kategorienplatz reserviert.")
                    if st.button("⚓ Auktion eröffnen", key=f"rank_begin_{st.session_state.rank_game_seed}_{st.session_state.rank_round_no}", type="primary", use_container_width=True, disabled=not online_can_control(spinner, "ranking")):
                        rank_begin_auction(int(opening))
                else:
                    st.error("Für diesen Spieler ist kein gültiges Gebot mehr möglich.")
                if not rank_is_ai_player(spinner) and rank_can_return(spinner, current_draw=True):
                    st.caption(f"Rückgaben übrig: {MAX_RETURNS - st.session_state.rank_returns_used[spinner]} · Strafe {money(RETURN_PENALTY)} pro Rückgabe.")
                    if st.button("↩ Karte zurückgeben · −1 €", key=f"rank_return_draw_{st.session_state.rank_game_seed}_{st.session_state.rank_round_no}", use_container_width=True, disabled=not online_can_control(spinner, "ranking")):
                        rank_return_current_draw(spinner)
            elif phase == "auction":
                auction = st.session_state.rank_auction
                character = auction["character"]
                turn, highest, bid = auction["current_turn"], auction["highest_bidder"], int(auction["current_bid"])
                rank_show_character_values(character)
                st.markdown(f'<div class="result-wrap"><div class="panel-label">HÖCHSTGEBOT</div><div class="auction-price">{money(bid)}</div><div class="auction-turn">Aktuell vorne: <b>{safe_text(players[highest]["name"])}</b></div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="winner-row" style="margin-top:10px;color:#e5edf6;background:rgba(232,189,100,.06);border-color:rgba(232,189,100,.2)">Am Zug: <b>{safe_text(players[turn]["name"])}</b></div>', unsafe_allow_html=True)
                if rank_is_ai_player(turn):
                    st.info("Die KI prüft Wert, Budget und offene Kategorien …")
                else:
                    max_turn = rank_max_bid(turn)
                    next_options = list(range(bid + 1, max_turn + 1)) if rank_slots(turn) > 0 else []
                    if next_options:
                        proposal = st.select_slider("Nächstes Gebot", options=next_options, value=min(bid + 1, max(next_options)), format_func=lambda x: money(x), key=f"rank_bid_{st.session_state.rank_game_seed}_{st.session_state.rank_round_no}_{turn}_{bid}")
                        if st.button(f"💰 Auf {money(proposal)} erhöhen", key=f"rank_raise_{st.session_state.rank_game_seed}_{st.session_state.rank_round_no}_{turn}_{bid}", type="primary", use_container_width=True, disabled=not online_can_control(turn, "ranking")):
                            auction["current_bid"] = int(proposal); auction["highest_bidder"] = turn; auction["current_turn"] = rank_other(turn)
                            st.session_state.rank_auction = auction; persist_game_state(); st.rerun()
                    else:
                        st.info("Du kannst das aktuelle Gebot nicht mehr überbieten, ohne das Mindestbudget zu unterschreiten.")
                    if st.button("✋ Passen · Höchstbietender gewinnt", key=f"rank_pass_{st.session_state.rank_game_seed}_{st.session_state.rank_round_no}_{turn}_{bid}", use_container_width=True, disabled=not online_can_control(turn, "ranking")):
                        rank_settle_auction(highest, bid)
            elif phase == "assign":
                player_key = st.session_state.rank_pending_player
                pending = next((item for item in players[player_key]["team"] if item.get("id") == st.session_state.rank_pending_character_id), None) if player_key else None
                if pending:
                    st.markdown(f'<div class="round-banner"><b>{safe_text(players[player_key]["name"])}</b> hat {safe_text(pending["name"])} gewonnen. Wähle jetzt einen freien Kategorienplatz.</div>', unsafe_allow_html=True)
                    rank_show_character_values(pending)
                    if rank_is_ai_player(player_key):
                        st.info("Die KI ordnet die Karte automatisch der besten freien Kategorie zu …")
                    else:
                        free = rank_free_categories(player_key)
                        if free:
                            profile = ranking_profile(pending)
                            try:
                                encoded = base64.b64encode(character_portrait(pending)).decode("ascii")
                                image_data = f"data:image/jpeg;base64,{encoded}"
                            except Exception:
                                image_data = ""
                            component_result = FIVEFOLD_WIDGET(
                                mode="assign",
                                player=players[player_key]["name"],
                                character={
                                    "id": int(pending["id"]),
                                    "name": pending["name"],
                                    "price_text": money(pending.get("price", 0)),
                                    "image_data": image_data,
                                },
                                occupied=[item.get("category") for item in players[player_key]["team"] if item.get("category")],
                                categories=[
                                    {"label": label, "available": label in free, "score": profile[RANK_CATEGORY_KEYS[label]], "description": desc}
                                    for label, _key, desc in RANKING_CATEGORIES
                                ],
                                key=f"rank_drag_assign_{st.session_state.rank_game_seed}_{st.session_state.rank_round_no}_{pending['id']}",
                                default=None,
                            )
                            if (
                                isinstance(component_result, dict)
                                and component_result.get("event") == "assign"
                                and component_result.get("character_id") == pending["id"]
                                and component_result.get("category") in free
                            ):
                                rank_assign_category(player_key, component_result["category"])
                            with st.expander("Alternative: Kategorie per Klick wählen"):
                                fallback_cols = st.columns(len(free))
                                for col, label in zip(fallback_cols, free):
                                    with col:
                                        key = RANK_CATEGORY_KEYS[label]
                                        st.markdown(f"**{safe_text(label)}**")
                                        st.caption(f"{profile[key]}/100")
                                        if st.button("Zuweisen", key=f"rank_assign_click_{st.session_state.rank_game_seed}_{st.session_state.rank_round_no}_{pending['id']}_{key}", use_container_width=True):
                                            rank_assign_category(player_key, label)

    # The final averages are intentionally revealed at the bottom only after all ten placements.
    if st.session_state.rank_phase == "finished":
        a_avg = rank_team_average(players["A"]["team"]) or 0.0
        b_avg = rank_team_average(players["B"]["team"]) or 0.0
        probability = rank_probability(players["A"]["team"], players["B"]["team"])
        st.markdown('<div class="result-wrap" style="margin-top:22px"><div class="eyebrow">DAS FINALE FIVEFOLD-ERGEBNIS</div><h2>Fünf Kategorien. Ein Durchschnitt.</h2><p class="small-muted">Erst jetzt werden die beiden Endwerte und die modellierte Gewinnchance aufgedeckt.</p></div>', unsafe_allow_html=True)
        final_a, final_vs, final_b = st.columns([1, .35, 1])
        with final_a:
            st.markdown(f'<div class="team-total-card" style="text-align:center;border-color:#e8bd6488"><div class="player-tag">{safe_text(players["A"]["name"])}</div><div class="crew-score" style="font-size:3.6rem">{a_avg:.1f}<span style="font-size:1rem;color:#9aafc3"> / 100</span></div><div class="small-muted">Enddurchschnitt</div></div>', unsafe_allow_html=True)
        with final_vs:
            st.markdown('<div style="text-align:center;font-size:1.2rem;font-weight:900;color:#e8bd64;padding-top:34px">VS</div>', unsafe_allow_html=True)
        with final_b:
            st.markdown(f'<div class="team-total-card" style="text-align:center;border-color:#77c8ed88"><div class="player-tag">{safe_text(players["B"]["name"])}</div><div class="crew-score" style="font-size:3.6rem;color:#77c8ed">{b_avg:.1f}<span style="font-size:1rem;color:#9aafc3"> / 100</span></div><div class="small-muted">Enddurchschnitt</div></div>', unsafe_allow_html=True)
        if probability:
            st.progress(probability["p_a"] / 100, text=f'Modellierte Gewinnchance: {safe_text(players["A"]["name"])} {probability["p_a"]:.1f}% · {safe_text(players["B"]["name"])} {probability["p_b"]:.1f}%')
            st.caption("Die Prozentwerte sind eine Prognose aus dem Durchschnittsabstand – kein vorweggenommenes Spielergebnis.")
        if a_avg > b_avg:
            st.success(f'{players["A"]["name"]} liegt im Fivefold-Ranking vorne: +{a_avg-b_avg:.1f} Punkte.')
        elif b_avg > a_avg:
            st.success(f'{players["B"]["name"]} liegt im Fivefold-Ranking vorne: +{b_avg-a_avg:.1f} Punkte.')
        else:
            st.info("Die Teams liegen exakt gleichauf.")

    st.markdown("### Fivefold-Regeln und Scoring")
    st.markdown("""
- **Teufelsfrucht:** Fruchtstärke und Beherrschung, inklusive Erwachen und Spezialeffekten. Ein Wert von 0 bedeutet, dass keine eigene Teufelsfrucht belegt ist; das ist kein Urteil über die allgemeine Kampfstärke.
- **Haki:** Bestätigte Meisterschaft erhält einen belegten Wert. Wenn Haki nicht bestätigt ist, wird ein konservativer, separat beschrifteter Fan-Schätzwert verwendet, damit alle fünf Kategorien für den Modus vergleichbar bleiben. Das ändert nicht die Haki-Behandlung im klassischen Modus.
- **Stärke:** Offensivkraft, physische Kraft, Defensive und Durchhaltevermögen; nicht nur das Power Level.
- **Geschwindigkeit:** Reaktionszeit, Kampftempo, Mobilität und belegte Geschwindigkeits-Feats.
- **Battle IQ:** 70 % taktische Kampfentscheidungen und 30 % allgemeine Intelligenz als Hilfswert. Cleverness außerhalb des Kampfes allein macht keinen Top-Battle-IQ.

Jeder Spieler besetzt jede der fünf Kategorien genau einmal. Der Endwert ist der Durchschnitt der fünf eingesetzten Kategorie-Werte, also maximal 100 und nicht 500. Die modellierte Gewinnchance verwendet die gleiche logistische 10-Punkte-Skala wie die klassischen Einzelduelle. Die Werte bleiben begründete Fan-Einschätzungen, keine offiziellen Oda-Statistiken.
""")
    with st.expander(f"Fivefold-Auktionschronik ({len(st.session_state.rank_history)} Deals)"):
        if not st.session_state.rank_history:
            st.caption("Noch keine Karte gewonnen.")
        else:
            for deal in reversed(st.session_state.rank_history[-20:]):
                category = f" · {deal['category']}" if deal.get("category") else " · Kategorie noch offen"
                st.markdown(f"- **#{deal['round']} {safe_text(deal['character'])}** — {safe_text(deal['winner'])}, {money(deal['price'])}{category}")
        if st.session_state.rank_return_history:
            st.markdown("**Rückgaben**")
            for item in reversed(st.session_state.rank_return_history):
                st.markdown(f"- {safe_text(item['player'])}: {safe_text(item['character'])} zurückgegeben · −{money(item['fee'])}")
    with st.expander("Quellen und Grenzen der Kategorie-Werte"):
        st.markdown("Die Wertung trennt bestätigte Manga-Fakten von Fan-Schätzungen. Verwendete Referenzen umfassen [One Piece Wiki – Teufelsfrucht](https://onepiece.fandom.com/wiki/Devil_Fruit), [Charlotte Katakuri](https://onepiece.fandom.com/wiki/Charlotte_Katakuri), [Boa Hancock](https://onepiece.fandom.com/wiki/Boa_Hancock), [Joy Boy](https://onepiece.fandom.com/wiki/Joy_Boy), [Loki](https://onepiece.fandom.com/wiki/Loki), [OPwiki – aktuelle Kapitel](https://opwiki.org/wiki/Aktuelle_Kapitel) und die [offizielle Kapitelübersicht](https://www.viz.com/shonenjump/chapters/one-piece). Community-Videos und Foren helfen beim Vergleich, gelten aber nicht als Kanonbeweis. Bewertungsstand: Kapitel 1197 (01.11.2026).")
    if st.button("🏴‍☠️ Charakter-Explorer anzeigen / schließen", key="toggle_roster_ranking", use_container_width=True):
        st.session_state["show_roster_browser_ranking"] = not st.session_state.get("show_roster_browser_ranking", False)
        st.rerun()
    if st.session_state.get("show_roster_browser_ranking", False):
        with st.container(border=True):
            render_roster_browser()
    with st.expander(f"Fivefold-Spielhistorie ({len(st.session_state.get('rank_match_history', []))} Spiele)"):
        history = st.session_state.get("rank_match_history", [])
        if not history:
            st.caption("Noch kein Fivefold-Ergebnis gespeichert.")
        else:
            wins = {}
            for row in history:
                if row.get("outcome") in {"A", "B"}:
                    wins[row.get("winner", "Unbekannt")] = wins.get(row.get("winner", "Unbekannt"), 0) + 1
            if wins:
                st.markdown("**Siege:** " + " · ".join(f"{safe_text(name)}: {count}" for name, count in sorted(wins.items())))
            for row in reversed(history[-20:]):
                result = "Unentschieden" if row["outcome"] == "tie" else f"Sieger: {row['winner']}"
                score_text = "" if row.get("score_a") is None or row.get("score_b") is None else f" · Ø {row['score_a']:.1f} : {row['score_b']:.1f}"
                st.markdown(f"- Spiel {row['game_no']}: **{safe_text(row['player_a'])}** vs. **{safe_text(row['player_b'])}** — {result}{score_text}. Start: {safe_text(row['starter_name'])}; nächste Runde beginnt {safe_text(row['next_starter_name'])}.")
        if history and not st.session_state.confirm_clear_rank_history:
            if st.button("Fivefold-Historie zurücksetzen", key="rank_clear_history_request"):
                st.session_state.confirm_clear_rank_history = True
                st.rerun()
        if st.session_state.confirm_clear_rank_history:
            st.warning("Soll die gesamte Fivefold-Spielhistorie dauerhaft gelöscht werden? Der aktuelle Draft bleibt bestehen.")
            clear_cols = st.columns(2)
            with clear_cols[0]:
                if st.button("Ja, Historie löschen", key="rank_clear_history_yes", type="primary"):
                    st.session_state.rank_match_history = []
                    st.session_state.rank_next_start_player = "A"
                    st.session_state.confirm_clear_rank_history = False
                    persist_game_state(); st.rerun()
            with clear_cols[1]:
                if st.button("Abbrechen", key="rank_clear_history_no"):
                    st.session_state.confirm_clear_rank_history = False
                    st.rerun()


def _flip_player_key(value: Any) -> Any:
    return "B" if value == "A" else "A" if value == "B" else value


def swap_active_player_identities() -> None:
    """Swap current human player identities while keeping each person's team/history association intact."""
    variant = st.session_state.get("draft_variant", "classic")
    mode = st.session_state.get("rank_game_mode", "friend") if variant == "ranking" else st.session_state.get("game_mode", "friend")
    if mode == "single":
        return

    # Input values are changed in a button callback, before the keyed widgets are rebuilt.
    a_name = st.session_state.get("name_input_a", "Spieler 1")
    b_name = st.session_state.get("name_input_b", "Spieler 2")
    st.session_state["name_input_a"], st.session_state["name_input_b"] = b_name, a_name

    if variant == "ranking":
        if "rank_players" in st.session_state:
            st.session_state.rank_players["A"], st.session_state.rank_players["B"] = st.session_state.rank_players["B"], st.session_state.rank_players["A"]
        if "rank_returns_used" in st.session_state:
            st.session_state.rank_returns_used["A"], st.session_state.rank_returns_used["B"] = st.session_state.rank_returns_used["B"], st.session_state.rank_returns_used["A"]
        for key in ("rank_spin_owner", "rank_next_spinner", "rank_start_player", "rank_next_start_player", "rank_pending_player"):
            if key in st.session_state:
                st.session_state[key] = _flip_player_key(st.session_state[key])
        auction = st.session_state.get("rank_auction")
        if isinstance(auction, dict):
            for key in ("opening_player", "current_turn", "highest_bidder"):
                if key in auction:
                    auction[key] = _flip_player_key(auction[key])
            st.session_state.rank_auction = auction
        for collection_key in ("rank_history", "rank_return_history"):
            for row in st.session_state.get(collection_key, []):
                for key in ("winner_key", "spinner", "player_key"):
                    if key in row:
                        row[key] = _flip_player_key(row[key])
        last = st.session_state.get("rank_last_winner")
        if isinstance(last, dict) and "player" in last:
            last["player"] = _flip_player_key(last["player"])
        if st.session_state.get("rank_result_recorded") in {"A", "B"}:
            st.session_state.rank_result_recorded = _flip_player_key(st.session_state.rank_result_recorded)
    else:
        if "players" in st.session_state:
            st.session_state.players["A"], st.session_state.players["B"] = st.session_state.players["B"], st.session_state.players["A"]
        if "returns_used" in st.session_state:
            st.session_state.returns_used["A"], st.session_state.returns_used["B"] = st.session_state.returns_used["B"], st.session_state.returns_used["A"]
        for key in ("spin_owner", "next_spinner", "classic_start_player", "classic_next_start_player"):
            if key in st.session_state:
                st.session_state[key] = _flip_player_key(st.session_state[key])
        auction = st.session_state.get("auction")
        if isinstance(auction, dict):
            for key in ("opening_player", "current_turn", "highest_bidder"):
                if key in auction:
                    auction[key] = _flip_player_key(auction[key])
            st.session_state.auction = auction
        for collection_key in ("history", "return_history"):
            for row in st.session_state.get(collection_key, []):
                for key in ("winner_key", "spinner", "player_key"):
                    if key in row:
                        row[key] = _flip_player_key(row[key])
        last = st.session_state.get("last_winner")
        if isinstance(last, dict) and "player" in last:
            last["player"] = _flip_player_key(last["player"])
        if st.session_state.get("classic_result_recorded") in {"A", "B"}:
            st.session_state.classic_result_recorded = _flip_player_key(st.session_state.classic_result_recorded)
    persist_game_state()


def record_completed_match(variant: str, outcome: str) -> None:
    """Record a user-confirmed result and pick the previous loser's seat as next starter."""
    if outcome not in {"A", "B", "tie"}:
        return
    ranking = variant == "ranking"
    players_key = "rank_players" if ranking else "players"
    result_key = "rank_result_recorded" if ranking else "classic_result_recorded"
    history_key = "rank_match_history" if ranking else "classic_match_history"
    next_key = "rank_next_start_player" if ranking else "classic_next_start_player"
    starter_key = "rank_start_player" if ranking else "classic_start_player"
    if st.session_state.get(result_key) is not None:
        return
    players = st.session_state[players_key]
    starter = st.session_state.get(starter_key, "A")
    next_starter = starter if outcome == "tie" else _flip_player_key(outcome)
    score_a = score_b = probability_a = probability_b = None
    if ranking:
        score_a = rank_team_average(players["A"]["team"])
        score_b = rank_team_average(players["B"]["team"])
        odds = rank_probability(players["A"]["team"], players["B"]["team"])
        if odds:
            probability_a, probability_b = odds["p_a"], odds["p_b"]
    else:
        profile_a = analyze_team(players["A"]["team"])
        profile_b = analyze_team(players["B"]["team"])
        score_a, score_b = profile_a.get("score"), profile_b.get("score")
        if score_a is not None and score_b is not None:
            delta = score_a - score_b
            probability_a = max(2.0, min(98.0, 100.0 / (1.0 + math.exp(max(-12.0, min(12.0, -delta / 10.0))))))
            probability_b = 100.0 - probability_a
    winner = players[outcome]["name"] if outcome in {"A", "B"} else "Unentschieden"
    loser_key = _flip_player_key(outcome) if outcome in {"A", "B"} else None
    entry = {
        "game_no": len(st.session_state.get(history_key, [])) + 1,
        "saved_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "player_a": players["A"]["name"], "player_b": players["B"]["name"],
        "starter": starter, "starter_name": players[starter]["name"],
        "outcome": outcome, "winner": winner,
        "loser": players[loser_key]["name"] if loser_key else "—",
        "next_starter": next_starter, "next_starter_name": players[next_starter]["name"],
        "score_a": score_a, "score_b": score_b,
        "probability_a": probability_a, "probability_b": probability_b,
    }
    st.session_state[history_key] = list(st.session_state.get(history_key, [])) + [entry]
    st.session_state[next_key] = next_starter
    st.session_state[result_key] = outcome
    persist_game_state()
    st.rerun()


# ---- Initialize state -------------------------------------------------------
st.session_state.setdefault("game_mode", "friend")
st.session_state.setdefault("online_room_code", None)
st.session_state.setdefault("online_role", None)
st.session_state.setdefault("online_revision", 0)
st.session_state.setdefault("online_last_hash", None)
st.session_state.setdefault("online_status", None)
st.session_state.setdefault("classic_pending_draw_character", None)
st.session_state.setdefault("classic_spin_id", None)
st.session_state.setdefault("classic_spin_started_at", None)
st.session_state.setdefault("rank_spin_started_at", None)
st.session_state.setdefault("draft_variant", "classic")
st.session_state.setdefault("rank_game_mode", "friend")
st.session_state.setdefault("mode_selector", "Freund-Modus" if st.session_state.game_mode == "friend" else "Einzelspieler vs. KI")
st.session_state.setdefault("rank_mode_selector", "Freund-Modus" if st.session_state.rank_game_mode == "friend" else "Einzelspieler vs. KI")
st.session_state.setdefault("name_input_a", "Spieler 1")
st.session_state.setdefault("name_input_b", "Spieler 2")
st.session_state.setdefault("live_bounties", {})
st.session_state.setdefault("bounty_data_updated", None)
st.session_state.setdefault("bounty_data_message", None)
st.session_state.setdefault("portrait_status", {})
if "portrait_link_overrides" not in st.session_state:
    st.session_state["portrait_link_overrides"] = load_portrait_link_overrides()
st.session_state.setdefault("show_roster_browser", False)
st.session_state.setdefault("classic_match_history", [])
st.session_state.setdefault("classic_next_start_player", "A")
st.session_state.setdefault("rank_match_history", [])
st.session_state.setdefault("rank_next_start_player", "A")
st.session_state.setdefault("confirm_clear_classic_history", False)
st.session_state.setdefault("confirm_clear_rank_history", False)
restore_persistent_game_state()
migrate_saved_character_pool()
init_game()
rank_init_game()
if st.session_state.get("draft_variant", "classic") == "ranking":
    rank_process_ai_automatic_actions()
else:
    process_ai_automatic_actions()
players = st.session_state.players
num_sold = len(st.session_state.history)
remaining_count = len(st.session_state.remaining)

# ---- Sidebar ---------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="eyebrow">GRAND LINE DRAFT</div>', unsafe_allow_html=True)
    st.markdown("### 🏴‍☠️ Spielmenü")
    st.markdown("Zwei Crews. Ein Lostopf. Fünf Plätze pro Team.")
    st.divider()
    with st.expander("Spielumgebung, Lobby & Spielernamen", expanded=True):
        mode_labels = {"Lokal · 2 Spieler": "friend", "Gegen KI": "single", "Online · Lobby": "online"}
        current_mode_value = st.session_state.get("rank_game_mode", "friend") if st.session_state.get("draft_variant", "classic") == "ranking" else st.session_state.get("game_mode", "friend")
        current_label = next((label for label, value in mode_labels.items() if value == current_mode_value), "Lokal · 2 Spieler")
        st.session_state.setdefault("play_environment_selector", current_label)
        st.radio("Spielumgebung", options=list(mode_labels), key="play_environment_selector")
        selected_mode = mode_labels[st.session_state.play_environment_selector]
        st.text_input("Dein Name / Spieler A", key="name_input_a", max_chars=24)
        if selected_mode == "friend":
            st.text_input("Spieler B", key="name_input_b", max_chars=24)
        elif selected_mode == "single":
            st.text_input("Gegner", value="Grand Line KI", disabled=True, key="ai_name_disabled")
        else:
            st.caption("Spieler B tritt über einen 8-stelligen Raumcode bei.")
        if st.button("Spielumgebung & Namen übernehmen", use_container_width=True, type="primary"):
            if st.session_state.get("online_room_code") and selected_mode != "online":
                st.session_state.online_room_code = None; st.session_state.online_role = None
            st.session_state.game_mode = selected_mode
            st.session_state.rank_game_mode = selected_mode
            reset_game(); rank_reset_game()
            persist_game_state(); st.rerun()
        current_mode = st.session_state.get("rank_game_mode", "friend") if st.session_state.get("draft_variant", "classic") == "ranking" else st.session_state.get("game_mode", "friend")
        st.button("⇄ Spieleridentitäten tauschen", key="swap_player_identities", on_click=swap_active_player_identities, disabled=current_mode in {"single", "online"}, use_container_width=True, help="Namen und Teams bleiben zusammen. Im KI- und Online-Modus deaktiviert.")
        if selected_mode == "online" or current_mode == "online":
            if not supabase_config():
                st.warning("Online-Lobbys benötigen eine einmalige Supabase-Konfiguration. Offline und gegen KI funktioniert die App ohne Einrichtung.")
                st.caption("Siehe ONLINE_SETUP.md und .streamlit/secrets.toml.example im Projektordner.")
            else:
                if st.button("🌐 Online-Raum erstellen", key="online_create_room_button", use_container_width=True, type="primary"):
                    ok, msg = online_create_room(st.session_state.get("draft_variant", "classic"))
                    (st.success if ok else st.error)(msg)
                    if ok: st.rerun()
                st.text_input("Raumcode beitreten", key="online_join_code", max_chars=8, placeholder="A1B2C3D4")
                if st.button("Online-Raum beitreten", key="online_join_room_button", use_container_width=True):
                    ok, msg = online_join_room(st.session_state.get("online_join_code", ""), st.session_state.get("name_input_a", "Spieler B"))
                    (st.success if ok else st.error)(msg)
                    if ok: st.rerun()
                if st.session_state.get("online_room_code"):
                    st.success(f"Verbunden: Raum {st.session_state.online_room_code} · Spieler {st.session_state.get('online_role','?')}")
                    render_online_poll_fragment()
                    if st.button("↻ Neueste Online-Version laden", key="online_force_pull_button", use_container_width=True, help="Überschreibt nicht synchronisierte lokale Änderungen mit dem letzten gemeinsamen Raumstand."):
                        ok, msg = online_force_pull()
                        (st.success if ok else st.warning)(msg)
                        if ok: st.rerun()
        st.caption("Die ausgewählte Spielumgebung gilt für Classic Draft und Fivefold Ranking. Die beiden Draft-Spielmodi bleiben getrennt gespeichert.")
    st.divider()
    st.markdown("**Aktuelle Regeln**")
    if st.session_state.get("draft_variant", "classic") == "ranking":
        st.markdown(f"- Startbudget: **{START_BUDGET} € je Spieler**\n- Kategorien: **5 pro Spieler, jede genau einmal**\n- Rückgaben: **max. {MAX_RETURNS} × je 1 € Strafe**\n- Mittelwert: **5 Kategorien mit je 20 % Gewicht**")
        st.caption("Es bleibt die klassische Auktion: Der Zuschlagspreis wird vom Budget abgezogen. Rückgaben erstatten den Kaufpreis nicht.")
    else:
        st.markdown(f"- Startbudget: **{START_BUDGET} € je Spieler**\n- Teamgröße: **{TEAM_SIZE} Charaktere**\n- Alle Teamplätze sind gleichwertig\n- Rückgaben: **max. {MAX_RETURNS} × je 1 € Strafe**")
        st.caption("Gebote halten mindestens 1 € für jeden offenen Teamplatz zurück. Rückgaben erstatten nicht den Kaufpreis.")
    st.divider()
    # The single end-of-run save below handles persistence once; do not hash/sync twice.
    export_data = current_game_state()
    st.download_button("⬇ Vollständigen Spielstand exportieren", data=json.dumps(export_data, ensure_ascii=False, indent=2), file_name="grand_line_draft_5_0_3_spielstand.json", mime="application/json", use_container_width=True)
    if st.button("📦 Komplett-Backup erzeugen", key="create_portable_backup", use_container_width=True, help="Packt App, Bewertungsdaten, aktuellen Spielstand und bereits lokal gespeicherte Charakterporträts in eine ZIP-Datei."):
        st.session_state["backup_bundle_bytes"] = make_portable_backup()
        st.session_state["backup_bundle_created_at"] = datetime.now().astimezone().strftime("%d.%m.%Y %H:%M")
        st.success("Backup erstellt. Du kannst es jetzt herunterladen.")
    if st.session_state.get("backup_bundle_bytes"):
        st.download_button("⬇ Komplett-Backup herunterladen", data=st.session_state["backup_bundle_bytes"], file_name="GrandLineDraft_3_6_Backup.zip", mime="application/zip", use_container_width=True, key=f"download_portable_backup_{st.session_state.get('backup_bundle_created_at', 'saved')}")
        st.caption(f"Backup erzeugt: {st.session_state.get('backup_bundle_created_at', 'Zeitpunkt unbekannt')}. Nach weiteren Spielzügen vor dem Download ein neues Backup erzeugen.")
    with st.expander("📂 Spielstand laden / wiederherstellen", expanded=False):
        uploaded_save = st.file_uploader("Grand Line Draft 3.5/3.6/5.0-Spielstand (JSON)", type=["json"], key="import_game_state_file")
        if uploaded_save is not None and st.button("Spielstand laden und fortsetzen", key="import_game_state_button", use_container_width=True, type="primary"):
            try:
                payload = json.loads(uploaded_save.getvalue().decode("utf-8"))
                ok, message = import_game_state(payload)
                if ok:
                    st.success(message)
                    persist_game_state(); st.rerun()
                else:
                    st.error(message)
            except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
                st.error("Die Datei ist keine gültige JSON-Spielstanddatei.")
        st.caption("Die automatische Speicherung läuft lokal im Ordner saves/autosave.json. Das ZIP-Backup sichert zusätzlich die Charakterbilder aus portraits/.")
    if st.button("↻ Neues Spiel", use_container_width=True, type="secondary"):
        if st.session_state.get("draft_variant", "classic") == "ranking":
            rank_reset_game()
        else:
            reset_game()
        persist_game_state(); st.rerun()
    st.divider()
    with st.expander("🖼 Eigene Charakterbilder hinzufügen / ersetzen", expanded=False):
        characters_for_portraits = get_characters()
        selected_portrait_name = st.selectbox(
            "Für welchen Charakter?",
            options=[ch["name"] for ch in characters_for_portraits],
            key="manual_portrait_character_select",
        )
        selected_portrait_character = next(ch for ch in characters_for_portraits if ch["name"] == selected_portrait_name)
        selected_manual_path = manual_portrait_path(selected_portrait_character)
        selected_linked_path = linked_portrait_path(selected_portrait_character)
        selected_cached_path = portrait_path(selected_portrait_character)
        portrait_links = st.session_state.get("portrait_link_overrides", {})
        selected_link_meta = portrait_links.get(str(selected_portrait_character["id"]), {}) if isinstance(portrait_links, dict) else {}

        st.image(character_portrait(selected_portrait_character), caption=f"Aktives Charakterbild · {selected_portrait_name}", use_container_width=True)
        if selected_link_meta.get("url") and selected_linked_path.exists():
            st.success("Aktiv: eigenes Bild aus einem Link. Die Bilddatei ist lokal gespeichert; die URL wird für die Verwaltung gemerkt.")
            st.caption(f"Quelle: {selected_link_meta['url']}")
        elif selected_manual_path.exists():
            st.success("Aktiv: manuell hochgeladenes Bild.")
        elif selected_cached_path.exists():
            st.caption("Aktiv: vorhandenes lokales Porträt. Ein neues Bild per Link oder Upload ersetzt es für diesen Charakter.")
        else:
            st.info("Für diesen Charakter ist noch kein echtes Bild lokal gespeichert.")

        st.markdown("**Bild direkt per Link einfügen oder ersetzen**")
        image_url = st.text_input(
            "Direkter Bildlink (JPG, PNG oder WEBP)",
            value=str(selected_link_meta.get("url", "")),
            key=f"portrait_url_{int(selected_portrait_character['id'])}",
            placeholder="https://…/charakterbild.jpg",
            help="Bitte eine direkte öffentliche Bilddatei verlinken, nicht nur die Wiki-Seite. Das Bild wird einmal heruntergeladen und lokal gespeichert.",
        )
        if st.button("🌐 Bild aus Link laden und als Charakterbild speichern", key=f"save_portrait_url_{int(selected_portrait_character['id'])}", use_container_width=True, type="primary"):
            with st.spinner("Bildlink wird geprüft und lokal gespeichert …"):
                ok, message = install_portrait_from_url(selected_portrait_character, image_url)
            if ok:
                try:
                    uploaded_count, upload_errors = upload_cloud_portraits([{
                        "id": int(selected_portrait_character["id"]), "name": selected_portrait_name,
                        "bytes": selected_linked_path.read_bytes(), "source": "direct_link",
                    }])
                    if uploaded_count:
                        st.success("Bild lokal gespeichert und in Supabase Storage synchronisiert. Es ist jetzt auf allen Geräten verfügbar.")
                    elif upload_errors:
                        st.warning("Bild lokal gespeichert, Cloud-Synchronisierung noch nicht möglich: " + upload_errors[0])
                    else:
                        st.success(message)
                except OSError:
                    st.warning("Bild lokal gespeichert; die Datei konnte für den Cloud-Upload nicht erneut gelesen werden.")
                st.image(str(selected_linked_path), caption=f"Neues Bild gespeichert · {selected_portrait_name}", use_container_width=True)
            else:
                st.error(message)

        st.divider()
        st.markdown("**Oder eine Bilddatei hochladen**")
        uploaded_portrait = st.file_uploader(
            "Bilddatei auswählen (PNG, JPG oder WEBP)",
            type=["png", "jpg", "jpeg", "webp"],
            key=f"manual_portrait_upload_{int(selected_portrait_character['id'])}",
            help="Das Bild bleibt lokal in portraits/ gespeichert. Empfohlen: klares Porträt, mindestens 250 × 300 Pixel.",
        )
        if uploaded_portrait is not None:
            st.image(uploaded_portrait, caption="Vorschau des ausgewählten Bildes", use_container_width=True)
            if st.button("Eigenes Upload-Bild speichern und verwenden", key=f"save_manual_portrait_{int(selected_portrait_character['id'])}", use_container_width=True, type="secondary"):
                normalized_image = image_as_jpeg(uploaded_portrait.getvalue())
                if normalized_image is None:
                    st.error("Das Bild konnte nicht gelesen werden oder ist kleiner als 80 × 80 Pixel. Bitte wähle ein anderes Bild.")
                else:
                    try:
                        PORTRAIT_DIR.mkdir(parents=True, exist_ok=True)
                        temp_path = selected_manual_path.with_suffix(".tmp")
                        temp_path.write_bytes(normalized_image)
                        temp_path.replace(selected_manual_path)
                        selected_linked_path.unlink(missing_ok=True)
                        portrait_links.pop(str(selected_portrait_character["id"]), None)
                        save_portrait_link_overrides(portrait_links)
                        st.session_state["portrait_link_overrides"] = portrait_links
                        st.session_state.setdefault("portrait_status", {})[selected_portrait_name] = "Eigenes Bild · manuell hinzugefügt"
                        _cached_portrait_bytes.clear()
                        uploaded_count, upload_errors = upload_cloud_portraits([{
                            "id": int(selected_portrait_character["id"]), "name": selected_portrait_name,
                            "bytes": normalized_image, "source": "manual_upload",
                        }])
                        if uploaded_count:
                            st.success(f"Eigenes Porträt für {selected_portrait_name} gespeichert und mit allen Geräten synchronisiert.")
                        elif upload_errors:
                            st.warning(f"Lokal gespeichert, Cloud-Upload noch nicht möglich: {upload_errors[0]}")
                        else:
                            st.success(f"Eigenes Porträt für {selected_portrait_name} lokal gespeichert.")
                        persist_game_state(); st.rerun()
                    except OSError as exc:
                        st.error(f"Das Bild konnte nicht gespeichert werden: {exc}")

        if selected_manual_path.exists() or selected_linked_path.exists():
            if st.button("Eigenes Bild entfernen", key=f"remove_custom_portrait_{int(selected_portrait_character['id'])}", use_container_width=True):
                try:
                    selected_manual_path.unlink(missing_ok=True)
                    selected_linked_path.unlink(missing_ok=True)
                    portrait_links.pop(str(selected_portrait_character["id"]), None)
                    save_portrait_link_overrides(portrait_links)
                    st.session_state["portrait_link_overrides"] = portrait_links
                    st.session_state.setdefault("portrait_status", {}).pop(selected_portrait_name, None)
                    _cached_portrait_bytes.clear()
                    cloud_ok, cloud_message = delete_cloud_portrait(int(selected_portrait_character["id"]))
                    st.success("Eigenes Bild lokal entfernt. " + (cloud_message if cloud_ok else "Cloud-Hinweis: " + cloud_message))
                    persist_game_state(); st.rerun()
                except OSError as exc:
                    st.error(f"Das eigene Bild konnte nicht entfernt werden: {exc}")
        st.caption("Bilder über Links werden lokal zwischengespeichert und – sobald cloud_portraits_schema.sql eingerichtet ist – automatisch zu Supabase Storage hochgeladen.")

    with st.expander("☁️ Gemeinsame Cloud-Bilderdatenbank · Supabase Storage", expanded=False):
        st.write("Eigene Porträts werden zentral gespeichert und anschließend auf allen Geräten angezeigt. Der Bucket bleibt privat; Downloads laufen serverseitig über die Streamlit-Secrets.")
        if not supabase_config():
            st.warning("Supabase ist nicht konfiguriert. Die lokalen Bilder bleiben unverändert.")
        else:
            schema_ok, schema_message = cloud_portrait_schema_ready()
            if schema_ok:
                st.success(schema_message)
                try:
                    config = supabase_config()
                    cloud_index = _cloud_portrait_index(config["url"], config["key"])
                    st.metric("Bilder in der Cloud", len(cloud_index))
                except Exception:
                    st.caption("Die Bildübersicht konnte gerade nicht geladen werden.")
            else:
                st.warning(schema_message)
                st.caption("Führe zuerst die neue Datei cloud_portraits_schema.sql im Supabase SQL Editor aus.")
            st.markdown("**Vorhandene Bilder von deinem PC importieren**")
            st.caption("Packe auf deinem PC den Inhalt des Ordners `portraits` als ZIP und lade das Archiv hier hoch. Die Dateien werden anhand ihrer Charakter-ID zugeordnet; es wird nichts unsicher in den Serverordner entpackt.")
            cloud_archive = st.file_uploader("Lokales portraits-Archiv (.zip)", type=["zip"], key="cloud_portrait_archive_upload")
            if cloud_archive is not None and st.button("📤 Bilderarchiv in die Cloud übertragen", key="cloud_portrait_archive_import", type="primary", use_container_width=True, disabled=not schema_ok):
                with st.spinner("Bilder werden geprüft, optimiert und zu Supabase Storage übertragen …"):
                    import_items, import_warnings = portrait_archive_items(cloud_archive.getvalue())
                    uploaded_count, upload_errors = upload_cloud_portraits(import_items)
                if uploaded_count:
                    st.success(f"{uploaded_count} Charakterbilder erfolgreich in Supabase Storage gespeichert.")
                if import_warnings:
                    st.warning(" · ".join(import_warnings[:12]))
                if upload_errors:
                    st.error(" · ".join(upload_errors[:8]))
                if uploaded_count:
                    st.rerun()
                if not import_items:
                    st.info("Im ZIP wurden keine passenden Charakterbilder gefunden. Erwartet werden z. B. manual_character_001.jpg, linked_character_001.jpg oder character_001_<hash>.jpg im portraits-Ordner.")
            if st.button("☁️ Bilder aus dem aktuellen Serverordner synchronisieren", key="cloud_portrait_local_sync", use_container_width=True, disabled=not schema_ok):
                local_items = local_portrait_items()
                with st.spinner(f"{len(local_items)} lokale Porträts werden übertragen …"):
                    uploaded_count, upload_errors = upload_cloud_portraits(local_items)
                if uploaded_count:
                    st.success(f"{uploaded_count} lokale Bilder wurden in die Cloud übertragen.")
                    st.rerun()
                elif not local_items:
                    st.info("Im aktuellen Serverordner portraits/ wurden keine echten Bilddateien gefunden. Lade stattdessen ein ZIP von deinem PC hoch.")
                if upload_errors:
                    st.error(" · ".join(upload_errors[:8]))
            st.caption("Hinweis: In der Cloud-App sieht der Server nur Dateien, die im GitHub-Repository enthalten sind oder über dieses Upload-Feld importiert wurden. Lokale Bilder auf deinem PC müssen daher einmal als ZIP hochgeladen werden.")

    st.divider()
    if st.button("🖼 Alle 135 Bildquellen prüfen & Porträts lokal speichern", use_container_width=True, help="Prüft die exakten Wiki-Seiten, lädt erreichbare echte Porträts und speichert sie lokal. Kann je nach Verbindung eine Weile dauern."):
        bar = st.progress(0, text="Bildquellen werden geprüft …")
        def update_portrait_progress(fraction):
            bar.progress(min(1.0, max(0.0, fraction)), text=f"Bildquellen geprüft: {round(fraction * len(get_characters()))}/{len(get_characters())} …")
        with st.spinner("Bis zu 135 Charakterporträts werden geprüft und lokal gespeichert. Bitte das Fenster offen lassen."):
            results = audit_all_portraits(update_portrait_progress)
        real = sum(1 for value in results.values() if not value.startswith("Kein echtes Bild") and "fehlgeschlagen" not in value)
        missing = [name for name, value in results.items() if value.startswith("Kein echtes Bild") or "fehlgeschlagen" in value]
        bar.progress(1.0, text="Bildprüfung abgeschlossen")
        st.success(f"{real}/{len(results)} echte Porträts lokal vorhanden oder gespeichert.")
        if missing:
            with st.expander(f"{len(missing)} Figuren ohne bestätigtes Online-Porträt"):
                st.write(", ".join(missing))
        else:
            st.caption("Alle Figuren haben ein echtes Porträt lokal im Ordner portraits/.")
    if st.session_state.get("portrait_status"):
        status_vals = list(st.session_state.portrait_status.values())
        real_count = sum(1 for v in status_vals if not str(v).startswith("Ersatzporträt"))
        st.caption(f"Bildstatus letzter Lauf: {real_count} Einträge mit echter Quelle / lokalem Cache.")
    if st.button("🌐 Kopfgeld-Daten online aktualisieren", use_container_width=True, help="Ruft öffentliche Kopfgelddaten nur bei Klick ab."):
        fetch_live_bounty_data.clear()
        with st.spinner("Öffentliche Kopfgelddaten werden abgerufen …"):
            values, message = fetch_live_bounty_data()
        st.session_state.live_bounties = values
        st.session_state.bounty_data_updated = message if values else None
        st.session_state.bounty_data_message = message
    if st.session_state.bounty_data_updated:
        st.caption(f"Kopfgeld-Daten zuletzt aktualisiert: {st.session_state.bounty_data_updated}. {len(st.session_state.live_bounties)} API-Einträge geladen.")
    elif st.session_state.bounty_data_message:
        st.caption(st.session_state.bounty_data_message)
    else:
        st.caption("Online-Datenabruf startet nur nach Klick. Die Bewertung läuft ansonsten lokal.")

# ---- Hero ------------------------------------------------------------------
hero_left, hero_right = st.columns([4, 1])
with hero_left:
    st.markdown("""<div class="brand-row"><div class="hero-mark">☠</div><div><div class="eyebrow">THE PIRATE AUCTION GAME</div><h1>GRAND LINE <span class="gold">DRAFT</span></h1><div class="hero-sub">VERSION 5.0.3 · PERFORMANCE EDITION · MANGA-STAND KAPITEL 1197 &nbsp;·&nbsp; Stelle deine Crew zusammen. Überbiete deinen Rivalen. Werde König der Auktion.</div></div></div>""", unsafe_allow_html=True)
with hero_right:
    active_ai_mode = rank_is_ai_mode() if st.session_state.get("draft_variant", "classic") == "ranking" else is_ai_mode()
    current_mode_for_badge = st.session_state.get("rank_game_mode", "friend") if st.session_state.get("draft_variant", "classic") == "ranking" else st.session_state.get("game_mode", "friend")
    mode_label = "VS KI" if active_ai_mode else ("VS ONLINE" if current_mode_for_badge == "online" else "VS FRIEND")
    environment_badge = "ONLINE LOBBY" if current_mode_for_badge == "online" else ("AI MATCH" if active_ai_mode else "LOCAL PASS & PLAY")
    st.markdown(f'<div style="text-align:right;padding-top:13px"><div class="brand-mini">ONE PIECE</div><div style="font-family:Barlow Condensed,sans-serif;font-size:1.15rem;font-weight:900;color:#e8bd64;letter-spacing:.15em">{mode_label}</div><div class="small-muted">{environment_badge}</div></div>', unsafe_allow_html=True)
st.markdown('<div class="eyebrow" style="margin-top:20px">SPIELMODUS WÄHLEN</div>', unsafe_allow_html=True)
mode_a, mode_b = st.columns(2, gap="medium")
with mode_a:
    st.markdown('<div class="team-total-card"><div class="panel-label">MODUS 01</div><h3>Klassischer Grand Line Draft</h3><div class="small-muted">Das ursprüngliche Auktionsspiel mit fünf Charakteren pro Team, Bieten und Kampfsimulation.</div></div>', unsafe_allow_html=True)
    if st.button("Klassischen Draft spielen" + (" · AKTIV" if st.session_state.draft_variant == "classic" else ""), key="choose_classic_mode", type="primary" if st.session_state.draft_variant == "classic" else "secondary", use_container_width=True):
        st.session_state.draft_variant = "classic"
        persist_game_state(); st.rerun()
with mode_b:
    st.markdown('<div class="team-total-card"><div class="panel-label">MODUS 02</div><h3>Fivefold Ranking</h3><div class="small-muted">Fünf Disziplinen, freie Platzwahl, 20 € Auktionsbudget und Durchschnittswertung mit Gewinnprognose.</div></div>', unsafe_allow_html=True)
    if st.button("Fivefold Ranking spielen" + (" · AKTIV" if st.session_state.draft_variant == "ranking" else ""), key="choose_ranking_mode", type="primary" if st.session_state.draft_variant == "ranking" else "secondary", use_container_width=True):
        st.session_state.draft_variant = "ranking"
        persist_game_state(); st.rerun()

if st.session_state.draft_variant == "ranking":
    rank_render_mode()
    persist_game_state()
    st.markdown('<div class="footer-note">GRAND LINE DRAFT 5.0.3 · PERFORMANCE EDITION · FIVEFOLD RANKING · Fan-Modell, Manga-Stichtag Kapitel 1197.</div>', unsafe_allow_html=True)
    st.stop()

st.markdown('<div class="stat-strip">' + html_stat("Charaktere im Pool", f'<span>{remaining_count}</span> / {len(get_characters())}') + html_stat("Auktionen abgeschlossen", f'<span>{num_sold}</span>') + html_stat("Startbudget", f'<span>{money(START_BUDGET)}</span> p. P.') + html_stat("Teamgröße", '<span>5</span> Slots') + '</div>', unsafe_allow_html=True)

# ---- Main gameplay ---------------------------------------------------------
left_col, center_col, right_col = st.columns([1.02, 1.42, 1.02], gap="medium")
with left_col:
    render_player("A")
with right_col:
    render_player("B")

with center_col:
    with st.container(border=True):
        st.markdown('<div class="panel-label">DAS AUKTIONSDECK</div>', unsafe_allow_html=True)
        if st.session_state.phase == "finished":
            st.markdown('<div class="result-wrap"><div class="eyebrow">ALLE CREWS VOLLSTÄNDIG</div><h2>Die Auktion ist beendet</h2><p class="small-muted">Beide Spieler haben ihre fünf Charaktere gesammelt. Power Level, bestätigtes Haki, Fähigkeiten und Teamchemie fließen in die Gesamtbewertung ein.</p></div>', unsafe_allow_html=True)
            a = analyze_team(players["A"]["team"]); b = analyze_team(players["B"]["team"])
            st.markdown(f'<div class="round-banner"><div style="display:flex;justify-content:space-between;gap:12px"><span>{safe_text(players["A"]["name"])} investiert</span><b style="color:#e8bd64">{money(a["spent"])}</b></div><div style="display:flex;justify-content:space-between;gap:12px;margin-top:6px"><span>{safe_text(players["B"]["name"])} investiert</span><b style="color:#e8bd64">{money(b["spent"])}</b></div><div style="display:flex;justify-content:space-between;gap:12px;margin-top:6px"><span>Teamchemie</span><b>Kleiner Synergiebonus berücksichtigt</b></div></div>', unsafe_allow_html=True)
            if st.session_state.get("classic_result_recorded") is None:
                st.markdown("**Spielergebnis speichern** · Die Teamwertung zeigt eine Modellprognose; sie entscheidet nicht automatisch, wer das tatsächliche Spiel gewonnen hat.")
                result_cols = st.columns(3)
                with result_cols[0]:
                    if st.button(f"{players['A']['name']} gewinnt", key="classic_result_a", use_container_width=True):
                        record_completed_match("classic", "A")
                with result_cols[1]:
                    if st.button(f"{players['B']['name']} gewinnt", key="classic_result_b", use_container_width=True):
                        record_completed_match("classic", "B")
                with result_cols[2]:
                    if st.button("Unentschieden", key="classic_result_tie", use_container_width=True):
                        record_completed_match("classic", "tie")
            else:
                outcome = st.session_state.classic_result_recorded
                result_label = "Unentschieden" if outcome == "tie" else f"{players[outcome]['name']} als Sieger gespeichert"
                st.success(f"Ergebnis gespeichert: {result_label}.")
                st.caption(f"Nächster Startspieler: {players[st.session_state.get('classic_next_start_player', 'A')]['name']} · Bei Unentschieden bleibt der bisherige Startspieler erhalten.")
                if st.button("Neue Runde starten", key="new_round_finished", type="primary", use_container_width=True):
                    reset_game(); persist_game_state(); st.rerun()

        elif st.session_state.phase == "ready":
            spinner = active_spinner()
            st.markdown(f'<div class="round-banner"><span class="status-dot"></span><b>Runde {st.session_state.round_no + 1}</b><span class="small-muted"> · </span><span class="small-muted">{safe_text(players[spinner]["name"])} dreht das Rad</span></div>', unsafe_allow_html=True)
            st.markdown("""<div class="wheel-shell"><div class="wheel-pointer">▼</div><div class="wheel"><div class="wheel-hub">☠</div></div><div class="wheel-caption">WER KOMMT AN BORD?</div><div class="small-muted" style="margin-top:5px">Jedes Los zählt gleich</div></div>""", unsafe_allow_html=True)
            pool_size = len(st.session_state.remaining)
            if pool_size:
                st.markdown(f"<div class='analysis-note' style='text-align:center;margin:4px 0 10px'><b>Faire Ziehung:</b> Jede der {pool_size} Figuren im Lostopf hat exakt die gleiche Chance von <b>{100 / pool_size:.2f}%</b> (1/{pool_size}). Bereits versteigerte Figuren sind nicht im Lostopf.</div>", unsafe_allow_html=True)
            if is_ai_player(spinner):
                st.info("Die KI zieht automatisch …")
                if pool_size:
                    draw_character()
            elif st.button("🎡  AM RAD DREHEN", key="spin_wheel", type="primary", use_container_width=True, disabled=(not st.session_state.remaining or not online_can_control(spinner, "classic"))):
                draw_character()
            st.markdown('<div class="small-muted" style="text-align:center;margin-top:6px">Gleichverteilte Ziehung · die Animation beeinflusst nicht das Los.</div>', unsafe_allow_html=True)
            if st.session_state.last_winner:
                last = st.session_state.last_winner
                st.markdown(f'<div style="margin-top:12px;border-top:1px solid rgba(210,226,243,.1);padding-top:11px"><div class="panel-label">LETZTER DEAL</div><b>{safe_text(last["character"])}</b><span class="small-muted"> · gewonnen von {safe_text(players[last["player"]]["name"])} für </span><span style="color:#e8bd64;font-weight:900">{money(last["price"])}</span></div>', unsafe_allow_html=True)

        elif st.session_state.phase == "spinning":
            spinner = st.session_state.spin_owner
            spin_id = st.session_state.get("classic_spin_id") or f"classic-{st.session_state.round_no + 1}"
            spin_result = FIVEFOLD_WIDGET(
                mode="wheel", variant="classic", spin_id=spin_id,
                player=players[spinner]["name"], round=st.session_state.round_no + 1,
                animation_ms=3200, broadcast_delay_ms=1200,
                start_at=st.session_state.get("classic_spin_started_at"),
                key=f"classic_wheel_{spin_id}", default=None,
            )
            if (isinstance(spin_result, dict) and spin_result.get("event") == "spin_complete"
                    and spin_result.get("spin_id") == spin_id
                    and online_can_control(spinner, "classic")):
                complete_classic_spin()

        elif st.session_state.phase == "drawn":
            ch = st.session_state.current_char
            spinner = st.session_state.spin_owner
            opponent = other(spinner)
            st.markdown(f'<div class="round-banner"><span class="status-dot"></span><b>Gezogen von {safe_text(players[spinner]["name"])}</b><span class="small-muted"> · Auktion #{st.session_state.round_no}</span></div>', unsafe_allow_html=True)
            st.image(character_portrait(ch), use_container_width=True)
            render_character_analysis(ch)
            cap = max_bid(spinner)
            opening_options = list(range(MIN_PRICE, cap + 1))
            if not opening_options:
                st.error(f'{players[spinner]["name"]} hat kein verfügbares Budget für einen weiteren Charakter.')
            elif is_ai_player(spinner):
                # Normally auto-started before render; defensive fallback.
                begin_auction(min(cap, max(1, int(round(character_profile(ch)["score"] / 32)))))
            else:
                default_open = min(2, max(opening_options))
                open_price = st.select_slider("Startgebot festlegen", options=opening_options, value=default_open, format_func=lambda x: money(x), key=f"opening_bid_{st.session_state.game_seed}_{st.session_state.round_no}")
                st.caption(f"Gebotsrahmen {players[spinner]['name']}: bis {money(cap)}. Mindestens 1 € bleibt für jeden weiteren Teamplatz reserviert.")
                if st.button("⚓  AUKTION ERÖFFNEN" if team_slots(opponent) > 0 else f"Für {money(open_price)} verpflichten", key=f"start_auction_{st.session_state.game_seed}_{st.session_state.round_no}", type="primary", use_container_width=True, disabled=not online_can_control(spinner, "classic")):
                    begin_auction(int(open_price))
                if can_return_card(spinner, current_draw=True):
                    st.caption(f"Rückgabe-Regel: Noch {MAX_RETURNS - st.session_state.returns_used[spinner]} von {MAX_RETURNS} Rückgaben · Strafe {money(RETURN_PENALTY)}.")
                    if st.button("↩ Gezogene Karte zurück in den Lostopf · 1 € Strafe", key=f"return_draw_{st.session_state.game_seed}_{st.session_state.round_no}", use_container_width=True, disabled=not online_can_control(spinner, "classic")):
                        returned = st.session_state.current_char
                        if returned and apply_return(spinner, returned, "gezogene Karte"):
                            st.session_state.current_char = None
                            st.session_state.phase = "ready"
                            st.session_state.next_spinner = other(spinner)
                            persist_game_state(); st.rerun()

        elif st.session_state.phase == "auction":
            auction = st.session_state.auction
            ch = auction["character"]
            turn = auction["current_turn"]
            highest = auction["highest_bidder"]
            bid = auction["current_bid"]
            st.markdown(f'<div class="round-banner"><span class="status-dot"></span><b>AUKTION LÄUFT</b><span class="small-muted"> · Runde {st.session_state.round_no}</span></div>', unsafe_allow_html=True)
            st.image(character_portrait(ch), use_container_width=True)
            render_character_analysis(ch)
            st.markdown(f'<div style="text-align:center;margin:13px 0 6px"><div class="panel-label">AKTUELLES HÖCHSTGEBOT</div><div class="auction-price">{money(bid)}</div><div class="auction-turn">Höchstbietend: <b>{safe_text(players[highest]["name"])}</b></div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="winner-row" style="color:#e5edf6;background:rgba(232,189,100,.06);border-color:rgba(232,189,100,.2)">Jetzt dran: <b>{safe_text(players[turn]["name"])}</b></div>', unsafe_allow_html=True)
            if is_ai_player(turn):
                st.info("Die KI prüft Kampfkraft, Budget und Teamchemie und antwortet automatisch …")
            else:
                max_for_turn = max_bid(turn)
                next_options = list(range(bid + 1, max_for_turn + 1)) if team_slots(turn) > 0 else []
                if next_options:
                    next_bid = st.select_slider("Dein nächstes Gebot", options=next_options, value=min(bid + 1, max(next_options)), format_func=lambda x: money(x), key=f"bid_{st.session_state.game_seed}_{st.session_state.round_no}_{turn}_{bid}")
                    st.caption(f"Dein Maximalgebot unter Berücksichtigung freier Teamplätze: {money(max_for_turn)}")
                    if st.button(f"💰  AUF {money(next_bid)} ERHÖHEN", key=f"raise_{st.session_state.game_seed}_{st.session_state.round_no}_{turn}_{bid}", type="primary", use_container_width=True, disabled=not online_can_control(turn, "classic")):
                        auction["current_bid"] = int(next_bid)
                        auction["highest_bidder"] = turn
                        auction["current_turn"] = other(turn)
                        st.session_state.auction = auction
                        persist_game_state(); st.rerun()
                else:
                    st.info("Du kannst das aktuelle Gebot nicht überbieten, ohne dein Mindestbudget zu gefährden.")
                if st.button("✋  PASSEN · HÖCHSTBIETENDER GEWINNT", key=f"pass_{st.session_state.game_seed}_{st.session_state.round_no}_{turn}_{bid}", use_container_width=True, disabled=not online_can_control(turn, "classic")):
                    settle_auction(highest, bid)
            st.markdown(f'<div class="small-muted" style="margin-top:8px">{safe_text(players[highest]["name"])} liegt vorne. Sobald der andere passt, bekommt der Höchstbietende die Figur.</div>', unsafe_allow_html=True)

# ---- Crew analysis ---------------------------------------------------------
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
with st.container(border=True):
    st.markdown('<div class="panel-label">POWER LEVEL · PRIME-FORMEN & MATCHMAKING</div><h2>Die Team-Bewertung</h2>', unsafe_allow_html=True)
    st.markdown('<div class="analysis-note">Stand: Manga-Kapitel 1197 (01.11.2026); alle Figuren in ihrer stärksten belegten Peak-/Prime-Form. Teamwertung: Power Level 68 %, bestätigtes Haki 14 %, Fähigkeiten/Nutzwert 14 % und Vielseitigkeit 4 %. Einzelduelle nutzen die importierte Power Matrix v5.0 mit 15.000 vorab berechnete Ergebnisziehungen je Paarung; Angriff, Defensive, Tempo, Ausdauer und Kampftaktik sind Teil der Ausgangsprofile. Der Haki-Wert wird ausschließlich aus den Teammitgliedern mit bestätigter Haki-Anwendung gemittelt. Nicht bestätigte/unklare Haki-Daten werden nicht als 0 gewertet und nicht in den Nenner aufgenommen. Wenn für keinen Charakter Haki bestätigt ist, entfällt der Haki-Faktor und die übrigen Gewichte werden proportional normalisiert. Intelligenz ist nur ein kleiner Bonus bis +0,45 Punkte; Teamchemie kann bis zu ±2 Punkte beitragen. Alle Teamplätze sind gleichwertig; es gibt keinen Kapitäns- oder Vizekapitänsbonus. Kopfgeld und Status bestimmen nie direkt die Gesamtwertung.</div>', unsafe_allow_html=True)
    team_a = analyze_team(st.session_state.players["A"]["team"])
    team_b = analyze_team(st.session_state.players["B"]["team"])
    if not team_a["profiles"] and not team_b["profiles"]:
        st.info("Die Analyse erscheint, sobald Charaktere ersteigert wurden.")
    else:
        eval_cols = st.columns(2, gap="medium")
        for col, key, info in [(eval_cols[0], "A", team_a), (eval_cols[1], "B", team_b)]:
            with col:
                name = players[key]["name"]
                st.markdown(f'<div class="player-heading"><div class="player-name">{safe_text(name.upper())}</div><div class="player-tag">{len(info["profiles"])}/{TEAM_SIZE} FIGUREN</div></div>', unsafe_allow_html=True)
                if info["score"] is None:
                    st.markdown('<div class="small-muted">Noch keine Figuren im Team.</div>', unsafe_allow_html=True)
                    continue
                st.markdown(
                    f'<div class="team-total-card"><div class="team-total-label">GESAMTPUNKTZAHL · AKTUELLER KADER</div>'
                    f'<div class="team-total-value">{info["score"]:.1f}<span>/ 100 PUNKTE</span></div>'
                    f'<div class="team-total-meta">Power Level + bestätigtes Haki + Fähigkeiten + Vielseitigkeit + kleine Intelligenz- und Teamchemie-Anpassung</div></div>',
                    unsafe_allow_html=True,
                )
                mc_top = st.columns(2, gap="medium")
                mc_bottom = st.columns(2, gap="medium")
                mc_top[0].metric("Ø Power Level", f'{info["avg_power"]:.1f} / 100')
                if info["haki_avg"] is not None:
                    mc_top[1].metric("Ø Haki (bestätigt)", f'{info["haki_avg"]:.1f} / 100', help=f'{info["haki_count"]} von {len(info["profiles"])} Charakteren berücksichtigt; unbestätigte Haki-Daten zählen nicht als 0.')
                else:
                    mc_top[1].metric("Ø Haki (bestätigt)", "Keine Daten", help="Für kein Teammitglied ist Haki ausreichend bestätigt; Haki wird für dieses Team ausgelassen und nicht als 0 gewertet.")
                mc_bottom[0].metric("Ø Fähigkeiten", f'{info["avg_abilities"]:.1f} / 100')
                mc_bottom[1].metric("Teamchemie", f'{info["chemistry"]:.1f} / 100')
                with st.expander("Bewertung im Detail · Haki-Durchschnitt & Punktebeiträge", expanded=False):
                    st.markdown("**Die Gesamtwertung ist ein Fan-Modell, keine offizielle One-Piece-Zahl. Unbekannte Haki-Werte werden nicht als 0 gewertet.**")
                    if info["haki_avg"] is not None:
                        st.success(f'Haki: {info["haki_count"]} von {len(info["profiles"])} Charakteren einbezogen. Der Haki-Durchschnitt von {info["haki_avg"]:.1f}/100 wird mit vollen 14 % gewichtet. Ausgeschlossen (nicht bestätigt/unklar): {info["haki_unknown_count"]}.')
                        st.caption("Einbezogen: " + ", ".join(info["haki_names"]))
                    else:
                        st.info("Für kein Teammitglied liegt eine bestätigte Haki-Bewertung vor. Der Haki-Faktor wird ausgelassen; die übrigen Gewichte werden proportional angepasst, damit fehlende Daten keinen Nachteil erzeugen.")
                    parts = info.get("weighted_contributions", {})
                    team_weights = info.get("effective_weights", {})
                    breakdown_rows = [
                        ("Power Level", info["avg_power"], team_weights.get("power", 0), parts.get("power", 0), "Geschätzte Kampfkraft in der stärksten bekannten Prime-Form"),
                        ("Haki-Fähigkeit", info["haki_avg"], team_weights.get("haki", 0), parts.get("haki", 0), "Durchschnitt nur der Charaktere mit bestätigter Haki-Nutzung"),
                        ("Fähigkeiten / Nutzwert", info["avg_abilities"], team_weights.get("abilities", 0), parts.get("abilities", 0), "Frucht/Haki-Wirkung, Reichweite, Kontrolle, Verteidigung und Spezialnutzen"),
                        ("Vielseitigkeit", info["avg_versatility"], team_weights.get("versatility", 0), parts.get("versatility", 0), "Anpassungsfähigkeit über verschiedene Situationen und Kampfstile"),
                    ]
                    def _fmt_haki_value(value):
                        return "Nicht verfügbar" if value is None else f"{value:.1f}/100"
                    st.markdown("| Faktor | Teamdurchschnitt | Gewicht | Beitrag zur Grundwertung | Erklärung |\n|---|---:|---:|---:|---|\n" + "\n".join(
                        f"| {label} | {_fmt_haki_value(value)} | {weight*100:.1f}% | {contribution:.2f} Pkt. | {description} |"
                        for label, value, weight, contribution, description in breakdown_rows
                    ))
                    st.markdown(f"**Intelligenzbonus:** +{info['intelligence_bonus']:.2f} Punkte (kleiner Bonus; Team-Ø Intelligenz {info['avg_intelligence']:.1f}/100, maximal +0,45).  ")
                    st.markdown(f"**Teamchemie:** {info['chemistry']:.1f}/100 → **{info['chemistry_bonus']:+.2f} Punkte**. 50 ist neutral; gute Synergie gibt Bonus, schlechte Konstellationen können abziehen.  ")
                    st.markdown(f"**Ergebnis:** {info['base_score']:.2f} Grundpunkte + {info['intelligence_bonus']:.2f} Intelligenz + {info['chemistry_bonus']:+.2f} Teamchemie = **{info['score']:.1f}/100** (auf 0–100 begrenzt).")
                    st.caption("Kopfgeld und Rang bleiben Kontextinformationen auf den Karten, beeinflussen aber die Gesamtwertung nicht. Nicht bestätigtes Haki bedeutet fehlende Daten, nicht automatisch Haki=0.")
                known = info["known_bounties"]
                bounty_text = f'{info["bounty_total"]:,}'.replace(',', '.') + ' ฿' if known else "Keine Daten"
                st.caption(f"Erfasste Kopfgelder: {bounty_text} · Datenlage: {info['confidence']} · Investiert: {money(info['spent'])}")
                with st.expander(f"Einzelanalyse: {name}"):
                    for index, profile in enumerate(sorted(info["profiles"], key=lambda x: x["power"], reverse=True)):
                        chname = profile["name"]
                        original_index = next(i for i, x in enumerate(st.session_state.players[key]["team"]) if x["name"] == chname)
                        slot = role_for_slot(original_index)
                        abilities = profile.get("ability_summary", "Keine Fähigkeitenkurzinfo hinterlegt.")
                        detail_markdown = (
                            f"**{slot} — {chname}**\n\n"
                            f"Power Level: **{profile['power']}/100** · "
                            f"Haki: **{str(profile.get('haki_score')) + '/100' if profile.get('haki_score') is not None else 'nicht bestätigt (aus Haki-Schnitt ausgeschlossen)'}** · "
                            f"Fähigkeiten/Nutzwert: **{int(profile.get('abilities', 50))}/100** · "
                            f"Kopfgeld: **{bounty_label(profile.get('bounty'), profile.get('bounty_state','unbekannt'))}** · "
                            f"Datenlage: {profile['confidence']}\n\n"
                            f"**Haki-Arten:** {safe_text(', '.join(profile.get('haki_types', [])) or 'keine Art sicher bestätigt')}\n\n"
                            f"**Haki-Nachweis:** {safe_text(profile.get('haki_note', 'Nicht bestätigt.'))}\n\n"
                            f"**Fähigkeiten:** {safe_text(abilities)}\n\n"
                            f"_{profile.get('rationale','Fan-Schätzung.')}_"
                        )
                        st.markdown(detail_markdown)
                        st.divider()
        if team_a["profiles"] and team_b["profiles"] and len(team_a["profiles"]) >= 3 and len(team_b["profiles"]) >= 3:
            st.divider()
            delta = team_a["score"] - team_b["score"]
            matchups = calculate_matchmaking(st.session_state.players["A"]["team"], st.session_state.players["B"]["team"])
            if matchups:
                avg_duel_margin = sum(float(m["margin"]) for m in matchups) / len(matchups)
                blended_margin = delta * 0.35 + avg_duel_margin * 0.65
            else:
                blended_margin = delta
            p_a = max(15.0, min(85.0, 100.0 / (1.0 + math.exp(-blended_margin / 13.0))))
            p_b = 100.0 - p_a
            leader = players["A"]["name"] if p_a > 50.5 else players["B"]["name"] if p_a < 49.5 else "Unentschieden"
            st.markdown("### Gesamtpunkte aus allen erfassten Kriterien")
            score_cols = st.columns(2, gap="medium")
            for score_col, player_key, team_info in ((score_cols[0], "A", team_a), (score_cols[1], "B", team_b)):
                with score_col:
                    score_col.markdown(
                        f'<div class="team-total-card"><div class="team-total-label">{safe_text(players[player_key]["name"])} · GESAMTSCORE</div>'
                        f'<div class="team-total-value">{team_info["score"]:.1f}<span>/ 100 PUNKTE</span></div>'
                        f'<div class="team-total-meta">Umfasst Power Level, bestätigtes Haki, Fähigkeiten, Vielseitigkeit, Intelligenzbonus und Teamchemie</div></div>',
                        unsafe_allow_html=True,
                    )
            st.markdown(f'<div class="result-wrap"><div class="eyebrow">GEWINN-TENDENZ · ZUSÄTZLICH ZUM PUNKTESTAND</div><h3>{safe_text(leader if leader == "Unentschieden" else leader + " liegt nach Power Level und Kontern vorn")}</h3><div style="display:flex;justify-content:space-between;gap:12px;margin:8px 0 6px"><b>{safe_text(players["A"]["name"])}: {p_a:.0f}%</b><b>{safe_text(players["B"]["name"])}: {p_b:.0f}%</b></div></div>', unsafe_allow_html=True)
            st.progress(p_a / 100, text="Modell-Tendenz aus Teamstärke, Teamchemie und zugeordneten Einzelduellen – keine objektive Siegwahrscheinlichkeit")
            st.markdown(f'<div class="analysis-note">{safe_text(battle_text(players["A"]["name"], team_a, players["B"]["name"], team_b, matchups))}</div>', unsafe_allow_html=True)
            st.caption("Die Einzelduell-Prognosen stammen aus der beigefügten Power Matrix v5.0 (15.000 Ergebnisziehungen pro Paarung). Sie sind Modellschätzungen, keine garantierten Canon-Ergebnisse; der Matchmaker sucht möglichst ausgeglichene Paarungen.")
            st.markdown("### ⚔️ Taktisches Matchmaking · Einzelduelle")
            st.caption(f"Der Matchmaker nutzt die v5.0-Matrix für alle 9.045 eindeutigen Paarungen mit 15.000 vorab berechneten Monte-Carlo-Ergebnisziehungen je Paarung und ordnet anschließend möglichst ausgeglichene Duelle zu. Die Angaben bleiben modellierte Schätzungen, keine Canon-Garantien.")
            for duel in matchups:
                left, center, right = st.columns([1.15, 1.35, 1.15], gap="small")
                with left:
                    st.image(character_portrait(duel["a"]), use_container_width=True)
                    st.markdown(f"**{safe_text(duel['a']['name'])}**")
                    st.caption(f"{safe_text(duel['role_a'])} · Power {character_profile(duel['a'])['power']}/100")
                    st.caption(f"Modellchance: {duel['p_a']:.0f}%")
                with center:
                    duel_label = 'ENGES DUELL' if 45 < duel['p_a'] < 55 else 'SIMULIERTE TENDENZ'
                    st.markdown(f"<div class='result-wrap'><div class='eyebrow'>DUELL {duel['number']}</div><div style='font-size:1.05rem;font-weight:900;color:#e8bd64'>{duel_label}</div><div style='font-size:.8rem;color:#e3eaf1'>{safe_text(duel['leader'])}</div></div>", unsafe_allow_html=True)
                    st.progress(duel['p_a'] / 100, text=f"{players['A']['name']} {duel['p_a']:.0f}% · {players['B']['name']} {100-duel['p_a']:.0f}%")
                    st.caption(safe_text(duel['reason']))
                    if duel.get('simulations'):
                        st.caption(f"{safe_text(duel['prediction_source'])} · {duel['simulations']} Durchgänge je Paarung · Sicherheit: {safe_text(duel['confidence'])}")
                with right:
                    st.image(character_portrait(duel["b"]), use_container_width=True)
                    st.markdown(f"**{safe_text(duel['b']['name'])}**")
                    st.caption(f"{safe_text(duel['role_b'])} · Power {character_profile(duel['b'])['power']}/100")
                    st.caption(f"Modellchance: {100-duel['p_a']:.0f}%")
                st.divider()
        else:
            st.info("Eine Siegtendenz und der Kampftext erscheinen ab mindestens 3 Figuren pro Team.")
    with st.expander("Wie werden Charaktere, Haki und Teamchemie bewertet? Quellen & Grenzen"):
        st.markdown("""
**Kartenwerte und interne Teamwertung**
- Das sichtbare Power Level bewertet die stärkste bekannte Prime-Form anhand von Manga-Leistungen, Kampfdarstellung und Einordnung.
- Die Charakterkarte zeigt Power Level, Haki-Fähigkeit (wenn bestätigt), Kopfgeld und Fähigkeiten/Nutzwert.
- Die Team-Grundwertung nutzt Power Level 68 %, Haki 14 %, Fähigkeiten/Nutzwert 14 % und Vielseitigkeit 4 %.
- **Faire Haki-Regel:** Es zählt ausschließlich der Durchschnitt der Charaktere mit bestätigter Haki-Anwendung. Unbestätigte oder unklare Daten sind nicht 0 und werden aus dem Nenner entfernt. Beispiel: Sind vier von fünf Figuren bestätigt, wird der Haki-Durchschnitt aus diesen vier berechnet; der Haki-Faktor bleibt bei 14 %. Sind drei bestätigt, zählt der Durchschnitt dieser drei usw.
- Wenn bei keinem Teammitglied Haki bestätigt ist, wird der Haki-Faktor ausgelassen und die übrigen Gewichte werden proportional normalisiert, sodass fehlende Daten keinen künstlichen Nachteil erzeugen.
- Die Haki-Werte sind Fan-Einschätzungen der gezeigten Haki-Meisterschaft, keine offiziellen Power-Level. „Nicht bestätigt“ bedeutet nicht, dass die Figur unmöglich Haki beherrscht, sondern dass keine ausreichende Bestätigung im verwendeten Kanon-Nachweis vorliegt.
- Intelligenz bleibt ein kleiner Bonus bis maximal +0,45 Punkte für das Team. Teamchemie ist bei 50 neutral und kann bis zu ±2 Punkte beitragen. Alle Teamplätze sind gleichwertig; es gibt keinen Kapitäns- oder Vizekapitänsbonus. Kopfgeld und Status fließen nicht in die Gesamtwertung ein.

**So wird Haki behandelt**
Jedes der 135 Profile enthält einen Haki-Status, einen Score (oder `null`), gegebenenfalls bestätigte Haki-Arten und eine kurze Erläuterung. In der Teamwertung werden nur Profile mit Status „bestätigt“ und numerischem Wert gezählt. Die Detailansicht nennt die einbezogenen Charaktere und den tatsächlich verwendeten Nenner.

**Taktisches Matchmaking:** Das Modell stellt passende Einzelduelle zusammen und kann Konter wie Ruffy gegen Enel oder Sanji gegen Nami berücksichtigen. Die Slot-Reihenfolge bringt keinen Vorteil.

**Stand und Quellenprüfung**
- Bewertungsstichtag: **Manga-Kapitel 1197 vom 1. November 2026**. Die aktuelle Kapitelübersicht listet Kapitel 1197 vom 1. November 2026; Kapitel 1198 ist für den 8. November 2026 angekündigt und noch nicht erschienen.
- **Kanon vor Community:** bestätigte Manga-Feats, bestätigte Haki-Arten und im Manga gezeigte Technik stehen über Titeln, Kopfgeld, Anime-Inszenierung und Fan-Rankings. Anime-Zusatzmaterial und Filme zählen nicht automatisch als Beleg.
- OPwiki und One Piece Wiki dienen dem Nachschlagen von Charakteren, Techniken und Haki-Arten. Analysen wie Library of Ohara, YouTube-Rankings und Fan-Foren dienen als zusätzliche Perspektiven – nicht als Beweis für eine offizielle Rangfolge.
- Die **Shanks-über-Kaido-Einordnung (97 zu 96)** ist eine bewusste Modellentscheidung: Shanks' Spitzen-Königshaki, Zukunftssicht/Observation-Killing und sein Kid-Feat geben ihm im Draft einen kleinen Vorsprung. Das ist kein im Manga endgültig bestätigter Satz, dass Shanks jedes Duell gegen Kaido gewinnen würde; Kaidos Ausdauer, Körper, Frucht und Wano-Kampfbelastung bleiben berücksichtigt. Gear-5-Ruffy liegt bei 95, mit klaren Zeit-/Energiegrenzen und noch nicht dauerhaft belegter Dominanz über fitte Top-Tiers.
- Imu und Joy Boy liegen auf 100 als gesetzte Obergrenze, Rocks D. Xebec bei 99, Roger und Prime-Whitebeard bei 98, Prime-Garp bei 98 sowie Shanks und Mihawk bei 97. Mihawk liegt in der reinen Schwertkunst vor Shanks; Shanks führt im separaten Haki-Teilwert.
- Die Skala ist **kein offizieller Oda-Wert**. 1 Punkt ist keine mathematisch exakte Siegwahrscheinlichkeit; nahe Werte markieren dieselbe Spitzenklasse, keine sichere Reihenfolge.

**Quellen & Gegenpositionen:** [Haki – One Piece Wiki](https://onepiece.fandom.com/wiki/Haki) · [Observationshaki-Nutzer](https://onepiece.fandom.com/wiki/Category:Observation_Haki_Users) · [Rüstungshaki-Nutzer](https://onepiece.fandom.com/wiki/Category:Armament_Haki_Users) · [Königshaki-Nutzer](https://onepiece.fandom.com/wiki/Category:Supreme_King_Haki_Users) · [OPwiki – aktuelle Kapitel](https://opwiki.org/wiki/Aktuelle_Kapitel) · [Offizielle Kapitelübersicht](https://www.viz.com/shonenjump/chapters/one-piece) · [Kapitel 1197](https://www.viz.com/shonenjump/one-piece-chapter-1197/chapter/52017) · [Haki-Analyse bis 1194](https://abysscurrent.com/ranking/strongest-haki-users) · [Zoros Königshaki-Fortschritt](https://abysscurrent.com/manga/does-zoro-have-conquerors-haki) · [Library of Ohara: Analyse zu 1195–1196](https://thelibraryofohara.com/2026/10/20/chapter-secrets-one-piece-chapters-1195-1196-in-depth-analysis/) · [YouTube-Ranking 2026](https://www.youtube.com/watch?v=TxAoXMaavG8) · [YouTube: Top 50 (2026)](https://www.youtube.com/watch?v=vf1M513rCwA) · [Worstgen-Debatte zu 1191](https://worstgen.alwaysdata.net/forum/threads/one-piece-chapter-spoiler-1191-spoilers-discussion.86950/page-53) · [Reddit-Debatte Shanks vs. Kaido](https://www.reddit.com/r/OnePiecePowerScaling/comments/1jwbtjz) · [Deutsches Pirateboard: Loki vs. Kaido](https://www.pirateboard.net/index.php?postID=1003731&thread%2F14472-kapitel-1174-die-st%C3%A4rkste-kreatur-der-welt%2F=)

Die Kampfkraft-, Haki-, Intelligenz- und Chemiewerte sind begründete Fan-Schätzungen, keine offiziellen Zahlen. Porträts werden über direkte Bildlinks, Uploads oder eine explizit gestartete Sammelprüfung lokal im Ordner `portraits/` gespeichert. Die normale Anzeige führt keine Netzwerkabfragen aus. Das Komplett-Backup nimmt diese Bilder samt Link-Metadaten mit; ein normales JSON-Spielstand-Export enthält nur den Spielstatus.
""")


# ---- Auction log and roster -----------------------------------------------
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
log_left, log_right = st.columns([1.25, 1])
with log_left:
    with st.container(border=True):
        st.markdown('<div class="panel-label">AUKTIONSCHRONIK</div><h3>Die bisherigen Deals</h3>', unsafe_allow_html=True)
        if not st.session_state.history:
            st.markdown('<div class="small-muted">Noch kein Deal abgeschlossen. Dreht das Rad und sichert euch eure erste Figur.</div>', unsafe_allow_html=True)
        else:
            for item in reversed(st.session_state.history[-10:]):
                st.markdown(f'<div class="history-row"><div class="history-no">#{item["round"]:02d}</div><div class="history-main"><b>{safe_text(item["character"])}</b><br><span class="small-muted">{safe_text(item["winner"])} · {safe_text(item["faction"])}</span></div><div class="history-price">{money(item["price"])}</div></div>', unsafe_allow_html=True)
        if st.session_state.return_history:
            with st.expander(f"Rückgabe-Chronik ({len(st.session_state.return_history)})"):
                for item in reversed(st.session_state.return_history):
                    st.markdown(f"- {safe_text(item['player'])}: **{safe_text(item['character'])}** zurückgegeben · −{money(item['fee'])} · {safe_text(item['reason'])}")
with log_right:
    with st.container(border=True):
        st.markdown('<div class="panel-label">DRAFT-REGELN</div><h3>So läuft die Runde</h3>', unsafe_allow_html=True)
        st.markdown("""<div style="display:flex;gap:10px;margin:10px 0"><div style="font-family:'Barlow Condensed';font-size:1.6rem;color:#e8bd64;font-weight:900">01</div><div><b>Los ziehen</b><div class="small-muted">Jedes verbleibende Los hat dieselbe Chance. Die Animation verändert das Ergebnis nicht.</div></div></div><div style="display:flex;gap:10px;margin:10px 0"><div style="font-family:'Barlow Condensed';font-size:1.6rem;color:#e8bd64;font-weight:900">02</div><div><b>Bieten</b><div class="small-muted">Der ziehende Spieler eröffnet. Danach wird abwechselnd erhöht oder gepasst.</div></div></div><div style="display:flex;gap:10px;margin:10px 0"><div style="font-family:'Barlow Condensed';font-size:1.6rem;color:#e8bd64;font-weight:900">03</div><div><b>Team führen</b><div class="small-muted">Alle fünf Plätze sind gleichwertig; die Reihenfolge bringt keinen Bonus.</div></div></div><div style="display:flex;gap:10px;margin:10px 0"><div style="font-family:'Barlow Condensed';font-size:1.6rem;color:#e8bd64;font-weight:900">04</div><div><b>Rückgabe mit Strafe</b><div class="small-muted">Jeder Spieler kann maximal drei Karten für je 1 € zurück in den Lostopf legen. Der Kaufpreis wird nicht erstattet.</div></div></div>""", unsafe_allow_html=True)
        st.caption("Jeder Kauf lässt mindestens 1 € für jeden noch offenen Teamplatz übrig. Rückgaben müssen diese Reserve ebenfalls erhalten.")

if st.button("🏴‍☠️ Charakterpool durchsuchen · 135 Figuren öffnen / schließen", key="toggle_roster_classic", use_container_width=True):
    st.session_state["show_roster_browser_classic"] = not st.session_state.get("show_roster_browser_classic", False)
    st.rerun()
if st.session_state.get("show_roster_browser_classic", False):
    with st.container(border=True):
        render_roster_browser()

with st.expander(f"📚 Spielhistorie ({len(st.session_state.get('classic_match_history', []))} Spiele)"):
    match_history = st.session_state.get("classic_match_history", [])
    if not match_history:
        st.caption("Noch kein klassisches Spielergebnis gespeichert.")
    else:
        win_counts = {}
        for row in match_history:
            if row.get("outcome") in {"A", "B"}:
                win_counts[row.get("winner", "Unbekannt")] = win_counts.get(row.get("winner", "Unbekannt"), 0) + 1
        if win_counts:
            st.markdown("**Siege insgesamt:** " + " · ".join(f"{safe_text(name)}: {count}" for name, count in sorted(win_counts.items())))
        for row in reversed(match_history[-20:]):
            result = "Unentschieden" if row["outcome"] == "tie" else f"Sieger: {row['winner']}"
            score_text = "" if row.get("score_a") is None or row.get("score_b") is None else f" · Modellwert {row['score_a']:.1f} : {row['score_b']:.1f}"
            st.markdown(f"- Spiel {row['game_no']}: **{safe_text(row['player_a'])}** vs. **{safe_text(row['player_b'])}** — {result}{score_text}. Start: {safe_text(row['starter_name'])}; nächste Runde beginnt {safe_text(row['next_starter_name'])}.")
    if match_history and not st.session_state.confirm_clear_classic_history:
        if st.button("Klassische Historie zurücksetzen", key="classic_clear_history_request"):
            st.session_state.confirm_clear_classic_history = True
            st.rerun()
    if st.session_state.confirm_clear_classic_history:
        st.warning("Soll die gesamte klassische Spielhistorie dauerhaft gelöscht werden? Der aktuelle Draft bleibt bestehen.")
        clear_cols = st.columns(2)
        with clear_cols[0]:
            if st.button("Ja, Historie löschen", key="classic_clear_history_yes", type="primary"):
                st.session_state.classic_match_history = []
                st.session_state.classic_next_start_player = "A"
                st.session_state.confirm_clear_classic_history = False
                persist_game_state(); st.rerun()
        with clear_cols[1]:
            if st.button("Abbrechen", key="classic_clear_history_no"):
                st.session_state.confirm_clear_classic_history = False
                st.rerun()

st.markdown('<div class="footer-note">GRAND LINE DRAFT 5.0.3 · PERFORMANCE EDITION · FAN-PROJEKT · One Piece und seine Charaktere gehören den jeweiligen Rechteinhabern. Porträts: One Piece Wiki, One Piece API und einzelne offizielle Seiten. Erfolgreiche Bilder werden im Projektordner portraits/ zwischengespeichert.</div>', unsafe_allow_html=True)


# Persist each fully rendered state as a safety net; key transitions also save before reruns.
persist_game_state()
