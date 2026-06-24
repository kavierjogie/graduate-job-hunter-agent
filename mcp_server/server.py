import os
import json
import logging
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP(
    "Job Search MCP Server",
    description="Provides tools for searching and retrieving graduate and entry-level job listings."
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JobSearchMCPServer")

# Path to the mock database
DB_PATH = os.path.join(os.path.dirname(__file__), "jobs_db.json")

def load_jobs() -> List[Dict[str, Any]]:
    """Helper to load mock jobs from JSON database."""
    try:
        if os.path.exists(DB_PATH):
            with open(DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading jobs database: {e}")
    return []

@mcp.tool()
def search_jobs(query: str, location: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search for graduate schemes, internships, and entry-level positions.

    Args:
        query: Keywords to search in job title, company, description, or requirements (e.g. 'python', 'intern').
        location: City or 'Remote' to filter results by (optional).
    """
    logger.info(f"Received search request: query='{query}', location='{location}'")
    jobs = load_jobs()
    
    query = query.lower()
    results = []
    
    for job in jobs:
        # Check text match
        text_match = (
            query in job.get("title", "").lower() or
            query in job.get("company", "").lower() or
            query in job.get("description", "").lower() or
            any(query in req.lower() for req in job.get("requirements", []))
        )
        
        # Check location match
        loc_match = True
        if location:
            loc_match = location.lower() in job.get("location", "").lower()
            
        if text_match and loc_match:
            results.append(job)
            
    logger.info(f"Returning {len(results)} search results.")
    return results

@mcp.tool()
def get_job_details(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve full details and requirements for a specific job listing.

    Args:
        job_id: The unique identifier of the job (e.g. 'grad_001').
    """
    logger.info(f"Received details request for job_id='{job_id}'")
    jobs = load_jobs()
    for job in jobs:
        if job.get("job_id") == job_id:
            return job
    return None

if __name__ == "__main__":
    # Start the FastMCP stdio server
    mcp.run()
