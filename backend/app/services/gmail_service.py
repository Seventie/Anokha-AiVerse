# backend/app/services/gmail_service.py

from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
import logging
from typing import Optional, Dict
from sqlalchemy.orm import Session
from app.services.google_oauth import google_oauth

logger = logging.getLogger(__name__)

class GmailService:
    """Send emails via Gmail API"""
    
    def send_email(
        self,
        user_id: str,
        to_email: str,
        subject: str,
        body_html: str,
        db: Session
    ) -> Optional[Dict]:
        """
        Send an email via Gmail API
        
        Returns: {"message_id": "...", "thread_id": "..."}
        """
        try:
            service = google_oauth.get_gmail_service(user_id, db)
            
            # Create message
            message = MIMEMultipart('alternative')
            message['To'] = to_email
            message['Subject'] = subject
            
            # HTML body
            html_part = MIMEText(body_html, 'html')
            message.attach(html_part)
            
            # Encode
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send
            result = service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            logger.info(f"✅ Email sent to {to_email}: {result.get('id')}")
            
            return {
                "message_id": result.get('id'),
                "thread_id": result.get('threadId')
            }
            
        except HttpError as e:
            logger.error(f"❌ Gmail API error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}", exc_info=True)
            return None
    
    def send_approval_notification(
        self,
        user_id: str,
        user_email: str,
        campaign_name: str,
        pending_count: int,
        approval_link: str,
        db: Session
    ) -> bool:
        """Send notification to user asking for approval"""
        try:
            subject = f"🎯 {pending_count} Cold Emails Ready for Review - {campaign_name}"
            
            body_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #4F46E5;">📧 Cold Email Campaign Ready</h2>
                
                <p>Hi there! 👋</p>
                
                <p>Your AI-generated cold emails are ready for review:</p>
                
                <div style="background: #F3F4F6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Campaign: {campaign_name}</h3>
                    <p><strong>{pending_count} emails</strong> waiting for your approval</p>
                </div>
                
                <p>Each email has been personalized based on:</p>
                <ul>
                    <li>✅ Your skills and experience</li>
                    <li>✅ Target company information</li>
                    <li>✅ Recipient's role and background</li>
                </ul>
                
                <div style="margin: 30px 0;">
                    <a href="{approval_link}" 
                       style="background: #4F46E5; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 6px; display: inline-block;">
                        Review & Approve Emails →
                    </a>
                </div>
                
                <p style="color: #6B7280; font-size: 14px;">
                    💡 <strong>Tip:</strong> Review each email carefully before sending. 
                    You can edit, approve, or reject individual emails.
                </p>
                
                <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 30px 0;">
                
                <p style="color: #9CA3AF; font-size: 12px;">
                    This is an automated notification from your Career AI Assistant.<br>
                    <a href="http://localhost:3000/dashboard/cold-email" 
                       style="color: #4F46E5;">Manage your campaigns</a>
                </p>
            </body>
            </html>
            """
            
            result = self.send_email(user_id, user_email, subject, body_html, db)
            return result is not None
            
        except Exception as e:
            logger.error(f"Failed to send approval notification: {e}")
            return False

gmail_service = GmailService()
