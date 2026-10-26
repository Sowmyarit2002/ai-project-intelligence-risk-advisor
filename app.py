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
    layout="wide"
)

st.title("AI Project Intelligence & Risk Advisor")
st.write(
    "Upload project documents, search their contents, "
    "and analyze scope, risks, blockers, and action items."
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

DEFAULT_STATE = {
    "processed_documents": {},
    "search_results": None,
    "scope_results": None,
    "risk_results": None,
    "blocker_results": None,
}

for key, default in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = default


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def render_list(items, empty_message):
    """Show a bullet list, or an info message if the list is empty."""
    if items:
        for item in items:
            st.write(f"- {item}")
    else:
        st.info(empty_message)


# --------------------------------------------------
# MODULE 1: DOCUMENT INGESTION
# --------------------------------------------------

st.header("1. Document Ingestion")

uploaded_files = st.file_uploader(
    "Upload project documents",
    type=["pdf", "docx", "csv", "txt"],
    accept_multiple_files=True
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

                st.write("Characters extracted:", len(text))
                st.write("Chunks created:", len(chunks))
                st.write("Chunks stored:", saved)

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

        st.success(
            f"Processing finished. Documents processed: {processed_count}. "
            f"Chunks stored or updated: {total_chunks}."
        )


# --------------------------------------------------
# MODULE 2: SEMANTIC SEARCH
# --------------------------------------------------

st.divider()
st.header("2. Search Project Documents")

question = st.text_input(
    "Ask a question about your project documents",
    placeholder="Example: What is the project deadline?"
)

if st.button("Search Documents"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        try:
            with st.spinner("Searching project documents..."):
                query_embedding = generate_embeddings([question])[0]
                results = search_chunks(query_embedding, n_results=3)

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

    st.subheader("Relevant Search Results")

    for index, document in enumerate(documents, start=1):
        st.markdown(f"**Result {index}**")
        st.write(document)

        if index <= len(metadata_list) and metadata_list[index - 1]:
            st.caption(
                "Source: "
                + metadata_list[index - 1].get("filename", "Unknown")
            )


# --------------------------------------------------
# MODULE 3: PROJECT INTELLIGENCE AGENTS
# --------------------------------------------------

st.divider()
st.header("3. Project Intelligence Agents")

processed_documents = st.session_state.processed_documents

if not processed_documents:
    st.info("Upload and process a document above to use the agents.")
else:
    selected_document = st.selectbox(
        "Choose a document to analyze",
        options=list(processed_documents.keys())
    )

    document_text = processed_documents[selected_document]

    tab_scope, tab_risk, tab_blockers = st.tabs([
        "Scope & Deliverables",
        "Risk Detection",
        "Blockers & Actions"
    ])

    # ----------------------------------------------
    # AGENT 1: SCOPE AND DELIVERABLES
    # ----------------------------------------------
    with tab_scope:
        st.subheader("Scope and Deliverable Extraction")

        if st.button("Analyze Scope", key="analyze_scope"):
            try:
                with st.spinner("Analyzing scope..."):
                    st.session_state.scope_results = (
                        extract_scope_and_deliverables(document_text)
                    )
            except Exception as error:
                st.error(f"Scope analysis failed: {error}")

        if st.session_state.scope_results is not None:
            labels = {
                "goals": "Project Goals",
                "deliverables": "Deliverables",
                "milestones": "Milestones",
                "timelines": "Timelines",
                "responsibilities": "Responsibilities"
            }

            for category, label in labels.items():
                st.markdown(f"**{label}**")
                items = st.session_state.scope_results.get(category, [])

                if items:
                    for item in items:
                        st.write(f"- {item}")
                else:
                    st.write("No matching information found.")

    # ----------------------------------------------
    # AGENT 2: RISK DETECTION
    # ----------------------------------------------
    with tab_risk:
        st.subheader("Risk Detection")

        st.caption(
            "This version detects risks using keywords; "
            "it does not calculate a reliable delivery-date forecast."
        )

        if st.button("Analyze Risks", key="analyze_risks"):
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
                for risk in risks:
                    st.markdown(
                        f"**Potential Risk:** {risk.get('risk_type', 'Unknown')}"
                    )
                    st.write(f"Evidence: {risk.get('evidence', 'N/A')}")

                    keywords = risk.get("matched_keywords", [])
                    if keywords:
                        st.caption(
                            "Matched keywords: " + ", ".join(keywords)
                        )

                    st.divider()
            else:
                st.info("No risks matched the current keyword rules.")

    # ----------------------------------------------
    # AGENT 3: BLOCKERS AND ACTION ITEMS
    # ----------------------------------------------
    with tab_blockers:
        st.subheader("Blockers & Action Items")

        if st.button(
            "Analyze Blockers & Action Items",
            key="analyze_blockers"
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

            st.markdown("### Blockers")
            render_list(
                blocker_data.get("blockers", []),
                "No blockers detected."
            )

            st.markdown("### Pending Decisions")
            render_list(
                blocker_data.get("pending_decisions", []),
                "No pending decisions detected."
            )

            st.markdown("### Action Items")
            render_list(
                blocker_data.get("action_items", []),
                "No action items detected."
            )