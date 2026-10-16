import streamlit as st

from ingestion import extract_text
from chunking import split_text
from embedding import generate_embeddings
from vector_store import store_chunks, search_chunks

st.set_page_config(
    page_title="AI Project Intelligence",
    page_icon="📊",
    layout="wide"
)

st.title("AI Project Intelligence & Risk Advisor")
st.write(
    "Upload project documents, extract their text, "
    "create embeddings, and store them for semantic search."
)

# MODULE 1: Document upload
st.header("1. Document Ingestion")

uploaded_files = st.file_uploader(
    "Upload your project documents",
    type=["pdf", "docx", "csv", "txt"],
    accept_multiple_files=True
)

if st.button("Process Documents", type="primary"):
    if not uploaded_files:
        st.warning("Please upload at least one document first.")
    else:
        total_chunks = 0

        for uploaded_file in uploaded_files:
            st.subheader(f"📄 {uploaded_file.name}")

            try:
                # Step 1: Extract text
                text = extract_text(uploaded_file)
                st.write("Characters extracted:", len(text))

                # Step 2: Split text into chunks
                chunks = split_text(text)
                st.write("Chunks created:", len(chunks))

                if not chunks:
                    st.warning("No text chunks were created.")
                    continue

                # Step 3: Generate embeddings
                with st.spinner("Generating embeddings..."):
                    embeddings = generate_embeddings(chunks)

                # Step 4: Store chunks in ChromaDB
                with st.spinner("Saving to vector database..."):
                    saved = store_chunks(
                        chunks,
                        embeddings,
                        uploaded_file.name
                    )

                total_chunks += saved
                st.success(
                    f"Processed successfully! {saved} chunks stored."
                )

                with st.expander("View extracted text"):
                    st.text(text)

                with st.expander("View text chunks"):
                    for i, chunk in enumerate(chunks, start=1):
                        st.markdown(f"**Chunk {i}**")
                        st.text(chunk)

            except Exception as error:
                st.error(
                    f"Could not process {uploaded_file.name}: {error}"
                )

        st.success(
            f"Document processing finished. "
            f"Total chunks stored or updated: {total_chunks}"
        )

# MODULE 2: Semantic search
st.divider()
st.header("2. Search Project Documents")

question = st.text_input(
    "Ask a question about your uploaded project documents",
    placeholder="Example: What is the project deadline?"
)

if st.button("Search Documents"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        try:
            with st.spinner("Searching relevant document chunks..."):
                query_embedding = generate_embeddings([question])[0]
                results = search_chunks(query_embedding, n_results=3)

            documents = results.get("documents", [[]])[0]

            if not documents:
                st.info(
                    "No documents found. Process a document first."
                )
            else:
                st.subheader("Relevant results")

                for i, document in enumerate(documents, start=1):
                    st.markdown(f"**Result {i}**")
                    st.write(document)

                    metadata_list = results.get("metadatas", [[]])[0]
                    if i <= len(metadata_list) and metadata_list[i - 1]:
                        st.caption(
                            f"Source: "
                            f"{metadata_list[i - 1].get('filename', 'Unknown')}"
                        )

        except Exception as error:
            st.error(f"Search failed: {error}")