AI Project Intelligence & Risk Advisor
Development of AI-Driven Enterprise Project Intelligence & Risk Management Platform
An AI-powered project intelligence and risk management platform developed as part of the Infosys Springboard Internship.
The application helps project teams analyze project documents, extract important project information, identify risks and blockers, generate project documentation, evaluate project health, and interact with project information through a conversational assistant.
---
Project Overview
The AI Project Intelligence & Risk Advisor is designed to simplify project monitoring and management by combining document processing, semantic search, specialized project intelligence agents, and Retrieval-Augmented Generation (RAG).
Users can upload project documents in PDF, DOCX, CSV, and TXT formats. The platform processes the uploaded information and provides structured project insights through an interactive Streamlit application.
Key Features
Milestone 1 – Document Ingestion and Semantic Search
Upload documents in PDF, DOCX, CSV, and TXT formats.
Extract text from uploaded documents.
Split extracted content into smaller text chunks.
Generate text embeddings using Sentence Transformers.
Store document chunks and embeddings in ChromaDB.
Perform semantic search to retrieve relevant project information.
Milestone 2 – Project Intelligence Agents
1. Scope & Deliverables Extraction Agent
Extract project goals and objectives.
Identify project deliverables.
Extract milestones and timelines.
Identify project responsibilities.
2. Risk Detection & Delivery Forecasting Agent
Identify potential project risks.
Detect schedule and dependency-related risks.
Display supporting evidence for identified risks.
3. Blocker & Action Item Identification Agent
Identify project blockers.
Extract pending decisions.
Identify action items requiring attention.
Milestone 3 – Documentation Generation, Project Health Scoring & Conversational Intelligence
1. Documentation Generation Agent
Generate project user stories.
Generate structured risk registers.
Generate project action-item lists.
Use extracted project information to prepare management documentation.
2. Project Health Scoring
Calculate an overall project health score.
Evaluate scope health.
Evaluate timeline health.
Evaluate blocker-related health.
Display a dimension-wise project health breakdown.
3. Conversational Project Intelligence Assistant
Answer project-related questions using uploaded project documents.
Retrieve relevant information through semantic search.
Provide context-based answers.
Display supporting evidence for answer verification.
4. Testing and Validation
Test individual agents using dedicated test scripts.
Validate document ingestion across supported formats.
Evaluate documentation generation and health scoring.
Test conversational responses for relevance and accuracy.
---
Technology Stack
Technology	Purpose
Python	Core application development
Streamlit	Interactive web application
Sentence Transformers	Text embedding generation
all-MiniLM-L6-v2	Embedding model
ChromaDB	Vector database
PyPDF	PDF text extraction
python-docx	DOCX document processing
Pandas	CSV processing and data handling
RAG	Context-based information retrieval
---
System Architecture
The application follows a modular architecture:
Document Upload: Users upload project documents.
Document Ingestion: Extract text from supported document formats.
Text Chunking: Divide extracted content into smaller chunks.
Embedding Generation: Convert text chunks into vector embeddings.
Vector Storage: Store embeddings and associated metadata in ChromaDB.
Semantic Retrieval: Retrieve relevant project information.
Project Intelligence Agents: Analyze scope, risks, blockers, and action items.
Documentation Generation: Generate user stories, risk registers, and action lists.
Project Health Assessment: Calculate and display project health scores.
Conversational Assistant: Answer questions using retrieved project information.
---
Project Structure
ai-project-intelligence-risk-advisor/
│
├── app.py
│
├── ingestion.py
├── chunking.py
├── embedding.py
├── vector_store.py
│
├── scope_agent.py
├── risk_agent.py
├── blocker_agent.py
│
├── documentation_agent.py
├── health_score.py
├── conversational_agent.py
│
├── test_embedding.py
├── test_vector_store.py
├── test_scope_agent.py
├── test_risk_agent.py
├── test_blocker_agent.py
├── test_documentation_agent.py
├── test_health_score.py
├── test_conversational_agent.py
│
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore

---
Installation and Setup
Prerequisites
Python 3.10 or a compatible supported Python version.
Git.
Visual Studio Code (recommended).
1. Clone the Repository
git clone https://github.com/Sowmyarit2002/ai-project-intelligence-risk-advisor.git

2. Navigate to the Project Directory
cd ai-project-intelligence-risk-advisor

3. Create a Virtual Environment
python -m venv .venv

4. Activate the Virtual Environment
For Windows PowerShell:
.\.venv\Scripts\Activate.ps1

5. Install Dependencies
pip install -r requirements.txt

6. Run the Application
python -m streamlit run app.py

The application will open in your default web browser.
---
Testing
The project contains individual test scripts for validating its core components.
Test File	Testing Area
test_embedding.py	Embedding generation
test_vector_store.py	Vector storage and retrieval
test_scope_agent.py	Scope and deliverable extraction
test_risk_agent.py	Project risk detection
test_blocker_agent.py	Blocker and action identification
test_documentation_agent.py	Documentation generation
test_health_score.py	Project health calculation
test_conversational_agent.py	Conversational question answering
Run an individual test using:
python test_scope_agent.py

Replace the filename to run another test.
Testing should be evaluated against the actual source documents. Extraction accuracy and conversational relevance may vary depending on document structure and content.
---
Current Project Status
Milestone	Deliverables	Status
Milestone 1	Document ingestion, chunking, embeddings, semantic search	Implemented
Milestone 2	Scope extraction, risk detection, blocker identification	Implemented
Milestone 3	Documentation generation, health scoring, conversational assistant	Implemented
---
Limitations and Future Enhancements
Improve scanned PDF support through OCR.
Improve risk detection and reduce false positives.
Enhance retrieval accuracy across multiple documents.
Improve conversational answer relevance and evidence quality.
Improve duplicate document handling.
Expand project health assessment capabilities.
---
Repository
GitHub: https://github.com/Sowmyarit2002/ai-project-intelligence-risk-advisor
License
This project is licensed under the MIT License. See the LICENSE file for more information.
---
Developed as part of the Infosys Springboard Internship Project.




