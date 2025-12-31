"""
Run this script to add cold email tables to your database WITHOUT dropping anything!
Usage: python add_cold_email_tables.py
"""

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/careerai_db")

def create_cold_email_tables():
    """Create cold email tables if they don't exist"""
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            print("🚀 Creating cold email tables...")
            
            # 1. Create enum types (if not exist)
            print("  ✅ Creating enum types...")
            conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE emailcampaignstatus AS ENUM (
                        'draft', 'pending_approval', 'approved', 'active', 'paused', 'completed'
                    );
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE emailstatus AS ENUM (
                        'draft', 'pending', 'approved', 'sent', 'delivered', 
                        'opened', 'replied', 'bounced', 'rejected'
                    );
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            # 2. Create cold_email_campaigns table
            print("  ✅ Creating cold_email_campaigns table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS cold_email_campaigns (
                    id VARCHAR PRIMARY KEY,
                    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR NOT NULL,
                    target_role VARCHAR NOT NULL,
                    target_companies JSON DEFAULT '[]',
                    status emailcampaignstatus DEFAULT 'draft',
                    send_interval_days INTEGER DEFAULT 3,
                    last_sent_at TIMESTAMP,
                    next_send_at TIMESTAMP,
                    total_recipients INTEGER DEFAULT 0,
                    emails_sent INTEGER DEFAULT 0,
                    emails_opened INTEGER DEFAULT 0,
                    emails_replied INTEGER DEFAULT 0,
                    require_approval BOOLEAN DEFAULT TRUE,
                    auto_send BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """))
            
            # 3. Create cold_email_recipients table
            print("  ✅ Creating cold_email_recipients table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS cold_email_recipients (
                    id VARCHAR PRIMARY KEY,
                    campaign_id VARCHAR NOT NULL REFERENCES cold_email_campaigns(id) ON DELETE CASCADE,
                    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR NOT NULL,
                    email VARCHAR NOT NULL,
                    title VARCHAR,
                    company VARCHAR NOT NULL,
                    linkedin_url VARCHAR,
                    company_info JSON DEFAULT '{}',
                    subject VARCHAR,
                    body TEXT,
                    generated_at TIMESTAMP,
                    status emailstatus DEFAULT 'draft',
                    sent_at TIMESTAMP,
                    opened_at TIMESTAMP,
                    replied_at TIMESTAMP,
                    approved BOOLEAN DEFAULT FALSE,
                    approved_at TIMESTAMP,
                    rejection_reason VARCHAR,
                    gmail_message_id VARCHAR,
                    gmail_thread_id VARCHAR,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """))
            
            # 4. Create indexes for performance
            print("  ✅ Creating indexes...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_cold_email_campaigns_user_id 
                ON cold_email_campaigns(user_id);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_cold_email_recipients_campaign_id 
                ON cold_email_recipients(campaign_id);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_cold_email_recipients_user_id 
                ON cold_email_recipients(user_id);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_cold_email_recipients_status 
                ON cold_email_recipients(status);
            """))
            
            # Commit transaction
            trans.commit()
            
            print("\n✅ SUCCESS! Cold email tables created!")
            print("\n📊 Verifying tables...")
            
            # Verify tables exist
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name IN ('cold_email_campaigns', 'cold_email_recipients')
                ORDER BY table_name;
            """))
            
            tables = result.fetchall()
            for table in tables:
                print(f"  ✅ {table[0]}")
            
            print("\n🎉 All done! You can now start your server.")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ ERROR: {e}")
            print("\n💡 This might mean:")
            print("  1. Tables already exist (that's OK!)")
            print("  2. Database connection issue")
            print("  3. Check your .env file has correct DATABASE_URL")
            raise

if __name__ == "__main__":
    create_cold_email_tables()
