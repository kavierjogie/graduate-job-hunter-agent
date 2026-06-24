import json
import sqlite3
import aiosqlite
from typing import List, Optional
from datetime import datetime
from shared.models import UserProfile, ApplicationState

class DatabaseManager:
    """
    Manages the local SQLite database for user profiles and job application tracking.
    Uses async operations via aiosqlite.
    """
    def __init__(self, db_path: str = "job_hunter.db"):
        self.db_path = db_path

    async def initialize_db(self) -> None:
        """
        Initializes the SQLite database schema if it doesn't already exist.
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Create user_profile table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_profile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT,
                    education TEXT,  -- JSON string
                    experience TEXT, -- JSON string
                    skills TEXT,     -- JSON string
                    base_cv_text TEXT NOT NULL,
                    preferences TEXT, -- JSON string
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Create applications table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    application_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    job_title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timeline TEXT,   -- JSON string
                    notes TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()

    async def save_user_profile(self, profile: UserProfile) -> None:
        """
        Saves or updates the single candidate profile.
        """
        async with aiosqlite.connect(self.db_path) as db:
            # First, check if a profile already exists
            async with db.execute("SELECT id FROM user_profile LIMIT 1") as cursor:
                row = await cursor.fetchone()
            
            education_json = json.dumps(profile.education)
            experience_json = json.dumps(profile.experience)
            skills_json = json.dumps(profile.skills)
            preferences_json = json.dumps(profile.preferences)

            if row:
                # Update existing profile
                await db.execute("""
                    UPDATE user_profile 
                    SET full_name = ?, email = ?, phone = ?, education = ?, 
                        experience = ?, skills = ?, base_cv_text = ?, 
                        preferences = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (profile.full_name, profile.email, profile.phone, education_json,
                      experience_json, skills_json, profile.base_cv_text, preferences_json, row[0]))
            else:
                # Insert new profile
                await db.execute("""
                    INSERT INTO user_profile (full_name, email, phone, education, experience, skills, base_cv_text, preferences)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (profile.full_name, profile.email, profile.phone, education_json,
                      experience_json, skills_json, profile.base_cv_text, preferences_json))
            await db.commit()

    async def get_user_profile(self) -> Optional[UserProfile]:
        """
        Retrieves the candidate's profile. Returns None if no profile has been saved yet.
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT full_name, email, phone, education, experience, skills, base_cv_text, preferences 
                FROM user_profile LIMIT 1
            """) as cursor:
                row = await cursor.fetchone()
                
            if not row:
                return None
                
            return UserProfile(
                full_name=row[0],
                email=row[1],
                phone=row[2],
                education=json.loads(row[3]),
                experience=json.loads(row[4]),
                skills=json.loads(row[5]),
                base_cv_text=row[6],
                preferences=json.loads(row[7])
            )

    async def save_application(self, app: ApplicationState) -> None:
        """
        Saves a new job application or updates an existing one.
        """
        # Generate application_id if not present
        app_id = app.application_id or f"app_{app.job_id}_{int(datetime.utcnow().timestamp())}"
        timeline_json = json.dumps(app.timeline)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO applications (application_id, job_id, job_title, company, status, timeline, notes, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(application_id) DO UPDATE SET
                    status = excluded.status,
                    timeline = excluded.timeline,
                    notes = excluded.notes,
                    last_updated = excluded.last_updated
            """, (app_id, app.job_id, app.job_title, app.company, app.status, 
                  timeline_json, app.notes, app.last_updated.isoformat()))
            await db.commit()

    async def list_applications(self) -> List[ApplicationState]:
        """
        Retrieves all job applications tracked in the database.
        """
        apps = []
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT application_id, job_id, job_title, company, status, timeline, notes, last_updated 
                FROM applications
            """) as cursor:
                async for row in cursor:
                    # Parse timestamp
                    try:
                        last_updated = datetime.fromisoformat(row[7])
                    except (ValueError, TypeError):
                        last_updated = datetime.utcnow()

                    apps.append(ApplicationState(
                        application_id=row[0],
                        job_id=row[1],
                        job_title=row[2],
                        company=row[3],
                        status=row[4],
                        timeline=json.loads(row[5]) if row[5] else [],
                        notes=row[6],
                        last_updated=last_updated
                    ))
        return apps

    async def get_application(self, application_id: str) -> Optional[ApplicationState]:
        """
        Retrieves a specific application by its ID.
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT application_id, job_id, job_title, company, status, timeline, notes, last_updated 
                FROM applications WHERE application_id = ?
            """, (application_id,)) as cursor:
                row = await cursor.fetchone()
                
            if not row:
                return None
                
            try:
                last_updated = datetime.fromisoformat(row[7])
            except (ValueError, TypeError):
                last_updated = datetime.utcnow()

            return ApplicationState(
                application_id=row[0],
                job_id=row[1],
                job_title=row[2],
                company=row[3],
                status=row[4],
                timeline=json.loads(row[5]) if row[5] else [],
                notes=row[6],
                last_updated=last_updated
            )
