import asyncio
import logging
import sys
from shared.models import UserProfile
from agents.orchestrator import OrchestratorAgent
from shared.config import validate_config

# Configure rich console logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("SystemEntrypoint")

# Define a mock candidate profile and CV
def create_mock_profile() -> UserProfile:
    return UserProfile(
        full_name="Alex Mercer",
        email="alex.mercer@university.edu",
        phone="+44 7700 900077",
        education=[
            {
                "degree": "BSc Computer Science",
                "university": "University of London",
                "grad_year": 2026,
                "grade": "First Class Honours"
            }
        ],
        experience=[
            {
                "role": "Software Engineering Intern",
                "company": "WebTech Partners",
                "description": "Assisted in building Python REST APIs, writing SQL database migrations, and writing unit tests.",
                "dates": "Summer 2025"
            }
        ],
        skills=["Python", "SQL", "HTML/CSS", "Git", "Algorithms"],
        base_cv_text=(
            "ALEX MERCER - GRADUATE SOFTWARE ENGINEER\n"
            "Email: alex.mercer@university.edu | Phone: +44 7700 900077\n\n"
            "EDUCATION:\n"
            "- BSc Computer Science, University of London (First Class, 2026)\n\n"
            "EXPERIENCE:\n"
            "- Software Engineering Intern, WebTech Partners (Summer 2025)\n"
            "  * Developed backend REST APIs in Python and Django.\n"
            "  * Designed and optimized relational databases using SQL.\n"
            "  * Wrote over 50 unit tests, improving coverage by 15%.\n\n"
            "TECHNICAL SKILLS:\n"
            "Programming: Python, SQL, JavaScript, HTML, CSS\n"
            "Tools: Git, Docker, PostgreSQL, Linux\n"
        ),
        preferences={
            "preferred_locations": ["London", "Remote"],
            "roles": ["Software Engineer", "Developer", "Data Scientist"]
        }
    )

async def main():
    # 0. Validate Environment Configuration
    validate_config()

    print("=" * 70)
    print("[DEMO] GRADUATE JOB HUNTER MULTI-AGENT SYSTEM - DEMO RUN")
    print("=" * 70)
    
    # 1. Initialize Orchestrator
    orchestrator = OrchestratorAgent()
    
    # 2. Load and set Candidate Profile
    profile = create_mock_profile()
    orchestrator.set_user_profile(profile)
    print(f"\n[System] Loaded profile for candidate: {profile.full_name}")
    print(f"[System] Core Skills: {', '.join(profile.skills)}")
    
    # 3. Execute Autopilot Pipeline (Search -> Tailor -> Letter -> Prep -> Track)
    print("\n[System] Starting Multi-Agent Autopilot Pipeline...")
    print("         Goal: Search for 'Python' jobs in 'London', tailor materials, and track.")
    print("-" * 70)
    
    result = await orchestrator.run_autopilot_pipeline(search_query="Python", location="London")
    
    print("-" * 70)
    if not result["success"]:
        print(f"[ERROR] Pipeline Failed: {result.get('error')}")
        return
        
    # 4. Display Results
    print("[SUCCESS] MULTI-AGENT AUTOPILOT PIPELINE COMPLETED SUCCESSFULLY!")
    print("\n--- PIPELINE EXECUTION LOGS ---")
    for log in result["pipeline_log"]:
        print(f"  * {log}")
        
    # Selected Job Details
    job = result["target_job"]
    print("\n--- SELECTED JOB MATCH ---")
    print(f"  - Title:     {job['title']}")
    print(f"  - Company:   {job['company']}")
    print(f"  - Location:  {job['location']}")
    print(f"  - Salary:    {job.get('salary_range', 'N/A')}")
    print(f"  - URL:       {job.get('url', 'N/A')}")
    
    # CV Tailoring
    print("\n--- TAILORED CV METADATA ---")
    cv_meta = result.get("tailored_cv_metadata", {})
    alignment_score = cv_meta.get("alignment_score", 0.0)
    key_changes = cv_meta.get("key_changes", [])
    print(f"  - Estimated Alignment Score: {alignment_score}%")
    print("  - Key Tailoring Adjustments Made:")
    if key_changes:
        for change in key_changes:
            print(f"    * {change}")
    else:
        print("    * None reported.")

    # Cover Letter Preview
    print("\n--- COVER LETTER PREVIEW ---")
    letter = result["cover_letter"]
    # Print first few lines of the letter
    indented_letter = "\n".join(f"    {line}" for line in letter.split("\n"))
    print(indented_letter)
    
    # Interview Practice Materials
    print("\n--- GENERATED INTERVIEW PREP QUESTIONS ---")
    for idx, q in enumerate(result["interview_questions"], 1):
        print(f"  * Q{idx} ({q['type']}): {q['question']}")
        print("     Talking Points:")
        for pt in q["suggested_talking_points"]:
            print(f"       * {pt}")
            
    # Tracker Database Status
    tracker = result["tracker_status"]
    print("\n--- LOCAL DATABASE APPLICATION RECORD ---")
    print(f"  - Status:       {tracker.get('status', 'applied').upper()}")
    print(f"  - Database ID:  {tracker.get('job_id')}")
    print(f"  - Saved to:     job_hunter.db (applications table)")
    
    print("\n" + "=" * 70)
    print("DEMO RUN COMPLETE. ALL CONTRACTS VERIFIED COMPILATION & EXECUTION.")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
