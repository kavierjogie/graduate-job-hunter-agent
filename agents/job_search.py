import logging
from agents.base import BaseAgent, AgentRequest, AgentResponse
from shared.mcp_client import JobSearchMCPClient

logger = logging.getLogger("JobSearchAgent")

class JobSearchAgent(BaseAgent):
    """
    Specialist agent that searches for graduate opportunities, internships,
    and entry-level jobs by interacting with the Job Search MCP Server.
    """
    def __init__(self, mcp_client: Optional[JobSearchMCPClient] = None):
        super().__init__(
            name="Job Search Agent",
            description="Finds relevant graduate programmes, internships, and entry-level positions."
        )
        self.mcp_client = mcp_client or JobSearchMCPClient()

    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Executes a job search using the query parameters passed in the payload.
        Expected payload keys:
          - 'query': str (e.g. "software engineer", "product manager")
          - 'location': str (optional, e.g. "London", "Remote")
        """
        reasoning_steps = ["Received request from Orchestrator."]
        
        query = request.payload.get("query")
        if not query:
            return AgentResponse(
                agent_name=self.name,
                success=False,
                output={},
                reasoning_steps=reasoning_steps,
                error_message="Missing required parameter 'query' in payload."
            )
            
        location = request.payload.get("location")
        
        reasoning_steps.append(f"Parsed parameters: query='{query}', location='{location}'.")
        reasoning_steps.append("Connecting to the Job Search MCP Server...")
        
        try:
            connected = await self.mcp_client.connect()
            if not connected:
                raise ConnectionError("Failed to establish session with MCP server.")
                
            reasoning_steps.append("Successfully connected to MCP Server.")
            reasoning_steps.append(f"Invoking tool 'search_jobs' on MCP Server with query='{query}'.")
            
            jobs = await self.mcp_client.search_jobs(query, location)
            reasoning_steps.append(f"Received {len(jobs)} job listings from MCP Server.")
            
            # Convert JobListing objects to dictionaries for output serialization
            jobs_data = [job.model_dump() for job in jobs]
            
            reasoning_steps.append("Closing MCP server connection.")
            await self.mcp_client.close()
            
            return AgentResponse(
                agent_name=self.name,
                success=True,
                output={"jobs": jobs_data},
                reasoning_steps=reasoning_steps
            )
            
        except Exception as e:
            logger.error(f"Error during job search: {e}", exc_info=True)
            reasoning_steps.append(f"Error occurred: {str(e)}")
            return AgentResponse(
                agent_name=self.name,
                success=False,
                output={},
                reasoning_steps=reasoning_steps,
                error_message=str(e)
            )

# Typing convenience import
from typing import Optional
