import logging
from typing import Optional
from datetime import datetime
from agents.base import BaseAgent, AgentRequest, AgentResponse
from shared.storage import DatabaseManager
from shared.models import ApplicationState

logger = logging.getLogger("TrackerAgent")

class TrackerAgent(BaseAgent):
    """
    Specialist agent that interacts with the SQLite storage layer to log,
    update, and retrieve job application tracking records.
    """
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        super().__init__(
            name="Tracker Agent",
            description="Manages job application status records in the local SQLite database."
        )
        self.db = db_manager or DatabaseManager()

    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Executes a database tracking operation.
        Expected payload keys:
          - 'action': str ('add_or_update', 'list', 'get')
          - 'application': dict (required for 'add_or_update', matches ApplicationState model)
          - 'application_id': str (required for 'get')
        """
        reasoning_steps = ["Received database request from Orchestrator."]
        action = request.payload.get("action")
        
        if not action:
            return AgentResponse(
                agent_name=self.name,
                success=False,
                output={},
                reasoning_steps=reasoning_steps,
                error_message="Missing required parameter 'action' in payload."
            )
            
        reasoning_steps.append(f"Initializing database at {self.db.db_path}...")
        await self.db.initialize_db()
        
        try:
            if action == "add_or_update":
                app_data = request.payload.get("application")
                if not app_data:
                    raise ValueError("Missing 'application' details in payload for 'add_or_update' action.")
                
                # Parse into ApplicationState model
                app = ApplicationState(**app_data)
                reasoning_steps.append(f"Saving application for {app.job_title} at {app.company} (Status: {app.status})...")
                
                await self.db.save_application(app)
                reasoning_steps.append("Application successfully saved to SQLite database.")
                
                return AgentResponse(
                    agent_name=self.name,
                    success=True,
                    output={"status": "saved", "job_id": app.job_id, "company": app.company},
                    reasoning_steps=reasoning_steps
                )
                
            elif action == "list":
                reasoning_steps.append("Retrieving all application records from database...")
                apps = await self.db.list_applications()
                reasoning_steps.append(f"Found {len(apps)} application records.")
                
                # Serialize applications list
                apps_data = [app.model_dump(mode="json") for app in apps]
                return AgentResponse(
                    agent_name=self.name,
                    success=True,
                    output={"applications": apps_data},
                    reasoning_steps=reasoning_steps
                )
                
            elif action == "get":
                app_id = request.payload.get("application_id")
                if not app_id:
                    raise ValueError("Missing 'application_id' in payload for 'get' action.")
                    
                reasoning_steps.append(f"Fetching application ID '{app_id}'...")
                app = await self.db.get_application(app_id)
                
                if not app:
                    reasoning_steps.append("Application record not found.")
                    return AgentResponse(
                        agent_name=self.name,
                        success=False,
                        output={},
                        reasoning_steps=reasoning_steps,
                        error_message=f"Application with ID '{app_id}' not found."
                    )
                    
                reasoning_steps.append("Application record retrieved.")
                return AgentResponse(
                    agent_name=self.name,
                    success=True,
                    output={"application": app.model_dump(mode="json")},
                    reasoning_steps=reasoning_steps
                )
            
            else:
                raise ValueError(f"Unknown action: {action}")
                
        except Exception as e:
            logger.error(f"Tracker Agent execution error: {e}", exc_info=True)
            reasoning_steps.append(f"Database error: {str(e)}")
            return AgentResponse(
                agent_name=self.name,
                success=False,
                output={},
                reasoning_steps=reasoning_steps,
                error_message=str(e)
            )
