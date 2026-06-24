import logging
from agents.base import BaseAgent, AgentRequest, AgentResponse

logger = logging.getLogger("InterviewAgent")

class InterviewAgent(BaseAgent):
    """
    Specialist agent that analyzes a role and generates likely behavioral,
    technical, and situational interview questions, along with bulleted talking points.
    """
    def __init__(self):
        super().__init__(
            name="Interview Agent",
            description="Generates custom practice interview questions and talking points for a role."
        )

    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Generates interview prep materials.
        Expected payload keys:
          - 'job_title': str (required)
          - 'job_description': str (required)
          - 'company': str (required)
        """
        reasoning_steps = ["Received request from Orchestrator."]
        
        payload = request.payload
        job_title = payload.get("job_title")
        job_description = payload.get("job_description")
        company = payload.get("company")
        
        if not all([job_title, job_description, company]):
            return AgentResponse(
                agent_name=self.name,
                success=False,
                output={},
                reasoning_steps=reasoning_steps,
                error_message="Missing required parameters. 'job_title', 'job_description', and 'company' must be provided."
            )
            
        reasoning_steps.append(f"Analyzing interview profile for '{job_title}' at '{company}'...")
        reasoning_steps.append("Formulating top technical questions based on job description...")
        reasoning_steps.append("Formulating top behavioral/situational questions...")
        
        # Stub questions
        questions = [
            {
                "question": f"Why do you want to work as a {job_title} at {company}?",
                "type": "behavioral",
                "suggested_talking_points": [
                    f"Express enthusiasm for {company}'s products or engineering culture.",
                    "Connect your graduate studies or internship projects to the role's responsibilities.",
                    "Highlight how this role matches your long-term career trajectory."
                ]
            },
            {
                "question": "Can you walk us through a challenging programming project you completed, and how you solved a difficult bug?",
                "type": "technical",
                "suggested_talking_points": [
                    "Use the STAR method (Situation, Task, Action, Result).",
                    "Explain your reasoning in choosing the technology stack.",
                    "Clearly describe the technical debugging steps and what you learned."
                ]
            }
        ]
        
        reasoning_steps.append("Interview question generation completed successfully.")
        
        return AgentResponse(
            agent_name=self.name,
            success=True,
            output={"questions": questions},
            reasoning_steps=reasoning_steps
        )
