AI Project Intelligence & Risk Advisor

An AI-driven project intelligence and risk management platform developed as part of the Infosys Springboard Internship.

Project Overview

This application analyzes project documents and provides insights into project scope, risks, blockers, documentation, project health, and conversational question answering.

Key Features

Milestone 1 – Document Ingestion & Semantic Search

- Supports PDF, DOCX, CSV, and TXT files.
- Text extraction, chunking, and embedding generation.
- Semantic search using ChromaDB.

Milestone 2 – Project Intelligence Agents

- Scope and deliverables extraction.
- Project risk detection.
- Blocker and action-item identification.

Milestone 3 – Advanced Project Intelligence

- Documentation generation (user stories, risk registers, action lists).
- Project health scoring with dimension-wise breakdown.
- Conversational project assistant using RAG.
- Evidence-based answers from uploaded documents.

Technology Stack

- Python
- Streamlit
- Sentence Transformers
- ChromaDB
- Pandas
- PyPDF
- python-docx
- Retrieval-Augmented Generation (RAG)

Project Setup

git clone https://github.com/Sowmyarit2002/ai-project-intelligence-risk-advisor.git
cd ai-project-intelligence-risk-advisor
pip install -r requirements.txt
python -m streamlit run app.py

Project Structure

├── app.py
├── ingestion.py
├── chunking.py
├── embedding.py
├── vector_store.py
├── scope_agent.py
├── risk_agent.py
├── blocker_agent.py
├── documentation_agent.py
├── health_score.py
├── conversational_agent.py
├── test_*.py
├── requirements.txt
├── README.md
└── LICENSE

Project Status

- Milestone 1: Completed
- Milestone 2: Completed
- Milestone 3: Implemented

Future Enhancements

- OCR support for scanned PDFs.
- Improved risk detection accuracy.
- Enhanced retrieval and conversational response quality.

License

MIT License.

Developed as part of the Infosys Springboard Internship Project.




