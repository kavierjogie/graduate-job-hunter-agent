import asyncio
import logging
import json
import sys
import os
from contextlib import AsyncExitStack
from typing import List, Dict, Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from shared.models import JobListing

# Set up logger
logger = logging.getLogger("JobSearchMCPClient")

class JobSearchMCPClient:
    """
    Client wrapper to interact with the Job Search MCP Server.
    Decouples the Job Search Agent from the transport and server mechanics.
    """
    def __init__(self, server_path: str = "mcp_server/server.py"):
        self.server_path = server_path
        self.client_session = None
        self.exit_stack = None

    async def connect(self) -> bool:
        """
        Establishes a connection to the Job Search MCP server using Stdio transport.
        Returns True if successful, False otherwise.
        """
        logger.info(f"Attempting connection to MCP server at {self.server_path}")
        
        # Use python executable from current sys.executable to ensure we use the same venv
        python_exe = sys.executable or "python"
        
        # Resolve server_path to an absolute path if it is relative
        server_abs_path = self.server_path
        if not os.path.isabs(server_abs_path):
            try:
                from shared.config import PROJECT_ROOT
                server_abs_path = str(PROJECT_ROOT / self.server_path)
            except Exception:
                # Fallback to absolute path relative to this file
                from pathlib import Path
                server_abs_path = str(Path(__file__).resolve().parent.parent / self.server_path)
                
        logger.info(f"Resolved MCP server absolute path to: {server_abs_path}")
        
        # Forward environment variables to the subprocess so it inherits Adzuna/Gemini keys
        env = os.environ.copy()
        
        server_params = StdioServerParameters(
            command=python_exe,
            args=[server_abs_path],
            env=env
        )
        
        try:
            self.exit_stack = AsyncExitStack()
            # Enter stdio_client context
            read_stream, write_stream = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            # Enter ClientSession context
            self.client_session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            # Perform MCP handshake initialization
            await self.client_session.initialize()
            logger.info("Connected to Job Search MCP Server and initialized session.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MCP Server: {e}", exc_info=True)
            if self.exit_stack:
                await self.exit_stack.aclose()
                self.exit_stack = None
            self.client_session = None
            return False

    async def search_jobs(self, query: str, location: Optional[str] = None) -> List[JobListing]:
        """
        Queries the MCP server's job-search tool.
        """
        logger.info(f"Querying MCP tool 'search_jobs' with query='{query}', location='{location}'")
        if not self.client_session:
            logger.error("No active MCP session. Did you call connect()?")
            return []
            
        try:
            arguments = {"query": query}
            if location:
                arguments["location"] = location
                
            response = await self.client_session.call_tool("search_jobs", arguments=arguments)
            
            job_listings = []
            for content in response.content:
                if content.type == "text":
                    try:
                        jobs_data = json.loads(content.text)
                        if isinstance(jobs_data, list):
                            for job_dict in jobs_data:
                                job_listings.append(JobListing(**job_dict))
                        elif isinstance(jobs_data, dict):
                            job_listings.append(JobListing(**jobs_data))
                    except Exception as json_err:
                        logger.error(f"Failed to parse tool response as JSON: {json_err}. Content was: {content.text}")
                        
            logger.info(f"Successfully retrieved and parsed {len(job_listings)} jobs from MCP server.")
            return job_listings
            
        except Exception as e:
            logger.error(f"Error querying MCP tool 'search_jobs': {e}", exc_info=True)
            return []

    async def close(self) -> None:
        """
        Closes the connection session and cleans up transport resources.
        """
        logger.info("Closing MCP connection session.")
        if self.exit_stack:
            try:
                await self.exit_stack.aclose()
            except Exception as e:
                logger.error(f"Error closing MCP connection exit stack: {e}")
            self.exit_stack = None
        self.client_session = None
