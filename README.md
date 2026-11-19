AI Project Intelligence & Risk Advisor

Infosys Springboard Internship Project

An AI-powered platform for analyzing project documents, identifying risks and blockers, monitoring project health, and generating actionable project insights.

Features & Milestones

Milestone 1 – Document Ingestion & Semantic Search

- Supports PDF, DOCX, CSV, and TXT files.
- Text extraction, chunking, and embedding generation.
- ChromaDB-based vector storage and semantic search.

Milestone 2 – AI Project Analysis Agents

- Project scope and deliverable extraction.
- Risk and blocker identification.
- Action items, milestones, and responsibilities extraction.

Milestone 3 – Project Intelligence & Conversational AI

- Automated project documentation generation.
- User stories, risk registers, and action-item reports.
- Project health score calculation.
- Conversational AI with document-based answers.

Milestone 4 – Dashboard & Incremental Updates

- Interactive project insights and risk dashboard.
- Project health, scope, timeline, and blocker summaries.
- Pending decisions and action-item tracking.
- Meeting updates and document merging.
- Updated document indexing and retrieval.

Tech Stack

- Python
- Streamlit
- Sentence Transformers ("all-MiniLM-L6-v2")
- ChromaDB
- Pandas
- PyPDF
- Python-docx
- Git & GitHub

Project Structure

Internship Project/
│
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
├── chroma_db/
├── .gitignore
├── LICENSE
└── README.md

Installation & Execution

1. Clone the repository

git clone https://github.com/Sowmyarit2002/ai-project-intelligence-risk-advisor.git
cd ai-project-intelligence-risk-advisor

2. Install dependencies

pip install streamlit chromadb sentence-transformers pandas pypdf python-docx

3. Run the application

streamlit run app.py

Open "http://localhost:8501" in your browser.

Testing

Run the individual test files using Python:

python test_embedding.py
python test_vector_store.py
python test_scope_agent.py
python test_risk_agent.py
python test_blocker_agent.py
python test_documentation_agent.py
python test_health_score.py
python test_conversational_agent.py

Repository

"GitHub – AI Project Intelligence & Risk Advisor" (https://github.com/Sowmyarit2002/ai-project-intelligence-risk-advisor)

License

This project is licensed under the MIT License. See the "LICENSE" file for details.
