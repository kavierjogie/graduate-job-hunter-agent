# Graduate Job Hunter Agent 🎓💼

An advanced multi-agent orchestrator system designed for recent graduates, interns, and entry-level job seekers. This project utilizes an Orchestrator-Worker pattern to automate and streamline the job hunt: searching for roles, tailoring CVs, writing cover letters, generating interview prep materials, and tracking application state in a local SQLite database.

It is built with **Model Context Protocol (MCP)** integration, allowing decoupled, secure, and extensible job board querying.

---

## 🌟 Key Features

1. **Orchestrator Agent**: Manages session state, holds the user profile, coordinates complex multi-step workflows, and routes tasks to specialist sub-agents.
2. **Job Search Agent**: Leverages a custom Job Search MCP Server to fetch graduate schemes, internships, and entry-level positions.
3. **CV Tailoring Agent**: Compares the candidate's base profile/CV against a target job description to produce a targeted, role-specific CV layout.
4. **Cover Letter Agent**: Drafts a highly personalized, professional cover letter combining the candidate's experience and the target job description.
5. **Interview Prep Agent**: Generates likely behavioral and technical interview questions, along with suggested talking points customized to the role.
6. **Tracker Agent**: Maintains a local SQLite datastore tracking applications across stages (Applied, Interviewing, Rejected, Offer).

---

## 🏗️ System Architecture

The project follows a decoupled, message-driven Orchestrator-Worker design with a distinct Model Context Protocol (MCP) seam for external tool integration.

```mermaid
graph TD
    User([Graduate Job Seeker]) <--> CLI[CLI Interface / run.py]
    CLI <--> Orch[Orchestrator Agent]
    
    subgraph Shared State & Storage
        DB[(SQLite Datastore)] <--> TrackerRepo[Tracker Repository]
        TrackerRepo <--> Orch
        Profile[(User Profile & CV State)] <--> Orch
    end

    subgraph Specialist Sub-Agents (Standard Interface)
        Orch <--> JobAgent[Job Search Agent]
        Orch <--> CVAgent[CV Tailoring Agent]
        Orch <--> CLAgent[Cover Letter Agent]
        Orch <--> InterviewAgent[Interview Prep Agent]
        Orch <--> TrackerAgent[Tracker Agent]
    end

    subgraph External Integrations (MCP Seam)
        JobAgent <--> MCPClient[MCP Client Wrapper]
        MCPClient <-->|MCP Protocol| MCPServer[Job Search MCP Server]
        MCPServer <-->|Local DB / API| JobAPIs[Mock Graduate Jobs DB]
    end

    classDef orchestrator fill:#4f46e5,stroke:#312e81,stroke-width:2px,color:#fff;
    classDef agent fill:#0ea5e9,stroke:#0369a1,stroke-width:2px,color:#fff;
    classDef storage fill:#10b981,stroke:#065f46,stroke-width:2px,color:#fff;
    classDef mcp fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff;

    class Orch orchestrator;
    class JobAgent,CVAgent,CLAgent,InterviewAgent,TrackerAgent agent;
    class DB,TrackerRepo,Profile storage;
    class MCPClient,MCPServer mcp;
```

---

## 📁 Repository Structure

```text
graduate-job-hunter-agent/
├── README.md                 # Project vision, architecture & quickstart
├── pyproject.toml            # Project metadata and tool configurations
├── requirements.txt          # Python dependency list
├── run.py                    # Main entry point to run CLI / demo
│
├── agents/                   # Concrete Agent implementations
│   ├── base.py               # Abstract BaseAgent & common agent interface
│   ├── orchestrator.py       # Orchestrator routing & state management
│   ├── job_search.py         # Job Search Specialist Agent
│   ├── cv_tailor.py          # CV Tailoring Specialist Agent
│   ├── cover_letter.py       # Cover Letter Specialist Agent
│   ├── interview.py          # Interview Specialist Agent
│   └── tracker.py            # SQLite Application Tracker Agent
│
├── mcp_server/               # Job Search MCP Server
│   ├── server.py             # FastMCP / MCP Server definition
│   └── jobs_db.json          # Mock graduate job listings database
│
├── shared/                   # Shared schemas, utilities, and client wrappers
│   ├── models.py             # Shared Pydantic models (User, Job, CV, Application)
│   ├── storage.py            # SQLite database manager (asyncio-compatible)
│   └── mcp_client.py         # Client wrapper to connect to the Job Search MCP
│
└── tests/                    # Unit & integration tests
    ├── test_agents.py
    ├── test_storage.py
    └── test_orchestrator.py
```

---

## ⚙️ Setup and Installation

### Prerequisites
- Python 3.10 or higher
- SQLite3

### 1. Clone & Navigate
Ensure your terminal is in the project directory.

### 2. Create Virtual Environment
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Application

### Running the CLI Demo
To run the mock execution pipeline showing the orchestrator routing request to sub-agents:
```bash
python run.py
```

### Running the MCP Server
To run the Job Search MCP Server standalone:
```bash
python mcp_server/server.py
```

### Running Tests
To verify that all interface contracts and database layers are correct:
```bash
pytest
```
