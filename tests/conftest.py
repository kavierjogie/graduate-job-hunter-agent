import os
import pytest
from unittest.mock import MagicMock, AsyncMock
from pydantic import BaseModel
from typing import Any

# Import google.antigravity's Agent class
try:
    from google.antigravity import Agent
    HAS_SDK = True
except ImportError:
    HAS_SDK = False

class MockChatResponse:
    def __init__(self, agent_instance, prompt):
        self.agent = agent_instance
        self.prompt = prompt
        
    async def text(self) -> str:
        name = getattr(self.agent, "name", "").lower()
        if "cv" in name or "tailor" in name:
            return "Tailored CV content."
        elif "cover" in name or "letter" in name:
            return "Cover Letter content."
        elif "interview" in name:
            return "Interview questions."
        return "Mock response text."

    async def structured_output(self) -> Any:
        # Access response_schema from config or agent instance
        schema = None
        if hasattr(self.agent, "response_schema"):
            schema = self.agent.response_schema
        elif hasattr(self.agent, "config") and hasattr(self.agent.config, "response_schema"):
            schema = self.agent.config.response_schema
            
        if not schema:
            return await self.text()
            
        schema_name = schema.__name__ if hasattr(schema, "__name__") else str(schema)
        
        if "CVTailorOutput" in schema_name:
            return schema(
                tailored_cv_text="Tailored CV content with PII restoration support.",
                alignment_score=95.0,
                key_changes=["Highlighted Python experience", "Moved SQL skills to top"]
            )
        elif "CoverLetterOutput" in schema_name:
            return schema(
                letter_text="Professional cover letter text.",
                tone="professional and enthusiastic",
                key_highlights=["Python programming", "MCP expert"]
            )
        elif "InterviewOutput" in schema_name:
            # Import InterviewQuestion to avoid circular import issues
            try:
                from agents.interview import InterviewQuestion
                questions = [
                    InterviewQuestion(
                        question="What is MCP?",
                        type="technical",
                        suggested_talking_points=["Explain Model Context Protocol", "Discuss resources and prompts"]
                    )
                ]
            except ImportError:
                questions = [
                    {
                        "question": "What is MCP?",
                        "type": "technical",
                        "suggested_talking_points": ["Explain Model Context Protocol", "Discuss resources and prompts"]
                    }
                ]
            return schema(questions=questions)
            
        # Fallback dynamic mock generation for any other schema
        mock_data = {}
        for field_name, field in schema.model_fields.items():
            annotation = field.annotation
            if annotation == str:
                mock_data[field_name] = "Mock String"
            elif annotation == int or annotation == float:
                mock_data[field_name] = 100
            elif getattr(annotation, "__origin__", None) == list:
                mock_data[field_name] = []
            else:
                mock_data[field_name] = None
        return schema(**mock_data)

@pytest.fixture(autouse=True)
def mock_antigravity_agent(monkeypatch):
    """
    Automatically mocks the google-antigravity Agent.chat method during tests
    to prevent hit rate limits/quotas and ensure fast, reliable test execution.
    Can be disabled by setting MOCK_LLM=False in the environment.
    """
    if os.environ.get("MOCK_LLM", "true").lower() != "true":
        yield
        return
        
    if HAS_SDK:
        async def mock_chat(self, prompt, *args, **kwargs):
            return MockChatResponse(self, prompt)
            
        monkeypatch.setattr(Agent, "chat", mock_chat)
        
    yield
