import pytest
from agents.base import AgentRequest, AgentResponse
from agents.job_search import JobSearchAgent
from agents.cv_tailor import CVTailorAgent
from agents.cover_letter import CoverLetterAgent
from agents.interview import InterviewAgent
from agents.tracker import TrackerAgent

@pytest.fixture
def base_request():
    return AgentRequest(
        session_id="test_session",
        payload={},
        context={
            "user_profile": {
                "full_name": "Test User",
                "email": "test@example.com",
                "base_cv_text": "Base CV content",
                "education": [],
                "experience": [],
                "skills": [],
                "preferences": {}
            }
        }
    )

@pytest.mark.asyncio
async def test_job_search_agent_interface(base_request):
    agent = JobSearchAgent()
    base_request.payload = {"query": "Python"}
    response = await agent.execute(base_request)
    
    assert isinstance(response, AgentResponse)
    assert response.agent_name == "Job Search Agent"
    assert response.success is True
    assert "jobs" in response.output
    assert len(response.output["jobs"]) > 0

@pytest.mark.asyncio
async def test_cv_tailor_agent_interface(base_request):
    agent = CVTailorAgent()
    base_request.payload = {"job_description": "We need a Python developer."}
    response = await agent.execute(base_request)
    
    assert isinstance(response, AgentResponse)
    assert response.agent_name == "CV Tailoring Agent"
    assert response.success is True
    assert "tailored_cv_text" in response.output
    assert "alignment_score" in response.output

@pytest.mark.asyncio
async def test_cover_letter_agent_interface(base_request):
    agent = CoverLetterAgent()
    base_request.payload = {
        "job_description": "We need a Python developer.",
        "company": "TechCorp",
        "job_title": "Developer"
    }
    response = await agent.execute(base_request)
    
    assert isinstance(response, AgentResponse)
    assert response.agent_name == "Cover Letter Agent"
    assert response.success is True
    assert "letter_text" in response.output

@pytest.mark.asyncio
async def test_interview_agent_interface(base_request):
    agent = InterviewAgent()
    base_request.payload = {
        "job_title": "Python Developer",
        "job_description": "Write code.",
        "company": "TechCorp"
    }
    response = await agent.execute(base_request)
    
    assert isinstance(response, AgentResponse)
    assert response.agent_name == "Interview Agent"
    assert response.success is True
    assert "questions" in response.output
    assert len(response.output["questions"]) > 0
