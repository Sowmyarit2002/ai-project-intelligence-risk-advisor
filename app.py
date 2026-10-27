import html

import streamlit as st

from ingestion import extract_text
from chunking import split_text
from embedding import generate_embeddings
from vector_store import store_chunks, search_chunks

from scope_agent import extract_scope_and_deliverables
from risk_agent import detect_project_risks
from blocker_agent import identify_blockers_and_actions


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
    --bg: #0A0E1F;
    --panel: #111733;
    --panel-2: #161D3F;
    --line: rgba(140, 150, 255, 0.16);
    --text: #E8EBFA;
    --muted: #96A0C8;
    --indigo: #7C83FF;
    --aqua: #3EE0D0;
    --amber: #FFB454;
    --rose: #FF6B8B;
}

html, body, [class*="css"], .stApp {
    font-family: 'DM Sans', sans-serif;
    color: var(--text);
}

.stApp {
    background:
        radial-gradient(900px 500px at 85% -10%, rgba(124,131,255,0.20), transparent 60%),
        radial-gradient(700px 420px at -5% 15%, rgba(62,224,208,0.10), transparent 60%),
        var(--bg);
}

#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }

.block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 1180px; }

h1, h2, h3, h4 { font-family: 'Sora', sans-serif; letter-spacing: -0.01em; }

/* ---------- Hero ---------- */
.hero {
    position: relative;
    padding: 2.4rem 2.4rem 2.2rem;
    border-radius: 22px;
    border: 1px solid var(--line);
    background:
        linear-gradient(135deg, rgba(124,131,255,0.18), rgba(62,224,208,0.06) 60%),
        var(--panel);
    overflow: hidden;
    margin-bottom: 1.6rem;
}
.hero::after {
    content: "";
    position: absolute; right: -80px; top: -80px;
    width: 280px; height: 280px; border-radius: 50%;
    background: radial-gradient(circle, rgba(62,224,208,0.35), transparent 70%);
    filter: blur(8px);
}
.hero .status {
    display: inline-flex; align-items: center; gap: .5rem;
    font-size: .82rem; color: var(--aqua);
    background: rgba(62,224,208,0.10);
    border: 1px solid rgba(62,224,208,0.30);
    padding: .25rem .75rem; border-radius: 999px; margin-bottom: 1rem;
}
.hero .dot {
    width: 8px; height: 8px; border-radius: 50%; background: var(--aqua);
    box-shadow: 0 0 0 0 rgba(62,224,208,.7);
    animation: pulse 2s infinite;
}
@keyframes pulse {
    70% { box-shadow: 0 0 0 9px rgba(62,224,208,0); }
    100% { box-shadow: 0 0 0 0 rgba(62,224,208,0); }
}
@media (prefers-reduced-motion: reduce) { .hero .dot { animation: none; } }
.hero h1 {
    margin: 0 0 .6rem; font-size: 2.3rem; line-height: 1.15; font-weight: 700;
    background: linear-gradient(90deg, #FFFFFF 10%, #B9BEFF 60%, #7FF0E3 100%);
    -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero p { margin: 0; color: var(--muted); max-width: 640px; font-size: 1.02rem; line-height: 1.55; }

/* ---------- Section headings ---------- */
.section-head { display: flex; align-items: center; gap: .9rem; margin: 2.4rem 0 1rem; }
.section-head .icon {
    width: 42px; height: 42px; border-radius: 12px; display: grid; place-items: center;
    font-size: 1.2rem; background: var(--panel-2); border: 1px solid var(--line);
}
.section-head h2 { margin: 0; font-size: 1.35rem; font-weight: 600; }
.section-head span.sub { display: block; color: var(--muted); font-size: .9rem; margin-top: .1rem; }

/* ---------- Cards ---------- */
.card {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 1.1rem 1.25rem;
    margin-bottom: .9rem;
}
.card h4 { margin: 0 0 .6rem; font-size: 1rem; font-weight: 600; }
.card ul { margin: 0; padding-left: 1.1rem; color: var(--text); }
.card li { margin-bottom: .35rem; line-height: 1.5; }
.card .empty { color: var(--muted); font-style: italic; margin: 0; }
.card p { margin: 0; line-height: 1.6; }

.card.result { border-left: 3px solid var(--indigo); }
.card.risk { border-left: 3px solid var(--rose); }
.card.risk .rtype { font-family: 'Sora', sans-serif; font-weight: 600; color: #FFD3DC; margin-bottom: .45rem; }
.card.blockers { border-top: 3px solid var(--rose); }
.card.decisions { border-top: 3px solid var(--amber); }
.card.actions { border-top: 3px solid var(--aqua); }

.pill {
    display: inline-block; font-size: .78rem; padding: .18rem .65rem; margin: .5rem .35rem 0 0;
    border-radius: 999px; color: #D6D9FF; background: rgba(124,131,255,0.14);
    border: 1px solid rgba(124,131,255,0.35);
}
.pill.source { color: var(--aqua); background: rgba(62,224,208,0.10); border-color: rgba(62,224,208,0.30); }

/* ---------- Stat tiles ---------- */
.stat {
    background: var(--panel); border: 1px solid var(--line); border-radius: 16px;
    padding: 1rem 1.2rem;
}
.stat .value { font-family: 'Sora', sans-serif; font-size: 1.7rem; font-weight: 700; color: #fff; }
.stat .label { color: var(--muted); font-size: .85rem; }

/* ---------- Streamlit widgets ---------- */
section[data-testid="stSidebar"] {
    background: #0D1229; border-right: 1px solid var(--line);
}

[data-testid="stFileUploader"] section {
    background: var(--panel); border: 1.5px dashed rgba(124,131,255,0.45);
    border-radius: 16px; padding: 1.4rem;
}
[data-testid="stFileUploader"] section:hover { border-color: var(--aqua); }

.stTextInput input {
    background: var(--panel) !important; border: 1px solid var(--line) !important;
    border-radius: 12px !important; color: var(--text) !important; padding: .75rem 1rem !important;
}
.stTextInput input:focus { border-color: var(--indigo) !important; box-shadow: 0 0 0 3px rgba(124,131,255,.25) !important; }

.stButton > button {
    border-radius: 12px; border: 1px solid var(--line); background: var(--panel-2);
    color: var(--text); font-weight: 600; padding: .55rem 1.3rem; transition: all .15s ease;
}
.stButton > button:hover { border-color: var(--indigo); color: #fff; transform: translateY(-1px); }
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(90deg, #6C74FF, #3EC7E0); border: none; color: #07101F;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover { filter: brightness(1.08); color: #07101F; }

.stTabs [data-baseweb="tab-list"] {
    gap: .4rem; background: var(--panel); padding: .35rem; border-radius: 14px;
    border: 1px solid var(--line);
}
.stTabs [data-baseweb="tab"] { border-radius: 10px; padding: .5rem 1.1rem; color: var(--muted); }
.stTabs [aria-selected="true"] { background: var(--panel-2); color: #fff !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

[data-testid="stExpander"] {
    background: var(--panel); border: 1px solid var(--line); border-radius: 14px;
}
div[data-baseweb="select"] > div { background: var(--panel); border-color: var(--line); border-radius: 12px; }

hr { border-color: var(--line) !important; }
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
}

for key, default in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = default


# --------------------------------------------------
# UI HELPERS
# --------------------------------------------------

def esc(value):
    """Escape text so document content can't break the HTML."""
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
    """Card with a bullet list, or an empty message."""
    if items:
        body = "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>"
    else:
        body = f'<p class="empty">{esc(empty_message)}</p>'

    st.markdown(
        f'<div class="card {css_class}"><h4>{esc(title)}</h4>{body}</div>',
        unsafe_allow_html=True,
    )


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
    st.write(("✅" if st.session_state.scope_results is not None else "⚪") + " Scope & deliverables")
    st.write(("✅" if st.session_state.risk_results is not None else "⚪") + " Risk detection")
    st.write(("✅" if st.session_state.blocker_results is not None else "⚪") + " Blockers & actions")


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
                # Extract text
                text = extract_text(uploaded_file)

                # Split text into chunks
                chunks = split_text(text)

                if not chunks:
                    st.warning(
                        f"No text chunks found in {uploaded_file.name}."
                    )
                    continue

                # Generate embeddings
                with st.spinner(
                    f"Generating embeddings for {uploaded_file.name}..."
                ):
                    embeddings = generate_embeddings(chunks)

                # Store chunks in ChromaDB
                with st.spinner("Saving to vector database..."):
                    saved = store_chunks(
                        chunks,
                        embeddings,
                        uploaded_file.name
                    )

                # Save document text for the agents
                st.session_state.processed_documents[
                    uploaded_file.name
                ] = text

                # Clear old analysis results after new processing
                st.session_state.scope_results = None
                st.session_state.risk_results = None
                st.session_state.blocker_results = None

                total_chunks += saved
                processed_count += 1

                st.success(
                    f"Processed successfully: {uploaded_file.name}"
                )

                c1, c2, c3 = st.columns(3)
                c1.markdown(stat_tile("Characters extracted", f"{len(text):,}"), unsafe_allow_html=True)
                c2.markdown(stat_tile("Chunks created", len(chunks)), unsafe_allow_html=True)
                c3.markdown(stat_tile("Chunks stored", saved), unsafe_allow_html=True)

                st.write("")

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
                results = search_chunks(query_embedding, n_results=1)

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
            source = metadata_list[index - 1].get("filename", "Unknown")
            source_pill = f'<span class="pill source">📄 {esc(source)}</span>'

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

section_header("🧠", "Project intelligence agents", "Scope, risks, blockers, and next steps")

processed_documents = st.session_state.processed_documents

if not processed_documents:
    st.info("Upload and process a document above to use the agents.")
else:
    selected_document = st.selectbox(
        "Choose a document to analyze",
        options=list(processed_documents.keys())
    )

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

        if st.button("Analyze Scope", key="analyze_scope", type="primary"):
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
                    list_card(label, items, "No matching information found.")

    # ----------------------------------------------
    # AGENT 2: RISK DETECTION
    # ----------------------------------------------
    with tab_risk:
        st.subheader("Risk Detection")

        st.caption(
            "This version detects risks using keywords; "
            "it does not calculate a reliable delivery-date forecast."
        )

        if st.button("Analyze Risks", key="analyze_risks", type="primary"):
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
                st.markdown(stat_tile("Potential risks found", len(risks)), unsafe_allow_html=True)
                st.write("")

                for risk in risks:
                    keywords = risk.get("matched_keywords", [])
                    pills = "".join(
                        f'<span class="pill">{esc(k)}</span>' for k in keywords
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
                with st.spinner("Analyzing blockers and action items..."):
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
                    "blockers",
                )

            with col_b:
                list_card(
                    "🤔 Pending Decisions",
                    blocker_data.get("pending_decisions", []),
                    "No pending decisions detected.",
                    "decisions",
                )

            with col_c:
                list_card(
                    "✅ Action Items",
                    blocker_data.get("action_items", []),
                    "No action items detected.",
                    "actions",
                )