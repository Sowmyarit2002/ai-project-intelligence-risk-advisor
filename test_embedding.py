from embedding import generate_embeddings

sample_chunks = [
    "The project deadline is 30 November 2026.",
    "The project is delayed by three days.",
    "The team completed document ingestion."
]

embeddings = generate_embeddings(sample_chunks)

print("Number of chunks:", len(sample_chunks))
print("Embedding shape:", embeddings.shape)
print("First embedding preview:", embeddings[0][:5])