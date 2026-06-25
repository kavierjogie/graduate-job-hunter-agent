import logging
from pydantic import BaseModel, Field
from typing import List
from agents.base import BaseAgent, AgentRequest, AgentResponse
from shared.llm_client import generate_structured

logger = logging.getLogger("InterviewAgent")

class InterviewQuestion(BaseModel):
    question: str = Field(..., description="The interview question.")
    type: str = Field(..., description="The type of the question, e.g., 'technical', 'behavioral', or 'situational'.")
    suggested_talking_points: List[str] = Field(..., description="Bulleted suggested talking points or strategies for answering this question.")

class InterviewOutput(BaseModel):
    questions: List[InterviewQuestion] = Field(..., description="A list of generated practice interview questions.")

class InterviewAgent(BaseAgent):
    """
    Specialist agent that analyzes a role and generates likely behavioral,
    technical, and situational interview questions, along with bulleted talking points.
    """
    def __init__(self):
        system_instructions = (
            "You are an expert interview coach. Your task is to analyze a target job description "
            "and generate a set of customized practice interview questions (technical, behavioral, "
            "or situational) along with suggested talking points."
        )
        super().__init__(
            name="Interview Agent",
            description="Generates custom practice interview questions and talking points for a role.",
            system_instructions=system_instructions,
            response_schema=InterviewOutput
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
        
        prompt = f"""
You are an expert interview coach.
Your task is to generate a set of custom practice interview questions and suggested talking points for a candidate interviewing for a role.

Job Title: {job_title}
Company: {company}

Target Job Description:
\"\"\"
{job_description}
\"\"\"

Instructions:
1. Generate a diverse mix of both technical and behavioral/situational questions (at least 3-5 questions total).
2. Each question must be highly relevant and directly grounded in the actual requirements and responsibilities detailed in the job description.
3. For each question, provide a list of concrete, helpful suggested talking points or strategies the candidate should focus on when answering.
"""
        
        reasoning_steps.append("Sent interview question generation request to Gemini.")
        
        try:
            # Call the native Antigravity Agent structured chat helper
            structured_response = await self.chat_structured(
                prompt=prompt
            )
            
            reasoning_steps.append("Received and parsed structured interview questions response from Gemini.")
            reasoning_steps.append("Interview question generation completed successfully.")
            
            # Serialize model to output format
            serialized_questions = [
                {
                    "question": q.question,
                    "type": q.type,
                    "suggested_talking_points": q.suggested_talking_points
                }
                for q in structured_response.questions
            ]
            
            return AgentResponse(
                agent_name=self.name,
                success=True,
                output={"questions": serialized_questions},
                reasoning_steps=reasoning_steps
            )
            
        except ValueError as e:
            logger.error(f"Validation or configuration error during interview question generation: {e}", exc_info=True)
            reasoning_steps.append(f"Configuration or validation error: {str(e)}")
            return AgentResponse(
                agent_name=self.name,
                success=False,
                output={},
                reasoning_steps=reasoning_steps,
                error_message=f"Configuration/Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Gemini API error during interview question generation: {e}", exc_info=True)
            reasoning_steps.append(f"Gemini API error occurred: {str(e)}")
            return AgentResponse(
                agent_name=self.name,
                success=False,
                output={},
                reasoning_steps=reasoning_steps,
                error_message=f"Gemini API execution error: {str(e)}"
            )

