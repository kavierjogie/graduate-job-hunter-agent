import os
import pytest
import asyncio
from datetime import datetime
from shared.models import UserProfile, ApplicationState
from shared.storage import DatabaseManager

# Use a test-specific SQLite database
TEST_DB = "test_job_hunter.db"

@pytest.fixture
async def db_manager():
    # Setup
    manager = DatabaseManager(db_path=TEST_DB)
    await manager.initialize_db()
    yield manager
    # Teardown: Remove the test database file
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError:
            pass

@pytest.mark.asyncio
async def test_user_profile_persistence(db_manager):
    # Create profile
    profile = UserProfile(
        full_name="Test User",
        email="test@example.com",
        phone="123456",
        base_cv_text="My base cv content",
        education=[],
        experience=[],
        skills=["Python"],
        preferences={}
    )
    
    # Save profile
    await db_manager.save_user_profile(profile)
    
    # Retrieve profile
    retrieved = await db_manager.get_user_profile()
    
    assert retrieved is not None
    assert retrieved.full_name == "Test User"
    assert retrieved.email == "test@example.com"
    assert retrieved.base_cv_text == "My base cv content"
    assert "Python" in retrieved.skills

@pytest.mark.asyncio
async def test_application_tracking(db_manager):
    app = ApplicationState(
        application_id="app_test_123",
        job_id="job_001",
        job_title="Software Engineer",
        company="TechCorp",
        status="applied",
        notes="First application",
        timeline=[{"date": "2026-06-24", "event": "Created"}]
    )
    
    # Save application
    await db_manager.save_application(app)
    
    # Retrieve application
    retrieved = await db_manager.get_application("app_test_123")
    assert retrieved is not None
    assert retrieved.job_title == "Software Engineer"
    assert retrieved.company == "TechCorp"
    assert retrieved.status == "applied"
    assert len(retrieved.timeline) == 1
    
    # List applications
    all_apps = await db_manager.list_applications()
    assert len(all_apps) == 1
    assert all_apps[0].application_id == "app_test_123"
