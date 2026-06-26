---
name: job_hunter_admin
description: Developer operational guide for managing, testing, and running the Graduate Job Hunter Agent codebase. Use this skill when asked to run tests, start servers, initialize the SQLite database, check environment variables, or debug project issues.
---
# Graduate Job Hunter Admin Skill 🎓💼

This skill guides you through the administrative, development, and operational workflows for the **Graduate Job Hunter Agent** multi-agent system. Use this guide to manage the codebase, run tests, spin up servers, and troubleshoot issues.

## 🛠️ Project Architecture Quick Reference
- **Orchestrator-Worker Pattern**: Coordinates specialists in `agents/`.
- **MCP Seam**: Integrates with external APIs via `mcp_server/server.py` and `shared/mcp_client.py`.
- **Streamlit Frontend**: Main interactive UI in `app_streamlit.py`.
- **Database**: Local SQLite database `job_hunter.db` managed by `shared/storage.py`.

---

## 1. 🗄️ Database Initialization & Maintenance
The database is an SQLite database located at `job_hunter.db`.

### How to Initialize the Database
The database tables are automatically initialized by the application when it starts, but they can be manually initialized using this short Python snippet:
```bash
python -c "import asyncio; from shared.storage import DatabaseManager; db = DatabaseManager(); asyncio.run(db.initialize_db()); print('Database initialized successfully.')"
```

### Inspecting the Database
To view the schema or current applications from the command line:
```bash
sqlite3 job_hunter.db "SELECT * FROM user_profile;"
sqlite3 job_hunter.db "SELECT application_id, job_title, company, status FROM applications;"
```

---

## 2. 🧪 Running Tests
The test suite validates agent interfaces, security features, database storage, and MCP server capabilities.

### Run All Tests
```bash
pytest
```

### Run Specific Test Modules
- **Agent Interfaces**: `pytest tests/test_agents.py`
- **Orchestrator Flow**: `pytest tests/test_orchestrator.py`
- **Database Storage**: `pytest tests/test_storage.py`
- **Security Guardrails**: `pytest tests/test_security.py`
- **MCP Client/Server capabilities**: `pytest tests/test_mcp_capabilities.py`

### Test Output Verbosity & Logging
To show print statements and logs during test execution:
```bash
pytest -s -v
```

---

## 3. 🔌 Starting the FastMCP Job Search Server
The Job Search MCP Server is built using FastMCP. It is decoupled from the main application.

### Start the Server (Development / Standalone Mode)
To run the MCP server on stdio:
```bash
python mcp_server/server.py
```
> [!NOTE]
> When running standalone, it requires `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` environment variables to be set in your `.env` file to successfully connect to the Adzuna API.

---

## 4. 🚀 Launching the Streamlit Web Application
The Streamlit application provides an interactive candidate profile editor, autopilot execution logger, and application tracker dashboard.

### Start the Web Application
```bash
streamlit run app_streamlit.py
```
This command will spin up the local development server (usually at `http://localhost:8501`).

---

## 5. 🔍 Troubleshooting Environment & API Issues
The application relies on external APIs (Gemini and Adzuna). Use these checks to troubleshoot issues.

### Checking Environment Variables
Ensure a `.env` file exists in the project root containing:
```env
GEMINI_API_KEY="your-gemini-api-key"
ADZUNA_APP_ID="your-adzuna-app-id"
ADZUNA_APP_KEY="your-adzuna-app-key"
ADZUNA_COUNTRY="gb"
GEMINI_MODEL="gemini-3.1-flash-lite"
```

### Verify Config & API Connectivity
You can run a quick diagnostics check using the `run.py` script, which will validate your configuration before starting the demo:
```bash
python run.py
```
If the config is invalid, the script will output a clear error describing what is missing.

### Common Errors & Solutions
1. **`ValueError: GEMINI_API_KEY is missing or invalid`**:
   - Verify that your `.env` file is in the project root directory.
   - Verify that you have activated your virtual environment (`.\venv\Scripts\activate` on Windows).
2. **Adzuna API returning no results (empty list)**:
   - Check if your `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` are correct.
   - Ensure you are not rate-limited (Adzuna free tier has strict rate limits; the server logs will show `HTTP 429` if this happens).
3. **`aiosqlite` errors**:
   - Check if another process is locking the `job_hunter.db` file.
   - Delete `job_hunter.db` to let the application recreate a fresh database.
