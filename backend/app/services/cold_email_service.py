# backend/app/services/cold_email_service.py

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid
import logging
from app.models.database import (
    ColdEmailCampaign, ColdEmailRecipient, User,
    EmailCampaignStatus, EmailStatus
)
from app.services.email_generator import email_generator
from app.services.gmail_service import gmail_service

logger = logging.getLogger(__name__)

class ColdEmailService:
    
    def create_campaign(
        self,
        user_id: str,
        name: str,
        target_role: str,
        target_companies: List[str],
        db: Session
    ) -> ColdEmailCampaign:
        """Create a new cold email campaign"""
        campaign_id = str(uuid.uuid4())
        
        campaign = ColdEmailCampaign(
            id=campaign_id,
            user_id=user_id,
            name=name,
            target_role=target_role,
            target_companies=target_companies,
            status=EmailCampaignStatus.DRAFT,
            send_interval_days=3,
            require_approval=True
        )
        
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        
        logger.info(f"✅ Created campaign {campaign_id} for user {user_id}")
        return campaign
    
    def add_recipients(
        self,
        campaign_id: str,
        recipients: List[Dict],
        db: Session
    ) -> List[ColdEmailRecipient]:
        """
        Add recipients to campaign
        
        recipients format:
        [
            {
                "name": "John Doe",
                "email": "john@company.com",
                "title": "Engineering Manager",
                "company": "TechCorp",
                "linkedin_url": "...",
                "company_info": {"tech_stack": "...", "recent_news": "..."}
            }
        ]
        """
        campaign = db.query(ColdEmailCampaign).filter(
            ColdEmailCampaign.id == campaign_id
        ).first()
        
        if not campaign:
            raise ValueError("Campaign not found")
        
        created_recipients = []
        
        for recipient_data in recipients:
            recipient_id = str(uuid.uuid4())
            
            recipient = ColdEmailRecipient(
                id=recipient_id,
                campaign_id=campaign_id,
                user_id=campaign.user_id,
                name=recipient_data["name"],
                email=recipient_data["email"],
                title=recipient_data.get("title"),
                company=recipient_data["company"],
                linkedin_url=recipient_data.get("linkedin_url"),
                company_info=recipient_data.get("company_info", {}),
                status=EmailStatus.DRAFT
            )
            
            db.add(recipient)
            created_recipients.append(recipient)
        
        campaign.total_recipients = len(created_recipients)
        db.commit()
        
        logger.info(f"✅ Added {len(created_recipients)} recipients to campaign {campaign_id}")
        return created_recipients
    
    def generate_emails_for_campaign(
        self,
        campaign_id: str,
        db: Session
    ) -> int:
        """Generate AI emails for all draft recipients"""
        recipients = db.query(ColdEmailRecipient).filter(
            ColdEmailRecipient.campaign_id == campaign_id,
            ColdEmailRecipient.status == EmailStatus.DRAFT
        ).all()
        
        generated_count = 0
        
        for recipient in recipients:
            try:
                email_content = email_generator.generate_cold_email(
                    user_id=recipient.user_id,
                    recipient_name=recipient.name,
                    recipient_title=recipient.title or "Hiring Manager",
                    company_name=recipient.company,
                    company_info=recipient.company_info or {},
                    db=db
                )
                
                recipient.subject = email_content["subject"]
                recipient.body = email_content["body"]
                recipient.generated_at = datetime.utcnow()
                recipient.status = EmailStatus.PENDING
                
                generated_count += 1
                
            except Exception as e:
                logger.error(f"Failed to generate email for {recipient.email}: {e}")
        
        db.commit()
        
        logger.info(f"✅ Generated {generated_count} emails for campaign {campaign_id}")
        return generated_count
    
    def request_approval(
        self,
        campaign_id: str,
        db: Session
    ) -> bool:
        """Send approval notification to user"""
        campaign = db.query(ColdEmailCampaign).filter(
            ColdEmailCampaign.id == campaign_id
        ).first()
        
        if not campaign:
            return False
        
        pending_count = db.query(ColdEmailRecipient).filter(
            ColdEmailRecipient.campaign_id == campaign_id,
            ColdEmailRecipient.status == EmailStatus.PENDING
        ).count()
        
        user = db.query(User).filter(User.id == campaign.user_id).first()
        
        approval_link = f"http://localhost:3000/dashboard/cold-email/{campaign_id}/approve"
        
        success = gmail_service.send_approval_notification(
            user_id=user.id,
            user_email=user.email,
            campaign_name=campaign.name,
            pending_count=pending_count,
            approval_link=approval_link,
            db=db
        )
        
        if success:
            campaign.status = EmailCampaignStatus.PENDING_APPROVAL
            db.commit()
        
        return success
    
    def approve_recipient(
        self,
        recipient_id: str,
        db: Session
    ) -> bool:
        """Approve a single recipient email"""
        recipient = db.query(ColdEmailRecipient).filter(
            ColdEmailRecipient.id == recipient_id
        ).first()
        
        if recipient:
            recipient.approved = True
            recipient.approved_at = datetime.utcnow()
            recipient.status = EmailStatus.APPROVED
            db.commit()
            return True
        
        return False
    
    def send_approved_emails(
        self,
        campaign_id: str,
        db: Session
    ) -> int:
        """Send all approved emails in a campaign"""
        approved_recipients = db.query(ColdEmailRecipient).filter(
            ColdEmailRecipient.campaign_id == campaign_id,
            ColdEmailRecipient.status == EmailStatus.APPROVED
        ).all()
        
        sent_count = 0
        
        for recipient in approved_recipients:
            try:
                result = gmail_service.send_email(
                    user_id=recipient.user_id,
                    to_email=recipient.email,
                    subject=recipient.subject,
                    body_html=recipient.body,
                    db=db
                )
                
                if result:
                    recipient.status = EmailStatus.SENT
                    recipient.sent_at = datetime.utcnow()
                    recipient.gmail_message_id = result.get("message_id")
                    recipient.gmail_thread_id = result.get("thread_id")
                    sent_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to send to {recipient.email}: {e}")
                recipient.status = EmailStatus.BOUNCED
        
        # Update campaign
        campaign = db.query(ColdEmailCampaign).filter(
            ColdEmailCampaign.id == campaign_id
        ).first()
        
        if campaign:
            campaign.emails_sent += sent_count
            campaign.last_sent_at = datetime.utcnow()
            campaign.next_send_at = datetime.utcnow() + timedelta(days=campaign.send_interval_days)
            campaign.status = EmailCampaignStatus.ACTIVE
        
        db.commit()
        
        logger.info(f"✅ Sent {sent_count} emails for campaign {campaign_id}")
        return sent_count

cold_email_service = ColdEmailService()
