import html

import streamlit as st

from ingestion import extract_text
from chunking import split_text
from embedding import generate_embeddings
from vector_store import store_chunks, search_chunks

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

with st.sidebar:
    st.markdown("### 📊 Project Intelligence")
    st.caption("Your documents, searched and analyzed.")
    st.divider()

    docs_count = len(st.session_state.processed_documents)

    st.markdown(
        stat_tile("Documents processed", docs_count)
        + '<div style="height:.7rem"></div>'
        + stat_tile("Chunks stored", st.session_state.total_chunks),
        unsafe_allow_html=True,
    )

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

        st.session_state.total_chunks += total_chunks

        st.success(
            f"Processing finished. Documents processed: {processed_count}. "
            f"Chunks stored or updated: {total_chunks}."
        )


# --------------------------------------------------
# MODULE 2: SEMANTIC SEARCH
# --------------------------------------------------

section_header("🔎", "Search project documents", "Ask a question in plain language")

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
                    n_results=1
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