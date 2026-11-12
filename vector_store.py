

import chromadb


# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------

client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_or_create_collection(
    name="project_documents"
)


# --------------------------------------------------
# HELPER FUNCTION
# --------------------------------------------------

def convert_to_list(data):
    """Convert NumPy arrays or similar objects into lists."""

    if hasattr(data, "tolist"):
        return data.tolist()

    return data


# --------------------------------------------------
# STORE DOCUMENT CHUNKS
# --------------------------------------------------

def store_chunks(chunks, embeddings, filename):
    """
    Store document chunks and embeddings.

    Re-uploading the same filename replaces its
    previous chunks instead of leaving stale data.
    """

    if not chunks:
        return 0

    if not filename:
        raise ValueError("Filename cannot be empty.")

    embeddings_list = convert_to_list(embeddings)

    if len(chunks) != len(embeddings_list):
        raise ValueError(
            "Number of chunks and embeddings must match."
        )

    ids = [
        f"{filename}_{i}"
        for i in range(len(chunks))
    ]

    metadatas = [
        {
            "filename": filename,
            "chunk_index": i
        }
        for i in range(len(chunks))
    ]

    # Remove old chunks belonging to this filename.
    collection.delete(
        where={"filename": filename}
    )

    # Store the latest version.
    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings_list,
        metadatas=metadatas
    )

    return len(chunks)


# --------------------------------------------------
# SEARCH DOCUMENT CHUNKS
# --------------------------------------------------

def search_chunks(query_embedding, n_results=3, filename=None):
    """
    Search all documents or a selected document.
    """

    if n_results < 1:
        return []

    available_count = collection.count()

    if available_count == 0:
        return []

    query_vector = convert_to_list(query_embedding)

    search_options = {
        "query_embeddings": [query_vector],
        "n_results": min(n_results, available_count)
    }

    if filename:
        search_options["where"] = {
            "filename": filename
        }

    return collection.query(**search_options)