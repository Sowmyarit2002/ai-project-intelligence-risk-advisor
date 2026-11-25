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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

:root {
    color-scheme: dark;

    --bg: #0B1220;
    --bg-soft: #0F1729;
    --panel: #121B2E;
    --panel-2: #172238;
    --panel-3: #1C2A44;
    --line: #202D45;
    --line-strong: #2F4062;

    --text: #D5DDEC;
    --muted: #8793AE;
    --ink: #F4F6FB;

    --gold: #E6B96A;
    --gold-deep: #C99A47;
    --gold-soft: rgba(230, 185, 106, 0.12);
    --gold-line: rgba(230, 185, 106, 0.35);
    --teal: #3FD0AE;
    --teal-soft: rgba(63, 208, 174, 0.12);
    --indigo: #93A2FF;
    --indigo-soft: rgba(147, 162, 255, 0.13);
    --rose: #F0626F;
    --rose-soft: rgba(240, 98, 111, 0.12);
    --amber: #F2B24C;
    --amber-soft: rgba(242, 178, 76, 0.12);
    --track: #22314D;

    --radius: 16px;
    --radius-sm: 11px;
    --shadow-sm: 0 1px 0 rgba(255, 255, 255, 0.03) inset, 0 1px 2px rgba(0, 0, 0, 0.35);
    --shadow: 0 1px 0 rgba(255, 255, 255, 0.035) inset, 0 10px 28px -16px rgba(0, 0, 0, 0.65);
    --ease: cubic-bezier(.22, .8, .3, 1);

    --font-body: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
    --font-display: 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif;
}

/* ---------- Base ---------- */
html, body, [class*="css"], .stApp {
    font-family: var(--font-body);
    color: var(--text);
    -webkit-font-smoothing: antialiased;
}

html { scroll-behavior: smooth; }

::selection { background: rgba(230, 185, 106, 0.28); color: #fff; }

.stApp {
    background:
        radial-gradient(900px 420px at 4% -10%, rgba(230, 185, 106, 0.07), transparent 65%),
        radial-gradient(800px 420px at 100% 0%, rgba(147, 162, 255, 0.06), transparent 60%),
        var(--bg);
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
    padding-top: 1rem;
    padding-bottom: 5rem;
    max-width: 1200px;
}

h1, h2, h3, h4, h5 {
    font-family: var(--font-display);
    letter-spacing: -0.012em;
    color: var(--ink);
}

h3 { font-weight: 700; font-size: 1.2rem; }
h4 { font-weight: 700; font-size: 1.02rem; }

[data-testid="stMain"] h2 a, [data-testid="stMain"] h3 a, [data-testid="stMain"] h4 a { display: none; }

hr {
    border: none !important;
    height: 1px !important;
    background: var(--line) !important;
    margin: 1.2rem 0 !important;
}

.ic { flex: none; display: block; }

/* ---------- Motion ---------- */
@keyframes riseIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulseDot {
    0%   { box-shadow: 0 0 0 0 rgba(63, 208, 174, .5); }
    70%  { box-shadow: 0 0 0 6px rgba(63, 208, 174, 0); }
    100% { box-shadow: 0 0 0 0 rgba(63, 208, 174, 0); }
}
@keyframes growX {
    from { transform: scaleX(0); }
    to   { transform: scaleX(1); }
}

.page-head, .section-head, .card, .dash-card, .kpi-card, .risk-row, .stat, .ov-card,
[data-testid="stExpander"], [data-testid="stMetric"], [data-testid="stAlert"] {
    animation: riseIn .4s var(--ease) both;
}

/* ---------- Top bar ---------- */
[data-testid="stElementContainer"]:has(.topbar) {
    position: sticky;
    top: .5rem;
    z-index: 60;
}

.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: .65rem 1.1rem;
    margin-bottom: 1.6rem;
    border-radius: 14px;
    background: rgba(15, 23, 41, 0.82);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid var(--line);
    box-shadow: 0 12px 30px -20px rgba(0, 0, 0, 0.8);
}

.topbar .crumbs {
    display: flex;
    align-items: center;
    gap: .55rem;
    font-size: .86rem;
    color: var(--muted);
}
.stApp .topbar .crumbs span { color: var(--muted); }
.stApp .topbar .crumbs b { color: var(--line-strong); font-weight: 500; }
.stApp .topbar .crumbs strong { color: var(--ink); font-weight: 600; }
.topbar .crumbs .ic { color: var(--muted); }

.topbar .status-row { display: flex; align-items: center; gap: 1.1rem; }

.stApp .status-pill {
    display: inline-flex;
    align-items: center;
    gap: .45rem;
    font-size: .68rem;
    font-weight: 600;
    letter-spacing: .09em;
    text-transform: uppercase;
    color: var(--muted);
    white-space: nowrap;
}
.status-pill i {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--teal);
    animation: pulseDot 2.4s infinite;
}
.status-pill.idle i { background: var(--amber); animation: none; }

/* ---------- Page header ---------- */
.page-head { margin: .2rem 0 1.8rem; scroll-margin-top: 90px; }

.stApp .page-head .eyebrow {
    display: block;
    font-size: .7rem;
    font-weight: 700;
    letter-spacing: .14em;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: .5rem;
}

.stApp .page-head h1 {
    margin: 0 0 .55rem;
    padding: 0;
    font-family: var(--font-display);
    font-size: 2.35rem;
    line-height: 1.12;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: var(--ink) !important;
}

.stApp .page-head h1 em {
    font-style: normal;
    color: var(--gold);
}

.stApp .page-head p {
    margin: 0;
    max-width: 640px;
    color: var(--muted) !important;
    font-size: 1rem;
    line-height: 1.65;
}

/* ---------- Overview tiles ---------- */
.ov-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: .9rem;
    margin-bottom: .6rem;
}

.ov-card {
    padding: 1.15rem 1.2rem 1.05rem;
    border-radius: var(--radius);
    background: var(--panel);
    border: 1px solid var(--line);
    box-shadow: var(--shadow-sm);
    transition: border-color .25s var(--ease), transform .25s var(--ease);
}
.ov-card:hover { border-color: var(--line-strong); transform: translateY(-1px); }

.ov-ico {
    width: 34px; height: 34px;
    border-radius: 10px;
    display: grid; place-items: center;
    margin-bottom: 1.05rem;
    color: var(--indigo);
    background: var(--indigo-soft);
    border: 1px solid rgba(147, 162, 255, 0.18);
}
.ov-card.gold  .ov-ico { color: var(--gold);  background: var(--gold-soft);  border-color: var(--gold-line); }
.ov-card.teal  .ov-ico { color: var(--teal);  background: var(--teal-soft);  border-color: rgba(63, 208, 174, 0.25); }
.ov-card.rose  .ov-ico { color: var(--rose);  background: var(--rose-soft);  border-color: rgba(240, 98, 111, 0.28); }
.ov-card.amber .ov-ico { color: var(--amber); background: var(--amber-soft); border-color: rgba(242, 178, 76, 0.28); }

.stApp .ov-label { display: block; font-size: .8rem; color: var(--muted); font-weight: 500; }
.stApp .ov-value {
    display: block;
    margin: .2rem 0 .25rem;
    font-family: var(--font-display);
    font-size: 1.95rem;
    font-weight: 700;
    line-height: 1.1;
    color: var(--ink);
}
.stApp .ov-sub { display: block; font-size: .74rem; color: var(--muted); opacity: .85; }

/* ---------- Section headings ---------- */
.section-head {
    display: flex;
    align-items: center;
    gap: .95rem;
    margin: 3rem 0 1.2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--line);
    scroll-margin-top: 90px;
}

.section-head .icon {
    width: 44px;
    height: 44px;
    flex: none;
    border-radius: 12px;
    display: grid;
    place-items: center;
    font-size: 1.15rem;
    color: var(--gold);
    background: var(--gold-soft);
    border: 1px solid var(--gold-line);
}

.stApp .section-head h2 {
    margin: 0;
    padding: 0;
    font-family: var(--font-display);
    font-size: 1.4rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--ink);
}

.stApp .section-head span.sub {
    display: block;
    color: var(--muted);
    font-size: .88rem;
    margin-top: .18rem;
}

/* ---------- Cards ---------- */
.card {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 1.15rem 1.35rem;
    margin-bottom: 1rem;
    box-shadow: var(--shadow-sm);
    transition: border-color .25s var(--ease);
}
.card:hover { border-color: var(--line-strong); }

.stApp .card h4 {
    margin: 0 0 .65rem;
    padding: 0;
    font-size: .95rem;
    font-weight: 700;
    color: var(--ink);
}

.card ul { margin: 0; padding-left: 1.1rem; color: var(--text); }
.card li { margin-bottom: .42rem; line-height: 1.6; color: var(--text); }
.card li::marker { color: var(--gold); }
.card .empty {
    color: var(--muted);
    font-style: normal;
    margin: 0;
    padding: 1rem;
    text-align: center;
    border: 1px dashed var(--line-strong);
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.015);
    font-size: .9rem;
}
.card p { margin: 0; line-height: 1.65; color: var(--text); }

.card.result { border-left: 3px solid var(--gold); }

.card.risk { border-left: 3px solid var(--rose); }
.card.risk .rtype { font-weight: 700; color: #FF8A95; margin-bottom: .45rem; }

.card.blockers  { border-top: 3px solid var(--rose); }
.card.decisions { border-top: 3px solid var(--amber); }
.card.actions   { border-top: 3px solid var(--teal); }
.card.blockers li::marker  { color: var(--rose); }
.card.decisions li::marker { color: var(--amber); }
.card.actions li::marker   { color: var(--teal); }

/* ---------- Pills ---------- */
.stApp .pill {
    display: inline-block;
    font-size: .72rem;
    font-weight: 600;
    padding: .2rem .65rem;
    margin: .5rem .35rem 0 0;
    border-radius: 999px;
    color: var(--gold);
    background: var(--gold-soft);
    border: 1px solid var(--gold-line);
}

.stApp .pill.source {
    color: var(--teal);
    background: var(--teal-soft);
    border-color: rgba(63, 208, 174, 0.3);
}

/* ---------- Stat tiles ---------- */
.stat {
    position: relative;
    display: flex;
    flex-direction: column;
    padding: .95rem 1.1rem;
    border-radius: 14px;
    background: var(--panel);
    border: 1px solid var(--line);
    box-shadow: var(--shadow-sm);
    overflow: hidden;
}

.stat::before {
    content: "";
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: var(--gold);
}

.stat .value {
    font-family: var(--font-display);
    font-size: 1.8rem;
    font-weight: 700;
    line-height: 1.1;
    color: var(--ink);
}

.stat .label {
    margin-top: .25rem;
    font-size: .78rem;
    font-weight: 500;
    color: var(--muted);
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: #0A101D;
    border-right: 1px solid var(--line);
}

section[data-testid="stSidebar"] > div { padding-top: .6rem; }

section[data-testid="stSidebar"] :is(p, span, label, li, h1, h2, h3, h4, h5) {
    color: var(--text);
}

section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
section[data-testid="stSidebar"] small {
    color: var(--muted) !important;
}

section[data-testid="stSidebar"] hr { margin: 1rem 0 !important; }

.side-brand {
    display: flex;
    align-items: center;
    gap: .75rem;
    padding: .2rem .2rem .3rem;
}
.side-brand .mark {
    width: 40px; height: 40px;
    flex: none;
    border-radius: 11px;
    display: grid; place-items: center;
    color: var(--gold);
    background: var(--panel-2);
    border: 1px solid var(--line-strong);
}
.stApp .side-brand .name { font-family: var(--font-display); font-weight: 700; font-size: 1rem; color: var(--ink); line-height: 1.2; display: block; }
.stApp .side-brand .tag { font-size: .6rem; font-weight: 600; letter-spacing: .14em; text-transform: uppercase; color: var(--muted); margin-top: .2rem; display: block; }

.side-label {
    font-size: .66rem;
    font-weight: 700;
    letter-spacing: .14em;
    text-transform: uppercase;
    color: var(--muted);
    margin: .3rem 0 .55rem .3rem;
}

.nav { display: flex; flex-direction: column; gap: .15rem; margin-bottom: 1.2rem; }

.stApp .nav a {
    display: flex;
    align-items: center;
    gap: .75rem;
    padding: .55rem .7rem;
    border-radius: 10px;
    font-size: .88rem;
    font-weight: 500;
    color: var(--muted);
    text-decoration: none;
    border: 1px solid transparent;
    transition: background .2s var(--ease), color .2s var(--ease), border-color .2s var(--ease);
}
.stApp .nav a .ic { color: var(--muted); transition: color .2s var(--ease); }
.stApp .nav a:hover {
    background: var(--panel-2);
    color: var(--ink);
    border-color: var(--line);
}
.stApp .nav a:hover .ic { color: var(--gold); }

.steps { display: flex; flex-direction: column; gap: .4rem; }

.step {
    display: flex;
    align-items: center;
    gap: .7rem;
    padding: .5rem .7rem;
    border-radius: 10px;
    font-size: .84rem;
    font-weight: 500;
    color: var(--muted);
    background: transparent;
    border: 1px solid var(--line);
}

.step .tick {
    width: 20px; height: 20px; flex: none;
    border-radius: 50%;
    display: grid; place-items: center;
    font-size: .65rem; font-weight: 700;
    color: var(--muted);
    background: var(--track);
}

.step.done { color: var(--ink); background: var(--panel-2); }
.step.done .tick { color: #0B1220; background: var(--teal); }

.side-status {
    display: flex;
    align-items: center;
    gap: .7rem;
    margin-top: 1.1rem;
    padding: .7rem .9rem;
    border-radius: 12px;
    background: var(--panel);
    border: 1px solid var(--line-strong);
    font-size: .85rem;
    color: var(--text);
}
.side-status .ic { color: var(--muted); }
.side-status .grow { flex: 1; }
.side-status i {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--teal);
    animation: pulseDot 2.4s infinite;
}

.stApp .side-foot {
    margin-top: .9rem;
    padding-left: .3rem;
    font-size: .72rem;
    color: var(--muted);
    display: flex; align-items: center; gap: .5rem;
}

/* ---------- File uploader ---------- */
[data-testid="stFileUploader"] section {
    background: rgba(255, 255, 255, 0.018);
    border: 1.5px dashed var(--line-strong);
    border-radius: var(--radius);
    padding: 1.5rem;
    transition: border-color .25s var(--ease), background .25s var(--ease);
}

[data-testid="stFileUploader"] section:hover {
    border-color: var(--gold);
    background: var(--gold-soft);
}

[data-testid="stFileUploader"] section span,
[data-testid="stFileUploader"] section small,
[data-testid="stFileUploader"] section div { color: var(--muted); }

[data-testid="stFileUploader"] section button {
    background: var(--panel-2);
    color: var(--ink);
    border: 1px solid var(--line-strong);
    border-radius: 10px;
    font-weight: 600;
}
[data-testid="stFileUploader"] section button:hover { border-color: var(--gold); color: var(--gold); }

[data-testid="stFileUploaderFile"] {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: .2rem .5rem;
}

/* ---------- Inputs ---------- */
.stTextInput input {
    background: var(--panel) !important;
    border: 1px solid var(--line-strong) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
    padding: .8rem 1rem !important;
    transition: border-color .2s, box-shadow .2s;
}

.stTextInput input::placeholder { color: var(--muted) !important; opacity: 1 !important; }

.stTextInput input:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 3px rgba(230, 185, 106, 0.18) !important;
}

.stTextInput label p, .stSelectbox label p, .stFileUploader label p {
    font-weight: 600;
    font-size: .86rem;
    color: var(--ink);
}

div[data-baseweb="select"] > div {
    background: var(--panel);
    border-color: var(--line-strong);
    border-radius: 12px;
    color: var(--text);
    min-height: 46px;
    transition: border-color .2s, box-shadow .2s;
}

div[data-baseweb="select"] > div:hover { border-color: var(--gold-deep); }
div[data-baseweb="select"] > div:focus-within {
    border-color: var(--gold);
    box-shadow: 0 0 0 3px rgba(230, 185, 106, 0.18);
}

div[data-baseweb="select"] span,
div[data-baseweb="select"] input { color: var(--text) !important; }
div[data-baseweb="select"] svg { fill: var(--muted); }

div[data-baseweb="popover"] > div {
    border-radius: 12px;
    border: 1px solid var(--line-strong);
    box-shadow: 0 22px 44px -18px rgba(0, 0, 0, 0.8);
    overflow: hidden;
    background: var(--panel-2);
}
div[data-baseweb="popover"] ul { background: var(--panel-2); padding: .3rem; }
div[data-baseweb="popover"] li { border-radius: 8px; color: var(--text); transition: background .15s; }
div[data-baseweb="popover"] li:hover,
div[data-baseweb="popover"] li[aria-selected="true"] { background: var(--panel-3); }

/* ---------- Buttons ---------- */
.stButton > button,
.stDownloadButton > button {
    border-radius: 11px;
    border: 1px solid var(--line-strong);
    background: var(--panel-2);
    color: var(--ink);
    font-weight: 600;
    padding: .55rem 1.3rem;
    box-shadow: var(--shadow-sm);
    transition: transform .2s var(--ease), border-color .2s, background .2s, box-shadow .2s;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: var(--gold);
    background: var(--panel-3);
    transform: translateY(-1px);
}

.stButton > button:active, .stDownloadButton > button:active { transform: translateY(0) scale(.985); }

.stButton > button:hover p,
.stDownloadButton > button:hover p { color: var(--gold); }

.stButton > button:focus-visible, .stDownloadButton > button:focus-visible {
    outline: 3px solid rgba(230, 185, 106, .35);
    outline-offset: 2px;
}

.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(180deg, #EBC67D 0%, #D7A653 100%);
    border: 1px solid #F0CF8F;
    color: #1B1406;
    box-shadow: 0 10px 22px -12px rgba(230, 185, 106, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.stButton > button[kind="primary"] p,
.stButton > button[data-testid="stBaseButton-primary"] p { color: #1B1406; font-weight: 700; }

.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
    filter: brightness(1.06);
    background: linear-gradient(180deg, #EBC67D 0%, #D7A653 100%);
    border-color: #F5D99D;
}

.stButton > button[kind="primary"]:hover p,
.stButton > button[data-testid="stBaseButton-primary"]:hover p { color: #1B1406; }

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {
    gap: .25rem;
    background: var(--panel);
    padding: .3rem;
    border-radius: 13px;
    border: 1px solid var(--line);
    width: fit-content;
    max-width: 100%;
    overflow-x: auto;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 9px;
    padding: .5rem 1.05rem;
    color: var(--muted);
    font-weight: 600;
    font-size: .88rem;
    transition: background .2s, color .2s;
}

.stTabs [data-baseweb="tab"]:hover { background: var(--panel-2); color: var(--ink); }

.stTabs [aria-selected="true"] {
    background: var(--gold-soft) !important;
    box-shadow: inset 0 0 0 1px var(--gold-line);
}

.stTabs [aria-selected="true"],
.stTabs [aria-selected="true"] p { color: var(--gold) !important; }

.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none; }

.stTabs [data-baseweb="tab-panel"] { padding-top: 1.4rem; }

/* ---------- Alerts, expanders, metrics, chat ---------- */
[data-testid="stAlert"] {
    border-radius: 12px;
    border: 1px solid var(--line);
}

[data-testid="stExpander"] {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 14px;
    box-shadow: var(--shadow-sm);
    overflow: hidden;
}

[data-testid="stExpander"] details { border: none; }

[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary p { color: var(--ink); font-weight: 600; }

[data-testid="stExpander"] summary:hover { background: var(--panel-2); }

[data-testid="stExpander"] pre,
[data-testid="stText"] { background: var(--bg-soft); color: var(--text); border-radius: 10px; }

[data-testid="stMetric"] {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 1rem 1.2rem;
    box-shadow: var(--shadow-sm);
}

[data-testid="stMetricValue"] { color: var(--ink); font-family: var(--font-display); }

div[data-testid="stProgress"] > div > div { background: var(--track); }
div[data-testid="stProgress"] > div > div > div > div {
    background: linear-gradient(90deg, var(--gold-deep), var(--gold));
    border-radius: 999px;
}

[data-testid="stChatMessage"] {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 16px;
    box-shadow: var(--shadow-sm);
    padding: 1rem 1.2rem;
}

[data-testid="stBottom"] > div { background: transparent; }

div[data-testid="stChatInput"] {
    background: var(--panel);
    border-radius: 16px;
    border: 1px solid var(--line-strong);
    box-shadow: var(--shadow);
}

div[data-testid="stChatInput"]:focus-within { border-color: var(--gold); }

div[data-testid="stChatInput"] textarea {
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
    caret-color: var(--gold) !important;
    background-color: var(--panel) !important;
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
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 1.35rem 1.5rem;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
}

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
    background: var(--panel);
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    box-shadow: inset 0 0 0 1px var(--line);
}

.gauge-inner .gv { font-family: var(--font-display); font-size: 2.2rem; font-weight: 700; line-height: 1; color: var(--ink); }
.gauge-inner small { color: var(--muted); font-size: .75rem; margin-top: .2rem; }
.gauge-status { font-weight: 700; font-size: 1.1rem; }
.gauge-label { color: var(--muted); font-size: .85rem; }

.dim { margin-bottom: .9rem; }
.dim-top { display: flex; justify-content: space-between; font-size: .9rem; margin-bottom: .3rem; color: var(--text); }

.dim-track {
    height: 8px;
    border-radius: 999px;
    background: var(--track);
    overflow: hidden;
}

.dim-fill {
    height: 100%;
    border-radius: 999px;
    transform-origin: left center;
    animation: growX 1s var(--ease) both;
}

.risk-row {
    background: var(--panel);
    border: 1px solid var(--line);
    border-left: 3px solid var(--rose);
    border-radius: 12px;
    padding: .85rem 1.05rem;
    margin-bottom: .65rem;
    box-shadow: var(--shadow-sm);
    transition: border-color .25s var(--ease);
}
.risk-row:hover { border-color: var(--line-strong); border-left-color: var(--rose); }

.risk-row .risk-title { font-weight: 700; font-size: .92rem; color: #FF8A95; margin-bottom: .25rem; }
.risk-row .risk-ev { color: var(--text); font-size: .88rem; line-height: 1.55; }

.legend {
    display: flex; flex-wrap: wrap; gap: .4rem .9rem;
    margin-top: .6rem; font-size: .82rem;
    color: var(--muted); justify-content: center;
}
.legend .lg { display: inline-flex; align-items: center; gap: .35rem; }
.legend i { width: 10px; height: 10px; border-radius: 4px; display: inline-block; }

.dash-title {
    font-family: var(--font-display);
    font-size: 1rem;
    font-weight: 700;
    margin: .4rem 0 .8rem;
    color: var(--ink);
}

.kpi-card {
    position: relative;
    overflow: hidden;
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 1.1rem 1.3rem;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
}

.kpi-card::before {
    content: "";
    position: absolute;
    left: 0; right: 0; top: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--gold), transparent 70%);
}

.kpi-label {
    font-size: .7rem;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--muted);
}

.kpi-value {
    font-family: var(--font-display);
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--ink);
    margin: .35rem 0;
}

.kpi-sub { font-size: .84rem; color: var(--muted); }

.level-badge {
    display: inline-block;
    font-size: .9rem;
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
    font-size: .78rem;
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
    font-size: .9rem; font-weight: 600;
    margin-bottom: .4rem; color: var(--text);
}

/* ---------- Scrollbars ---------- */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: rgba(147, 162, 255, .22); border-radius: 999px; border: 2px solid transparent; background-clip: content-box; }
::-webkit-scrollbar-thumb:hover { background: rgba(230, 185, 106, .5); background-clip: content-box; border: 2px solid transparent; }

/* ---------- Responsive ---------- */
@media (max-width: 1000px) {
    .ov-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .stApp .page-head h1 { font-size: 2rem; }
}

@media (max-width: 800px) {
    .radar-wrap { grid-template-columns: 1fr; }
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    .stApp .page-head h1 { font-size: 1.7rem; }
    .section-head { margin-top: 2.2rem; gap: .8rem; }
    .stApp .section-head h2 { font-size: 1.2rem; }
    .section-head .icon { width: 40px; height: 40px; }
    .topbar .status-row .status-pill:nth-child(2) { display: none; }
}

@media (max-width: 520px) {
    .ov-grid { grid-template-columns: 1fr; }
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


def risk_meta_pills(risk, compact=False):
    """
    Pills for the extra fields of the improved risk agent: confidence,
    likelihood / impact / status when the document states them, and where
    the risk came from. Missing fields are simply left out (older saved
    results have none of them).
    """

    def level_text(value):
        return f"{value}/5" if isinstance(value, int) else None

    pills = []

    confidence = risk.get("confidence")
    if confidence:
        pills.append(("pill", f"Confidence: {confidence}"))

    if not compact:
        for label, key in (("Likelihood", "likelihood"), ("Impact", "impact")):
            text = level_text(risk.get(key))
            if text:
                pills.append(("pill", f"{label}: {text} (stated)"))

    if risk.get("mitigation_status"):
        pills.append(("pill", f"Status: {risk['mitigation_status']}"))

    source_document = risk.get("source_document")
    source_line = risk.get("source_line")
    if source_document or (not compact and source_line):
        place = source_document or "original document"
        if source_line and not compact:
            place += f" · line {source_line}"
        pills.append(("pill source", f"Source: {place}"))

    also = risk.get("also_found_in")
    if also and not compact and isinstance(also, (list, tuple)):
        pills.append(("pill source", "Also in: " + ", ".join(str(a) for a in also)))

    return "".join(
        f'<span class="{css}">{esc(text)}</span>' for css, text in pills
    )


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
        f'{pills}{risk_meta_pills(risk, compact=True)}</div>'
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



# --------------------------------------------------
# ICONS (inline SVG, UI only)
# --------------------------------------------------

_ICON_PATHS = {
    "brand": '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/><path d="M10 6.5h2.5a2 2 0 0 1 2 2V14"/>',
    "overview": '<path d="M3 13a9 9 0 1 1 18 0"/><path d="M12 13l4-4"/>',
    "docs": '<rect x="8" y="3" width="12" height="14" rx="2"/><path d="M16 21H6a2 2 0 0 1-2-2V8"/>',
    "upload": '<path d="M12 16V4"/><path d="M7 9l5-5 5 5"/><path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/>',
    "update": '<path d="M20 12a8 8 0 1 1-2.6-5.9"/><path d="M20 4v5h-5"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2"/>',
    "shield": '<path d="M12 3l8 3v6c0 4.5-3.2 7.6-8 9-4.8-1.4-8-4.5-8-9V6z"/>',
    "tasks": '<path d="M10 6h10M10 12h10M10 18h10"/><path d="M3.5 6l1.5 1.5L7.5 5M3.5 12l1.5 1.5 2.5-2.5M3.5 18l1.5 1.5 2.5-2.5"/>',
    "write": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
    "heart": '<path d="M19 14c1.5-1.5 2-3 2-4.5A4.5 4.5 0 0 0 12 7a4.5 4.5 0 0 0-9 2.5c0 4.5 6 9 9 11 1.4-.9 3.2-2.3 4.8-4"/><path d="M3 12h4l2-3 3 6 2-3h2"/>',
    "chat": '<path d="M21 12a8 8 0 0 1-11.5 7.2L4 20l1-4.2A8 8 0 1 1 21 12z"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/>',
    "pulse": '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 0 0-.1-1.2l2-1.5-2-3.4-2.3.9a7 7 0 0 0-2-1.2L14.3 3h-4.6l-.4 2.6a7 7 0 0 0-2 1.2l-2.3-.9-2 3.4 2 1.5a7 7 0 0 0 0 2.4l-2 1.5 2 3.4 2.3-.9a7 7 0 0 0 2 1.2l.4 2.6h4.6l.4-2.6a7 7 0 0 0 2-1.2l2.3.9 2-3.4-2-1.5c.1-.4.1-.8.1-1.2z"/>',
    "book": '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 19V5M9 7h6"/>',
    "alert": '<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.01"/>',
    "check": '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M8.5 12.5l2.5 2.5 4.5-5"/>',
    "box": '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M12 12l8-4.5M12 12v9M12 12L4 7.5"/>',
    "lock": '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
}


def icon(name, size=18):
    return (
        f'<svg class="ic" width="{size}" height="{size}" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        f'{_ICON_PATHS.get(name, "")}</svg>'
    )


def nav_link(href, icon_name, label):
    return f'<a href="#{href}" target="_self">{icon(icon_name)}<span>{esc(label)}</span></a>'


def overview_tile(icon_name, tone, label, value, sub):
    return (
        f'<div class="ov-card {tone}"><div class="ov-ico">{icon(icon_name, 17)}</div>'
        f'<span class="ov-label">{esc(label)}</span>'
        f'<span class="ov-value">{esc(value)}</span>'
        f'<span class="ov-sub">{esc(sub)}</span></div>'
    )


def render_overview(slot):
    """Read-only summary of what is already in session state."""

    state = st.session_state

    def count_of(container, key):
        if isinstance(container, dict):
            value = container.get(key)
            return len(value) if isinstance(value, (list, tuple)) else 0
        return 0

    documents = len(state.processed_documents)

    risks = (
        str(len(unique_risk_records(state.risk_results)))
        if state.risk_results is not None else "—"
    )
    blockers = (
        str(count_of(state.blocker_results, "blockers"))
        if state.blocker_results is not None else "—"
    )
    actions = (
        str(count_of(state.blocker_results, "action_items"))
        if state.blocker_results is not None else "—"
    )
    deliverables = (
        str(count_of(state.scope_results, "deliverables"))
        if state.scope_results is not None else "—"
    )

    health_value, health_sub = "—", "Calculate in Project Health"
    if isinstance(state.health_results, dict):
        health_value = f'{state.health_results.get("overall_score", 0)} / 100'
        health_sub = str(state.health_results.get("status", ""))
        assessed_dims = state.health_results.get("assessed_dimensions")

        if isinstance(assessed_dims, int) and assessed_dims < 5:
            health_sub += f" · {assessed_dims}/5 assessed"

    docs_value, docs_sub = "—", "Generate in Documentation tab"
    generated = state.documentation_results
    if isinstance(generated, dict):
        extra = generated.get("action_items", {})
        docs_value = str(
            len(generated.get("user_stories", []) or [])
            + len(generated.get("risk_register", []) or [])
            + sum(
                len(v) for v in extra.values() if isinstance(v, (list, tuple))
            ) if isinstance(extra, dict) else
            len(generated.get("user_stories", []) or [])
            + len(generated.get("risk_register", []) or [])
        )
        docs_sub = "Stories, risks and actions"

    slot.markdown(
        '<div class="ov-grid">'
        + overview_tile("docs", "", "Documents processed", documents, "Indexed this session")
        + overview_tile("box", "teal", "Chunks stored", state.total_chunks, "In the vector store")
        + overview_tile("shield", "gold", "Identified risks", risks, "Risk detection findings")
        + overview_tile("alert", "rose", "Total blockers", blockers, "From blocker analysis")
        + overview_tile("check", "", "Action items", actions, "Pending follow-ups")
        + overview_tile("target", "teal", "Deliverables", deliverables, "Scope agent output")
        + overview_tile("heart", "amber", "Project health", health_value, health_sub)
        + overview_tile("write", "gold", "Generated documentation", docs_value, docs_sub)
        + "</div>",
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.markdown(
        '<div class="side-brand"><div class="mark">' + icon("brand", 20) + '</div>'
        '<div><span class="name">Project Intelligence</span>'
        '<span class="tag">Intelligence platform</span></div></div>',
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown(
        '<div class="side-label">Workspace</div><div class="nav">'
        + nav_link("overview", "overview", "Overview")
        + nav_link("document-ingestion", "upload", "Document upload")
        + nav_link("add-updates", "update", "Incremental upload")
        + '</div>'
        '<div class="side-label">Project intelligence</div><div class="nav">'
        + nav_link("project-intelligence-agents", "target", "Scope & Deliverables")
        + nav_link("project-intelligence-agents", "shield", "Risk Intelligence")
        + nav_link("project-intelligence-agents", "tasks", "Blockers & Actions")
        + nav_link("milestone-3-project-intelligence", "write", "Documentation generation")
        + nav_link("milestone-3-project-intelligence", "heart", "Project health")
        + nav_link("milestone-3-project-intelligence", "chat", "Project assistant")
        + '</div>'
        '<div class="side-label">Analytics & insights</div><div class="nav">'
        + nav_link("milestone-4-insights-dashboard", "chart", "Project insights")
        + '</div>',
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown('<div class="side-label">At a glance</div>', unsafe_allow_html=True)

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
        + "</div>"
        '<div class="side-status">' + icon("pulse") + '<span class="grow">Workspace ready</span><i></i></div>'
        '<div class="side-foot">' + icon("lock", 14) + 'Local-first project workspace</div>',
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# HERO
# --------------------------------------------------

st.markdown(
    '<div class="topbar" id="overview">'
    '<div class="crumbs">' + icon("book", 17)
    + '<span>Project Intelligence</span><b>/</b><strong>Overview</strong></div>'
    '<div class="status-row">'
    '<span class="status-pill"><i></i>App running</span>'
    f'<span class="status-pill"><i></i>{len(st.session_state.processed_documents)} documents indexed</span>'
    '</div></div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="page-head">
        <span class="eyebrow">Workspace</span>
        <h1>AI Project Intelligence &amp; <em>Risk Advisor</em></h1>
        <p>Upload project documents, search their contents, and analyze
        scope, risks, blockers, and action items.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

overview_slot = st.empty()


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
            "it does not calculate a reliable delivery-date forecast. "
            "Likelihood, impact and status are shown only when the "
            "document states them."
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
                            {pills}{risk_meta_pills(risk)}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            else:
                st.info(
                    "No risks matched the current keyword rules. "
                    "This does not prove the project has no risks."
                )

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

                assessed_count = health.get("assessed_dimensions")

                if assessed_count is not None:
                    st.caption(
                        f"Based on {assessed_count} of 5 assessed dimensions."
                    )

            with col2:

                st.markdown("**Project Status**")

                if status == "Healthy":
                    st.success(status)

                elif status in ("Moderate Risk", "High Risk"):
                    st.warning(status)

                elif status == "Critical":
                    st.error(status)

                else:
                    st.info(status)

            # An analysis agent failed or returned unusable output: say so
            # instead of silently showing a clean score.
            for agent_error in health.get("agent_errors", []) or []:
                st.warning(str(agent_error))

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

            elif status == "High Risk":

                st.warning(
                    "The project has high risk. Review the identified "
                    "risks, timeline issues and blockers soon to avoid "
                    "delivery problems."
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

            list_card(
                "Risk Score Findings",
                assessment.get("risk", []),
                "No scored risks to report."
            )

            st.markdown("#### 3. Blocker & Dependency Assessment")

            list_card(
                "Blockers and Pending Decisions",
                assessment.get("blockers", []),
                "No blockers or pending decisions detected."
            )

            quality_findings = assessment.get("quality", [])

            if quality_findings:

                st.markdown("#### Quality Assessment")

                list_card(
                    "Quality Findings",
                    quality_findings,
                    "No quality evidence available."
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
            col4, col5, _spare = st.columns(3)

            score_dimensions = [
                ("Scope Score", "scope_score", "scope", col1),
                ("Timeline Score", "timeline_score", "schedule", col2),
                ("Risk Score", "risk_score", "risk", col3),
                ("Quality Score", "quality_score", "quality", col4),
                ("Blocker Score", "blocker_score", "blocker", col5),
            ]

            dimension_info = health.get("dimension_status", {}) or {}

            for label, key, status_key, column in score_dimensions:

                value = health.get(key)
                info = dimension_info.get(status_key) or {}
                assessed = info.get("assessed", True)

                with column:

                    # Results saved by an older version may lack a score,
                    # and a dimension without evidence has no real score.
                    if value is None or not assessed:

                        st.metric(label, "Not assessed")
                        st.progress(0.0)

                        if info.get("basis"):
                            st.caption(info["basis"])

                    else:

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
        With no detected risks the level is "NONE DETECTED" and the score 0
        (keyword detection finding nothing is not proof of no risk).
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
                f'stroke="#2A3957" stroke-width="1"{dash}/>'
            )
            parts.append(
                f'<text x="{cx + 4}" y="{cy - radius * level / 100 + 3:.1f}" '
                f'font-size="8" fill="#5E6C8A">{level}</text>'
            )

        for index in range(count):
            x, y = point(index, 100)
            parts.append(
                f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" '
                'stroke="#2A3957" stroke-width="1"/>'
            )

        shape = " ".join(
            f"{x:.1f},{y:.1f}"
            for x, y in (
                point(i, dash_clamp(factor[1]))
                for i, factor in enumerate(factors)
            )
        )

        parts.append(
            f'<polygon points="{shape}" fill="rgba(230,185,106,0.18)" '
            'stroke="#E6B96A" stroke-width="2.5" stroke-linejoin="round"/>'
        )

        for index, factor in enumerate(factors):

            label, value = factor[0], factor[1]
            assessed = factor[2] if len(factor) > 2 else True

            dot_color = dash_score_color(value) if assessed else "#5E6C8A"
            x, y = point(index, dash_clamp(value))
            parts.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" '
                f'fill="{dot_color}" stroke="#121B2E" '
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
                f'font-size="12" font-weight="600" fill="#D5DDEC">'
                f'{esc(label)}</text>'
                f'<text x="{lx:.1f}" y="{score_y:.1f}" text-anchor="{anchor}" '
                f'font-size="11" font-weight="600" fill="{dot_color}">'
                f'{esc(score_text)}</text>'
            )

        parts.append(
            f'<text x="{cx}" y="{cy + 6}" text-anchor="middle" font-size="26" '
            f'font-weight="700" fill="#E6B96A" opacity="0.85">{esc(center_value)}</text>'
            f'<text x="{cx}" y="{cy + 20}" text-anchor="middle" font-size="9" '
            'fill="#8793AE">health score</text></svg>'
        )

        return "".join(parts)


    def dash_clamp(value):
        try:
            return max(0.0, min(float(value), 100.0))
        except (TypeError, ValueError):
            return 0.0


    def dash_status_color(status_value):
        return {
            "Healthy": "#3FD0AE",
            "Moderate Risk": "#F2B24C",
            "High Risk": "#F08A4B",
            "Critical": "#F0626F",
        }.get(status_value, "#E6B96A")


    def dash_score_color(value):
        pct = dash_clamp(value)
        return (
            "#3FD0AE" if pct >= 70
            else "#F2B24C" if pct >= 40
            else "#F0626F"
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
            color = dash_score_color(value) if assessed else "#5E6C8A"
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

                if risk_info.get("risk_count", 0) == 0:
                    risk_sub = "None detected · keyword-based"
                else:
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



# Fill the overview tiles once the whole run has finished,
# so they always reflect the latest session state.
render_overview(overview_slot)
