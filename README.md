AI Project Intelligence & Risk Advisor

An AI-driven platform for project document analysis, risk identification, and project management support.

Project Overview

Software development teams and student project groups often struggle with incomplete planning, missed deadlines, unresolved blockers, and scattered project documentation. Reviewing proposals, meeting notes, project plans, and progress updates manually can make it difficult to identify important information and potential risks.

The AI Project Intelligence & Risk Advisor aims to simplify this process by extracting useful information from project documents, searching relevant content, and identifying project scope, risks, blockers, and action items.

This project is being developed as part of the Infosys Springboard internship project, Development of AI-Driven Enterprise Project Intelligence & Risk Management Platform.

Objectives

- Ingest and process project documents in multiple formats.
- Convert extracted text into manageable chunks for search and analysis.
- Generate embeddings to support semantic document search.
- Extract project goals, deliverables, milestones, timelines, and responsibilities.
- Identify potential project risks and supporting evidence.
- Detect blockers, pending decisions, and action items.
- Validate the application using sample project documents and test cases.

Features Implemented

Milestone 1: Document Ingestion and Search

- Upload project documents in PDF, DOCX, CSV, and TXT formats.
- Extract text from supported documents.
- Split extracted text into smaller chunks.
- Generate embeddings for document chunks.
- Store document chunks for retrieval.
- Search project documents using semantic similarity.
- Display relevant search results through a Streamlit interface.

Milestone 2: Project Intelligence Agents

1. Scope and Deliverables Agent ("scope_agent.py")

Identifies project information such as:

- Project goals and objectives
- Deliverables
- Milestones and timelines
- Roles and responsibilities

2. Risk Detection Agent ("risk_agent.py")

Identifies potential project risks from document content, including:

- Schedule and deadline risks
- Dependency-related concerns
- Delivery challenges
- Supporting text and matched keywords

3. Blocker and Action Item Agent ("blocker_agent.py")

Extracts information related to:

- Project blockers and unresolved issues
- Pending decisions
- Action items and follow-up activities

The current agents use rule-based or keyword-matching logic where applicable. Their outputs should be validated against the original documents and are intended to support, not replace, human project decisions.

Technology Stack

- Programming language: Python
- User interface: Streamlit
- Document processing: PDF, DOCX, CSV, and TXT text extraction
- Text processing: Chunking and preprocessing
- Semantic search: Embeddings and vector-based retrieval
- Testing: Python test scripts and automated tests where configured
- Version control: Git and GitHub
- Development environment: Visual Studio Code

Project Structure

The main project files include:

ai-project-intelligence-risk-advisor/
│
├── app.py
├── ingestion.py
├── chunking.py
├── embedding.py
├── vector_store.py
│
├── scope_agent.py
├── risk_agent.py
├── blocker_agent.py
│
├── test_embedding.py
├── test_vector_store.py
├── test_scope_agent.py
├── test_risk_agent.py
├── test_blocker_agent.py
│
├── .gitignore
├── README.md
└── requirements.txt

Note: The structure above describes the expected main files. Keep the README aligned with the files actually present in the repository. Add "requirements.txt" if it does not yet exist.

Installation and Setup

Prerequisites

- Python 3.12 or another compatible Python version
- Visual Studio Code
- Git
- Internet access for installing required Python packages

1. Clone the repository

git clone https://github.com/Sowmyarit2002/ai-project-intelligence-risk-advisor.git

2. Open the project directory

cd ai-project-intelligence-risk-advisor

3. Create a virtual environment

Windows PowerShell:

python -m venv .venv

4. Install dependencies

If the repository contains a complete "requirements.txt" file:

.\.venv\Scripts\python.exe -m pip install -r requirements.txt

If dependencies are not listed yet, install the packages required by the current source files and document-processing libraries before running the application.

5. Run the application

.\.venv\Scripts\python.exe -m streamlit run app.py

Streamlit will display a local URL in the terminal, usually:

http://localhost:8501

Open that URL in your browser to use the application.

How to Use

1. Start the Streamlit application.
2. Upload a supported project document.
3. Allow the application to extract the document text and create chunks and embeddings.
4. Enter a search query to retrieve relevant project information.
5. Use the Scope and Deliverables module to review project scope information.
6. Use the Risk Detection module to inspect potential risks and their supporting evidence.
7. Use the Blockers and Actions module to review unresolved issues, pending decisions, and action items.
8. Compare the results with the source documents to validate their accuracy.

Testing

The repository contains test scripts for the embedding, vector-store, scope, risk, and blocker components.

To run the tests using "pytest", install it if necessary and execute:

.\.venv\Scripts\python.exe -m pytest -v

Review test results and investigate any failures before treating the corresponding feature as validated. Also test document ingestion and the Streamlit workflow using representative PDF, DOCX, CSV, and TXT files.

Current Limitations

- Risk and blocker detection may rely on keywords and predefined rules, which can produce false positives or miss relevant information.
- Extracted results depend on the quality, formatting, and completeness of the uploaded documents.
- Delivery forecasts and risk assessments should not be treated as guaranteed predictions.
- Human review is required before acting on extracted risks, decisions, or action items.
- Support for additional document formats and more advanced AI-based analysis can be added in future development.

Future Enhancements

- Improve risk prioritization using likelihood and impact scores.
- Enhance extraction of dates, dependencies, task owners, and project status.
- Add more robust evaluation datasets and automated test coverage.
- Improve cross-document analysis and source traceability.
- Introduce advanced AI or LLM-based analysis where appropriate.
- Develop more detailed project dashboards and reporting features.

Project Status

- Milestone 1: Document ingestion, chunking, embeddings, vector storage, and semantic search.
- Milestone 2: Scope and deliverable extraction, risk detection, and blocker/action-item identification.

The project is under active development. Features and evaluation methods may evolve as additional milestones are completed.

Author

Sowmyarit Padhy

B.Tech — Information Technology

KIIT, Bhubaneswar, Odisha, India

Repository

"GitHub: AI Project Intelligence & Risk Advisor" (https://github.com/Sowmyarit2002/ai-project-intelligence-risk-advisor)

License

This project includes an MIT License in the repository. Refer to the "LICENSE" file for the applicable terms.

