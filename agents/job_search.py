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
            description="Finds relevant graduate programmes, internships, and entry-level positions.",
            system_instructions="You are a job search specialist agent. You query the MCP server to find job listings."
        )
        self.mcp_client = mcp_client or JobSearchMCPClient()

    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Executes a job search, reads a resource, or retrieves a prompt using the MCP client.
        Expected payload keys:
          - 'action': str (optional, e.g. 'search', 'read_resource', 'get_prompt')
          - For 'search' (default):
            - 'query': str (required)
            - 'location': str (optional)
          - For 'read_resource':
            - 'uri': str (required)
          - For 'get_prompt':
            - 'name': str (required)
            - 'arguments': dict (optional)
        """
        reasoning_steps = ["Received request from Orchestrator."]
        
        action = request.payload.get("action", "search")
        reasoning_steps.append(f"Determined action: '{action}'.")
        
        try:
            connected = await self.mcp_client.connect()
            if not connected:
                raise ConnectionError("Failed to establish session with MCP server.")
                
            reasoning_steps.append("Successfully connected to MCP Server.")
            
            if action == "read_resource":
                uri = request.payload.get("uri")
                if not uri:
                    raise ValueError("Missing required parameter 'uri' for action 'read_resource'.")
                reasoning_steps.append(f"Reading MCP resource '{uri}'...")
                resource_content = await self.mcp_client.read_resource(uri)
                reasoning_steps.append("Resource successfully retrieved.")
                await self.mcp_client.close()
                return AgentResponse(
                    agent_name=self.name,
                    success=True,
                    output={"resource_content": resource_content},
                    reasoning_steps=reasoning_steps
                )
                
            elif action == "get_prompt":
                name = request.payload.get("name")
                if not name:
                    raise ValueError("Missing required parameter 'name' for action 'get_prompt'.")
                arguments = request.payload.get("arguments", {})
                reasoning_steps.append(f"Retrieving MCP prompt '{name}' with arguments: {arguments}...")
                prompt_content = await self.mcp_client.get_prompt(name, arguments)
                reasoning_steps.append("Prompt successfully retrieved.")
                await self.mcp_client.close()
                return AgentResponse(
                    agent_name=self.name,
                    success=True,
                    output={"prompt_content": prompt_content},
                    reasoning_steps=reasoning_steps
                )
                
            else: # Default search action
                query = request.payload.get("query")
                if not query:
                    raise ValueError("Missing required parameter 'query' in payload.")
                location = request.payload.get("location")
                reasoning_steps.append(f"Parsed parameters: query='{query}', location='{location}'.")
                reasoning_steps.append(f"Invoking tool 'search_jobs' on MCP Server.")
                jobs = await self.mcp_client.search_jobs(query, location)
                reasoning_steps.append(f"Received {len(jobs)} job listings from MCP Server.")
                jobs_data = [job.model_dump() for job in jobs]
                await self.mcp_client.close()
                return AgentResponse(
                    agent_name=self.name,
                    success=True,
                    output={"jobs": jobs_data},
                    reasoning_steps=reasoning_steps
                )
            
        except Exception as e:
            logger.error(f"Error during Job Search Agent execution: {e}", exc_info=True)
            reasoning_steps.append(f"Error occurred: {str(e)}")
            try:
                await self.mcp_client.close()
            except Exception:
                pass
            return AgentResponse(
                agent_name=self.name,
                success=False,
                output={},
                reasoning_steps=reasoning_steps,
                error_message=str(e)
            )

# Typing convenience import
from typing import Optional
