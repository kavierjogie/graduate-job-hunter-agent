import streamlit as st
import asyncio
import json
from datetime import datetime
from shared.models import UserProfile, ApplicationState
from agents.orchestrator import OrchestratorAgent
from shared.config import validate_config, GEMINI_API_KEY
from shared.storage import DatabaseManager

# Page Configuration
st.set_page_config(
    page_title="Graduate Job Hunter Agent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark/Modern Premium Theme)
st.markdown("""
<style>
    /* Google Font Import */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Background & Text Color adjustments for Premium feel */
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    /* Custom Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid #334155;
    }
    
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #38bdf8 !important;
    }

    /* Gradient Header styling */
    .header-container {
        background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
        border: 1px solid #312e81;
        border-radius: 16px;
        padding: 2.5rem 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }
    
    .header-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(to right, #60a5fa, #c084fc, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .header-subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        font-weight: 400;
    }
    
    /* Elegant Card style for text blocks */
    .premium-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .premium-card-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #38bdf8;
        margin-bottom: 1rem;
        border-bottom: 1px solid #334155;
        padding-bottom: 0.5rem;
    }

    /* Code/Text Viewer box styling */
    .text-viewer {
        background-color: #090d16;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 1.25rem;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.9rem;
        color: #e2e8f0;
        white-space: pre-wrap;
        max-height: 400px;
        overflow-y: auto;
        line-height: 1.5;
    }

    /* Custom Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.8rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.6) !important;
    }
    
    /* Error Card styling */
    .error-card {
        background-color: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        color: #fca5a5;
    }
    
    .error-card-title {
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #ef4444;
    }
    
    /* Status Badge styling */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-applied {
        background-color: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    .badge-interviewing {
        background-color: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .badge-offer {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-rejected {
        background-color: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    /* HTML Table styling for Application Tracker */
    .tracker-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        font-size: 0.95rem;
        background-color: #1e293b;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #334155;
    }
    .tracker-table th {
        background-color: #0f172a;
        color: #38bdf8;
        text-align: left;
        padding: 12px 16px;
        font-weight: 600;
        border-bottom: 2px solid #334155;
    }
    .tracker-table td {
        padding: 12px 16px;
        border-bottom: 1px solid #334155;
        color: #cbd5e1;
    }
    .tracker-table tr:hover {
        background-color: #334155;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to run async tasks safely in Streamlit
def run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
        
    if loop and loop.is_running():
        import threading
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)

# Default Candidate Profile (Matching run.py)
DEFAULT_PROFILE_VALUES = {
    "full_name": "Alex Mercer",
    "email": "alex.mercer@university.edu",
    "phone": "+44 7700 900077",
    "education": [
        {
            "degree": "BSc Computer Science",
            "university": "University of London",
            "grad_year": 2026,
            "grade": "First Class Honours"
        }
    ],
    "experience": [
        {
            "role": "Software Engineering Intern",
            "company": "WebTech Partners",
            "description": "Assisted in building Python REST APIs, writing SQL database migrations, and writing unit tests.",
            "dates": "Summer 2025"
        }
    ],
    "skills": ["Python", "SQL", "HTML/CSS", "Git", "Algorithms"],
    "base_cv_text": (
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
    "preferences": {
        "preferred_locations": ["London", "Remote"],
        "roles": ["Software Engineer", "Developer", "Data Scientist"]
    }
}

# 1. Configuration Check
config_valid = True
config_error_msg = ""
try:
    validate_config()
except ValueError as e:
    config_valid = False
    config_error_msg = str(e)

# Render main page header
st.markdown("""
<div class="header-container">
    <div class="header-title">Graduate Job Hunter Agent</div>
    <div class="header-subtitle">An intelligent multi-agent autopilot system powered by Gemini to search, tailor, draft, and track your job applications.</div>
</div>
""", unsafe_allow_html=True)

if not config_valid:
    st.markdown(f"""
    <div class="error-card">
        <div class="error-card-title">⚠️ Environment Configuration Error</div>
        <p>Your <code>GEMINI_API_KEY</code> is missing or invalid. Please check the instructions below to configure the app:</p>
        <pre style="background-color:#1e293b; color:#cbd5e1; padding: 1rem; border-radius: 8px; border: 1px solid #ef4444; white-space: pre-wrap;">{config_error_msg}</pre>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# 2. Sidebar - Candidate Profile Form
st.sidebar.header("👤 Candidate Profile")
st.sidebar.markdown("Customize your graduate credentials and job preferences below.")

with st.sidebar.form("profile_form"):
    full_name = st.text_input("Full Name", value=DEFAULT_PROFILE_VALUES["full_name"])
    email = st.text_input("Email", value=DEFAULT_PROFILE_VALUES["email"])
    phone = st.text_input("Phone", value=DEFAULT_PROFILE_VALUES["phone"])
    
    st.markdown("---")
    st.markdown("### 🎓 Education & Experience")
    education_json = st.text_area(
        "Education History (JSON)",
        value=json.dumps(DEFAULT_PROFILE_VALUES["education"], indent=2),
        height=120
    )
    experience_json = st.text_area(
        "Work Experience (JSON)",
        value=json.dumps(DEFAULT_PROFILE_VALUES["experience"], indent=2),
        height=120
    )
    
    st.markdown("---")
    st.markdown("### 🛠️ Skills & Base CV")
    skills_str = st.text_input(
        "Skills (comma-separated)",
        value=", ".join(DEFAULT_PROFILE_VALUES["skills"])
    )
    base_cv_text = st.text_area(
        "Raw Base CV Text",
        value=DEFAULT_PROFILE_VALUES["base_cv_text"],
        height=200
    )
    
    st.markdown("---")
    st.markdown("### 🎯 Preferences")
    locations_str = st.text_input(
        "Preferred Locations (comma-separated)",
        value=", ".join(DEFAULT_PROFILE_VALUES["preferences"]["preferred_locations"])
    )
    roles_str = st.text_input(
        "Preferred Roles (comma-separated)",
        value=", ".join(DEFAULT_PROFILE_VALUES["preferences"]["roles"])
    )
    
    save_profile_btn = st.form_submit_button("Update Session Profile")
    if save_profile_btn:
        st.sidebar.success("Session profile updated successfully.")

# Parse Candidate Profile State
try:
    education_parsed = json.loads(education_json)
except Exception:
    st.sidebar.error("Invalid JSON format in Education History.")
    education_parsed = DEFAULT_PROFILE_VALUES["education"]

try:
    experience_parsed = json.loads(experience_json)
except Exception:
    st.sidebar.error("Invalid JSON format in Work Experience.")
    experience_parsed = DEFAULT_PROFILE_VALUES["experience"]

skills_parsed = [s.strip() for s in skills_str.split(",") if s.strip()]
locations_parsed = [l.strip() for l in locations_str.split(",") if l.strip()]
roles_parsed = [r.strip() for r in roles_str.split(",") if r.strip()]

active_profile = UserProfile(
    full_name=full_name,
    email=email,
    phone=phone if phone else None,
    education=education_parsed,
    experience=experience_parsed,
    skills=skills_parsed,
    base_cv_text=base_cv_text,
    preferences={
        "preferred_locations": locations_parsed,
        "roles": roles_parsed
    }
)

# 3. Main Interface Navigation Tabs
tab_autopilot, tab_tracker = st.tabs(["🚀 Autopilot Pipeline", "📋 Application Tracker"])

# ==========================================
# TAB 1: AUTOPILOT PIPELINE
# ==========================================
with tab_autopilot:
    st.markdown("### Launch End-to-End Autopilot Job Hunter")
    st.markdown("Input your desired role and target location, and the multi-agent system will search the database, select a job, tailor your materials, generate practice interview questions, and record it in the application tracker.")
    
    col_q, col_l = st.columns(2)
    with col_q:
        search_query = st.text_input("Job Title / Technology", value="Python")
    with col_l:
        search_location = st.text_input("Location", value="London")
        
    run_pipeline = st.button("Run Autopilot Pipeline")
    
    if run_pipeline:
        st.markdown("---")
        progress_placeholder = st.empty()
        error_placeholder = st.empty()
        
        with st.spinner("Autopilot started. Coordinating specialist sub-agents..."):
            try:
                # Initialize Orchestrator and set active profile
                orchestrator = OrchestratorAgent()
                orchestrator.set_user_profile(active_profile)
                
                # Execute pipeline asynchronously
                result = run_async(orchestrator.run_autopilot_pipeline(
                    search_query=search_query,
                    location=search_location
                ))
                
                if not result["success"]:
                    # Display logs up to failure and failure reason
                    error_placeholder.markdown(f"""
                    <div class="error-card">
                        <div class="error-card-title">❌ Autopilot Pipeline Failed</div>
                        <p>A step in the multi-agent pipeline failed. See reasoning logs and error details below:</p>
                        <p><strong>Error Message:</strong> {result.get('error')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show partial logs
                    with st.expander("⛓️ Multi-Agent Reasoning Logs (Failure State)", expanded=True):
                        for step in result.get("pipeline_log", []):
                            st.write(f"🔹 {step}")
                else:
                    st.success("🎉 Autopilot Pipeline completed successfully.")
                    
                    # 1. Pipeline Log
                    with st.expander("⛓️ Multi-Agent Reasoning & Execution Logs", expanded=True):
                        st.markdown("<p style='color:#94a3b8; font-size:0.9rem;'>Judges view: trace how the Orchestrator delegates tasks to specialist sub-agents in real-time.</p>", unsafe_allow_html=True)
                        for step in result["pipeline_log"]:
                            st.write(f"✅ {step}")
                            
                    # 2. Selected Job Match
                    job = result["target_job"]
                    st.markdown(f"""
                    <div class="premium-card">
                        <div class="premium-card-title">💼 Selected Job Match</div>
                        <h3 style="color:#f8fafc; margin:0 0 0.5rem 0;">{job['title']}</h3>
                        <p style="color:#38bdf8; font-weight:600; margin:0 0 1rem 0;">{job['company']} — {job['location']}</p>
                        <table style="width:100%; border-top:1px solid #334155; padding-top:0.5rem;">
                            <tr>
                                <td style="color:#94a3b8; width:150px; font-weight:600;">Salary Range:</td>
                                <td style="color:#cbd5e1;">{job.get('salary_range', 'Not Specified')}</td>
                            </tr>
                            <tr>
                                <td style="color:#94a3b8; font-weight:600;">Job ID:</td>
                                <td style="color:#cbd5e1;"><code>{job.get('job_id')}</code></td>
                            </tr>
                            <tr>
                                <td style="color:#94a3b8; font-weight:600;">Source URL:</td>
                                <td style="color:#cbd5e1;"><a href="{job.get('url', '#')}" target="_blank" style="color:#60a5fa;">{job.get('url', 'N/A')}</a></td>
                            </tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 3. Tailored CV
                    with st.expander("📄 Tailored CV & Adjustments", expanded=True):
                        col_cv, col_adj = st.columns([2, 1])
                        with col_cv:
                            st.markdown("#### Tailored CV Content")
                            st.markdown(f'<div class="text-viewer">{result["tailored_cv"]}</div>', unsafe_allow_html=True)
                        with col_adj:
                            st.markdown("#### Adjustments Made")
                            cv_meta = result.get("tailored_cv_metadata", {})
                            st.metric(
                                label="Estimated Job Alignment Score",
                                value=f"{cv_meta.get('alignment_score', 0.0)}%"
                            )
                            st.markdown("**Core Adjustments:**")
                            key_changes = cv_meta.get("key_changes", [])
                            if key_changes:
                                for change in key_changes:
                                    st.write(f"✨ {change}")
                            else:
                                st.write("No major adjustments reported.")
                                
                    # 4. Cover Letter
                    with st.expander("✉️ Customized Cover Letter", expanded=True):
                        st.markdown("#### Generated Cover Letter")
                        st.markdown(f'<div class="text-viewer">{result["cover_letter"]}</div>', unsafe_allow_html=True)
                        
                    # 5. Interview Prep Questions
                    with st.expander("🧠 Tailored Interview Prep Questions", expanded=True):
                        st.markdown("<p style='color:#94a3b8; font-size:0.9rem;'>AI-generated practice questions with suggested talking points customized to this job description.</p>", unsafe_allow_html=True)
                        for idx, q in enumerate(result["interview_questions"], 1):
                            q_type = q.get("type", "Behavioral").upper()
                            st.markdown(f"**Q{idx}: {q['question']}**")
                            st.markdown(f"<span class='badge badge-applied'>{q_type}</span>", unsafe_allow_html=True)
                            with st.expander("💡 View Suggested Talking Points", expanded=False):
                                for pt in q.get("suggested_talking_points", []):
                                    st.write(f"• {pt}")
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                    # 6. Tracker Record Confirmation
                    tracker = result["tracker_status"]
                    status_val = tracker.get("status", "applied")
                    st.markdown(f"""
                    <div class="premium-card" style="border: 1px solid rgba(16, 185, 129, 0.4); background-color: rgba(16, 185, 129, 0.05);">
                        <div class="premium-card-title" style="color:#10b981;">📋 SQLite Application Tracker Status</div>
                        <p style="margin:0 0 0.5rem 0;">Successfully wrote the application record to local storage (<code>job_hunter.db</code>).</p>
                        <p><strong>Job ID:</strong> <code>{tracker.get('job_id')}</code> | <strong>Company:</strong> <code>{tracker.get('company')}</code></p>
                        <div><strong>Status:</strong> <span class="badge badge-offer">{status_val}</span></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
            except Exception as e:
                import traceback
                error_placeholder.markdown(f"""
                <div class="error-card">
                    <div class="error-card-title">💥 Unexpected Pipeline Exception</div>
                    <p>An unexpected exception occurred during the pipeline execution:</p>
                    <pre style="background-color:#1e293b; color:#cbd5e1; padding: 1rem; border-radius: 8px; border: 1px solid #ef4444; white-space: pre-wrap;">{traceback.format_exc()}</pre>
                </div>
                """, unsafe_allow_html=True)

# ==========================================
# TAB 2: APPLICATION TRACKER
# ==========================================
with tab_tracker:
    st.markdown("### Persistent Job Application Database")
    st.markdown("This view queries the SQLite database directly (using `DatabaseManager` in `shared.storage`), displaying all job applications saved by the Tracker Agent across your autopilot runs.")
    
    refresh_db = st.button("Refresh Database View")
    
    try:
        # Load and display database items
        db = DatabaseManager()
        # Initialize DB if not present
        run_async(db.initialize_db())
        
        # Load applications
        applications = run_async(db.list_applications())
        
        if not applications:
            st.info("No job application records found in the database. Run the Autopilot Pipeline to log your first application!")
        else:
            # Render HTML Table for premium display
            table_rows = ""
            for app in applications:
                status_class = "badge-applied"
                if app.status == "interviewing":
                    status_class = "badge-interviewing"
                elif app.status == "offer":
                    status_class = "badge-offer"
                elif app.status == "rejected":
                    status_class = "badge-rejected"
                
                # Format Date
                updated_date_str = app.last_updated.strftime("%Y-%m-%d %H:%M")
                
                # Format Notes
                notes = app.notes if app.notes else "N/A"
                
                row_html = f"""
                <tr>
                    <td><code>{app.job_id}</code></td>
                    <td><strong>{app.job_title}</strong></td>
                    <td>{app.company}</td>
                    <td><span class="badge {status_class}">{app.status}</span></td>
                    <td>{notes}</td>
                    <td>{updated_date_str}</td>
                </tr>
                """
                table_rows += row_html
                
            table_html = f"""
            <table class="tracker-table">
                <thead>
                    <tr>
                        <th>Job ID</th>
                        <th>Job Title</th>
                        <th>Company</th>
                        <th>Status</th>
                        <th>Notes</th>
                        <th>Last Updated</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            """
            st.markdown(table_html, unsafe_allow_html=True)
            
            # Application Details Explorer
            st.markdown("### 🔍 Application Detail & Timeline Explorer")
            app_options = {f"{app.job_title} at {app.company} (ID: {app.job_id})": app for app in applications}
            selected_app_name = st.selectbox("Select an application to view full timeline details:", list(app_options.keys()))
            
            if selected_app_name:
                selected_app = app_options[selected_app_name]
                st.markdown(f"#### Timeline for {selected_app.job_title} at {selected_app.company}")
                if selected_app.timeline:
                    for event in selected_app.timeline:
                        evt_date = event.get("date", "N/A")
                        evt_text = event.get("event", "N/A")
                        st.write(f"📅 **{evt_date}**: {evt_text}")
                else:
                    st.write("No timeline events logged for this application.")
                    
    except Exception as e:
        import traceback
        st.error("Failed to query SQLite database.")
        st.code(traceback.format_exc())
