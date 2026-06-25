import os
from typing import Type, TypeVar, Optional
from pydantic import BaseModel
from google import genai
from google.genai import types
from shared.config import validate_config

T = TypeVar('T', bound=BaseModel)

# The single seam for model configuration
DEFAULT_MODEL = "gemini-3.1-flash-lite"

# Global client cache to avoid multiple instantiations
_client_instance = None

def get_client() -> genai.Client:
    """
    Lazily retrieves or initializes the Gemini client.
    Performs configuration validation and raises a clear error if keys are missing.
    """
    global _client_instance
    if _client_instance is None:
        validate_config()
        api_key = os.environ.get("GEMINI_API_KEY")
        _client_instance = genai.Client(api_key=api_key)
    return _client_instance

async def generate_structured(
    prompt: str, 
    response_schema: Type[T], 
    model: str = DEFAULT_MODEL,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None
) -> T:
    """
    Asynchronously sends a prompt to Gemini and returns structured JSON output 
    validated against the provided response_schema, with automatic retries and 
    exponential backoff for transient 503 ServerErrors.
    Applies input guardrails and transparent PII redaction/re-hydration.
    """
    import asyncio
    from google.genai.errors import ServerError
    from shared.security import check_guardrails, redact_text, rehydrate_object
    
    # 1. Run input guardrail check
    check_guardrails(prompt)
    
    # 2. Apply PII redaction
    redacted_prompt, redaction_map = redact_text(
        prompt,
        full_name=full_name,
        email=email,
        phone=phone
    )
    
    client = get_client()
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=response_schema,
        temperature=0.2,
    )
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = await client.aio.models.generate_content(
                model=model,
                contents=redacted_prompt,
                config=config
            )
            if not response.text:
                raise ValueError("Gemini returned an empty response.")
            
            parsed_response = response_schema.model_validate_json(response.text)
            
            # 3. Re-hydrate the parsed response object
            return rehydrate_object(parsed_response, redaction_map)
            
        except ServerError as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + 0.5
                await asyncio.sleep(wait_time)
                continue
            raise

