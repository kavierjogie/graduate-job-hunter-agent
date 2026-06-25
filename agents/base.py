import os
import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Any, Optional, Dict, List, Type
from pydantic import BaseModel, Field
from google.antigravity import Agent, LocalAgentConfig

# Set up logger
logger = logging.getLogger("BaseAgent")

# Define TypeVars for generic agent inputs/outputs
InputType = TypeVar('InputType', bound=BaseModel)
OutputType = TypeVar('OutputType', bound=BaseModel)

class AgentRequest(BaseModel):
    """
    Standard request wrapper received by all sub-agents.
    Ensures consistent data format across the orchestrator boundary.
    """
    session_id: str = Field(..., description="Unique session identifier for state tracking")
    payload: Dict[str, Any] = Field(..., description="Agent-specific input arguments")
    context: Dict[str, Any] = Field(default_factory=dict, description="Shared global context, e.g. user profile data")

class AgentResponse(BaseModel):
    """
    Standard response wrapper returned by all sub-agents.
    Ensures the orchestrator can consistently read logs, status, and outputs.
    """
    agent_name: str = Field(..., description="Name of the agent that executed the task")
    success: bool = Field(..., description="Flag indicating if the task completed successfully")
    output: Dict[str, Any] = Field(..., description="Agent-specific output payload")
    reasoning_steps: List[str] = Field(default_factory=list, description="Audit log of agent thoughts/actions")
    error_message: Optional[str] = Field(None, description="Detailed error message if execution failed")

class BaseAgent(Agent, ABC, Generic[InputType, OutputType]):
    """
    Abstract Base Class for all specialist agents.
    Inherits from the official Google Antigravity Agent.
    """
    def __init__(
        self, 
        name: str, 
        description: str,
        system_instructions: str = "You are a helpful assistant.",
        response_schema: Optional[Type[BaseModel]] = None
    ):
        self.name = name
        self.description = description
        self.system_instructions = system_instructions
        self.response_schema = response_schema
        
        # Load API key and model from environment configuration seam
        from shared.config import GEMINI_API_KEY
        api_key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        model_name = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
        
        # Configure the official Antigravity Agent
        config = LocalAgentConfig(
            system_instructions=system_instructions,
            response_schema=response_schema,
            api_key=api_key,
            model=model_name
        )
        super().__init__(config)

    @abstractmethod
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Processes the request and returns a standardized AgentResponse.
        Each specialist agent overrides this method.
        """
        pass

    async def chat_structured(
        self, 
        prompt: str, 
        user_profile: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Helper method to run a secure, structured chat session using the native Antigravity Agent.
        Handles prompt injection guardrails, PII redaction, and local re-hydration transparently.
        """
        from shared.security import check_guardrails, redact_text, rehydrate_object
        
        # 1. Run input guardrail check
        check_guardrails(prompt)
        
        # 2. Apply PII redaction
        full_name = user_profile.get("full_name") if user_profile else None
        email = user_profile.get("email") if user_profile else None
        phone = user_profile.get("phone") if user_profile else None
        
        redacted_prompt, redaction_map = redact_text(
            prompt,
            full_name=full_name,
            email=email,
            phone=phone
        )
        
        # 3. Execute chat using the native Antigravity Agent context with rate-limiting retries
        import asyncio
        max_retries = 5
        backoff = 2.0
        
        for attempt in range(max_retries):
            try:
                async with self as agent:
                    chat_response = await agent.chat(redacted_prompt)
                    
                    # Retrieve structured output if a schema is defined
                    if self.response_schema:
                        try:
                            raw_output = await chat_response.structured_output()
                            if isinstance(raw_output, BaseModel):
                                parsed_response = raw_output
                            elif isinstance(raw_output, dict):
                                parsed_response = self.response_schema(**raw_output)
                            else:
                                parsed_response = self.response_schema.model_validate(raw_output)
                        except Exception as err:
                            logger.warning(f"Failed to get structured output on attempt {attempt+1}: {err}. Falling back to text parsing.")
                            text_val = await chat_response.text()
                            parsed_response = self.response_schema.model_validate_json(text_val)
                    else:
                        parsed_response = await chat_response.text()
                break # Success, break out of retry loop
            except Exception as e:
                # Identify if the error is a rate-limit (429) or transient server error (503)
                err_msg = str(e).lower()
                is_rate_limit = "429" in err_msg or "quota" in err_msg or "rate" in err_msg
                is_transient = "503" in err_msg or "unavailable" in err_msg
                
                if (is_rate_limit or is_transient) and attempt < max_retries - 1:
                    # Calculate base wait time with exponential backoff
                    base_wait = (backoff ** attempt) + 5.0
                    wait_time = base_wait
                    
                    # Attempt to extract exact retry delay from the error message (e.g. "Please retry in 55.02s")
                    import re
                    match = re.search(r"(?:please retry in|retrydelay:?)\s*([\d.]+)\s*s?", err_msg)
                    if match:
                        try:
                            parsed_delay = float(match.group(1))
                            wait_time = max(wait_time, parsed_delay + 1.0)
                        except ValueError:
                            pass
                    
                    logger.warning(
                        f"Temporary API issue ({'429 Rate Limit' if is_rate_limit else '503 Service Unavailable'}) "
                        f"encountered: {e}. Retrying in {wait_time:.2f}s... (Attempt {attempt+1}/{max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    # Reraise the exception if retries are exhausted or it's a non-retryable error
                    logger.error(f"Agent chat execution failed after {attempt+1} attempts: {e}")
                    raise
                
        # 4. Re-hydrate the structured response containing placeholders
        return rehydrate_object(parsed_response, redaction_map)
