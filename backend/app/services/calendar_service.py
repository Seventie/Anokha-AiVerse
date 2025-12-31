# backend/app/services/calendar_service.py

from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import logging
from app.services.google_oauth import google_oauth

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    
    async def create_events_for_user(
        self,
        user_id: str,
        schedule: List[Dict[str, Any]],
        db: Session
    ) -> List[str]:
        """Create calendar events using stored OAuth credentials"""
        try:
            # Get service
            service = google_oauth.get_calendar_service(user_id, db)
            
            event_ids = []
            
            for day_schedule in schedule:
                if not day_schedule.get('primary_task'):
                    continue
                
                # Parse date
                date_str = day_schedule.get('date')
                date = datetime.strptime(date_str, '%Y-%m-%d')
                
                # Set time to 9 AM - 11 AM IST
                start_time = date.replace(hour=9, minute=0, second=0)
                end_time = date.replace(hour=11, minute=0, second=0)
                
                event = {
                    'summary': f"🎯 Learn {day_schedule.get('skill_name', 'Unknown')}",
                    'description': f"""
📚 Learning Session

🎯 Goal: {day_schedule.get('primary_task', 'Study session')}
⏱️ Duration: 2 hours
📖 Focus: {day_schedule.get('skill_name', 'Skill development')}

🔗 Resources:
{chr(10).join(day_schedule.get('resources', [])[:3])}

💡 Tip: Use Pomodoro technique (25 min work, 5 min break)
                    """,
                    'start': {
                        'dateTime': start_time.isoformat(),
                        'timeZone': 'Asia/Kolkata',
                    },
                    'end': {
                        'dateTime': end_time.isoformat(),
                        'timeZone': 'Asia/Kolkata',
                    },
                    'colorId': '9',  # Blue
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'popup', 'minutes': 30},
                            {'method': 'email', 'minutes': 60},
                        ],
                    },
                    'extendedProperties': {
                        'private': {
                            'task_id': day_schedule.get('task_id', ''),
                            'app': 'career_assistant'
                        }
                    }
                }
                
                result = service.events().insert(
                    calendarId='primary',
                    body=event
                ).execute()
                
                event_id = result.get('id')
                event_ids.append(event_id)
                logger.info(f"✅ Created event: {event_id} for {date_str}")
            
            logger.info(f"🎉 Created {len(event_ids)} calendar events for user {user_id}")
            return event_ids
            
        except ValueError as e:
            logger.error(f"❌ Credentials error: {e}")
            raise
        except HttpError as e:
            logger.error(f"❌ Calendar API error: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}", exc_info=True)
            return []
    
    async def delete_all_roadmap_events(self, user_id: str, db: Session) -> bool:
        """Delete all roadmap events for user"""
        try:
            service = google_oauth.get_calendar_service(user_id, db)
            
            # Get events
            now = datetime.utcnow().isoformat() + 'Z'
            future = (datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                timeMax=future,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            deleted_count = 0
            
            for event in events:
                props = event.get('extendedProperties', {}).get('private', {})
                if props.get('app') == 'career_assistant':
                    service.events().delete(
                        calendarId='primary',
                        eventId=event['id']
                    ).execute()
                    deleted_count += 1
            
            logger.info(f"🗑️ Deleted {deleted_count} events")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete events: {e}")
            return False

calendar_service = GoogleCalendarService()
