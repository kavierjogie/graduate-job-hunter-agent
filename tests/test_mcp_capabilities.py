import pytest
import os
import shutil
import json
from pathlib import Path
from shared.models import UserProfile, ApplicationState
from shared.storage import DatabaseManager
from shared.mcp_client import JobSearchMCPClient
from agents.base import AgentRequest
from agents.job_search import JobSearchAgent
from agents.cv_tailor import CVTailorAgent
from agents.cover_letter import CoverLetterAgent

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "job_hunter.db"
DB_BAK_PATH = PROJECT_ROOT / "job_hunter.db.bak"

@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    # 1. Back up existing database
    backed_up = False
    if DB_PATH.exists():
        shutil.move(str(DB_PATH), str(DB_BAK_PATH))
        backed_up = True
        
    # 2. Initialize test database and mock data using asyncio.run
    import asyncio
    
    async def async_setup():
        db = DatabaseManager(db_path=str(DB_PATH))
        await db.initialize_db()
        
        # Save a mock user profile
        profile = UserProfile(
            full_name="Test MCP Candidate",
            email="mcp_test@example.com",
            phone="123-456-7890",
            education=[{"degree": "BSc", "school": "Test Uni"}],
            experience=[{"role": "Developer", "company": "Test Co"}],
            skills=["Python", "MCP"],
            base_cv_text="This is a test base CV content for MCP resources.",
            preferences={"location": "Remote"}
        )
        await db.save_user_profile(profile)
        
        # Save a mock application
        app = ApplicationState(
            job_id="test_mcp_job_001",
            job_title="Test Engineer",
            company="MCP Corp",
            status="interviewing",
            notes="Test notes",
            timeline=[{"date": "2026-06-25", "event": "Applied"}]
        )
        await db.save_application(app)
        
    asyncio.run(async_setup())
    
    yield
    
    # 3. Clean up test database
    if DB_PATH.exists():
        try:
            os.remove(str(DB_PATH))
        except Exception:
            pass
        
    # 4. Restore original database
    if backed_up and DB_BAK_PATH.exists():
        try:
            shutil.move(str(DB_BAK_PATH), str(DB_PATH))
        except Exception:
            pass

@pytest.mark.asyncio
async def test_mcp_client_read_resources():
    client = JobSearchMCPClient()
    connected = await client.connect()
    assert connected is True
    
    # Test reading cv://base
    cv_text = await client.read_resource("cv://base")
    assert cv_text is not None
    assert "test base CV content" in cv_text
    
    # Test reading tracker://applications
    apps_json = await client.read_resource("tracker://applications")
    assert apps_json is not None
    apps_data = json.loads(apps_json)
    assert isinstance(apps_data, list)
    assert len(apps_data) == 1
    assert apps_data[0]["company"] == "MCP Corp"
    
    await client.close()

@pytest.mark.asyncio
async def test_mcp_client_get_prompts():
    client = JobSearchMCPClient()
    connected = await client.connect()
    assert connected is True
    
    # Test getting tailor_cv prompt
    prompt = await client.get_prompt(
        name="tailor_cv",
        arguments={"base_cv": "My CV text", "job_description": "Target job description"}
    )
    assert prompt is not None
    assert "My CV text" in prompt
    assert "Target job description" in prompt
    
    # Test getting draft_cover_letter prompt
    prompt = await client.get_prompt(
        name="draft_cover_letter",
        arguments={
            "job_title": "Developer",
            "company": "TechCorp",
            "job_description": "Need Python dev",
            "cv_text": "Experienced coder",
            "tone": "enthusiastic"
        }
    )
    assert prompt is not None
    assert "Developer" in prompt
    assert "TechCorp" in prompt
    assert "Need Python dev" in prompt
    assert "Experienced coder" in prompt
    
    await client.close()

@pytest.mark.asyncio
async def test_job_search_agent_resource_and_prompt_actions():
    agent = JobSearchAgent()
    
    # Test read_resource action
    req_res = AgentRequest(
        session_id="test_session",
        payload={"action": "read_resource", "uri": "cv://base"}
    )
    res = await agent.execute(req_res)
    assert res.success is True
    assert "resource_content" in res.output
    assert "test base CV content" in res.output["resource_content"]
    
    # Test get_prompt action
    req_prompt = AgentRequest(
        session_id="test_session",
        payload={
            "action": "get_prompt",
            "name": "tailor_cv",
            "arguments": {"base_cv": "Base CV content", "job_description": "Job desc"}
        }
    )
    res = await agent.execute(req_prompt)
    assert res.success is True
    assert "prompt_content" in res.output
    assert "Base CV content" in res.output["prompt_content"]

@pytest.mark.asyncio
async def test_cv_tailor_agent_dynamic_prompt():
    agent = CVTailorAgent()
    req = AgentRequest(
        session_id="test_session",
        payload={"job_description": "We need an MCP expert."},
        context={
            "user_profile": {
                "full_name": "Test User",
                "email": "test@example.com",
                "base_cv_text": "CV text with Python.",
                "education": [],
                "experience": [],
                "skills": [],
                "preferences": {}
            }
        }
    )
    res = await agent.execute(req)
    assert res.success is True
    assert "tailored_cv_text" in res.output
    # The reasoning steps should show that it loaded the prompt from the MCP server
    assert any("Loaded CV tailoring prompt dynamically from MCP server" in step or "Successfully loaded CV tailoring prompt" in step for step in res.reasoning_steps)

@pytest.mark.asyncio
async def test_cover_letter_agent_dynamic_prompt():
    agent = CoverLetterAgent()
    req = AgentRequest(
        session_id="test_session",
        payload={
            "job_description": "We need an MCP expert.",
            "company": "MCP Corp",
            "job_title": "MCP Specialist"
        },
        context={
            "user_profile": {
                "full_name": "Test User",
                "email": "test@example.com",
                "base_cv_text": "CV text with Python.",
                "education": [],
                "experience": [],
                "skills": [],
                "preferences": {}
            }
        }
    )
    res = await agent.execute(req)
    assert res.success is True
    assert "letter_text" in res.output
    # The reasoning steps should show that it loaded the prompt from the MCP server
    assert any("Loaded cover letter prompt dynamically from MCP server" in step or "Successfully loaded cover letter prompt" in step for step in res.reasoning_steps)
