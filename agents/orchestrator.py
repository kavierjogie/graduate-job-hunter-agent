import logging
from typing import Dict, Any, List, Optional
from agents.base import AgentRequest, AgentResponse
from agents.job_search import JobSearchAgent
from agents.cv_tailor import CVTailorAgent
from agents.cover_letter import CoverLetterAgent
from agents.interview import InterviewAgent
from agents.tracker import TrackerAgent
from shared.models import UserProfile, ApplicationState

logger = logging.getLogger("OrchestratorAgent")

class OrchestratorAgent:
    """
    Main coordinator of the multi-agent system.
    Maintains user session profile state, routes user intents to appropriate
    specialists, and runs end-to-end multi-agent pipelines.
    """
    def __init__(self):
        # Initialize the specialists
        self.job_search_agent = JobSearchAgent()
        self.cv_tailor_agent = CVTailorAgent()
        self.cover_letter_agent = CoverLetterAgent()
        self.interview_agent = InterviewAgent()
        self.tracker_agent = TrackerAgent()
        
        # In-memory session state (in a real system, synced to SQLite/Redis)
        self.user_profile: Optional[UserProfile] = None
        self.session_id: str = "session_default"

    def set_user_profile(self, profile: UserProfile) -> None:
        """Sets the active candidate profile for the session context."""
        self.user_profile = profile

    def _get_context(self) -> Dict[str, Any]:
        """Prepares the global context dict sent to all sub-agents."""
        return {
            "user_profile": self.user_profile.model_dump() if self.user_profile else None
        }

    async def route_request(self, intent: str, payload: Dict[str, Any]) -> AgentResponse:
        """
        Routes a single user intent to the corresponding specialist agent.
        """
        request = AgentRequest(
            session_id=self.session_id,
            payload=payload,
            context=self._get_context()
        )
        
        logger.info(f"Orchestrator routing intent '{intent}' to specialist...")
        
        if intent == "job_search":
            return await self.job_search_agent.execute(request)
        elif intent == "cv_tailor":
            return await self.cv_tailor_agent.execute(request)
        elif intent == "cover_letter":
            return await self.cover_letter_agent.execute(request)
        elif intent == "interview_prep":
            return await self.interview_agent.execute(request)
        elif intent == "track_application":
            return await self.tracker_agent.execute(request)
        else:
            return AgentResponse(
                agent_name="Orchestrator",
                success=False,
                output={},
                reasoning_steps=["Inspected intent."],
                error_message=f"Unknown intent: {intent}"
            )

    async def run_autopilot_pipeline(self, search_query: str, location: Optional[str] = None) -> Dict[str, Any]:
        """
        A high-value, multi-step pipeline executing genuine multi-agent reasoning:
        1. Find jobs matching the query via the Job Search Agent.
        2. Select the first job found.
        3. Tailor the base CV for that job via the CV Tailoring Agent.
        4. Draft a custom cover letter via the Cover Letter Agent.
        5. Generate tailored interview questions via the Interview Agent.
        6. Record the application as 'applied' via the Tracker Agent.
        """
        pipeline_log = ["Starting Autopilot Pipeline."]
        
        if not self.user_profile:
            return {
                "success": False,
                "pipeline_log": pipeline_log,
                "error": "Cannot run autopilot without a loaded User Profile."
            }

        # Step 1: Search Jobs
        pipeline_log.append("Step 1: Searching for job opportunities...")
        search_res = await self.route_request("job_search", {"query": search_query, "location": location})
        if not search_res.success or not search_res.output.get("jobs"):
            return {
                "success": False,
                "pipeline_log": pipeline_log + search_res.reasoning_steps,
                "error": f"Job search failed or returned no results: {search_res.error_message}"
            }
        
        target_job_dict = search_res.output["jobs"][0]
        job_title = target_job_dict["title"]
        company = target_job_dict["company"]
        job_description = target_job_dict["description"]
        job_id = target_job_dict["job_id"]
        pipeline_log.append(f"Selected Job: {job_title} at {company} (ID: {job_id}).")

        # Step 2: Tailor CV
        pipeline_log.append("Step 2: Tailoring base CV to job description...")
        cv_res = await self.route_request("cv_tailor", {"job_description": job_description})
        if not cv_res.success:
            return {
                "success": False,
                "pipeline_log": pipeline_log + cv_res.reasoning_steps,
                "error": f"CV Tailoring failed: {cv_res.error_message}"
            }
        tailored_cv_text = cv_res.output["tailored_cv_text"]
        pipeline_log.append("CV successfully tailored.")

        # Step 3: Write Cover Letter
        pipeline_log.append("Step 3: Drafting a custom cover letter...")
        cl_res = await self.route_request("cover_letter", {
            "job_description": job_description,
            "company": company,
            "job_title": job_title,
            "cv_text": tailored_cv_text
        })
        if not cl_res.success:
            return {
                "success": False,
                "pipeline_log": pipeline_log + cl_res.reasoning_steps,
                "error": f"Cover Letter drafting failed: {cl_res.error_message}"
            }
        cover_letter_text = cl_res.output["letter_text"]
        pipeline_log.append("Cover letter successfully drafted.")

        # Step 4: Generate Interview Prep Questions
        pipeline_log.append("Step 4: Creating role-specific interview practice materials...")
        int_res = await self.route_request("interview_prep", {
            "job_title": job_title,
            "job_description": job_description,
            "company": company
        })
        interview_questions = int_res.output.get("questions", []) if int_res.success else []
        pipeline_log.append("Interview prep questions generated.")

        # Step 5: Log to Tracker
        pipeline_log.append("Step 5: Logging application status in SQLite local database...")
        app_state = {
            "job_id": job_id,
            "job_title": job_title,
            "company": company,
            "status": "applied",
            "notes": "Autopilot generated application.",
            "timeline": [
                {"date": "2026-06-24", "event": "Application generated and tailored by Agent"}
            ]
        }
        track_res = await self.route_request("track_application", {
            "action": "add_or_update",
            "application": app_state
        })
        pipeline_log.append("Application logged to local SQLite datastore.")

        pipeline_log.append("Autopilot Pipeline completed successfully.")
        
        return {
            "success": True,
            "pipeline_log": pipeline_log,
            "target_job": target_job_dict,
            "tailored_cv": tailored_cv_text,
            "tailored_cv_metadata": cv_res.output,
            "cover_letter": cover_letter_text,
            "interview_questions": interview_questions,
            "tracker_status": track_res.output
        }
