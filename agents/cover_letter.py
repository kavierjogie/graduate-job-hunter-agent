import logging
from pydantic import BaseModel, Field
from typing import List
from agents.base import BaseAgent, AgentRequest, AgentResponse
from shared.llm_client import generate_structured

logger = logging.getLogger("CoverLetterAgent")

class CoverLetterOutput(BaseModel):
    letter_text: str = Field(..., description="The complete, professional cover letter text.")
    tone: str = Field(..., description="The tone used in the letter (e.g., professional and enthusiastic).")
    key_highlights: List[str] = Field(..., description="A list of the main experiences/achievements highlighted in the letter.")

class CoverLetterAgent(BaseAgent):
    """
    Specialist agent that drafts highly tailored, persuasive cover letters
    by marrying a candidate's background/CV with a specific job listing's requirements.
    """
    def __init__(self):
        super().__init__(
            name="Cover Letter Agent",
            description="Drafts customized cover letters using CV details and job specifications."
        )

    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Drafts a cover letter.
        Expected payload keys:
          - 'cv_text': str (optional, defaults to tailored or base CV from context)
          - 'job_description': str (required)
          - 'company': str (required)
          - 'job_title': str (required)
          - 'tone': str (optional, defaults to 'professional')
        """
        reasoning_steps = ["Received request from Orchestrator."]
        
        payload = request.payload
        job_description = payload.get("job_description")
        company = payload.get("company")
        job_title = payload.get("job_title")
        tone = payload.get("tone", "professional and enthusiastic")

        if not all([job_description, company, job_title]):
            return AgentResponse(
                agent_name=self.name,
                success=False,
                output={},
                reasoning_steps=reasoning_steps,
                error_message="Missing one or more required parameters: 'job_description', 'company', 'job_title'."
            )
            
        # Retrieve CV text, check payload first, then fall back to context
        cv_text = payload.get("cv_text")
        if not cv_text:
            cv_text = request.context.get("user_profile", {}).get("base_cv_text")
            
        if not cv_text:
            return AgentResponse(
                agent_name=self.name,
                success=False,
                output={},
                reasoning_steps=reasoning_steps,
                error_message="No CV or profile text found to build the cover letter from."
            )
            
        reasoning_steps.append(f"Creating a cover letter request for '{job_title}' at '{company}' using {tone} tone.")
        
        prompt = f"""
You are an expert career advisor.
Your task is to draft a complete, professional cover letter for the candidate applying to the target job at the specified company.

Job Title: {job_title}
Company: {company}
Tone: {tone}

Candidate CV:
\"\"\"
{cv_text}
\"\"\"

Target Job Description:
\"\"\"
{job_description}
\"\"\"

Instructions:
1. Write a complete, professional cover letter addressing the hiring team at {company} for the {job_title} position.
2. Ground the letter ONLY in the CV content provided. Do NOT invent achievements, projects, or background that are not in the CV.
3. Tailor the narrative to highlight how the candidate's actual experiences (from their CV) make them a strong fit for the job requirements.
4. Maintain the requested tone: {tone}.
5. Provide a list of the key highlights/experiences you emphasized in the cover letter.
"""
        
        reasoning_steps.append("Sent cover letter drafting request to Gemini.")
        
        try:
            # Call the shared structured LLM client
            structured_response = await generate_structured(
                prompt=prompt,
                response_schema=CoverLetterOutput
            )
            
            reasoning_steps.append("Received and parsed structured cover letter response from Gemini.")
            reasoning_steps.append("Cover letter draft completed.")
            
            return AgentResponse(
                agent_name=self.name,
                success=True,
                output={
                    "letter_text": structured_response.letter_text,
                    "tone": structured_response.tone,
                    "key_highlights": structured_response.key_highlights
                },
                reasoning_steps=reasoning_steps
            )
            
        except ValueError as e:
            logger.error(f"Validation or configuration error during cover letter drafting: {e}", exc_info=True)
            reasoning_steps.append(f"Configuration or validation error: {str(e)}")
            return AgentResponse(
                agent_name=self.name,
                success=False,
                output={},
                reasoning_steps=reasoning_steps,
                error_message=f"Configuration/Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Gemini API error during cover letter drafting: {e}", exc_info=True)
            reasoning_steps.append(f"Gemini API error occurred: {str(e)}")
            return AgentResponse(
                agent_name=self.name,
                success=False,
                output={},
                reasoning_steps=reasoning_steps,
                error_message=f"Gemini API execution error: {str(e)}"
            )

