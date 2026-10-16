from embedding import generate_embeddings
from vector_store import store_chunks, search_chunks

chunks = [
    "The project deadline is 30 November 2026.",
    "The project is delayed by three days.",
    "The team completed document ingestion."
]

embeddings = generate_embeddings(chunks)

saved = store_chunks(
    chunks,
    embeddings,
    "test_project.txt"
)

print("Chunks stored:", saved)

query = "Which task is delayed?"
query_embedding = generate_embeddings([query])[0]

results = search_chunks(query_embedding, n_results=2)

print("\nSearch results:")

for document in results["documents"][0]:
    print("-", document)