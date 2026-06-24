import logging
from agents.base import BaseAgent, AgentRequest, AgentResponse

logger = logging.getLogger("CoverLetterAgent")

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
            
        reasoning_steps.append(f"Creating a cover letter for '{job_title}' at '{company}' using {tone} tone.")
        reasoning_steps.append("Aligning applicant's key achievements with job requirements...")
        reasoning_steps.append("Writing opening, body, and closing paragraphs...")
        
        # Stub draft text
        draft_text = (
            f"Dear Hiring Team at {company},\n\n"
            f"I am writing to express my strong interest in the {job_title} position. "
            f"With a background in software development and a keen passion for engineering, "
            f"I am eager to contribute to your team's goals.\n\n"
            f"My technical skills and past projects align closely with your requirements, "
            f"specifically my experience with key technologies mentioned in your job description. "
            f"Thank you for your time and consideration.\n\n"
            f"Sincerely,\n[Candidate Name]"
        )
        
        key_highlights = [
            f"Aligned background with {job_title} responsibilities.",
            f"Emphasized interest in {company}'s industry presence."
        ]
        
        reasoning_steps.append("Cover letter draft completed.")
        
        return AgentResponse(
            agent_name=self.name,
            success=True,
            output={
                "letter_text": draft_text,
                "tone": tone,
                "key_highlights": key_highlights
            },
            reasoning_steps=reasoning_steps
        )
