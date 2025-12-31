# backend/app/routes/cold_email.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from app.config.database import get_db
from app.utils.auth import get_current_user_dict
from app.services.cold_email_service import cold_email_service
from app.models.database import ColdEmailCampaign, ColdEmailRecipient
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cold-email", tags=["Cold Email"])

# Schemas
class CreateCampaignRequest(BaseModel):
    name: str
    target_role: str
    target_companies: List[str]

class AddRecipientsRequest(BaseModel):
    recipients: List[Dict]

@router.get("/campaigns")
async def get_campaigns(
    current_user: dict = Depends(get_current_user_dict),
    db: Session = Depends(get_db)
):
    """Get all campaigns for user"""
    user_id = current_user["user_id"]
    
    campaigns = db.query(ColdEmailCampaign).filter(
        ColdEmailCampaign.user_id == user_id
    ).order_by(ColdEmailCampaign.created_at.desc()).all()
    
    return {"campaigns": campaigns}

@router.post("/campaigns")
async def create_campaign(
    request: CreateCampaignRequest,
    current_user: dict = Depends(get_current_user_dict),
    db: Session = Depends(get_db)
):
    """Create new campaign"""
    user_id = current_user["user_id"]
    
    campaign = cold_email_service.create_campaign(
        user_id=user_id,
        name=request.name,
        target_role=request.target_role,
        target_companies=request.target_companies,
        db=db
    )
    
    return {"campaign": campaign}

@router.post("/campaigns/{campaign_id}/recipients")
async def add_recipients(
    campaign_id: str,
    request: AddRecipientsRequest,
    current_user: dict = Depends(get_current_user_dict),
    db: Session = Depends(get_db)
):
    """Add recipients to campaign"""
    recipients = cold_email_service.add_recipients(
        campaign_id=campaign_id,
        recipients=request.recipients,
        db=db
    )
    
    return {"recipients": recipients, "count": len(recipients)}

@router.get("/campaigns/{campaign_id}/recipients")
async def get_recipients(
    campaign_id: str,
    current_user: dict = Depends(get_current_user_dict),
    db: Session = Depends(get_db)
):
    """Get all recipients for campaign"""
    recipients = db.query(ColdEmailRecipient).filter(
        ColdEmailRecipient.campaign_id == campaign_id
    ).all()
    
    return {"recipients": recipients}

@router.post("/campaigns/{campaign_id}/generate")
async def generate_emails(
    campaign_id: str,
    current_user: dict = Depends(get_current_user_dict),
    db: Session = Depends(get_db)
):
    """Generate AI emails for all recipients"""
    count = cold_email_service.generate_emails_for_campaign(campaign_id, db)
    return {"generated_count": count}

@router.post("/campaigns/{campaign_id}/request-approval")
async def request_approval(
    campaign_id: str,
    current_user: dict = Depends(get_current_user_dict),
    db: Session = Depends(get_db)
):
    """Send approval notification to user"""
    success = cold_email_service.request_approval(campaign_id, db)
    
    if success:
        return {"message": "Approval notification sent to your Gmail"}
    else:
        raise HTTPException(500, "Failed to send notification")

@router.post("/recipients/{recipient_id}/approve")
async def approve_recipient(
    recipient_id: str,
    current_user: dict = Depends(get_current_user_dict),
    db: Session = Depends(get_db)
):
    """Approve a single email"""
    success = cold_email_service.approve_recipient(recipient_id, db)
    
    if success:
        return {"message": "Email approved"}
    else:
        raise HTTPException(404, "Recipient not found")

@router.post("/campaigns/{campaign_id}/send")
async def send_approved_emails(
    campaign_id: str,
    current_user: dict = Depends(get_current_user_dict),
    db: Session = Depends(get_db)
):
    """Send all approved emails"""
    sent_count = cold_email_service.send_approved_emails(campaign_id, db)
    return {"sent_count": sent_count}
