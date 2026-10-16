AI Project Intelligence & Risk Advisor

Project Overview

The AI Project Intelligence & Risk Advisor is a Python-based application designed to help software development teams organize project documents and retrieve relevant information efficiently.

The system extracts text from project documents, divides it into smaller chunks, generates embeddings, and stores them in a vector database for semantic search.

Objectives

- Extract text from project documents.
- Split documents into manageable chunks.
- Generate text embeddings.
- Store and search document chunks.
- Provide a simple web interface.

Technologies Used

- Python
- Streamlit
- Sentence Transformers
- ChromaDB
- Pandas
- PyPDF
- python-docx

Current Features

- Upload PDF, DOCX, CSV, and TXT files.
- Extract text from supported documents.
- Split text into chunks.
- Generate embeddings using Sentence Transformers.
- Store document chunks in ChromaDB.
- Search relevant document content through the Streamlit interface.

Project Status

In Progress — Milestone 1

Document ingestion, text chunking, embedding generation, vector storage, and semantic search have been implemented. Future development will focus on AI-generated answers, project risk analysis, and dashboard features.

How to Run

After installing the project dependencies, run:

python -m streamlit run app.py

Author

Sowmyarit Padhy
