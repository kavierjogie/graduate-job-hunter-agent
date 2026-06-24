import logging
from agents.base import BaseAgent, AgentRequest, AgentResponse

logger = logging.getLogger("CVTailorAgent")

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
        reasoning_steps.append("Analyzing job description for key requirements...")
        reasoning_steps.append("Drafting customized bullet points and emphasizing matched skills...")
        
        # Stub logic for tailoring:
        # In a real implementation, this would invoke Gemini with a structured prompt, 
        # comparing experiences and outputting the tailored text and metadata.
        tailored_cv = f"{base_cv_text}\n\n[TAILORED ADJUSTMENT] Highlighted skills matching: {job_description[:50]}..."
        alignment_score = 88.0
        key_changes = [
            "Reordered technical skills section to place relevant programming languages first.",
            "Revised past project descriptions to emphasize database and API design experiences.",
            "Added summary statement aligning career goals with the target company's mission."
        ]
        
        reasoning_steps.append(f"CV tailoring completed. Alignment score estimated at {alignment_score}%.")
        
        return AgentResponse(
            agent_name=self.name,
            success=True,
            output={
                "tailored_cv_text": tailored_cv,
                "alignment_score": alignment_score,
                "key_changes": key_changes
            },
            reasoning_steps=reasoning_steps
        )
