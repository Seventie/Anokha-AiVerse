# test_columns.py
from app.config.database import SessionLocal
from app.models.database import User, RoadmapTask

db = SessionLocal()

# Check User
user = db.query(User).first()
print(f"✅ User has google_access_token: {hasattr(user, 'google_access_token')}")

# Check RoadmapTask
task = db.query(RoadmapTask).first()
if task:
    print(f"✅ Task has google_calendar_event_id: {hasattr(task, 'google_calendar_event_id')}")

db.close()
