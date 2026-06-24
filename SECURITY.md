# Security & Secret Management Manual

This document outlines the security architecture, secret management practices, and threat containment features built into the Graduate Job Hunter Agent.

---

## 🔒 1. Secret & Configuration Management

API keys and sensitive credentials are never hardcoded or committed to version control.

### The `.env` Pattern
- **Local Configuration**: The application utilizes a `.env` file in the project root to load secrets dynamically.
- **Template Provided**: A [.env.example](file:///.env.example) template is provided in the repository to guide users on required keys without exposing any active credentials.
- **Git Protection**: The [.gitignore](file:///.gitignore) file is explicitly configured to ignore `.env`, virtual environment folders (`venv/`, `.venv/`), and SQLite databases (`*.db`, `*.sqlite`), ensuring zero credential leakage.

### Centralized Startup Validation
- **Module**: [shared/config.py](file:///shared/config.py)
- **Startup Enforcement**: The configuration module automatically loads variables using `python-dotenv` and exposes `validate_config()`.
- **Immediate Failure**: Both the main entrypoint ([run.py](file:///run.py)) and the LLM client wrapper ([shared/llm_client.py](file:///shared/llm_client.py)) invoke `validate_config()` at startup. If the `GEMINI_API_KEY` is missing or contains template placeholders, the application aborts immediately with a clear, user-friendly error message detailing setup instructions.

---

## 🛡️ 2. Input Validation & API Boundary Security

Data entering the multi-agent orchestration boundary is strictly validated to prevent malformed payloads, injection, or type confusion.

- **Pydantic Schemas**: All core data models (e.g. `UserProfile`, `JobListing`, `TailoredCV`, `CoverLetter`, and `ApplicationState`) are defined as Pydantic `BaseModel` classes in [shared/models.py](file:///shared/models.py).
- **Strict Data Contracts**: The orchestrator strictly validates the shape, types, and constraints of payloads before routing requests to specialist sub-agents.
- **Structured LLM Outputs**: Sub-agents use strict Pydantic response schemas (e.g. `CVTailorOutput`, `CoverLetterOutput`, `InterviewOutput`) during Gemini API calls. We enforce JSON schemas (`response_mime_type="application/json"`), completely eliminating free-text parsing vulnerabilities and ensuring the output matches our exact structured contracts.

---

## 🗄️ 3. Database Security (SQL Injection Immunity)

The local SQLite tracking datastore is completely secure against SQL injection attacks.

- **Centralized Database Manager**: Implemented in [shared/storage.py](file:///shared/storage.py).
- **100% Parameterized Queries**: Every database query that takes user input or external data utilizes **parameterized SQL placeholders (`?`)**.
- **No Interpolation**: There is **zero** string formatting (`f"..."`), concatenation (`+`), or interpolation used in any SQL query assembly. 
- **Safe Type Casting**: Inputs (such as JSON strings and ISO-formatted dates) are converted and bound as safe, typed variables by the SQLite driver itself.

---

## ☣️ 4. Failure Containment & Error Handling

To protect the orchestrator pipeline and prevent stack trace leaks:
- **Encapsulated Sub-agents**: All specialist agents wrap their LLM calls and third-party interactions in comprehensive `try...except` blocks.
- **Structured Error Responses**: In case of API failures, rate limits (`429`), or transient errors (`503`), the agent intercepts the exception and returns a valid `AgentResponse` with `success=False` and a descriptive, safe `error_message`, rather than throwing unhandled crashes up the call stack.
