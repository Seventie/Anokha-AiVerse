# backend/app/services/google_oauth.py

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
import json
import logging
from datetime import datetime
from app.config.settings import settings
from app.models.database import User

logger = logging.getLogger(__name__)

class GoogleOAuthService:
    def __init__(self):
        self.scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/gmail.send'
        ]
        
        # Validate credentials on init
        if not settings.GOOGLE_CLIENT_ID or settings.GOOGLE_CLIENT_ID == "your-client-id":
            logger.error("❌ GOOGLE_CLIENT_ID not configured in .env")
            raise ValueError("Google OAuth not configured. Please set GOOGLE_CLIENT_ID in .env")
        
        if not settings.GOOGLE_CLIENT_SECRET or settings.GOOGLE_CLIENT_SECRET == "your-client-secret":
            logger.error("❌ GOOGLE_CLIENT_SECRET not configured in .env")
            raise ValueError("Google OAuth not configured. Please set GOOGLE_CLIENT_SECRET in .env")
        
        self.client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
        
        logger.info("✅ Google OAuth Service initialized")
        logger.info(f"📍 Redirect URI: {settings.GOOGLE_REDIRECT_URI}")
    
    def get_authorization_url(self, user_id: str) -> str:
        """Generate Google OAuth URL for user to approve"""
        try:
            logger.info(f"🔗 Creating OAuth flow for user {user_id}")
            
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes,
                redirect_uri=settings.GOOGLE_REDIRECT_URI
            )
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=user_id,
                prompt='consent'
            )
            
            logger.info(f"✅ Generated OAuth URL for user {user_id}")
            logger.info(f"🔗 URL: {authorization_url[:100]}...")
            
            return authorization_url
            
        except Exception as e:
            logger.error(f"❌ Failed to generate OAuth URL: {e}", exc_info=True)
            raise
    
    def exchange_code_for_token(self, code: str, user_id: str, db: Session) -> dict:
        """Exchange authorization code for access token"""
        try:
            logger.info(f"🔄 Exchanging code for token (user: {user_id})")
            
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes,
                redirect_uri=settings.GOOGLE_REDIRECT_URI
            )
            
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Save to database
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.google_access_token = credentials.token
                user.google_refresh_token = credentials.refresh_token
                user.google_token_expiry = credentials.expiry
                db.commit()
                
                logger.info(f"✅ Saved Google tokens for user {user_id}")
            else:
                logger.error(f"❌ User {user_id} not found")
                raise ValueError("User not found")
            
            return {
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "expiry": credentials.expiry.isoformat() if credentials.expiry else None
            }
            
        except Exception as e:
            logger.error(f"❌ Token exchange failed: {e}", exc_info=True)
            raise
    
    def get_credentials(self, user_id: str, db: Session) -> Credentials:
        """Get stored credentials for user"""
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.google_access_token:
            raise ValueError("No Google credentials found. Please connect Google account.")
        
        credentials = Credentials(
            token=user.google_access_token,
            refresh_token=user.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=self.scopes
        )
        
        # Check if expired and refresh
        if credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
                
                # Update database
                user.google_access_token = credentials.token
                user.google_token_expiry = credentials.expiry
                db.commit()
                
                logger.info(f"🔄 Refreshed token for user {user_id}")
            except Exception as e:
                logger.error(f"❌ Token refresh failed: {e}")
                raise ValueError("Token expired. Please reconnect Google account.")
        
        return credentials
    
    def get_calendar_service(self, user_id: str, db: Session):
        """Get Google Calendar service"""
        credentials = self.get_credentials(user_id, db)
        return build('calendar', 'v3', credentials=credentials)
    
    def get_gmail_service(self, user_id: str, db: Session):
        """Get Gmail service"""
        credentials = self.get_credentials(user_id, db)
        return build('gmail', 'v1', credentials=credentials)

# Singleton - with error handling
try:
    google_oauth = GoogleOAuthService()
    logger.info("✅ Google OAuth service ready")
except Exception as e:
    logger.error(f"❌ Failed to initialize Google OAuth: {e}")
    google_oauth = None
