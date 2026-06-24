import logging
from pydantic import BaseModel, Field
from typing import List
from agents.base import BaseAgent, AgentRequest, AgentResponse
from shared.llm_client import generate_structured

logger = logging.getLogger("CVTailorAgent")

class CVTailorOutput(BaseModel):
    tailored_cv_text: str = Field(..., description="The fully tailored CV text, highlighting and reordering experience to align with the job description without fabricating any information.")
    alignment_score: float = Field(..., description="An estimated alignment score between the candidate's CV and the job description, on a scale of 0.0 to 100.0.")
    key_changes: List[str] = Field(..., description="A short list of concrete, specific adjustments made to reorder/reframe/rephrase the CV content.")

class CVTailorAgent(BaseAgent):
    """
    Specialist agent that tailors a candidate's base CV/profile to align with 
    a specific job description. Highlights key skills and relevant projects.
    """
    def __init__(self):
        super().__init__(
            name="CV Tailoring Agent",
            description="Tailors a candidate's CV/resume to match a target job description."
        )

    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Tailors a CV.
        Expected payload keys:
          - 'base_cv_text': str (optional, defaults to context's base CV if present)
          - 'job_description': str (required)
        """
        reasoning_steps = ["Received request from Orchestrator."]
        
        job_description = request.payload.get("job_description")
        if not job_description:
            return AgentResponse(
                agent_name=self.name,
                success=False,
                output={},
                reasoning_steps=reasoning_steps,
                error_message="Missing required parameter 'job_description' in payload."
            )
            
        # Extract base CV from payload, fall back to global context
        base_cv_text = request.payload.get("base_cv_text")
        if not base_cv_text:
            base_cv_text = request.context.get("user_profile", {}).get("base_cv_text")
            
        if not base_cv_text:
            return AgentResponse(
                agent_name=self.name,
                success=False,
                output={},
                reasoning_steps=reasoning_steps,
                error_message="Base CV text not provided in payload or global context."
            )
            
        reasoning_steps.append("Successfully retrieved base CV and target job description.")
        
        prompt = f"""
You are an expert CV tailoring assistant.
Your task is to tailor the candidate's base CV to align with the target job description.

Candidate Base CV:
\"\"\"
{base_cv_text}
\"\"\"

Target Job Description:
\"\"\"
{job_description}
\"\"\"

Instructions:
1. Rewrite and reorder the CV content to emphasize experience and skills relevant to the job description.
2. Maintain a professional, clean tone.
3. CRITICAL: Do NOT fabricate any experience, qualifications, projects, or skills that the candidate does not have. Only reorder, reframe, or rephrase the existing content to highlight matching elements.
4. Estimate an alignment score (0.0 to 100.0) reflecting how well the tailored CV matches the job requirements.
5. Provide a short list of concrete, specific changes/adjustments made.
"""
        
        reasoning_steps.append("Sent CV tailoring request to Gemini.")
        
        try:
            # Call the shared structured LLM client
            structured_response = await generate_structured(
                prompt=prompt,
                response_schema=CVTailorOutput
            )
            
            reasoning_steps.append("Received and parsed structured CV tailoring response from Gemini.")
            reasoning_steps.append(f"CV tailoring completed. Alignment score estimated at {structured_response.alignment_score}%.")
            
            return AgentResponse(
                agent_name=self.name,
                success=True,
                output={
                    "tailored_cv_text": structured_response.tailored_cv_text,
                    "alignment_score": structured_response.alignment_score,
                    "key_changes": structured_response.key_changes
                },
                reasoning_steps=reasoning_steps
            )
            
        except ValueError as e:
            logger.error(f"Validation or configuration error during CV tailoring: {e}", exc_info=True)
            reasoning_steps.append(f"Configuration or validation error: {str(e)}")
            return AgentResponse(
                agent_name=self.name,
                success=False,
                output={},
                reasoning_steps=reasoning_steps,
                error_message=f"Configuration/Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Gemini API error during CV tailoring: {e}", exc_info=True)
            reasoning_steps.append(f"Gemini API error occurred: {str(e)}")
            return AgentResponse(
                agent_name=self.name,
                success=False,
                output={},
                reasoning_steps=reasoning_steps,
                error_message=f"Gemini API execution error: {str(e)}"
            )

