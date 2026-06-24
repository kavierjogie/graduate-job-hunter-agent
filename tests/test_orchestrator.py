import pytest
import os
from shared.models import UserProfile
from agents.orchestrator import OrchestratorAgent

TEST_DB_ORCH = "test_orchestrator.db"

@pytest.fixture
def orchestrator():
    orch = OrchestratorAgent()
    # Override database manager path to avoid polluting main database
    orch.tracker_agent.db.db_path = TEST_DB_ORCH
    
    profile = UserProfile(
        full_name="Test Candidate",
        email="candidate@test.com",
        base_cv_text="BSc Computer Science. Python developer.",
        education=[],
        experience=[],
        skills=["Python"],
        preferences={}
    )
    orch.set_user_profile(profile)
    yield orch
    
    # Teardown database file if it exists
    if os.path.exists(TEST_DB_ORCH):
        try:
            os.remove(TEST_DB_ORCH)
        except PermissionError:
            pass

@pytest.mark.asyncio
async def test_orchestrator_routing(orchestrator):
    # Test job search routing
    res = await orchestrator.route_request("job_search", {"query": "Python"})
    assert res.success is True
    assert res.agent_name == "Job Search Agent"
    assert "jobs" in res.output

@pytest.mark.asyncio
async def test_orchestrator_autopilot_pipeline(orchestrator):
    # Execute end-to-end autopilot pipeline
    result = await orchestrator.run_autopilot_pipeline(search_query="Python", location="London")
    
    assert result["success"] is True
    assert "target_job" in result
    assert "tailored_cv" in result
    assert "cover_letter" in result
    assert "interview_questions" in result
    assert "tracker_status" in result
    assert len(result["pipeline_log"]) > 0
    assert len(result["target_job"]["company"]) > 0
