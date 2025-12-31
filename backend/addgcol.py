# backend/add_google_columns.py

from sqlalchemy import create_engine, text
from app.config.settings import settings

engine = create_engine(settings.DATABASE_URL)

sql = """
-- Add Google OAuth columns
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS google_access_token VARCHAR,
ADD COLUMN IF NOT EXISTS google_refresh_token VARCHAR,
ADD COLUMN IF NOT EXISTS google_token_expiry TIMESTAMP;

-- Add calendar sync columns
ALTER TABLE roadmap_tasks
ADD COLUMN IF NOT EXISTS google_calendar_event_id VARCHAR,
ADD COLUMN IF NOT EXISTS calendar_synced BOOLEAN DEFAULT FALSE;
"""

with engine.connect() as conn:
    conn.execute(text(sql))
    conn.commit()

print("✅ Google OAuth columns added successfully!")
