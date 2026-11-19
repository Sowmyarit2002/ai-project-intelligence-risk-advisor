
AI Project Intelligence & Risk Advisor
An AI-driven enterprise project intelligence and risk management platform
Developed as part of the Infosys Springboard Internship Project.
---
1. Project Overview
The AI Project Intelligence & Risk Advisor is an AI-powered application designed to analyze enterprise project documents, extract important project information, identify potential risks and blockers, and provide actionable project insights through an interactive dashboard.
The platform uses document processing, semantic search, vector databases, and AI-powered analysis agents to help project managers understand project progress, monitor risks, track deliverables, and make informed decisions.
The application provides a centralized interface for project document analysis, risk assessment, project health monitoring, and conversational question answering.
2. Key Objectives
Automate project document ingestion and analysis.
Extract project goals, scope, deliverables, milestones, and responsibilities.
Identify project risks, blockers, and action items.
Generate structured project documentation.
Calculate and monitor overall project health.
Enable conversational question answering using project documents.
Provide an interactive project intelligence dashboard.
Support additional meeting updates and document information merging.
3. Technologies Used
Technology	Purpose
Python	Core application development
Streamlit	Interactive web application
Sentence Transformers	Text embedding generation
all-MiniLM-L6-v2	Embedding model
ChromaDB	Vector database and semantic retrieval
Pandas	Structured data processing
PyPDF	PDF document processing
Python-docx	Word document processing
Git & GitHub	Version control and source code management
4. Project Milestones
Milestone 1 – Document Ingestion and Semantic Search
Implemented document processing and semantic retrieval functionality.
Features:
Upload and process PDF, DOCX, CSV, and TXT documents.
Extract text from different document formats.
Split extracted text into smaller chunks.
Generate text embeddings using Sentence Transformers.
Store document embeddings in ChromaDB.
Perform semantic search across indexed project documents.
Retrieve relevant information with source document identification.
Main components:
ingestion.py
chunking.py
embedding.py
vector_store.py
Milestone 2 – AI Project Analysis Agents
Developed specialized agents to extract and analyze project-related information.
Features:
Project scope and deliverable extraction.
Identification of project risks.
Detection of project blockers.
Identification of action items.
Extraction of milestones, deadlines, and responsibilities.
Main components:
scope_agent.py
risk_agent.py
blocker_agent.py
Milestone 3 – Project Intelligence and Conversational AI
Implemented project documentation generation, project health assessment, and conversational question answering.
Features:
Automated project documentation generation.
User story generation.
Risk register generation.
Action-item documentation.
Project health score calculation.
Scope, timeline, and blocker assessment.
Conversational project assistant.
Context-based answers using retrieved project document information.
Main components:
documentation_agent.py
health_score.py
conversational_agent.py
Milestone 4 – Project Insights Dashboard and Incremental Updates
Enhanced the application with project-level insights, dashboard functionality, and document update management.
Features:
Interactive project insights and risk summary dashboard.
Overall project health score and status.
Scope, timeline, and blocker score breakdown.
Project goals, deliverables, milestones, and responsibilities.
Risk summaries and supporting evidence.
Blocker, pending-decision, and action-item summaries.
Upload additional project documents and meeting updates.
Merge new meeting information with existing project documents.
Reprocess and index updated project information for retrieval.
Support end-to-end application testing.
5. Project Architecture
The application follows a modular architecture in which individual components handle document processing, semantic retrieval, project analysis, and dashboard presentation.
                 PROJECT DOCUMENTS
             PDF | DOCX | CSV | TXT
                        |
                        v
              DOCUMENT INGESTION
                  ingestion.py
                        |
                        v
                 TEXT CHUNKING
                  chunking.py
                        |
                        v
              EMBEDDING GENERATION
                  embedding.py
                        |
                        v
                  CHROMADB
                vector_store.py
                        |
             +----------+----------+
             |          |          |
             v          v          v
         SCOPE       RISK      BLOCKER
         AGENT       AGENT       AGENT
             |          |          |
             +----------+----------+
                        |
                        v
              PROJECT INTELLIGENCE
             +----------+-----------+
             |          |           |
             v          v           v
        DOCUMENTATION HEALTH    CONVERSATIONAL
           AGENT      SCORE         AGENT
             |          |           |
             +----------+-----------+
                        |
                        v
               STREAMLIT DASHBOARD
                        |
                        v
              PROJECT INSIGHTS

6. Project Directory Structure
Internship Project/
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
├── chroma_db/
│
├── .venv/
├── .gitignore
├── LICENSE
└── README.md

Note: The directory structure above lists the main project files. Additional configuration and dependency files may also be present.
7. Installation and Setup
Prerequisites
Python installed on Windows.
Visual Studio Code.
Git installed.
Required Python dependencies.
Internet connection for downloading dependencies and the embedding model when needed.
Step 1 – Clone the repository
git clone https://github.com/Sowmyarit2002/ai-project-intelligence-risk-advisor.git

Step 2 – Open the project folder
cd ai-project-intelligence-risk-advisor

Open this folder in Visual Studio Code.
Step 3 – Create a virtual environment (if one does not already exist)
python -m venv .venv

Step 4 – Activate the virtual environment
For Windows PowerShell:
.\.venv\Scripts\Activate.ps1

If PowerShell blocks activation, you can use the virtual environment's Python executable directly.
Step 5 – Install dependencies
If the repository contains a requirements.txt file:
python -m pip install -r requirements.txt

Otherwise, install the dependencies specified by the project:
python -m pip install streamlit chromadb sentence-transformers pandas pypdf python-docx

8. Running the Application
From the project directory, execute:
.\.venv\Scripts\python.exe -m streamlit run app.py

Once Streamlit starts, open the following address in your browser:
http://localhost:8501

The application interface will be available for document uploads, project analysis, semantic search, and dashboard operations.
9. Testing
The project includes individual test modules for important components.
Run individual tests using:
.\.venv\Scripts\python.exe test_embedding.py

.\.venv\Scripts\python.exe test_vector_store.py

.\.venv\Scripts\python.exe test_scope_agent.py

.\.venv\Scripts\python.exe test_risk_agent.py

.\.venv\Scripts\python.exe test_blocker_agent.py

.\.venv\Scripts\python.exe test_documentation_agent.py

.\.venv\Scripts\python.exe test_health_score.py

.\.venv\Scripts\python.exe test_conversational_agent.py

Run the tests from the project root directory.
10. Expected Application Capabilities
After successful setup and execution, the application is designed to provide:
Document upload and text extraction.
Semantic search and relevant document retrieval.
Automated project scope and deliverable extraction.
Project risk identification.
Blocker and action-item identification.
Project documentation generation.
Project health score calculation.
Conversational question answering.
Interactive project insights dashboard.
Additional meeting updates and updated document indexing.
Actual extraction and dashboard results depend on the information available in the uploaded documents and the behavior of the analysis agents.
11. Future Enhancements
Potential future improvements include:
Advanced multi-agent orchestration.
Improved risk prediction and delivery forecasting.
More accurate blocker and dependency detection.
User authentication and role-based access.
Real-time project monitoring.
Integration with enterprise project management tools.
Exportable project reports and dashboards.
Advanced analytics and historical project comparisons.
12. Repository
GitHub:
https://github.com/Sowmyarit2002/ai-project-intelligence-risk-advisor
13. Internship Project Information
Project Title: Development of AI-Driven Enterprise Project Intelligence & Risk Management Platform
Application Name: AI Project Intelligence & Risk Advisor
Project Type: AI / Machine Learning / Natural Language Processing / Project Management
Development Environment: Python, Visual Studio Code, Streamlit
Version Control: Git and GitHub
---
License
This project is licensed under the MIT License. See the LICENSE file for details.



