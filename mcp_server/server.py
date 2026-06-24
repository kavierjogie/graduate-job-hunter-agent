import os
import sys
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import httpx
from fastmcp import FastMCP

# Ensure the project root is added to sys.path to allow imports of shared packages
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Import config to trigger .env loading from project root
import shared.config as config

# Initialize FastMCP Server
mcp = FastMCP(
    "Job Search MCP Server",
    description="Provides tools for searching and retrieving graduate and entry-level job listings."
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JobSearchMCPServer")

# Cache for storing search results to support get_job_details.
# Since the Adzuna API does not provide a direct job-by-ID lookup endpoint,
# we cache the mapped job objects returned from the search_jobs calls.
# Limitation: get_job_details can only retrieve details for jobs that have been
# returned in a previous search_jobs call during the lifetime of this server process.
JOB_CACHE: Dict[str, Dict[str, Any]] = {}

def map_adzuna_job(adzuna_job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper to map Adzuna job response schema to the JobListing Pydantic schema
    expected by the rest of the multi-agent system.
    """
    # Extract company name safely
    company_obj = adzuna_job.get("company") or {}
    company_name = company_obj.get("display_name") or "Unknown Company"
    
    # Extract location name safely
    location_obj = adzuna_job.get("location") or {}
    location_name = location_obj.get("display_name") or "Unknown Location"
    
    # Extract and format salary range safely
    salary_min = adzuna_job.get("salary_min")
    salary_max = adzuna_job.get("salary_max")
    salary_range = None
    if salary_min is not None or salary_max is not None:
        if salary_min is not None and salary_max is not None:
            if salary_min == salary_max:
                salary_range = f"£{int(salary_min):,}"
            else:
                salary_range = f"£{int(salary_min):,} - £{int(salary_max):,}"
        elif salary_min is not None:
            salary_range = f"£{int(salary_min):,}+"
        else:
            salary_range = f"£{int(salary_max):,} max"
            
    # Format date_posted from ISO timestamp 'created'
    created = adzuna_job.get("created")
    date_posted = None
    if created:
        try:
            # Extract YYYY-MM-DD from '2026-06-24T17:00:00Z'
            date_posted = created.split("T")[0]
        except Exception:
            date_posted = created

    # Default requirements to empty list to match Pydantic model
    requirements = []
    
    # Ensure job ID is a string
    job_id_val = str(adzuna_job.get("id"))
    
    return {
        "job_id": job_id_val,
        "title": adzuna_job.get("title") or "Untitled Position",
        "company": company_name,
        "description": adzuna_job.get("description") or "",
        "location": location_name,
        "url": adzuna_job.get("redirect_url"),
        "salary_range": salary_range,
        "date_posted": date_posted,
        "requirements": requirements
    }

@mcp.tool()
async def search_jobs(query: str, location: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search for graduate schemes, internships, and entry-level positions.

    Args:
        query: Keywords to search in job title, company, description, or requirements (e.g. 'python', 'intern').
        location: City or 'Remote' to filter results by (optional).
    """
    logger.info(f"Received search request: query='{query}', location='{location}'")
    
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    country = os.environ.get("ADZUNA_COUNTRY", "gb")
    
    if not app_id or not app_key:
        logger.error("Adzuna API credentials (ADZUNA_APP_ID or ADZUNA_APP_KEY) are missing or not set.")
        return []
        
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": query,
        "content-type": "application/json"
    }
    if location:
        params["where"] = location
        
    logger.info(f"Querying Adzuna API at {url} with params what='{query}', where='{location}'")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            
            if response.status_code == 429:
                logger.error("Adzuna API returned HTTP 429 (Rate Limit Exceeded).")
                return []
                
            response.raise_for_status()
            data = response.json()
            
    except httpx.TimeoutException as e:
        logger.error(f"Adzuna API request timed out: {e}")
        return []
    except httpx.HTTPStatusError as e:
        logger.error(f"Adzuna API HTTP error (status {e.response.status_code}): {e}")
        return []
    except Exception as e:
        logger.error(f"Adzuna API unexpected error: {e}")
        return []
        
    results = data.get("results", [])
    if not results:
        logger.info("Adzuna API returned no results.")
        return []
        
    mapped_results = []
    for job in results:
        try:
            mapped_job = map_adzuna_job(job)
            mapped_results.append(mapped_job)
            # Cache the job details keyed by job_id for get_job_details tool
            JOB_CACHE[mapped_job["job_id"]] = mapped_job
        except Exception as e:
            logger.error(f"Error mapping Adzuna job: {e}")
            
    logger.info(f"Returning {len(mapped_results)} search results from Adzuna API (and cached them).")
    return mapped_results

@mcp.tool()
def get_job_details(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve full details and requirements for a specific job listing from the local cache.

    Args:
        job_id: The unique identifier of the job.
    """
    logger.info(f"Received details request for job_id='{job_id}'")
    # Since the Adzuna API does not support direct job-ID lookup,
    # we retrieve the job from the local cache populated by previous searches.
    job = JOB_CACHE.get(job_id)
    if not job:
        logger.warning(f"Job ID '{job_id}' not found in cache. Adzuna does not support direct lookup.")
    return job

if __name__ == "__main__":
    # Start the FastMCP stdio server
    mcp.run()
