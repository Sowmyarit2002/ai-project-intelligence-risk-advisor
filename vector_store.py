import chromadb

# Create a local database folder
client = chromadb.PersistentClient(
    path="./chroma_db"
)

# Create or reuse a collection
collection = client.get_or_create_collection(
    name="project_documents"
)


def store_chunks(chunks, embeddings, filename):
    if not chunks:
        return 0

    ids = [
        f"{filename}_{i}"
        for i in range(len(chunks))
    ]

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings.tolist(),
        metadatas=[
            {"filename": filename, "chunk_index": i}
            for i in range(len(chunks))
        ]
    )

    return len(chunks)


def search_chunks(query_embedding, n_results=3):
    if collection.count() == 0:
        return []

    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=min(n_results, collection.count())
    )

    return results