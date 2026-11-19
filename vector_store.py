import datetime

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

    Re-uploading the same filename replaces its previous chunks.
    The replacement is stored and verified first; old chunks that
    are no longer needed are removed only after that succeeds, so a
    failed save never destroys the existing document.
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

    # Remember which chunks currently belong to this filename.
    existing = collection.get(
        where={"filename": filename},
        include=[]
    )

    old_ids = existing.get("ids", [])

    # Store the latest version first. If this raises, the old
    # chunks are still in the database untouched.
    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings_list,
        metadatas=metadatas
    )

    # Confirm the replacement chunks are really there.
    stored = collection.get(
        ids=ids,
        include=[]
    )

    if len(stored.get("ids", [])) != len(ids):
        raise RuntimeError(
            "Could not confirm that the new chunks were stored. "
            "The previous version was kept."
        )

    # Only now remove old chunks that the new version does not use
    # (for example, when the new document is shorter).
    new_ids = set(ids)

    stale_ids = [
        old_id for old_id in old_ids
        if old_id not in new_ids
    ]

    if stale_ids:
        collection.delete(ids=stale_ids)

    return len(chunks)


# --------------------------------------------------
# APPEND DOCUMENT CHUNKS (INCREMENTAL UPDATES)
# --------------------------------------------------

def get_chunk_count(filename):
    """Return how many chunks are stored for a document."""

    if not filename:
        return 0

    existing = collection.get(
        where={"filename": filename},
        include=[]
    )

    return len(existing.get("ids", []))


def list_document_names():
    """Return the filenames of all documents stored in the database."""

    records = collection.get(include=["metadatas"])

    names = {
        meta.get("filename")
        for meta in (records.get("metadatas") or [])
        if meta and meta.get("filename")
    }

    return sorted(names)


def get_total_chunk_count():
    """Return the actual number of chunk records in the database."""

    return collection.count()


def append_chunks(chunks, embeddings, filename, source=None):
    """
    Add new chunks to an existing document without touching
    the chunks that are already stored.

    Use this for new meeting notes or progress updates so only
    the new text needs to be embedded. If the document does not
    exist yet, it is created.

    source: optional name of the update file the chunks came from.
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

    existing = collection.get(
        where={"filename": filename},
        include=["metadatas"]
    )

    existing_indexes = [
        meta.get("chunk_index", 0)
        for meta in (existing.get("metadatas") or [])
        if meta
    ]

    start_index = (
        max(existing_indexes) + 1
        if existing_indexes
        else 0
    )

    added_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    ids = [
        f"{filename}_{start_index + i}"
        for i in range(len(chunks))
    ]

    metadatas = []

    for i in range(len(chunks)):

        metadata = {
            "filename": filename,
            "chunk_index": start_index + i,
            "added_at": added_at
        }

        if source:
            metadata["source"] = source

        metadatas.append(metadata)

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

    # When searching one document, only count that document's chunks.
    if filename:
        available_count = get_chunk_count(filename)
    else:
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