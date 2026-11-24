import html
import re

import streamlit as st

from ingestion import extract_text
from chunking import split_text
from embedding import generate_embeddings
from vector_store import (
    store_chunks,
    search_chunks,
    append_chunks,
    get_chunk_count,
    list_document_names,
)

from scope_agent import extract_scope_and_deliverables
from risk_agent import detect_project_risks
from blocker_agent import identify_blockers_and_actions

from documentation_agent import generate_documentation
from health_score import calculate_project_health
from conversational_agent import answer_project_question


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="AI Project Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# STYLING
# --------------------------------------------------

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&display=swap');

:root {
    color-scheme: light;

    --bg: #F6F4FB;
    --panel: rgba(255, 255, 255, 0.82);
    --panel-solid: #FFFFFF;
    --panel-2: #F3F1FA;
    --line: rgba(76, 62, 140, 0.10);
    --line-strong: rgba(76, 62, 140, 0.20);

    --text: #292745;
    --muted: #6D6B88;
    --ink: #1F1D3D;

    --violet: #6C63D9;
    --violet-dark: #4F46B8;
    --lilac: #EDE9FF;
    --mint: #3DB8A4;
    --mint-dark: #2A8F7F;
    --mint-soft: #DFF5F0;
    --peach: #FFE9DA;
    --amber: #DFA03F;
    --rose: #D6586E;
    --track: #E8E4F5;

    --radius: 18px;
    --radius-sm: 12px;
    --shadow-sm: 0 1px 2px rgba(60, 48, 120, 0.05), 0 2px 8px -4px rgba(60, 48, 120, 0.08);
    --shadow: 0 1px 2px rgba(60, 48, 120, 0.04), 0 14px 32px -18px rgba(60, 48, 120, 0.22);
    --shadow-lg: 0 24px 48px -24px rgba(79, 70, 184, 0.35);
    --ease: cubic-bezier(.22, .8, .3, 1);

    --font-body: 'DM Sans', system-ui, -apple-system, 'Segoe UI', sans-serif;
    --font-display: 'Fraunces', Georgia, 'Times New Roman', serif;
}

/* ---------- Base ---------- */
html, body, [class*="css"], .stApp {
    font-family: var(--font-body);
    color: var(--text);
    -webkit-font-smoothing: antialiased;
}

html { scroll-behavior: smooth; }

::selection { background: rgba(108, 99, 217, 0.22); }

.stApp {
    background:
        radial-gradient(900px 520px at 8% -8%, rgba(188, 174, 255, 0.38), transparent 62%),
        radial-gradient(800px 480px at 98% 4%, rgba(160, 228, 214, 0.34), transparent 60%),
        radial-gradient(700px 520px at 60% 108%, rgba(255, 214, 190, 0.30), transparent 60%),
        linear-gradient(180deg, #FBFAFE 0%, var(--bg) 100%);
    background-attachment: fixed;
}

.stApp p, .stApp li, .stApp label, .stApp span,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5,
.stMarkdown, [data-testid="stMarkdownContainer"],
[data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
    color: var(--text);
}

[data-testid="stCaptionContainer"], .stApp small {
    color: var(--muted) !important;
}

#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {
    visibility: hidden;
}

header[data-testid="stHeader"] { background: transparent; }

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 5rem;
    max-width: 1180px;
}

h1, h2, h3, h4, h5 {
    font-family: var(--font-body);
    letter-spacing: -0.012em;
    color: var(--ink);
}

h3 { font-weight: 700; font-size: 1.3rem; }
h4 { font-weight: 700; font-size: 1.05rem; }

[data-testid="stMain"] h2 a, [data-testid="stMain"] h3 a, [data-testid="stMain"] h4 a { display: none; }

hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, var(--line-strong), transparent) !important;
    margin: 1.4rem 0 !important;
}

/* ---------- Entrance animation ---------- */
@keyframes riseIn {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes drift {
    0%, 100% { transform: translate3d(0, 0, 0); }
    50%      { transform: translate3d(14px, -10px, 0); }
}
@keyframes pulseDot {
    0%   { box-shadow: 0 0 0 0 rgba(61, 184, 164, .55); }
    70%  { box-shadow: 0 0 0 8px rgba(61, 184, 164, 0); }
    100% { box-shadow: 0 0 0 0 rgba(61, 184, 164, 0); }
}
@keyframes growX {
    from { transform: scaleX(0); }
    to   { transform: scaleX(1); }
}

.hero, .section-head, .card, .dash-card, .kpi-card, .risk-row, .stat,
[data-testid="stExpander"], [data-testid="stMetric"], [data-testid="stAlert"] {
    animation: riseIn .55s var(--ease) both;
}

/* ---------- Top navigation ---------- */
[data-testid="stElementContainer"]:has(.topnav) {
    position: sticky;
    top: .6rem;
    z-index: 60;
}

.topnav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: .5rem .55rem .5rem 1rem;
    margin-bottom: 1.2rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.72);
    backdrop-filter: blur(18px) saturate(1.4);
    -webkit-backdrop-filter: blur(18px) saturate(1.4);
    border: 1px solid rgba(255, 255, 255, 0.9);
    box-shadow: 0 10px 30px -16px rgba(60, 48, 120, 0.35), inset 0 0 0 1px var(--line);
}

.topnav .brand {
    display: flex;
    align-items: center;
    gap: .6rem;
    font-weight: 700;
    font-size: .95rem;
    color: var(--ink);
    white-space: nowrap;
}

.topnav .mark, .side-brand .mark {
    width: 30px;
    height: 30px;
    border-radius: 10px;
    display: grid;
    place-items: center;
    color: #fff;
    font-size: .85rem;
    background: linear-gradient(135deg, #8B7CF6, #5B8DEF 60%, #3DB8A4);
    box-shadow: 0 6px 14px -6px rgba(91, 100, 220, 0.7);
}

.topnav nav {
    display: flex;
    align-items: center;
    gap: .15rem;
    overflow-x: auto;
    scrollbar-width: none;
}
.topnav nav::-webkit-scrollbar { display: none; }

.stApp .topnav nav a {
    padding: .42rem .85rem;
    border-radius: 999px;
    font-size: .86rem;
    font-weight: 500;
    color: var(--muted);
    text-decoration: none;
    white-space: nowrap;
    transition: background .2s var(--ease), color .2s var(--ease);
}

.stApp .topnav nav a:hover {
    background: var(--lilac);
    color: var(--violet-dark);
}

.topnav .live {
    display: inline-flex;
    align-items: center;
    gap: .45rem;
    padding: .42rem .9rem;
    border-radius: 999px;
    font-size: .8rem;
    font-weight: 600;
    color: var(--mint-dark);
    background: var(--mint-soft);
    white-space: nowrap;
}

.topnav .live i {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--mint);
    animation: pulseDot 2.2s infinite;
}

/* ---------- Hero ---------- */
.hero {
    position: relative;
    padding: 2.8rem 2.8rem 2.5rem;
    border-radius: 28px;
    border: 1px solid rgba(255, 255, 255, 0.85);
    background:
        linear-gradient(135deg, rgba(255,255,255,.85) 0%, rgba(244,240,255,.75) 50%, rgba(231,248,244,.8) 100%);
    box-shadow: var(--shadow), inset 0 0 0 1px var(--line);
    overflow: hidden;
    margin-bottom: 1.8rem;
}

.hero::before, .hero::after {
    content: "";
    position: absolute;
    border-radius: 50%;
    filter: blur(40px);
    pointer-events: none;
    animation: drift 14s ease-in-out infinite;
}
.hero::before {
    width: 320px; height: 320px; right: -60px; top: -90px;
    background: radial-gradient(circle, rgba(167, 150, 255, .55), transparent 70%);
}
.hero::after {
    width: 260px; height: 260px; right: 160px; bottom: -120px;
    background: radial-gradient(circle, rgba(255, 196, 160, .55), transparent 70%);
    animation-delay: -6s;
}

.hero > * { position: relative; z-index: 1; }

.hero .status {
    display: inline-flex;
    align-items: center;
    gap: .55rem;
    font-size: .8rem;
    font-weight: 600;
    color: var(--violet-dark);
    background: rgba(255, 255, 255, .75);
    border: 1px solid var(--line);
    padding: .32rem .85rem;
    border-radius: 999px;
    margin-bottom: 1.1rem;
}

.hero .dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--mint);
    animation: pulseDot 2.2s infinite;
}

.stApp .hero h1 {
    margin: 0 0 .8rem;
    padding: 0;
    max-width: 700px;
    font-family: var(--font-display);
    font-size: 2.9rem;
    line-height: 1.1;
    font-weight: 600;
    letter-spacing: -0.025em;
    color: var(--ink) !important;
}

.stApp .hero h1 em {
    font-style: italic;
    background: linear-gradient(100deg, #6C63D9, #3DB8A4);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}

.stApp .hero p {
    margin: 0;
    color: var(--muted) !important;
    max-width: 580px;
    font-size: 1.05rem;
    line-height: 1.65;
}

.hero-chips {
    display: flex;
    flex-wrap: wrap;
    gap: .5rem;
    margin-top: 1.5rem;
}

.stApp .hero-chips span {
    font-size: .82rem;
    font-weight: 600;
    color: var(--text);
    padding: .4rem .9rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, .8);
    border: 1px solid var(--line);
    box-shadow: var(--shadow-sm);
    transition: transform .25s var(--ease), box-shadow .25s var(--ease);
}
.hero-chips span:hover { transform: translateY(-2px); box-shadow: var(--shadow); }

/* ---------- Section headings ---------- */
.section-head {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin: 3rem 0 1.2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--line);
    scroll-margin-top: 90px;
}

.section-head .icon {
    width: 46px;
    height: 46px;
    flex: none;
    border-radius: 15px;
    display: grid;
    place-items: center;
    font-size: 1.25rem;
    background: linear-gradient(145deg, #F1EDFF, #E1F6F1);
    border: 1px solid rgba(255,255,255,.9);
    box-shadow: 0 8px 18px -10px rgba(79, 70, 184, 0.5);
}

.stApp .section-head h2 {
    margin: 0;
    padding: 0;
    font-family: var(--font-display);
    font-size: 1.6rem;
    font-weight: 600;
    letter-spacing: -0.02em;
    color: var(--ink);
}

.stApp .section-head span.sub {
    display: block;
    color: var(--muted);
    font-size: .92rem;
    margin-top: .2rem;
}

/* ---------- Cards ---------- */
.card {
    background: var(--panel);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,.9);
    border-radius: var(--radius);
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    box-shadow: var(--shadow), inset 0 0 0 1px var(--line);
    transition: transform .3s var(--ease), box-shadow .3s var(--ease);
}

.card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-lg), inset 0 0 0 1px var(--line-strong);
}

.stApp .card h4 {
    margin: 0 0 .65rem;
    padding: 0;
    font-size: .98rem;
    font-weight: 700;
    color: var(--ink);
}

.card ul { margin: 0; padding-left: 1.15rem; color: var(--text); }
.card li { margin-bottom: .4rem; line-height: 1.6; color: var(--text); }
.card li::marker { color: var(--violet); }
.card .empty { color: var(--muted); font-style: italic; margin: 0; }
.card p { margin: 0; line-height: 1.65; color: var(--text); }

.card.result {
    border-left: 4px solid var(--violet);
    background: linear-gradient(90deg, rgba(108,99,217,0.07), var(--panel) 40%);
}

.card.risk {
    border-left: 4px solid var(--rose);
    background: linear-gradient(90deg, rgba(214,88,110,0.07), var(--panel) 40%);
}

.card.risk .rtype {
    font-weight: 700;
    color: #B63F57;
    margin-bottom: .45rem;
}

.card.blockers  { border-top: 4px solid var(--rose); }
.card.decisions { border-top: 4px solid var(--amber); }
.card.actions   { border-top: 4px solid var(--mint); }

/* ---------- Pills ---------- */
.stApp .pill {
    display: inline-block;
    font-size: .76rem;
    font-weight: 600;
    padding: .2rem .7rem;
    margin: .5rem .35rem 0 0;
    border-radius: 999px;
    color: var(--violet-dark);
    background: var(--lilac);
    border: 1px solid rgba(108, 99, 217, 0.18);
}

.stApp .pill.source {
    color: var(--mint-dark);
    background: var(--mint-soft);
    border-color: rgba(61, 184, 164, 0.25);
}

/* ---------- Stat tiles ---------- */
.stat {
    position: relative;
    display: flex;
    flex-direction: column;
    padding: 1rem 1.1rem;
    border-radius: 16px;
    background: rgba(255, 255, 255, .85);
    border: 1px solid rgba(255,255,255,.9);
    box-shadow: var(--shadow-sm), inset 0 0 0 1px var(--line);
    overflow: hidden;
    transition: transform .25s var(--ease);
}
.stat:hover { transform: translateY(-2px); }

.stat::before {
    content: "";
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 4px;
    background: linear-gradient(180deg, var(--violet), var(--mint));
}

.stat .value {
    font-family: var(--font-display);
    font-size: 2rem;
    font-weight: 600;
    line-height: 1.1;
    color: var(--ink);
}

.stat .label {
    margin-top: .25rem;
    font-size: .8rem;
    font-weight: 500;
    color: var(--muted);
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background:
        radial-gradient(360px 260px at 0% 0%, rgba(188,174,255,.35), transparent 70%),
        radial-gradient(320px 260px at 100% 100%, rgba(160,228,214,.30), transparent 70%),
        rgba(252, 251, 255, 0.92);
    border-right: 1px solid var(--line);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
}

section[data-testid="stSidebar"] :is(p, span, label, li, h1, h2, h3, h4, h5) {
    color: var(--text);
}

section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
section[data-testid="stSidebar"] small {
    color: var(--muted) !important;
}

.side-brand {
    display: flex;
    align-items: center;
    gap: .75rem;
    margin-bottom: .3rem;
}
.side-brand .mark { width: 38px; height: 38px; border-radius: 12px; font-size: 1rem; }
.side-brand .name { font-weight: 700; font-size: 1.02rem; color: var(--ink); line-height: 1.2; }
.side-brand .tag { font-size: .8rem; color: var(--muted); line-height: 1.35; margin-top: .1rem; }

.side-label {
    font-size: .72rem;
    font-weight: 700;
    letter-spacing: .09em;
    text-transform: uppercase;
    color: var(--muted);
    margin: .2rem 0 .7rem;
}

.steps { display: flex; flex-direction: column; gap: .5rem; }

.step {
    display: flex;
    align-items: center;
    gap: .7rem;
    padding: .6rem .8rem;
    border-radius: 12px;
    font-size: .9rem;
    font-weight: 500;
    color: var(--muted);
    background: rgba(255,255,255,.55);
    border: 1px solid var(--line);
    transition: transform .25s var(--ease), background .25s var(--ease);
}
.step:hover { transform: translateX(3px); background: rgba(255,255,255,.95); }

.step .tick {
    width: 22px; height: 22px; flex: none;
    border-radius: 50%;
    display: grid; place-items: center;
    font-size: .7rem; font-weight: 700;
    color: var(--muted);
    background: var(--track);
}

.step.done { color: var(--ink); background: rgba(255,255,255,.95); }
.step.done .tick { color: #fff; background: linear-gradient(135deg, #3DB8A4, #2A8F7F); }

/* ---------- File uploader ---------- */
[data-testid="stFileUploader"] section {
    background: rgba(255,255,255,.7);
    border: 1.5px dashed rgba(108, 99, 217, 0.4);
    border-radius: var(--radius);
    padding: 1.6rem;
    transition: all .25s var(--ease);
}

[data-testid="stFileUploader"] section:hover {
    border-color: var(--violet);
    background: linear-gradient(135deg, rgba(237,233,255,.8), rgba(223,245,240,.7));
    transform: translateY(-2px);
}

[data-testid="stFileUploader"] section span,
[data-testid="stFileUploader"] section small,
[data-testid="stFileUploader"] section div { color: var(--muted); }

[data-testid="stFileUploader"] section button {
    background: var(--panel-solid);
    color: var(--violet-dark);
    border: 1px solid var(--line-strong);
    border-radius: 10px;
    font-weight: 600;
}

[data-testid="stFileUploaderFile"] {
    background: rgba(255,255,255,.8);
    border-radius: 12px;
    padding: .2rem .5rem;
}

/* ---------- Inputs ---------- */
.stTextInput input {
    background: var(--panel-solid) !important;
    border: 1px solid var(--line-strong) !important;
    border-radius: 14px !important;
    color: var(--text) !important;
    padding: .85rem 1.1rem !important;
    box-shadow: var(--shadow-sm);
    transition: border-color .2s, box-shadow .2s;
}

.stTextInput input::placeholder { color: var(--muted) !important; opacity: 1 !important; }

.stTextInput input:focus {
    border-color: var(--violet) !important;
    box-shadow: 0 0 0 4px rgba(108, 99, 217, 0.15) !important;
}

.stTextInput label p, .stSelectbox label p, .stFileUploader label p {
    font-weight: 600;
    font-size: .88rem;
    color: var(--ink);
}

div[data-baseweb="select"] > div {
    background: var(--panel-solid);
    border-color: var(--line-strong);
    border-radius: 14px;
    color: var(--text);
    min-height: 46px;
    box-shadow: var(--shadow-sm);
    transition: border-color .2s, box-shadow .2s;
}

div[data-baseweb="select"] > div:hover { border-color: var(--violet); }
div[data-baseweb="select"] > div:focus-within {
    border-color: var(--violet);
    box-shadow: 0 0 0 4px rgba(108, 99, 217, 0.15);
}

div[data-baseweb="select"] span,
div[data-baseweb="select"] input { color: var(--text) !important; }

/* Dropdown menus */
div[data-baseweb="popover"] > div {
    border-radius: 14px;
    border: 1px solid var(--line);
    box-shadow: 0 20px 44px -18px rgba(60, 48, 120, 0.4);
    overflow: hidden;
}
div[data-baseweb="popover"] ul { background: var(--panel-solid); padding: .3rem; }
div[data-baseweb="popover"] li { border-radius: 10px; color: var(--text); transition: background .15s; }
div[data-baseweb="popover"] li:hover,
div[data-baseweb="popover"] li[aria-selected="true"] { background: var(--lilac); }

/* ---------- Buttons ---------- */
.stButton > button,
.stDownloadButton > button {
    border-radius: 12px;
    border: 1px solid var(--line-strong);
    background: var(--panel-solid);
    color: var(--ink);
    font-weight: 600;
    padding: .6rem 1.4rem;
    box-shadow: var(--shadow-sm);
    transition: transform .2s var(--ease), box-shadow .2s var(--ease), border-color .2s, background .2s;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: var(--violet);
    background: #FFFFFF;
    transform: translateY(-2px);
    box-shadow: 0 12px 22px -14px rgba(79, 70, 184, 0.55);
}

.stButton > button:active, .stDownloadButton > button:active { transform: translateY(0) scale(.98); }

.stButton > button:hover p,
.stDownloadButton > button:hover p { color: var(--violet-dark); }

.stButton > button:focus-visible, .stDownloadButton > button:focus-visible {
    outline: 3px solid rgba(108, 99, 217, .35);
    outline-offset: 2px;
}

.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #7C6FF0 0%, #5B63DC 55%, #4C8FD9 100%);
    border: none;
    color: #FFFFFF;
    box-shadow: 0 14px 26px -14px rgba(91, 99, 220, 0.9);
}

.stButton > button[kind="primary"] p,
.stButton > button[data-testid="stBaseButton-primary"] p { color: #FFFFFF; }

.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
    filter: brightness(1.07);
    background: linear-gradient(135deg, #7C6FF0 0%, #5B63DC 55%, #4C8FD9 100%);
    box-shadow: 0 18px 30px -14px rgba(91, 99, 220, 1);
}

.stButton > button[kind="primary"]:hover p,
.stButton > button[data-testid="stBaseButton-primary"]:hover p { color: #FFFFFF; }

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {
    gap: .3rem;
    background: rgba(108, 99, 217, 0.08);
    padding: .35rem;
    border-radius: 16px;
    box-shadow: inset 0 0 0 1px var(--line);
    overflow-x: auto;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 12px;
    padding: .55rem 1.2rem;
    color: var(--muted);
    font-weight: 600;
    transition: background .2s, color .2s;
}

.stTabs [data-baseweb="tab"]:hover { background: rgba(255, 255, 255, 0.65); }

.stTabs [aria-selected="true"] {
    background: var(--panel-solid) !important;
    box-shadow: 0 8px 18px -10px rgba(79, 70, 184, 0.55);
}

.stTabs [aria-selected="true"],
.stTabs [aria-selected="true"] p { color: var(--violet-dark) !important; }

.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none; }

.stTabs [data-baseweb="tab-panel"] { padding-top: 1.4rem; }

/* ---------- Alerts, expanders, metrics, chat ---------- */
[data-testid="stAlert"] {
    border-radius: 14px;
    border: 1px solid var(--line);
    box-shadow: var(--shadow-sm);
}

[data-testid="stExpander"] {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 16px;
    box-shadow: var(--shadow-sm);
    overflow: hidden;
    transition: box-shadow .25s var(--ease);
}
[data-testid="stExpander"]:hover { box-shadow: var(--shadow); }

[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary p { color: var(--ink); font-weight: 600; }

[data-testid="stExpander"] summary:hover { background: rgba(237, 233, 255, .5); }

[data-testid="stExpander"] pre,
[data-testid="stText"] { background: var(--panel-2); color: var(--text); border-radius: 10px; }

[data-testid="stMetric"] {
    background: var(--panel);
    border: 1px solid rgba(255,255,255,.9);
    border-radius: 16px;
    padding: 1rem 1.2rem;
    box-shadow: var(--shadow-sm), inset 0 0 0 1px var(--line);
}

[data-testid="stMetricValue"] { color: var(--ink); font-family: var(--font-display); }

div[data-testid="stProgress"] > div > div > div > div {
    background: linear-gradient(90deg, #8B7CF6, #3DB8A4);
    border-radius: 999px;
}

[data-testid="stChatMessage"] {
    background: var(--panel);
    border: 1px solid rgba(255,255,255,.9);
    border-radius: 18px;
    box-shadow: var(--shadow-sm), inset 0 0 0 1px var(--line);
    padding: 1rem 1.2rem;
}

div[data-testid="stChatInput"] {
    background: var(--panel-solid);
    border-radius: 18px;
    border: 1px solid var(--line-strong);
    box-shadow: var(--shadow);
}

div[data-testid="stChatInput"] textarea {
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
    caret-color: var(--violet) !important;
    background-color: var(--panel-solid) !important;
}

div[data-testid="stChatInput"] textarea::placeholder {
    color: var(--muted) !important;
    -webkit-text-fill-color: var(--muted) !important;
    opacity: 1 !important;
}

div[data-testid="stChatInput"] textarea:focus {
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
}

/* ---------- Insights dashboard ---------- */
.dash-card {
    background: var(--panel);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,.9);
    border-radius: 20px;
    padding: 1.4rem 1.5rem;
    box-shadow: var(--shadow), inset 0 0 0 1px var(--line);
    margin-bottom: 1rem;
    transition: transform .3s var(--ease), box-shadow .3s var(--ease);
}
.dash-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-lg), inset 0 0 0 1px var(--line-strong); }

.gauge-card { text-align: center; }

.gauge {
    width: 160px; height: 160px;
    margin: .2rem auto .8rem;
    border-radius: 50%;
    background: conic-gradient(var(--clr) calc(var(--pct) * 1%), var(--track) 0);
    display: grid; place-items: center;
}

.gauge-inner {
    width: 122px; height: 122px;
    border-radius: 50%;
    background: var(--panel-solid);
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    box-shadow: inset 0 0 0 1px var(--line);
}

.gauge-inner .gv { font-family: var(--font-display); font-size: 2.3rem; font-weight: 600; line-height: 1; color: var(--ink); }
.gauge-inner small { color: var(--muted); font-size: .75rem; margin-top: .2rem; }
.gauge-status { font-weight: 700; font-size: 1.1rem; }
.gauge-label { color: var(--muted); font-size: .85rem; }

.dim { margin-bottom: .9rem; }
.dim-top { display: flex; justify-content: space-between; font-size: .9rem; margin-bottom: .3rem; color: var(--text); }

.dim-track {
    height: 9px;
    border-radius: 999px;
    background: var(--track);
    overflow: hidden;
}

.dim-fill {
    height: 100%;
    border-radius: 999px;
    transform-origin: left center;
    animation: growX 1.1s var(--ease) both;
}

.risk-row {
    background: var(--panel);
    border: 1px solid var(--line);
    border-left: 4px solid var(--rose);
    border-radius: 14px;
    padding: .9rem 1.1rem;
    margin-bottom: .7rem;
    box-shadow: var(--shadow-sm);
    transition: transform .25s var(--ease), box-shadow .25s var(--ease);
}
.risk-row:hover { transform: translateX(4px); box-shadow: var(--shadow); }

.risk-row .risk-title { font-weight: 700; font-size: .93rem; color: #B63F57; margin-bottom: .25rem; }
.risk-row .risk-ev { color: var(--text); font-size: .9rem; line-height: 1.55; }

.legend {
    display: flex; flex-wrap: wrap; gap: .4rem .9rem;
    margin-top: .6rem; font-size: .82rem;
    color: var(--muted); justify-content: center;
}
.legend .lg { display: inline-flex; align-items: center; gap: .35rem; }
.legend i { width: 10px; height: 10px; border-radius: 4px; display: inline-block; }

.dash-title {
    font-size: 1.02rem;
    font-weight: 700;
    margin: .4rem 0 .8rem;
    color: var(--ink);
}

.kpi-card {
    position: relative;
    overflow: hidden;
    background: linear-gradient(160deg, #FFFFFF 0%, #F5F2FF 100%);
    border: 1px solid rgba(255,255,255,.9);
    border-radius: 18px;
    padding: 1.15rem 1.3rem;
    box-shadow: var(--shadow), inset 0 0 0 1px var(--line);
    margin-bottom: 1rem;
    transition: transform .3s var(--ease), box-shadow .3s var(--ease);
}
.kpi-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-lg), inset 0 0 0 1px var(--line-strong); }

.kpi-card::before {
    content: "";
    position: absolute;
    right: -30px; top: -30px;
    width: 110px; height: 110px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(139,124,246,.28), transparent 70%);
}

.kpi-label {
    font-size: .72rem;
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--muted);
}

.kpi-value {
    font-family: var(--font-display);
    font-size: 2rem;
    font-weight: 600;
    color: var(--ink);
    margin: .35rem 0;
}

.kpi-sub { font-size: .84rem; color: var(--muted); }

.level-badge {
    display: inline-block;
    font-size: .92rem;
    font-weight: 700;
    letter-spacing: .06em;
    padding: .22rem .85rem;
    border-radius: 999px;
    border: 1px solid;
}

.radar-head {
    display: flex; justify-content: space-between; align-items: center;
    flex-wrap: wrap; gap: .6rem; margin-bottom: .8rem;
}

.chip {
    font-size: .8rem;
    font-weight: 600;
    padding: .3rem .9rem;
    border-radius: 999px;
    border: 1px solid;
}

.radar-wrap {
    display: grid;
    grid-template-columns: minmax(240px, 1fr) 1.2fr;
    gap: 1.6rem;
    align-items: center;
}

.factor { margin-bottom: 1.1rem; }

.factor-top {
    display: flex; justify-content: space-between;
    font-size: .92rem; font-weight: 600;
    margin-bottom: .4rem; color: var(--text);
}

/* ---------- Scrollbars ---------- */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: rgba(108, 99, 217, .25); border-radius: 999px; border: 2px solid transparent; background-clip: content-box; }
::-webkit-scrollbar-thumb:hover { background: rgba(108, 99, 217, .45); background-clip: content-box; border: 2px solid transparent; }

/* ---------- Responsive ---------- */
@media (max-width: 1000px) {
    .topnav nav { display: none; }
    .stApp .hero h1 { font-size: 2.3rem; }
}

@media (max-width: 800px) {
    .radar-wrap { grid-template-columns: 1fr; }
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    .hero { padding: 1.8rem 1.4rem; border-radius: 22px; }
    .stApp .hero h1 { font-size: 1.85rem; }
    .stApp .hero p { font-size: .97rem; }
    .section-head { margin-top: 2.2rem; gap: .8rem; }
    .stApp .section-head h2 { font-size: 1.3rem; }
    .section-head .icon { width: 40px; height: 40px; border-radius: 13px; }
    .topnav { padding-left: .8rem; }
}

@media (max-width: 520px) {
    .topnav .live { display: none; }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: .001ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: .001ms !important;
        scroll-behavior: auto !important;
    }
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

DEFAULT_STATE = {
    "processed_documents": {},
    "search_results": None,
    "scope_results": None,
    "risk_results": None,
    "blocker_results": None,
    "total_chunks": 0,
    "documentation_results": None,
    "health_results": None,
    "chat_history": [],
    "last_selected_document": None,
}

for key, default in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = default


# --------------------------------------------------
# UI HELPERS
# --------------------------------------------------

def esc(value):
    return html.escape(str(value))


def section_header(icon, title, subtitle):
    anchor = re.sub(r"[^a-z0-9]+", "-", str(title).lower()).strip("-")
    st.markdown(
        f"""
        <div class="section-head" id="{anchor}">
            <div class="icon">{icon}</div>
            <div><h2>{esc(title)}</h2><span class="sub">{esc(subtitle)}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def stat_tile(label, value):
    return (
        f'<div class="stat"><div class="value">{esc(value)}</div>'
        f'<div class="label">{esc(label)}</div></div>'
    )


def list_card(title, items, empty_message, css_class=""):
    if items:
        body = "<ul>" + "".join(
            f"<li>{esc(i)}</li>" for i in items
        ) + "</ul>"
    else:
        body = f'<p class="empty">{esc(empty_message)}</p>'

    st.markdown(
        f'<div class="card {css_class}"><h4>{esc(title)}</h4>{body}</div>',
        unsafe_allow_html=True,
    )


# FIX: Supports both dictionary and string evidence
def display_evidence_item(item):

    if isinstance(item, dict):
        st.write(item.get("content", ""))
        st.caption(
            f"Source: {item.get('filename', 'Unknown document')}"
        )
    else:
        st.write(str(item))


def unique_risk_records(risks):
    """
    Return one record per distinct risk.

    New risk_agent results already have one record per risk (each with a
    risk_id). Older grouped results (one entry per category, several
    statements in 'evidence') are split into one record per statement.
    A risk that appears more than once is counted only once.
    """

    records = []
    seen_ids = set()
    seen_text = set()
    fallback_number = 0

    for item in (risks or []):

        if not isinstance(item, dict):
            continue

        if item.get("risk_id"):
            candidates = [item]

        else:
            lines = [
                line.strip()
                for line in str(item.get("evidence", "")).splitlines()
                if line.strip()
            ] or [""]

            candidates = []

            for line in lines:
                fallback_number += 1
                id_match = re.match(r"^([A-Za-z]\d+)\s*[—–-]", line)
                candidates.append({
                    **item,
                    "risk_id": (
                        id_match.group(1).upper()
                        if id_match else f"G{fallback_number}"
                    ),
                    "evidence": line,
                })

        for record in candidates:

            text_key = " ".join(
                str(record.get("evidence", "")).split()
            ).casefold()

            if record["risk_id"] in seen_ids:
                continue

            if text_key and text_key in seen_text:
                continue

            seen_ids.add(record["risk_id"])

            if text_key:
                seen_text.add(text_key)

            records.append(record)

    return records


def risk_row_html(risk):
    """Compact HTML row for one risk record."""

    evidence = " ".join(str(risk.get("evidence", "")).split())

    if len(evidence) > 140:
        evidence = evidence[:140].rstrip() + "…"

    pills = "".join(
        f'<span class="pill">{esc(k)}</span>'
        for k in risk.get("matched_keywords", [])[:4]
    )

    return (
        '<div class="risk-row">'
        f'<div class="risk-title">{esc(risk.get("risk_id", "–"))} · '
        f'{esc(risk.get("risk_type", "Unknown"))}</div>'
        f'<div class="risk-ev">{esc(evidence)}</div>'
        f'{pills}</div>'
    )


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

def actual_chunk_count():
    """
    Number of chunk records in ChromaDB that belong to the documents
    processed in this session (chunks left over from earlier sessions
    are not counted, so the number matches 'Documents processed').
    """

    try:
        count = sum(
            get_chunk_count(name)
            for name in st.session_state.processed_documents
        )
    except Exception:
        return st.session_state.total_chunks

    st.session_state.total_chunks = count
    return count


def render_sidebar_stats(slot):
    slot.markdown(
        stat_tile(
            "Documents processed",
            len(st.session_state.processed_documents)
        )
        + '<div style="height:.7rem"></div>'
        + stat_tile("Chunks stored", actual_chunk_count()),
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.markdown(
        """
        <div class="side-brand">
            <div class="mark">◆</div>
            <div>
                <div class="name">Project Intelligence</div>
                <div class="tag">Your documents, searched and analyzed.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown('<div class="side-label">Overview</div>', unsafe_allow_html=True)

    sidebar_stats_slot = st.empty()
    render_sidebar_stats(sidebar_stats_slot)

    st.divider()
    st.markdown(
        '<div class="side-label">Analyses completed</div>',
        unsafe_allow_html=True,
    )

    def _step(done, label):
        return (
            f'<div class="step{" done" if done else ""}">'
            f'<span class="tick">{"✓" if done else ""}</span>{esc(label)}</div>'
        )

    st.markdown(
        '<div class="steps">'
        + _step(st.session_state.scope_results is not None, "Scope & deliverables")
        + _step(st.session_state.risk_results is not None, "Risk detection")
        + _step(st.session_state.blocker_results is not None, "Blockers & actions")
        + "</div>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# HERO
# --------------------------------------------------

st.markdown(
    """
    <div class="topnav">
        <div class="brand"><span class="mark">◆</span> Project Intelligence</div>
        <nav>
            <a href="#document-ingestion" target="_self">Ingest</a>
            <a href="#add-updates" target="_self">Updates</a>
            <a href="#project-intelligence-agents" target="_self">Agents</a>
            <a href="#milestone-3-project-intelligence" target="_self">Generate</a>
            <a href="#milestone-4-insights-dashboard" target="_self">Dashboard</a>
        </nav>
        <span class="live"><i></i> AI analysis ready</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <div class="status"><span class="dot"></span> AI analysis ready</div>
        <h1>AI Project Intelligence &amp; <em>Risk Advisor</em></h1>
        <p>Upload project documents, search their contents, and analyze
        scope, risks, blockers, and action items.</p>
        <div class="hero-chips">
            <span>📁 Upload</span><span>🧠 Analyze</span>
            <span>📈 Insights</span><span>💬 Ask</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# MODULE 1: DOCUMENT INGESTION
# --------------------------------------------------

section_header("📁", "Document ingestion", "Upload PDF, Word, CSV, or text files")

uploaded_files = st.file_uploader(
    "Upload project documents",
    type=["pdf", "docx", "csv", "txt"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if st.button("Process Documents", type="primary"):

    if not uploaded_files:
        st.warning("Please upload at least one document.")

    else:
        total_chunks = 0
        processed_count = 0

        for uploaded_file in uploaded_files:

            st.subheader(f"📄 {uploaded_file.name}")

            try:
                text = extract_text(uploaded_file)
                chunks = split_text(text)

                if not chunks:
                    st.warning(
                        f"No text chunks found in {uploaded_file.name}."
                    )
                    continue

                with st.spinner(
                    f"Generating embeddings for {uploaded_file.name}..."
                ):
                    embeddings = generate_embeddings(chunks)

                with st.spinner("Saving to vector database..."):
                    saved = store_chunks(
                        chunks,
                        embeddings,
                        uploaded_file.name
                    )

                st.session_state.processed_documents[
                    uploaded_file.name
                ] = text

                st.session_state.scope_results = None
                st.session_state.risk_results = None
                st.session_state.blocker_results = None
                st.session_state.documentation_results = None
                st.session_state.health_results = None
                st.session_state.chat_history = []
                st.session_state.search_results = None

                total_chunks += saved
                processed_count += 1

                st.success(
                    f"Processed successfully: {uploaded_file.name}"
                )

                c1, c2, c3 = st.columns(3)

                c1.markdown(
                    stat_tile("Characters extracted", f"{len(text):,}"),
                    unsafe_allow_html=True
                )

                c2.markdown(
                    stat_tile("Chunks created", len(chunks)),
                    unsafe_allow_html=True
                )

                c3.markdown(
                    stat_tile("Chunks stored", saved),
                    unsafe_allow_html=True
                )

                with st.expander("View extracted text"):
                    st.text(text)

                with st.expander("View text chunks"):
                    for index, chunk in enumerate(chunks, start=1):
                        st.markdown(f"**Chunk {index}**")
                        st.text(chunk)

            except Exception as error:
                st.error(
                    f"Could not process {uploaded_file.name}: {error}"
                )

        render_sidebar_stats(sidebar_stats_slot)

        st.success(
            f"Processing finished. Documents processed: {processed_count}. "
            f"Chunks stored or updated: {total_chunks}."
        )


# --------------------------------------------------
# MODULE 1B: INCREMENTAL UPDATES (MILESTONE 4)
# --------------------------------------------------

import datetime
import hashlib
import os

st.session_state.setdefault("update_log", [])
st.session_state.setdefault("processed_update_hashes", [])
st.session_state.setdefault("failed_update_hashes", [])

section_header(
    "🔄",
    "Add updates",
    "Add meeting notes or progress updates; the knowledge base updates automatically"
)

NEW_DOCUMENT_OPTION = "➕ Keep as a separate document"


def make_unique_document_name(filename):
    """Return a filename that does not clash with any stored document."""

    def name_in_use(name):
        return (
            name in st.session_state.processed_documents
            or get_chunk_count(name) > 0
        )

    if not name_in_use(filename):
        return filename

    stem, extension = os.path.splitext(filename)
    number = 2

    while name_in_use(f"{stem} ({number}){extension}"):
        number += 1

    return f"{stem} ({number}){extension}"


def invalidate_document_results(document_name):
    """Clear analysis results if they belong to this document."""

    if st.session_state.last_selected_document == document_name:
        st.session_state.scope_results = None
        st.session_state.risk_results = None
        st.session_state.blocker_results = None
        st.session_state.documentation_results = None
        st.session_state.health_results = None


def clear_failed_updates():
    st.session_state.failed_update_hashes = []


if not st.session_state.processed_documents:

    st.info(
        "Process at least one project document above, "
        "then add meeting notes or progress updates here."
    )

else:

    update_target = st.selectbox(
        "Add updates to",
        options=[NEW_DOCUMENT_OPTION]
        + list(st.session_state.processed_documents.keys()),
        key="incremental_target",
    )

    st.caption(
        "Choose an existing document to merge the update into it, "
        "or keep it as its own document. Files are processed "
        "automatically as soon as you add them."
    )

    update_files = st.file_uploader(
        "Add meeting notes or progress updates",
        type=["pdf", "docx", "csv", "txt"],
        accept_multiple_files=True,
        key="incremental_uploader",
        label_visibility="collapsed",
    )

    current_update_hashes = {
        hashlib.md5(item.getvalue()).hexdigest() + "|" + update_target
        for item in (update_files or [])
    }

    # Forget failures for files that were removed from the uploader,
    # so removing and re-adding a file also retries it.
    st.session_state.failed_update_hashes = [
        failed_hash
        for failed_hash in st.session_state.failed_update_hashes
        if failed_hash in current_update_hashes
    ]

    if update_files:

        something_changed = False

        for update_file in update_files:

            file_hash = (
                hashlib.md5(update_file.getvalue()).hexdigest()
                + "|"
                + update_target
            )

            if (
                file_hash in st.session_state.processed_update_hashes
                or file_hash in st.session_state.failed_update_hashes
            ):
                continue

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

            log_entry = {
                "time": timestamp,
                "file": update_file.name,
                "target": update_target,
                "status": "ok",
                "message": "",
            }

            try:
                with st.spinner(
                    f"Adding {update_file.name} to the knowledge base..."
                ):

                    new_text = extract_text(update_file)

                    if not new_text or not str(new_text).strip():
                        raise ValueError("No readable text found in the file.")

                    merging = update_target != NEW_DOCUMENT_OPTION

                    if merging:
                        document_name = update_target
                        update_block = (
                            f"--- Update added {timestamp} "
                            f"({update_file.name}) ---\n"
                            + str(new_text)
                        )
                        full_text = (
                            st.session_state.processed_documents[
                                document_name
                            ]
                            + "\n\n"
                            + update_block
                        )

                    else:
                        document_name = make_unique_document_name(
                            update_file.name
                        )
                        update_block = str(new_text)
                        full_text = update_block

                    update_chunks = split_text(update_block)

                    if not update_chunks:
                        raise ValueError("No text chunks could be created.")

                    update_embeddings = generate_embeddings(update_chunks)

                    if merging:
                        saved_chunks = append_chunks(
                            update_chunks,
                            update_embeddings,
                            document_name,
                            source=update_file.name
                        )

                    else:
                        saved_chunks = store_chunks(
                            update_chunks,
                            update_embeddings,
                            document_name
                        )

                st.session_state.processed_documents[document_name] = full_text

                # The stored chunks changed, so old search results are stale.
                st.session_state.search_results = None

                if merging:
                    invalidate_document_results(document_name)

                log_entry["target"] = document_name
                log_entry["message"] = f"{len(update_chunks)} new chunks indexed"

                if not merging and document_name != update_file.name:
                    log_entry["message"] += (
                        f" (name already in use, saved as {document_name})"
                    )

                # Only a fully successful update is remembered as done.
                st.session_state.processed_update_hashes.append(file_hash)
                something_changed = True

            except Exception as error:
                log_entry["status"] = "failed"
                log_entry["message"] = str(error)

                # Remember the failure so it is not retried on every
                # rerun (no rerun loop); the user can retry explicitly.
                st.session_state.failed_update_hashes.append(file_hash)

            st.session_state.update_log.append(log_entry)

        if something_changed:
            st.rerun()

    if st.session_state.failed_update_hashes:

        st.button(
            "Retry failed updates",
            key="retry_failed_updates",
            on_click=clear_failed_updates,
        )

    if st.session_state.update_log:

        recent_updates = [
            (
                f"{entry['time']} — {entry['file']} → {entry['target']}: "
                f"{entry['message']}"
                if entry["status"] == "ok"
                else f"⚠️ {entry['time']} — {entry['file']} failed: "
                f"{entry['message']}"
            )
            for entry in reversed(st.session_state.update_log[-5:])
        ]

        list_card(
            "Recent updates",
            recent_updates,
            "No updates yet.",
            "actions"
        )


# --------------------------------------------------
# MODULE 3: PROJECT INTELLIGENCE AGENTS
# --------------------------------------------------

section_header(
    "🧠",
    "Project intelligence agents",
    "Scope, risks, blockers, and next steps"
)

processed_documents = st.session_state.processed_documents

if not processed_documents:

    st.info("Upload and process a document above to use the agents.")

else:

    selected_document = st.selectbox(
        "Choose a document to analyze",
        options=list(processed_documents.keys())
    )

    if st.session_state.last_selected_document != selected_document:

        st.session_state.scope_results = None
        st.session_state.risk_results = None
        st.session_state.blocker_results = None
        st.session_state.documentation_results = None
        st.session_state.health_results = None

        st.session_state.last_selected_document = selected_document

    document_text = processed_documents[selected_document]

    st.write("")

    tab_scope, tab_risk, tab_blockers = st.tabs([
        "🎯 Scope & Deliverables",
        "⚠️ Risk Detection",
        "🚧 Blockers & Actions"
    ])

    # ----------------------------------------------
    # AGENT 1: SCOPE AND DELIVERABLES
    # ----------------------------------------------

    with tab_scope:

        st.subheader("Scope and Deliverable Extraction")

        if st.button(
            "Analyze Scope",
            key="analyze_scope",
            type="primary"
        ):

            try:
                with st.spinner("Analyzing scope..."):

                    st.session_state.scope_results = (
                        extract_scope_and_deliverables(document_text)
                    )

            except Exception as error:
                st.error(f"Scope analysis failed: {error}")

        if st.session_state.scope_results is not None:

            labels = {
                "goals": "🎯 Project Goals",
                "deliverables": "📦 Deliverables",
                "milestones": "🏁 Milestones",
                "timelines": "🗓️ Timelines",
                "responsibilities": "👥 Responsibilities"
            }

            left, right = st.columns(2)

            for position, (category, label) in enumerate(labels.items()):

                items = st.session_state.scope_results.get(category, [])

                with (left if position % 2 == 0 else right):
                    list_card(
                        label,
                        items,
                        "No matching information found."
                    )

    # ----------------------------------------------
    # AGENT 2: RISK DETECTION
    # ----------------------------------------------

    with tab_risk:

        st.subheader("Risk Detection")

        st.caption(
            "This version detects risks using keywords; "
            "it does not calculate a reliable delivery-date forecast."
        )

        if st.button(
            "Analyze Risks",
            key="analyze_risks",
            type="primary"
        ):

            try:
                with st.spinner("Analyzing risks..."):

                    st.session_state.risk_results = (
                        detect_project_risks(document_text)
                    )

            except Exception as error:
                st.error(f"Risk analysis failed: {error}")

        if st.session_state.risk_results is not None:

            risks = unique_risk_records(st.session_state.risk_results)

            if risks:

                st.markdown(
                    stat_tile("Potential risks found", len(risks)),
                    unsafe_allow_html=True
                )

                st.write("")

                for risk in risks:

                    keywords = risk.get("matched_keywords", [])

                    pills = "".join(
                        f'<span class="pill">{esc(k)}</span>'
                        for k in keywords
                    )

                    st.markdown(
                        f"""
                        <div class="card risk">
                            <div class="rtype">Potential Risk: {esc(risk.get('risk_id', ''))} · {esc(risk.get('risk_type', 'Unknown'))}</div>
                            <p><b>Evidence:</b> {esc(risk.get('evidence', 'N/A'))}</p>
                            {pills}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            else:
                st.info("No risks matched the current keyword rules.")

    # ----------------------------------------------
    # AGENT 3: BLOCKERS AND ACTION ITEMS
    # ----------------------------------------------

    with tab_blockers:

        st.subheader("Blockers & Action Items")

        if st.button(
            "Analyze Blockers & Action Items",
            key="analyze_blockers",
            type="primary"
        ):

            try:
                with st.spinner(
                    "Analyzing blockers and action items..."
                ):

                    st.session_state.blocker_results = (
                        identify_blockers_and_actions(document_text)
                    )

            except Exception as error:
                st.error(f"Blocker analysis failed: {error}")

        if st.session_state.blocker_results is not None:

            blocker_data = st.session_state.blocker_results

            col_a, col_b, col_c = st.columns(3)

            with col_a:
                list_card(
                    "🚧 Blockers",
                    blocker_data.get("blockers", []),
                    "No blockers detected.",
                    "blockers"
                )

            with col_b:
                list_card(
                    "🤔 Pending Decisions",
                    blocker_data.get("pending_decisions", []),
                    "No pending decisions detected.",
                    "decisions"
                )

            with col_c:
                list_card(
                    "✅ Action Items",
                    blocker_data.get("action_items", []),
                    "No action items detected.",
                    "actions"
                )

    # --------------------------------------------------
    # MODULE 4: MILESTONE 3
    # --------------------------------------------------

    section_header(
        "🚀",
        "Milestone 3: Project Intelligence",
        "Generate documentation, assess project health, and ask questions"
    )

    tab_docs, tab_health, tab_chat = st.tabs([
        "📑 Documentation Generator",
        "📊 Project Health",
        "💬 Project Assistant"
    ])

    # ----------------------------------------------
    # AGENT 4: DOCUMENTATION GENERATION
    # ----------------------------------------------

    with tab_docs:

        st.subheader("Documentation Generation Agent")

        if st.button(
            "Generate Project Documentation",
            key="generate_documentation",
            type="primary"
        ):

            try:
                with st.spinner(
                    "Generating project documentation..."
                ):

                    st.session_state.documentation_results = (
                        generate_documentation(document_text)
                    )

            except Exception as error:
                st.error(
                    f"Documentation generation failed: {error}"
                )

        documentation = st.session_state.documentation_results

        if documentation is not None:

            st.markdown("### User Stories")

            list_card(
                "Generated User Stories",
                documentation.get("user_stories", []),
                "No user stories generated."
            )

            st.markdown("### Risk Register")

            risk_register = documentation.get("risk_register", [])

            if risk_register:

                for risk in risk_register:

                    with st.expander(risk["risk_type"]):

                        st.write("**Description:**")
                        st.write(risk["description"])

                        st.write("**Matched keywords:**")
                        st.write(", ".join(risk["matched_keywords"]))

                        st.write("**Status:**", risk["status"])

                        st.write("**Suggested mitigation:**")
                        st.write(risk["mitigation"])

            else:
                st.info("No risks found for the selected document.")

            st.markdown("### Action Items")

            actions = documentation.get("action_items", {})

            col1, col2, col3 = st.columns(3)

            with col1:
                list_card(
                    "Blockers",
                    actions.get("blockers", []),
                    "No blockers found.",
                    "blockers"
                )

            with col2:
                list_card(
                    "Pending Decisions",
                    actions.get("pending_decisions", []),
                    "No pending decisions found.",
                    "decisions"
                )

            with col3:
                list_card(
                    "Action Items",
                    actions.get("action_items", []),
                    "No action items found.",
                    "actions"
                )

    # ----------------------------------------------
    # PROJECT HEALTH SCORING
    # ----------------------------------------------

    with tab_health:

        st.subheader("Project Health Scoring")

        if st.button(
            "Calculate Project Health",
            key="calculate_health",
            type="primary"
        ):

            try:
                with st.spinner("Calculating project health..."):

                    st.session_state.health_results = (
                        calculate_project_health(document_text)
                    )

            except Exception as error:
                st.error(f"Health calculation failed: {error}")

        health = st.session_state.health_results

        if health is not None:

            st.markdown("### Overall Project Health")

            score = health.get("overall_score", 0)
            status = health.get("status", "Unknown")

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Overall Health Score",
                    f"{score}/100"
                )

            with col2:

                st.markdown("**Project Status**")

                if status == "Healthy":
                    st.success(status)

                elif status == "Moderate Risk":
                    st.warning(status)

                elif status == "Critical":
                    st.error(status)

                else:
                    st.info(status)

            st.markdown("---")

            st.markdown("### Project Assessment")

            assessment = health.get("assessment", {})

            st.markdown("#### Executive Summary")

            if status == "Healthy":

                st.success(
                    "The project is in good condition based on the "
                    "available documentation. Continue monitoring "
                    "progress and managing potential risks."
                )

            elif status == "Moderate Risk":

                st.warning(
                    "The project has moderate risks. Review identified "
                    "timeline issues, dependencies, and blockers "
                    "to avoid possible delivery problems."
                )

            elif status == "Critical":

                st.error(
                    "The project requires immediate attention. "
                    "Review the identified risks and resolve "
                    "blockers as a priority."
                )

            else:

                st.info(
                    "There is insufficient project information "
                    "to provide a complete assessment."
                )

            st.markdown("#### 1. Scope Assessment")

            list_card(
                "Scope Findings",
                assessment.get("scope", []),
                "No scope information available."
            )

            st.markdown("#### 2. Timeline & Risk Assessment")

            list_card(
                "Timeline and Risk Findings",
                assessment.get("timeline", []),
                "No timeline risks detected."
            )

            st.markdown("#### 3. Blocker & Dependency Assessment")

            list_card(
                "Blockers and Pending Decisions",
                assessment.get("blockers", []),
                "No blockers or pending decisions detected."
            )

            st.markdown("#### 4. Recommended Actions")

            list_card(
                "Suggested Actions",
                assessment.get("recommendations", []),
                "No additional recommendations available."
            )

            st.markdown("---")
            st.markdown("### Health Score Breakdown")

            col1, col2, col3 = st.columns(3)

            score_dimensions = [
                ("Scope Score", "scope_score", col1),
                ("Timeline Score", "timeline_score", col2),
                ("Blocker Score", "blocker_score", col3)
            ]

            for label, key, column in score_dimensions:

                value = health.get(key, 0)

                with column:

                    st.metric(label, f"{value}/100")

                    st.progress(
                        max(0, min(int(value), 100)) / 100
                    )

    # ----------------------------------------------
    # PROJECT ASSISTANT
    # ----------------------------------------------

    with tab_chat:

        st.subheader("Project Assistant")

        st.markdown(
            """
            <div class="card result">
                <h4>About the assistant</h4>
                <p>Ask questions in plain language and receive
                evidence-based responses from indexed project documents.
                The assistant can help with scope, deliverables,
                timelines, risks, blockers, and next steps.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        list_card(
            "Example questions",
            [
                "What is the project deadline?",
                "What are the main deliverables?",
                "Who is responsible for each task?",
                "What are the biggest risks or blockers?",
            ],
            "",
        )

        if st.session_state.chat_history:

            if st.button("Clear chat", key="clear_chat"):

                st.session_state.chat_history = []
                st.rerun()

        # Display previous conversations

        for message in st.session_state.chat_history:

            with st.chat_message(message["role"]):

                st.write(message["content"])

                if message["role"] == "assistant":

                    sources = message.get("sources", [])
                    evidence = message.get("evidence", [])

                    if sources:

                        st.markdown("**Sources:**")

                        for source in sources:
                            st.caption(f"📄 {source}")

                    if evidence:

                        with st.expander("View supporting evidence"):

                            for item in evidence:
                                display_evidence_item(item)

        chat_question = st.chat_input(
            "Ask a question about your project documents...",
            key="project_chat_input",
        )

        if chat_question:

            st.session_state.chat_history.append({
                "role": "user",
                "content": chat_question
            })

            with st.chat_message("user"):
                st.write(chat_question)

            try:

                with st.chat_message("assistant"):

                    with st.spinner("Searching project documents..."):

                        result = answer_project_question(
                            chat_question,
                            n_results=3,
                            filename=selected_document
                        )

                    if isinstance(result, dict):

                        answer = result.get(
                            "answer",
                            "No answer was returned."
                        )

                        sources = result.get("sources", [])
                        evidence = result.get("evidence", [])

                    else:

                        answer = str(result)
                        sources = []
                        evidence = []

                    st.write(answer)

                    if sources:

                        st.markdown("**Sources:**")

                        for source in sources:
                            st.caption(f"📄 {source}")

                    if evidence:

                        with st.expander("View supporting evidence"):

                            for item in evidence:
                                display_evidence_item(item)

                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "evidence": evidence
                    })

            except Exception as error:

                st.error(
                    f"Could not answer the question: {error}"
                )

    # --------------------------------------------------
    # MODULE 5: MILESTONE 4 - INSIGHTS DASHBOARD
    # --------------------------------------------------

    section_header(
        "📈",
        "Milestone 4: Insights dashboard",
        "Project health at a glance"
    )

    from health_score import assess_risk_matrix

    def dash_risk_matrix(risk_records):
        """
        5x5 risk matrix from the actual likelihood and impact of the
        detected risks (see health_score.assess_risk_matrix). It does not
        use the overall health score or simply count risks.
        Criticality bands: Low 1-4, Medium 5-9, High 10-16, Critical 17-25.
        Returns (likelihood, impact, score, level, color, info).
        """

        info = assess_risk_matrix(risk_records or [])

        return (
            info["likelihood"], info["impact"], info["score"],
            info["level"], info["color"], info,
        )



    def dash_radar_svg(factors, center_value):
        """
        Radar chart as inline SVG, any number of axes (five dimensions).
        factors = [(label, value 0-100, assessed)]; 'assessed' may be left
        out (treated as True). Unassessed axes are drawn in grey and
        labelled "no evidence".
        """

        import math

        width, height = 460, 360
        cx, cy, radius = 230, 178, 110
        label_gap = 26
        count = len(factors)

        def point(index, value, extra=0.0):
            angle = -math.pi / 2 + 2 * math.pi * index / count
            reach = radius * value / 100 + extra
            return cx + reach * math.cos(angle), cy + reach * math.sin(angle)

        parts = [
            f'<svg viewBox="0 0 {width} {height}" width="100%" '
            'xmlns="http://www.w3.org/2000/svg" role="img" '
            'font-family="Inter, sans-serif">'
        ]

        for level in (20, 40, 60, 80, 100):
            ring = " ".join(
                f"{x:.1f},{y:.1f}"
                for x, y in (point(i, level) for i in range(count))
            )
            dash = "" if level == 100 else ' stroke-dasharray="3 3"'
            parts.append(
                f'<polygon points="{ring}" fill="none" '
                f'stroke="#E3DFF2" stroke-width="1"{dash}/>'
            )
            parts.append(
                f'<text x="{cx + 4}" y="{cy - radius * level / 100 + 3:.1f}" '
                f'font-size="8" fill="#A9A6C2">{level}</text>'
            )

        for index in range(count):
            x, y = point(index, 100)
            parts.append(
                f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" '
                'stroke="#E3DFF2" stroke-width="1"/>'
            )

        shape = " ".join(
            f"{x:.1f},{y:.1f}"
            for x, y in (
                point(i, dash_clamp(factor[1]))
                for i, factor in enumerate(factors)
            )
        )

        parts.append(
            f'<polygon points="{shape}" fill="rgba(15,143,134,0.22)" '
            'stroke="#6C63D9" stroke-width="2.5" stroke-linejoin="round"/>'
        )

        for index, factor in enumerate(factors):

            label, value = factor[0], factor[1]
            assessed = factor[2] if len(factor) > 2 else True

            dot_color = dash_score_color(value) if assessed else "#A9A6C2"
            x, y = point(index, dash_clamp(value))
            parts.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" '
                f'fill="{dot_color}" stroke="#FFFFFF" '
                'stroke-width="1.5"/>'
            )

            # Axis label sits outside the outer ring: a name line plus a
            # score line, anchored by side and nudged by top / bottom so
            # neighbouring labels never overlap.
            lx, ly = point(index, 100, label_gap)
            cos_value = (lx - cx) / (radius + label_gap)
            sin_value = (ly - cy) / (radius + label_gap)
            anchor = (
                "middle" if abs(cos_value) < 0.3
                else "start" if cos_value > 0
                else "end"
            )

            if sin_value < -0.6:
                name_y, score_y = ly - 6, ly + 8
            else:
                name_y, score_y = ly + 2, ly + 16

            score_text = (
                f"{int(round(dash_clamp(value)))}/100"
                if assessed else "no evidence"
            )

            parts.append(
                f'<text x="{lx:.1f}" y="{name_y:.1f}" text-anchor="{anchor}" '
                f'font-size="12" font-weight="600" fill="#292745">'
                f'{esc(label)}</text>'
                f'<text x="{lx:.1f}" y="{score_y:.1f}" text-anchor="{anchor}" '
                f'font-size="11" font-weight="600" fill="{dot_color}">'
                f'{esc(score_text)}</text>'
            )

        parts.append(
            f'<text x="{cx}" y="{cy + 6}" text-anchor="middle" font-size="26" '
            f'font-weight="700" fill="#4F46B8" opacity="0.85">{esc(center_value)}</text>'
            f'<text x="{cx}" y="{cy + 20}" text-anchor="middle" font-size="9" '
            'fill="#6D6B88">health score</text></svg>'
        )

        return "".join(parts)


    def dash_clamp(value):
        try:
            return max(0.0, min(float(value), 100.0))
        except (TypeError, ValueError):
            return 0.0


    def dash_status_color(status_value):
        return {
            "Healthy": "#2E9E6B",
            "Moderate Risk": "#D39A1F",
            "High Risk": "#D9772B",
            "Critical": "#C2443D",
        }.get(status_value, "#6C63D9")


    def dash_score_color(value):
        pct = dash_clamp(value)
        return (
            "#2E9E6B" if pct >= 70
            else "#D39A1F" if pct >= 40
            else "#C2443D"
        )


    def dash_kpi_card(label, value="", subtitle="", value_html=None):
        sub = f'<div class="kpi-sub">{esc(subtitle)}</div>' if subtitle else ""
        return (
            '<div class="kpi-card">'
            f'<div class="kpi-label">{esc(label)}</div>'
            f'<div class="kpi-value">{value_html or esc(value)}</div>'
            f'{sub}</div>'
        )


    def dash_factor_list(factors):
        """factors = [(icon, label, value 0-100, assessed)]; assessed optional."""

        rows = ""

        for factor in factors:

            icon, label, value = factor[0], factor[1], factor[2]
            assessed = factor[3] if len(factor) > 3 else True

            pct = dash_clamp(value)
            color = dash_score_color(value) if assessed else "#A9A6C2"
            score_html = (
                f'<b style="color:{color}">{int(round(pct))}/100</b>'
                if assessed else
                f'<b style="color:{color}">{int(round(pct))}/100 '
                '<span style="font-weight:500;font-size:.78rem">'
                '(no evidence)</span></b>'
            )

            rows += (
                '<div class="factor"><div class="factor-top">'
                f'<span>{icon} {esc(label)}</span>'
                f'{score_html}</div>'
                '<div class="dim-track">'
                f'<div class="dim-fill" style="width:{pct}%;background:{color}"></div>'
                '</div></div>'
            )

        return rows


    def dash_radar_card(factors, status_value, overall_score):
        """
        factors = [(icon, label, value 0-100, assessed)]. Returns the radar
        card HTML. The headline number is the overall health score from the
        health calculation, so it always matches the Health score card.
        """

        score_text = f"{round(dash_clamp(overall_score), 2):g}"
        color = dash_status_color(status_value)

        radar_factors = [
            (factor[1], factor[2], factor[3] if len(factor) > 3 else True)
            for factor in factors
        ]

        return (
            '<div class="dash-card">'
            '<div class="radar-head">'
            '<div class="dash-title" style="margin:0">'
            '🕸️ Project Health Radar – Five Dimensions</div>'
            f'<span class="chip" style="color:{color};border-color:{color}66;'
            f'background:{color}1A">Health score {score_text}/100 · '
            f'{esc(status_value)}</span></div>'
            '<div class="radar-wrap">'
            f'<div>{dash_radar_svg(radar_factors, score_text)}</div>'
            f'<div>{dash_factor_list(factors)}</div>'
            '</div></div>'
        )

    if st.button(
        "Generate Insights Dashboard",
        key="generate_dashboard",
        type="primary"
    ):

        with st.spinner("Building project dashboard..."):

            dashboard_steps = [
                ("scope_results", extract_scope_and_deliverables, "Scope analysis"),
                ("risk_results", detect_project_risks, "Risk analysis"),
                ("blocker_results", identify_blockers_and_actions, "Blocker analysis"),
                ("health_results", calculate_project_health, "Health calculation"),
            ]

            for state_key, agent_function, step_name in dashboard_steps:

                try:
                    st.session_state[state_key] = agent_function(document_text)

                except Exception as error:
                    st.error(f"{step_name} failed: {error}")

    dash_scope = st.session_state.scope_results
    dash_risks = st.session_state.risk_results
    dash_blockers = st.session_state.blocker_results
    dash_health = st.session_state.health_results

    if all(
        result is None
        for result in (dash_scope, dash_risks, dash_blockers, dash_health)
    ):

        st.info("Click 'Generate Insights Dashboard' to begin.")

    else:

        blocker_count = len((dash_blockers or {}).get("blockers", []))
        decision_count = len((dash_blockers or {}).get("pending_decisions", []))
        action_count = len((dash_blockers or {}).get("action_items", []))
        dash_risk_records = unique_risk_records(dash_risks)
        risk_count = len(dash_risk_records)

        # ---- Health scoring module: KPI cards + radar ----

        if dash_health is not None:

            health_status = dash_health.get("status", "Unknown")
            health_overall = dash_clamp(dash_health.get("overall_score", 0))

            dimension_status = dash_health.get("dimension_status", {})

            def dash_dimension(icon, label, score_key, status_key):
                """(icon, label, score, assessed) for one health dimension."""

                value = dash_health.get(score_key)
                info = dimension_status.get(status_key)

                # Results saved before the five-dimension upgrade have no
                # score for the new dimensions: show them as not assessed.
                if value is None:
                    return (icon, label, 50, False)

                assessed = info.get("assessed", True) if info else True
                return (icon, label, dash_clamp(value), assessed)

            health_factors = [
                dash_dimension("📅", "Schedule", "timeline_score", "schedule"),
                dash_dimension("🎯", "Scope", "scope_score", "scope"),
                dash_dimension("⚠️", "Risk", "risk_score", "risk"),
                dash_dimension("✅", "Quality", "quality_score", "quality"),
                dash_dimension("🚧", "Blockers", "blocker_score", "blocker"),
            ]

            st.markdown(
                '<div class="dash-title">📊 Project health scoring</div>',
                unsafe_allow_html=True,
            )

            kpi_health, kpi_risk, kpi_level = st.columns(3)

            kpi_health.markdown(
                dash_kpi_card(
                    "📊 Health score",
                    f"{round(health_overall, 2):g}/100",
                    health_status,
                ),
                unsafe_allow_html=True,
            )

            if dash_risks is not None:

                # Risk score and criticality come from the likelihood and
                # impact of the detected risks, not from the health score.
                (
                    risk_likelihood, risk_impact, risk_total,
                    risk_level, risk_level_color, risk_info,
                ) = dash_risk_matrix(dash_risk_records)

                risk_sub = f"L{risk_likelihood} × I{risk_impact}"

                if risk_info["estimated_count"]:
                    risk_sub += " · partly estimated"

                kpi_risk.markdown(
                    dash_kpi_card(
                        "⚠️ Risk score (L × I)",
                        f"{risk_total}/25",
                        risk_sub,
                    ),
                    unsafe_allow_html=True,
                )

                kpi_level.markdown(
                    dash_kpi_card(
                        "🛡️ Criticality",
                        value_html=(
                            '<span class="level-badge" '
                            f'style="background:{risk_level_color}22;'
                            f'color:{risk_level_color};'
                            f'border-color:{risk_level_color}66">'
                            f'{esc(risk_level)}</span>'
                        ),
                    ),
                    unsafe_allow_html=True,
                )

            else:

                kpi_risk.markdown(
                    dash_kpi_card("⚠️ Risk score (L × I)", "—", "Run risk analysis"),
                    unsafe_allow_html=True,
                )

                kpi_level.markdown(
                    dash_kpi_card("🛡️ Criticality", "—"),
                    unsafe_allow_html=True,
                )

            st.markdown(
                dash_radar_card(health_factors, health_status, health_overall),
                unsafe_allow_html=True,
            )

        else:
            st.info("Health score not calculated yet.")

        # ---- Key numbers ----

        tile_cols = st.columns(4)
        tile_cols[0].markdown(stat_tile("Risks", risk_count), unsafe_allow_html=True)
        tile_cols[1].markdown(stat_tile("Blockers", blocker_count), unsafe_allow_html=True)
        tile_cols[2].markdown(stat_tile("Decisions", decision_count), unsafe_allow_html=True)
        tile_cols[3].markdown(stat_tile("Actions", action_count), unsafe_allow_html=True)

        st.write("")

        # ---- Risks + action items ----

        risk_col, action_col = st.columns(2)

        with risk_col:

            st.markdown(
                f'<div class="dash-title">⚠️ Risks ({risk_count})</div>',
                unsafe_allow_html=True,
            )

            if dash_risk_records:

                for risk in dash_risk_records[:5]:
                    st.markdown(risk_row_html(risk), unsafe_allow_html=True)

                if len(dash_risk_records) > 5:
                    with st.expander(
                        f"Show {len(dash_risk_records) - 5} more risks"
                    ):
                        for risk in dash_risk_records[5:]:
                            st.markdown(
                                risk_row_html(risk),
                                unsafe_allow_html=True,
                            )

            elif dash_risks is None:
                st.info("Not analyzed yet.")

            else:
                st.info("No risks found.")

        with action_col:

            st.markdown('<div class="dash-title">✅ Next steps</div>', unsafe_allow_html=True)

            if dash_blockers is not None:

                list_card(
                    "Action items",
                    dash_blockers.get("action_items", [])[:3],
                    "None.",
                    "actions"
                )

                list_card(
                    "Blockers",
                    dash_blockers.get("blockers", [])[:3],
                    "None.",
                    "blockers"
                )

                list_card(
                    "Pending decisions",
                    dash_blockers.get("pending_decisions", [])[:3],
                    "None.",
                    "decisions"
                )

            else:
                st.info("Not analyzed yet.")

            if dash_health is not None:

                list_card(
                    "Recommended actions",
                    dash_health.get("assessment", {}).get("recommendations", [])[:5],
                    "No additional recommendations.",
                    "actions"
                )
