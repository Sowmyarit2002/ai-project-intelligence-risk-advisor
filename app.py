import html

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
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=DM+Sans:wght@400;500;600&display=swap');

:root {
    --bg: #F5F7FF;
    --panel: #FFFFFF;
    --panel-2: #EEF1FF;
    --line: rgba(91, 91, 240, 0.16);
    --text: #1E2347;
    --muted: #5B6490;
    --indigo: #5B5BF0;
    --aqua: #0FB5A6;
    --aqua-dark: #0A857B;
    --amber: #F59E0B;
    --rose: #EF476F;
    --shadow: 0 4px 16px rgba(60, 70, 160, 0.08);
}

html, body, [class*="css"], .stApp {
    font-family: 'DM Sans', sans-serif;
    color: var(--text);
}

.stApp {
    background:
        radial-gradient(900px 500px at 90% -10%, rgba(124,131,255,0.22), transparent 60%),
        radial-gradient(700px 420px at -5% 10%, rgba(15,181,166,0.16), transparent 60%),
        radial-gradient(600px 400px at 50% 110%, rgba(255,180,84,0.14), transparent 60%),
        var(--bg);
}

/* Make sure all default Streamlit text stays readable on the light theme */
.stApp p, .stApp li, .stApp label, .stApp span,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5,
.stMarkdown, [data-testid="stMarkdownContainer"],
[data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
    color: var(--text);
}

[data-testid="stCaptionContainer"], .stApp small {
    color: var(--muted) !important;
}

#MainMenu, footer, header[data-testid="stHeader"] {
    visibility: hidden;
    height: 0;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 4rem;
    max-width: 1180px;
}

h1, h2, h3, h4 {
    font-family: 'Sora', sans-serif;
    letter-spacing: -0.01em;
}

.hero {
    position: relative;
    padding: 2.4rem 2.4rem 2.2rem;
    border-radius: 22px;
    border: 1px solid var(--line);
    background:
        linear-gradient(135deg, rgba(124,131,255,0.16), rgba(15,181,166,0.12) 60%, rgba(255,180,84,0.14)),
        var(--panel);
    box-shadow: var(--shadow);
    overflow: hidden;
    margin-bottom: 1.6rem;
}

.hero::after {
    content: "";
    position: absolute;
    right: -80px;
    top: -80px;
    width: 280px;
    height: 280px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(15,181,166,0.30), transparent 70%);
    filter: blur(8px);
}

.hero .status {
    display: inline-flex;
    align-items: center;
    gap: .5rem;
    font-size: .82rem;
    font-weight: 500;
    color: var(--aqua-dark);
    background: rgba(15,181,166,0.12);
    border: 1px solid rgba(15,181,166,0.35);
    padding: .25rem .75rem;
    border-radius: 999px;
    margin-bottom: 1rem;
}

.hero .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--aqua);
    box-shadow: 0 0 0 0 rgba(15,181,166,.6);
    animation: pulse 2s infinite;
}

@keyframes pulse {
    70% { box-shadow: 0 0 0 9px rgba(15,181,166,0); }
    100% { box-shadow: 0 0 0 0 rgba(15,181,166,0); }
}

@media (prefers-reduced-motion: reduce) {
    .hero .dot { animation: none; }
}

.hero h1 {
    margin: 0 0 .6rem;
    font-size: 2.3rem;
    line-height: 1.15;
    font-weight: 700;
    background: linear-gradient(90deg, #4338CA 10%, #5B5BF0 50%, #0A9E92 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent !important;
    -webkit-text-fill-color: transparent;
}

.hero p {
    margin: 0;
    color: var(--muted);
    max-width: 640px;
    font-size: 1.02rem;
    line-height: 1.55;
}

.section-head {
    display: flex;
    align-items: center;
    gap: .9rem;
    margin: 2.4rem 0 1rem;
}

.section-head .icon {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    display: grid;
    place-items: center;
    font-size: 1.2rem;
    background: linear-gradient(135deg, #E4E7FF, #D6F6F1);
    border: 1px solid var(--line);
    box-shadow: var(--shadow);
}

.section-head h2 {
    margin: 0;
    font-size: 1.35rem;
    font-weight: 600;
    color: var(--text);
}

.section-head span.sub {
    display: block;
    color: var(--muted);
    font-size: .9rem;
    margin-top: .1rem;
}

.card {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 1.1rem 1.25rem;
    margin-bottom: .9rem;
    box-shadow: var(--shadow);
}

.card h4 {
    margin: 0 0 .6rem;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text);
}

.card ul {
    margin: 0;
    padding-left: 1.1rem;
    color: var(--text);
}

.card li {
    margin-bottom: .35rem;
    line-height: 1.5;
    color: var(--text);
}

.card .empty {
    color: var(--muted);
    font-style: italic;
    margin: 0;
}

.card p {
    margin: 0;
    line-height: 1.6;
    color: var(--text);
}

.card.result {
    border-left: 4px solid var(--indigo);
    background: linear-gradient(90deg, rgba(91,91,240,0.06), #FFFFFF 40%);
}

.card.risk {
    border-left: 4px solid var(--rose);
    background: linear-gradient(90deg, rgba(239,71,111,0.07), #FFFFFF 40%);
}

.card.risk .rtype {
    font-family: 'Sora', sans-serif;
    font-weight: 600;
    color: #C72A52;
    margin-bottom: .45rem;
}

.card.blockers {
    border-top: 4px solid var(--rose);
}

.card.decisions {
    border-top: 4px solid var(--amber);
}

.card.actions {
    border-top: 4px solid var(--aqua);
}

.pill {
    display: inline-block;
    font-size: .78rem;
    font-weight: 500;
    padding: .18rem .65rem;
    margin: .5rem .35rem 0 0;
    border-radius: 999px;
    color: #3F3FC8;
    background: rgba(91,91,240,0.10);
    border: 1px solid rgba(91,91,240,0.30);
}

.pill.source {
    color: var(--aqua-dark);
    background: rgba(15,181,166,0.12);
    border-color: rgba(15,181,166,0.35);
}

.stat {
    background: linear-gradient(135deg, #FFFFFF, #F0F3FF);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 1rem 1.2rem;
    box-shadow: var(--shadow);
}

.stat .value {
    font-family: 'Sora', sans-serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: var(--indigo);
}

.stat .label {
    color: var(--muted);
    font-size: .85rem;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #EEF1FF, #E6F8F5);
    border-right: 1px solid var(--line);
}

[data-testid="stFileUploader"] section {
    background: var(--panel);
    border: 1.5px dashed rgba(91,91,240,0.50);
    border-radius: 16px;
    padding: 1.4rem;
}

[data-testid="stFileUploader"] section:hover {
    border-color: var(--aqua);
    background: #F3FFFD;
}

[data-testid="stFileUploader"] section span,
[data-testid="stFileUploader"] section small,
[data-testid="stFileUploader"] section div {
    color: var(--muted);
}

[data-testid="stFileUploader"] section button {
    background: var(--panel-2);
    color: var(--indigo);
    border: 1px solid var(--line);
    border-radius: 10px;
}

.stTextInput input {
    background: var(--panel) !important;
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
    padding: .75rem 1rem !important;
}

.stTextInput input::placeholder {
    color: var(--muted) !important;
    opacity: 1 !important;
}

.stTextInput input:focus {
    border-color: var(--indigo) !important;
    box-shadow: 0 0 0 3px rgba(91,91,240,.20) !important;
}

.stButton > button {
    border-radius: 12px;
    border: 1px solid var(--line);
    background: var(--panel);
    color: var(--indigo);
    font-weight: 600;
    padding: .55rem 1.3rem;
    box-shadow: var(--shadow);
    transition: all .15s ease;
}

.stButton > button:hover {
    border-color: var(--indigo);
    color: var(--indigo);
    background: var(--panel-2);
    transform: translateY(-1px);
}

.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(90deg, #6366F1, #06B6D4);
    border: none;
    color: #FFFFFF;
}

.stButton > button[kind="primary"] p,
.stButton > button[data-testid="stBaseButton-primary"] p {
    color: #FFFFFF;
}

.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
    filter: brightness(1.07);
    color: #FFFFFF;
    background: linear-gradient(90deg, #6366F1, #06B6D4);
}

.stTabs [data-baseweb="tab-list"] {
    gap: .4rem;
    background: var(--panel);
    padding: .35rem;
    border-radius: 14px;
    border: 1px solid var(--line);
    box-shadow: var(--shadow);
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: .5rem 1.1rem;
    color: var(--muted);
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(90deg, rgba(91,91,240,0.14), rgba(15,181,166,0.14));
    color: var(--indigo) !important;
}

.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {
    display: none;
}

[data-testid="stExpander"] {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 14px;
    box-shadow: var(--shadow);
}

[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary p {
    color: var(--text);
}

[data-testid="stExpander"] pre,
[data-testid="stText"] {
    background: #F5F7FF;
    color: var(--text);
}

div[data-baseweb="select"] > div {
    background: var(--panel);
    border-color: var(--line);
    border-radius: 12px;
    color: var(--text);
}

div[data-baseweb="select"] span,
div[data-baseweb="select"] input {
    color: var(--text) !important;
}

[data-testid="stMetric"] {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: .8rem 1rem;
    box-shadow: var(--shadow);
}

[data-testid="stMetricValue"] {
    color: var(--indigo);
    font-family: 'Sora', sans-serif;
}

div[data-testid="stProgress"] > div > div > div > div {
    background: linear-gradient(90deg, #6366F1, #0FB5A6);
}

[data-testid="stChatMessage"] {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 14px;
    box-shadow: var(--shadow);
}

hr {
    border-color: var(--line) !important;
}

div[data-testid="stChatInput"] {
    background: var(--panel);
    border-radius: 14px;
}

div[data-testid="stChatInput"] textarea {
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
    caret-color: var(--indigo) !important;
    background-color: #FFFFFF !important;
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

/* ---------- Milestone 4: Insights dashboard ---------- */
.dash-card {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 1.2rem 1.3rem;
    box-shadow: var(--shadow);
    margin-bottom: .9rem;
}

.gauge-card {
    text-align: center;
}

.gauge {
    width: 160px;
    height: 160px;
    margin: .2rem auto .8rem;
    border-radius: 50%;
    background: conic-gradient(var(--clr) calc(var(--pct) * 1%), #E4E8FB 0);
    display: grid;
    place-items: center;
}

.gauge-inner {
    width: 122px;
    height: 122px;
    border-radius: 50%;
    background: #FFFFFF;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow: inset 0 0 0 1px var(--line);
}

.gauge-inner .gv {
    font-family: 'Sora', sans-serif;
    font-size: 2.4rem;
    font-weight: 700;
    line-height: 1;
    color: var(--text);
}

.gauge-inner small {
    color: var(--muted);
    font-size: .75rem;
    margin-top: .2rem;
}

.gauge-status {
    font-family: 'Sora', sans-serif;
    font-weight: 600;
    font-size: 1.1rem;
}

.gauge-label {
    color: var(--muted);
    font-size: .85rem;
}

.dim {
    margin-bottom: .9rem;
}

.dim-top {
    display: flex;
    justify-content: space-between;
    font-size: .9rem;
    margin-bottom: .3rem;
    color: var(--text);
}

.dim-track {
    height: 10px;
    border-radius: 999px;
    background: #E4E8FB;
    overflow: hidden;
}

.dim-fill {
    height: 100%;
    border-radius: 999px;
}

.risk-row {
    background: var(--panel);
    border: 1px solid var(--line);
    border-left: 4px solid var(--rose);
    border-radius: 14px;
    padding: .8rem 1rem;
    margin-bottom: .6rem;
    box-shadow: var(--shadow);
}

.risk-row .risk-title {
    font-family: 'Sora', sans-serif;
    font-weight: 600;
    font-size: .95rem;
    color: #C72A52;
    margin-bottom: .25rem;
}

.risk-row .risk-ev {
    color: var(--text);
    font-size: .9rem;
    line-height: 1.5;
}

.dash-title {
    font-family: 'Sora', sans-serif;
    font-size: 1rem;
    font-weight: 600;
    margin: .4rem 0 .7rem;
    color: var(--text);
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
    st.markdown(
        f"""
        <div class="section-head">
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
    st.markdown("### 📊 Project Intelligence")
    st.caption("Your documents, searched and analyzed.")
    st.divider()

    sidebar_stats_slot = st.empty()
    render_sidebar_stats(sidebar_stats_slot)

    st.divider()
    st.markdown("**Analyses completed**")

    st.write(
        ("✅" if st.session_state.scope_results is not None else "⚪")
        + " Scope & deliverables"
    )

    st.write(
        ("✅" if st.session_state.risk_results is not None else "⚪")
        + " Risk detection"
    )

    st.write(
        ("✅" if st.session_state.blocker_results is not None else "⚪")
        + " Blockers & actions"
    )


# --------------------------------------------------
# HERO
# --------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <div class="status"><span class="dot"></span> AI analysis ready</div>
        <h1>AI Project Intelligence &amp; Risk Advisor</h1>
        <p>Upload project documents, search their contents, and analyze
        scope, risks, blockers, and action items.</p>
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
# MODULE 2: SEMANTIC SEARCH
# --------------------------------------------------

section_header("🔎", "Search project documents", "Ask a question in plain language")

SEARCH_ALL_OPTION = "All documents"

try:
    searchable_documents = list_document_names()
except Exception:
    searchable_documents = []

for stored_name in st.session_state.processed_documents:
    if stored_name not in searchable_documents:
        searchable_documents.append(stored_name)

search_scope = st.selectbox(
    "Search in",
    options=searchable_documents + [SEARCH_ALL_OPTION],
    key="search_scope",
)

question = st.text_input(
    "Ask a question about your project documents",
    placeholder="Example: What is the project deadline?",
    label_visibility="collapsed",
)

if st.button("Search Documents"):

    if not question.strip():
        st.warning("Please enter a question.")

    else:
        try:
            with st.spinner("Searching project documents..."):

                query_embedding = generate_embeddings([question])[0]

                results = search_chunks(
                    query_embedding,
                    n_results=3,
                    filename=(
                        None
                        if search_scope == SEARCH_ALL_OPTION
                        else search_scope
                    )
                )

            if not isinstance(results, dict):
                st.session_state.search_results = None
                st.info("No documents found. Process a document first.")

            else:
                documents = results.get("documents", [[]])[0]

                if not documents:
                    st.session_state.search_results = None
                    st.info("No matching document chunks found.")

                else:
                    st.session_state.search_results = results

        except Exception as error:
            st.error(f"Search failed: {error}")


if st.session_state.search_results:

    search_data = st.session_state.search_results

    documents = search_data.get("documents", [[]])[0]
    metadata_list = search_data.get("metadatas", [[]])[0]

    st.markdown("#### Relevant results")

    for index, document in enumerate(documents, start=1):

        source_pill = ""

        if index <= len(metadata_list) and metadata_list[index - 1]:

            source = metadata_list[index - 1].get(
                "filename", "Unknown"
            )

            source_pill = (
                f'<span class="pill source">📄 {esc(source)}</span>'
            )

            update_source = metadata_list[index - 1].get("source")

            if update_source:
                source_pill += (
                    f'<span class="pill">🔄 update: {esc(update_source)}</span>'
                )

        st.markdown(
            f"""
            <div class="card result">
                <h4>Result {index}</h4>
                <p>{esc(document)}</p>
                {source_pill}
            </div>
            """,
            unsafe_allow_html=True,
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

            risks = st.session_state.risk_results

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
                            <div class="rtype">Potential Risk: {esc(risk.get('risk_type', 'Unknown'))}</div>
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
        "Project Intelligence",
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
    # MODULE 5: MILESTONE 4 - INSIGHTS & RISK DASHBOARD
    # --------------------------------------------------

    section_header(
        "📈",
        "Insights & Risk Dashboard",
        "Health score, risks, action items, and scope in one view"
    )

    def dash_status_color(status_value):
        return {
            "Healthy": "#10B981",
            "Moderate Risk": "#F59E0B",
            "Critical": "#EF476F",
        }.get(status_value, "#5B5BF0")

    def dash_clamp(value):
        try:
            return max(0.0, min(float(value), 100.0))
        except (TypeError, ValueError):
            return 0.0

    def dash_gauge(score_value, status_value):
        pct = dash_clamp(score_value)
        color = dash_status_color(status_value)
        return (
            '<div class="dash-card gauge-card">'
            f'<div class="gauge" style="--pct:{pct};--clr:{color}">'
            '<div class="gauge-inner">'
            f'<span class="gv">{int(pct)}</span><small>out of 100</small>'
            '</div></div>'
            f'<div class="gauge-status" style="color:{color}">{esc(status_value)}</div>'
            '<div class="gauge-label">Overall project health</div>'
            '</div>'
        )

    def dash_bar(label, value):
        pct = dash_clamp(value)
        color = (
            "#10B981" if pct >= 70
            else "#F59E0B" if pct >= 40
            else "#EF476F"
        )
        return (
            '<div class="dim"><div class="dim-top">'
            f'<span>{esc(label)}</span><b>{int(pct)}/100</b></div>'
            '<div class="dim-track">'
            f'<div class="dim-fill" style="width:{pct}%;background:{color}"></div>'
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

        st.info(
            "Click 'Generate Insights Dashboard' to run all analyses "
            "and see the project summary."
        )

    else:

        # ---- Row 1: health gauge + key numbers ----

        dash_left, dash_right = st.columns([1, 2])

        with dash_left:

            if dash_health is not None:
                st.markdown(
                    dash_gauge(
                        dash_health.get("overall_score", 0),
                        dash_health.get("status", "Unknown"),
                    ),
                    unsafe_allow_html=True,
                )
            else:
                st.info("Health score not calculated yet.")

        with dash_right:

            blocker_count = len((dash_blockers or {}).get("blockers", []))
            decision_count = len((dash_blockers or {}).get("pending_decisions", []))
            action_count = len((dash_blockers or {}).get("action_items", []))
            risk_count = len(dash_risks or [])

            k1, k2 = st.columns(2)
            k1.markdown(stat_tile("Risks found", risk_count), unsafe_allow_html=True)
            k2.markdown(stat_tile("Blockers", blocker_count), unsafe_allow_html=True)

            st.write("")

            k3, k4 = st.columns(2)
            k3.markdown(stat_tile("Pending decisions", decision_count), unsafe_allow_html=True)
            k4.markdown(stat_tile("Action items", action_count), unsafe_allow_html=True)

            if dash_health is not None:

                st.write("")

                st.markdown(
                    '<div class="dash-card">'
                    + dash_bar("Scope clarity", dash_health.get("scope_score", 0))
                    + dash_bar("Timeline", dash_health.get("timeline_score", 0))
                    + dash_bar("Blockers", dash_health.get("blocker_score", 0))
                    + '</div>',
                    unsafe_allow_html=True,
                )

        # ---- Row 2: risks + action items ----

        risk_col, action_col = st.columns(2)

        with risk_col:

            st.markdown('<div class="dash-title">⚠️ Top risks</div>', unsafe_allow_html=True)

            if dash_risks:

                for risk in dash_risks[:6]:

                    evidence_text = str(risk.get("evidence", "N/A"))

                    if len(evidence_text) > 160:
                        evidence_text = evidence_text[:160] + "…"

                    risk_pills = "".join(
                        f'<span class="pill">{esc(k)}</span>'
                        for k in risk.get("matched_keywords", [])
                    )

                    st.markdown(
                        '<div class="risk-row">'
                        f'<div class="risk-title">{esc(risk.get("risk_type", "Unknown"))}</div>'
                        f'<div class="risk-ev">{esc(evidence_text)}</div>'
                        f'{risk_pills}</div>',
                        unsafe_allow_html=True,
                    )

                if len(dash_risks) > 6:
                    st.caption(
                        f"Showing 6 of {len(dash_risks)} risks. "
                        "See the Risk Detection tab for all."
                    )

            elif dash_risks is None:
                st.info("Risks not analyzed yet.")

            else:
                st.info("No risks matched the current keyword rules.")

        with action_col:

            st.markdown('<div class="dash-title">✅ Action items &amp; blockers</div>', unsafe_allow_html=True)

            if dash_blockers is not None:

                list_card(
                    "Action items",
                    dash_blockers.get("action_items", [])[:5],
                    "No action items detected.",
                    "actions"
                )

                list_card(
                    "Blockers",
                    dash_blockers.get("blockers", [])[:5],
                    "No blockers detected.",
                    "blockers"
                )

                list_card(
                    "Pending decisions",
                    dash_blockers.get("pending_decisions", [])[:5],
                    "No pending decisions detected.",
                    "decisions"
                )

            else:
                st.info("Blockers and action items not analyzed yet.")

        # ---- Row 3: scope summary ----

        st.markdown('<div class="dash-title">🎯 Scope summary</div>', unsafe_allow_html=True)

        if dash_scope is not None:

            scope_labels = [
                ("goals", "Goals"),
                ("deliverables", "Deliverables"),
                ("milestones", "Milestones"),
                ("timelines", "Timelines"),
                ("responsibilities", "Responsibilities"),
            ]

            scope_columns = st.columns(len(scope_labels))

            for column, (scope_key, scope_label) in zip(scope_columns, scope_labels):
                column.markdown(
                    stat_tile(scope_label, len(dash_scope.get(scope_key, []))),
                    unsafe_allow_html=True
                )

            st.write("")

            goal_col, deliverable_col = st.columns(2)

            with goal_col:
                list_card(
                    "🎯 Key goals",
                    dash_scope.get("goals", [])[:3],
                    "No goals found.",
                    "result"
                )

            with deliverable_col:
                list_card(
                    "📦 Key deliverables",
                    dash_scope.get("deliverables", [])[:3],
                    "No deliverables found.",
                    "result"
                )

        else:
            st.info("Scope not analyzed yet.")