# 🚀 CareerAI - AI-Powered Career Development Companion

<div align="center">

![CareerAI Banner](Images/Whisk_8c48828dea189739602491e7850d8817dr.jpeg)

# CareerAI – Automate, Learn, and Grow 🚀

![Python](https://img.shields.io/badge/python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![Architecture](https://img.shields.io/badge/architecture-agentic_AI-purple)


---

[🚀 Quick Start](#-quick-start) •
[🤖 AI Agents](#-ai-agents) •
[🖼 Demo](#-screenshots)

</div>

***

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Workflow](#-complete-workflow)
- [AI Agent System](#-ai-agents)
- [Database Design](#-database-architecture)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Automation](#-automation--scheduling)
- [Screenshots](#-screenshots)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)

***

## 🌟 Overview

**CareerAI** is an intelligent, fully-automated career development platform that acts as your **long-term AI companion**. Built with a sophisticated multi-agent orchestration system, it automates every aspect of your career journey - from personalized learning roadmaps to AI-powered interviews, job matching, cold email outreach, and continuous learning through daily reflections.

### **What Makes CareerAI Different?**

🤖 **Fully Autonomous** - 8 specialized AI agents working 24/7 for you  
🧠 **Long-term Memory** - Learns from every interaction via vector embeddings  
⏰ **Smart Automation** - Auto-schedules tasks, sends emails, finds jobs  
🎯 **Integrated Ecosystem** - Syncs with Gmail, Google Calendar  
🎤 **Voice-First Interviews** - Natural conversation with AI interviewer  
📊 **Data-Driven Insights** - Multi-database architecture for deep analytics  

![Platform Overview](./docs/images/platform- ✨ Key Features

### 🎓 **Smart Resume Onboarding**

![Resume Upload](./docs/images/resume-dious form-filling, just upload your resume:

- **Automatic Parsing** - Extract education, experience, skills, projects
- **AI Verification** - Review and confirm extracted data
- **Multi-database Sync** - Saves to PostgreSQL, Neo4j, ChromaDB simultaneously
- **Instant Profile Creation** - Complete registration in 2 minutes

**Flow:** Upload PDF/DOCX → AI parses → Pre-filled form → User verifies → Profile ready

***

### 🤖 **Orchestrated AI Agent System**

![Agent System](./docs/images/agent- specialized agents** coordinated by an Orchestrator using **LangGraph + LangChain**:

| Agent | Runs | Purpose |
|-------|------|---------|
| **Orchestrator** | Every 12 hours | Coordinates all agents, triggers automation |
| **Profile Agent** | On-demand | Syncs user data across 3 databases |
| **Resume Agent** | On-demand | Parses resumes, analyzes ATS score, compares versions |
| **Roadmap Agent** | Auto + On-demand | Creates learning schedules, syncs Google Calendar |
| **Interview Agent** | On-demand | Conducts voice interviews with Whisper + Piper TTS |
| **Opportunities Agent** | Every 12 hours | Scrapes jobs, matches with user skills |
| **Cold Email Agent** | Every 3 days | Sends personalized outreach via Gmail API |
| **Journal Agent** | Daily | Analyzes reflections, builds long-term memory |
| **Summary Agent** | Real-time | Aggregates dashboard data, scrapes quotes/news |

***

### 📚 **Automated Learning Roadmap**

![Roadmap Calendar](./docs/images/roadmap-generated learning path that **manages itself**:

**How it Works:**
1. Analyzes skill gaps using Neo4j knowledge graph
2. Generates 7-day learning schedule
3. **Automatically creates Google Calendar events**
4. User marks tasks complete (syncs to dashboard)
5. If delayed 10+ days → **Auto-reschedules** tasks
6. Sends Gmail reminders for upcoming milestones

**Manual Override:** User can request custom rescheduling anytime

**Integration:** 
- ✅ Google Calendar (2-way sync)
- ✅ Gmail notifications
- ✅ Dashboard progress tracking

***

### 🎤 **AI Voice Interview Simulator**

![Interview Room](./docs/images/interview-room.pngd interviews with **real-time AI evaluation**:

**Interview Flow:**

```
User Schedules Interview
         ↓
Interview Agent Retrieves Pre-stored Questions (PostgreSQL)
         ↓
Plays Question Audio (Piper TTS)
         ↓
User Answers (Voice/Text)
         ↓
Transcription (Whisper STT)
         ↓
LLM Analyzes Answer (Groq API)
         ↓
Follow-up Question (Context-aware)
         ↓
Repeat → Final Scoring → Detailed Feedback
```

**Features:**
- **Pre-stored Question Bank** - 100+ role-specific questions
- **Dynamic Follow-ups** - LLM generates contextual questions
- **Conversation Memory** - Temporary field stores interview context
- **Multi-modal Input** - Voice OR text answers
- **Instant Feedback** - STAR method analysis, improvement tips
- **Historical Analytics** - Track improvement over time

**Tech Stack:** Whisper (STT) + Piper TTS + Groq LLM + PostgreSQL

***

### 💼 **Automated Job Matching (Every 12 Hours)**

![Job Dashboard](./docs/images/job- opportunity** - AI finds and ranks jobs while you sleep:

**Automation Workflow:**

```
[Every 12 Hours]
Orchestrator Triggers Opportunities Agent
         ↓
Scrapes Job Boards (LinkedIn, Indeed, Glassdoor)
         ↓
Saves Jobs to PostgreSQL
         ↓
Generates Embeddings in ChromaDB
         ↓
Vector Similarity Search with User Profile
         ↓
Filters by Neo4j Skill Requirements
         ↓
Ranks by Compatibility Score
         ↓
Updates Dashboard Home Page
```

**Matching Algorithm:**
```
Score = Skills Match (40%) + Experience (30%) + 
        Location (15%) + Salary (10%) + Culture (5%)
```

**Dashboard View:** Top 20 matches with match score, reasons, one-click apply tracking

***

### 📧 **Automated Cold Email Outreach**

![Cold Email]( sends personalized cold emails every 3 days** (with your permission):

**How It Works:**
1. User provides target list (companies/people)
2. User opts-in to automation
3. Every 3 days:
   - Cold Email Agent activates
   - Queries target list from PostgreSQL
   - LLM generates personalized emails based on user skills
   - Sends via **Gmail API**
   - Tracks responses in database
4. User reviews sent emails and responses in dashboard

**Customization:**
- Email templates can be reviewed before automation
- Pause/resume anytime
- Track open rates and replies

***

### 📝 **AI Learning Journal - Your Long-term Companion**

![Journal](./docs/images/journal.png build a **persistent memory** of your journey:

**Journal Agent Features:**
- **Sentiment Analysis** - Tracks mood and motivation trends
- **LLM Insights** - Extracts key learnings and patterns
- **Vector Embeddings** - Stores entries in ChromaDB for memory retrieval
- **Long-term Learning** - AI remembers past reflections to personalize guidance
- **Pattern Recognition** - Identifies what strategies work best for you

**Example Insights:**
- "You learn best on Tuesday mornings"
- "React projects boost your confidence more than Python"
- "You've been feeling overwhelmed - let's adjust your roadmap pace"

**Flow:** Write entry → LLM analyzes → Sentiment score → Embeddings stored → Insights generated

***

### 📄 **Resume Analyzer & Comparator**

![Resume Analyzer](./docs/images/resume powerful resume tools:**

**1. ATS Compatibility Checker**
- Upload resume + job description
- AI calculates match score
- Highlights missing keywords
- Suggests improvements

**2. Resume Comparison**
- Compare two versions side-by-side
- See which performs better for specific roles
- A/B testing recommendations

**3. Resume Enhancement**
- AI rewrites bullet points for impact
- Quantifies achievements
- Optimizes formatting

***

### 📊 **Unified Dashboard - Everything Connected**

![Dashboard Home](./docs/images/dashboard-** aggregates data from all systems in real-time:

**Dashboard Sections:**

| Section | Data Source | Update Frequency |
|---------|-------------|------------------|
| **Daily Quote** | Web scraper | Daily |
| **Industry News** | News API (user's goal) | Real-time |
| **Roadmap Progress** | Google Calendar + PostgreSQL | Real-time |
| **Interview Stats** | PostgreSQL | Real-time |
| **Job Matches** | Opportunities Agent | Every 12 hours |
| **Cold Email Status** | Gmail API + PostgreSQL | Every 3 days |
| **Journal Insights** | Journal Agent | Daily |
| **Skill Growth** | Neo4j + ChromaDB | Real-time |

**Everything is connected** - marking roadmap complete updates calendar, interview scores influence job matching, journal sentiment adjusts roadmap pace.

***

## 🏗️ System Architecture

### **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────┐
│         FRONTEND (React 18 + TypeScript)                │
│   Landing | Login | Dashboard | Interview | Roadmap     │
│         JWT Auth | MediaRecorder API                    │
└────────────────────────┬────────────────────────────────┘
                         │ REST API
                         ▼
┌─────────────────────────────────────────────────────────┐
│           BACKEND API (FastAPI + Python 3.11)           │
│                                                          │
│  Routes: /auth /profile /interview /roadmap             │
│          /opportunities /journal /resume                │
│                                                          │
│  Middleware: JWT + CORS + Background Scheduler          │
└──┬─────────┬──────────┬──────────┬────────────┬────────┘
   │         │          │          │            │
   ▼         ▼          ▼          ▼            ▼
┌──────┐ ┌──────┐ ┌─────────┐ ┌────────┐ ┌──────────┐
│PostgreSQL Neo4j│ ChromaDB │ Whisper │ │Piper TTS │
│ (Facts)│(Graph)│ (Memory)│ │  (STT) │ │ (Voice)  │
└──────┘ └──────┘ └─────────┘ └────────┘ └──────────┘
   │         │          │          │            │
   └─────────┴──────────┴──────────┴────────────┘
                         │
                         ▼
           ┌──────────────────────────┐
           │   LangGraph Orchestrator │
           │  (Coordinates 8 Agents)  │
           └──────────────────────────┘
```

![Architecture Diagram](./docs/images/ **Multi-Agent Orchestration (LangGraph + LangChain)**

```
                  ┌─────────────────────┐
                  │  ORCHESTRATOR       │
                  │  (Supervisor Agent) │
                  │                     │
                  │  • Runs every 12hrs │
                  │  • Routes requests  │
                  │  • Manages state    │
                  └──────────┬──────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│Profile Agent │     │Resume Agent  │     │Roadmap Agent │
│              │     │              │     │              │
│• Sync 3 DBs  │     │• Parse docs  │     │• Neo4j query │
│• Update graph│     │• ATS score   │     │• Cal sync    │
└──────────────┘     └──────────────┘     └──────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│Interview     │     │Opportunities │     │Cold Email    │
│Agent         │     │Agent         │     │Agent         │
│              │     │              │     │              │
│• STT/TTS     │     │• Job scraping│     │• Gmail API   │
│• LLM eval    │     │• Vector match│     │• Every 3 days│
└──────────────┘     └──────────────┘     └──────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             ▼
                    ┌──────────────────┐
                    │  Journal Agent   │
                    │  Summary Agent   │
                    │                  │
                    │• Sentiment       │
                    │• Embeddings      │
                    │• Dashboard data  │
                    └──────────────────┘
```

***

## 🔄 Complete Workflow

### **1. User Registration Flow**

![Registration Flow](./docs/images/registration-
         ↓
Click "Get Started"
         ↓
Upload Resume (PDF/DOCX)
         ↓
Resume Agent Parses Document
         ↓
Auto-fills Registration Form
  • Email, Name, Location
  • Education (institution, degree, dates)
  • Experience (role, company, duration)
  • Skills (technical + soft)
  • Projects (title, tech stack)
         ↓
User Reviews & Verifies Data
         ↓
Submit Registration
         ↓
[Backend Processing]
  1. Save to PostgreSQL (user, education, experience, skills, projects)
  2. Generate JWT token
  3. Background Task: Profile Agent syncs to Neo4j
  4. Background Task: Create embeddings in ChromaDB
         ↓
User Redirected to Dashboard
```

**Result:** Complete profile created in < 2 minutes

***

### **2. Automated Job Matching (Every 12 Hours)**

![Job Automation](./docs/images/job-t 00:00 & 12:00 Daily]
         ↓
Orchestrator Triggers Opportunities Agent
         ↓
┌─────────────────────────────────────────┐
│ Opportunities Agent Workflow            │
├─────────────────────────────────────────┤
│ 1. Scrape Job Boards:                  │
│    • LinkedIn Jobs API                  │
│    • Indeed (BeautifulSoup)            │
│    • Glassdoor (Selenium)              │
│                                         │
│ 2. Parse & Clean Data:                │
│    • Title, Company, Location          │
│    • Salary, Requirements              │
│    • Posted Date, Source URL           │
│                                         │
│ 3. Store in PostgreSQL:                │
│    • Table: opportunities              │
│    • Deduplicate existing jobs         │
│                                         │
│ 4. Generate Embeddings:                │
│    • Job description → ChromaDB        │
│    • Store with metadata               │
│                                         │
│ 5. Match with User Profile:           │
│    • Vector search (user skills)       │
│    • Neo4j skill requirement filter    │
│    • Calculate compatibility score     │
│                                         │
│ 6. Rank Top 20 Matches                │
│                                         │
│ 7. Update Dashboard                    │
└─────────────────────────────────────────┘
         ↓
User Sees New Job Matches on Dashboard
```

**User Experience:** Log in anytime to see fresh, personalized job matches

***

### **3. Automated Learning Roadmap**

![Roadmap Automation](./docs/images/roadmap-automation.pngonths"]
         ↓
Roadmap Agent Workflow:
         ↓
1. Query Neo4j for Skill Gaps
   • User current skills: [React, Node.js]
   • Target role requires: [React, Node.js, PostgreSQL, Docker, AWS]
   • Gaps identified: [PostgreSQL, Docker, AWS]
         ↓
2. Generate Learning Path (Neo4j Graph Traversal)
   • Week 1-2: PostgreSQL fundamentals
   • Week 3-4: Docker containerization
   • Week 5-7: AWS basics (EC2, S3, RDS)
   • Week 8: Capstone project
         ↓
3. Create 7-Day Schedule
   • Break down into daily tasks
   • Allocate time based on user availability
         ↓
4. Sync to Google Calendar (via API)
   • Create events with descriptions
   • Set reminders
         ↓
5. Store in PostgreSQL
   • Table: roadmap_tasks
   • Track status: pending, in_progress, completed, delayed
         ↓
User Receives Gmail Notification: "Your roadmap is ready!"
         ↓
═══════════════════════════════════════
    ONGOING AUTOMATION
═══════════════════════════════════════
         ↓
User Marks Task Complete (Dashboard)
         ↓
Updates: PostgreSQL + Google Calendar
         ↓
[If task delayed 10+ days]
         ↓
Roadmap Agent Auto-reschedules
         ↓
Sends Gmail: "Your schedule has been adjusted"
         ↓
[User can manually request rescheduling anytime]
```

**Key Integrations:**
- Google Calendar API (OAuth 2.0)
- Gmail API (send notifications)
- PostgreSQL (task tracking)

***

### **4. AI Interview Session**

![Interview Flow](./docs/images/interview-   ↓
Interview Setup:
  • Select role (e.g., "Backend Engineer")
  • Choose difficulty (Easy/Medium/Hard)
  • Duration (15/30/45 mins)
         ↓
Interview Agent Initializes:
         ↓
1. Retrieve Pre-stored Questions (PostgreSQL)
   • Filter by role + difficulty
   • Select 10-15 questions
         ↓
2. Create Interview Session
   • Generate interview_id
   • Initialize temporary conversation context field
         ↓
═══════════════════════════════════════
    INTERVIEW LOOP (For Each Question)
═══════════════════════════════════════
         ↓
3. Play Question Audio
   • Text → Piper TTS → WAV file
   • Stream to frontend
         ↓
4. User Answers (Voice or Text)
   • If voice: MediaRecorder → WebM blob
         ↓
5. Transcribe Answer (Whisper STT)
   • WebM → WAV conversion
   • Whisper model transcribes
         ↓
6. Store in Temporary Context
   • Append to conversation history
   • Pass to LLM for context awareness
         ↓
7. LLM Evaluates Answer (Groq API)
   Prompt:
   """
   Question: {question}
   Answer: {transcribed_answer}
   Conversation history: {context}
   
   Evaluate based on:
   - Relevance (1-10)
   - STAR structure (1-10)
   - Technical accuracy (1-10)
   - Communication clarity (1-10)
   
   Generate:
   - Score
   - Feedback
   - Follow-up question (if needed)
   """
         ↓
8. Save Response to PostgreSQL
   • interview_responses table
   • Link to question_id
         ↓
9. Display Feedback to User (Real-time)
         ↓
10. Generate Follow-up Question (LLM)
    • Based on conversation context
    • Adaptive difficulty
         ↓
[Repeat Loop for Next Question]
         ↓
═══════════════════════════════════════
    INTERVIEW COMPLETION
═══════════════════════════════════════
         ↓
11. Calculate Final Score
    • Weighted average across all questions
         ↓
12. Generate Comprehensive Feedback
    • Strengths
    • Improvement areas
    • Recommended resources
         ↓
13. Save to PostgreSQL
    • interviews table (status: completed)
         ↓
14. Display Results Dashboard
    • Score breakdown
    • Question-by-question review
    • Historical comparison
```

**Tech Stack:**
- **Whisper Base** (offline, 74M parameters)
- **Piper TTS** (en_US-lessac-medium model)
- **Groq LLM** (question generation + evaluation)
- **PostgreSQL** (question bank + results)
- **Temporary Context Field** (in-memory conversation state)

***

### **5. Cold Email Automation (Every 3 Days)**

![Cold Email Flow](./docs/images/      ↓
User Navigates to "Cold Email" Section
         ↓
1. Upload Target List (CSV/Manual Entry)
   • Columns: Name, Email, Company, Role
         ↓
2. Review AI-Generated Email Template
   Sample:
   """
   Hi {name},
   
   I noticed {company} is hiring for {role}. With my experience
   in {user_skills}, I believe I could contribute to...
   
   [Personalized based on user profile]
   """
         ↓
3. Opt-in to Automation
   • User agrees to send every 3 days
   • Set max emails per batch (e.g., 10)
         ↓
4. Target List Saved to PostgreSQL
   • Table: cold_email_targets
   • Status: pending
         ↓
═══════════════════════════════════════
    AUTOMATED WORKFLOW (Every 3 Days)
═══════════════════════════════════════
         ↓
[Background Scheduler - 9:00 AM Every 3 Days]
         ↓
Orchestrator Triggers Cold Email Agent
         ↓
1. Query PostgreSQL for Pending Targets
   • Filter: status = 'pending'
   • Limit: user-defined batch size
         ↓
2. For Each Target:
   a. Retrieve User Profile from PostgreSQL
   b. LLM Generates Personalized Email
      Prompt:
      """
      User skills: {skills}
      User projects: {projects}
      Target: {name} at {company}
      Target role: {role}
      
      Generate a compelling cold email introducing
      the user and expressing interest in {role}.
      Keep it concise (150 words).
      """
   c. Store Generated Email in PostgreSQL
         ↓
3. Send via Gmail API
   • OAuth 2.0 authentication
   • Use user's Gmail account
   • Add to "Sent" folder
         ↓
4. Update Status in PostgreSQL
   • Status: sent
   • Timestamp: sent_at
         ↓
5. Track Responses
   • Gmail API watches for replies
   • Updates status: replied
         ↓
User Views Dashboard:
  • Emails sent: 30
  • Replies received: 5
  • Open rate: 40%
         ↓
[User can pause/resume automation anytime]
```

**Key Features:**
- **User Control:** Review templates before automation
- **Rate Limiting:** Max emails per batch to avoid spam
- **Response Tracking:** Gmail API monitors replies
- **Personalization:** LLM customizes each email

***

### **6. Daily Journal → Long-term Memory**

![Journal Memory](./docs/images/journal-         ↓
User Navigates to "Journal" Tab
         ↓
Writes Reflection:
"""
Today I completed the PostgreSQL module. It was challenging at
first, but the hands-on project helped me understand joins better.
I feel more confident now. Tomorrow I'll start Docker.
"""
         ↓
User Clicks "Save Entry"
         ↓
Journal Agent Workflow:
         ↓
1. Store Raw Text in PostgreSQL
   • Table: journal_entries
   • Timestamp, user_id, entry_text
         ↓
2. Sentiment Analysis (Transformers/BERT)
   • Positive/Negative/Neutral score
   • Confidence level
   • Result: Positive (0.85 confidence)
         ↓
3. LLM Extracts Insights (Groq API)
   Prompt:
   """
   Analyze this journal entry:
   {entry_text}
   
   Extract:
   - Key learnings
   - Skills practiced
   - Emotions/sentiment
   - Challenges faced
   - Next actions
   """
   
   Result:
   • Learning: PostgreSQL joins
   • Skill: Database querying
   • Emotion: Confident
   • Challenge: Initially confusing
   • Next: Docker module
         ↓
4. Generate Embeddings (Sentence Transformers)
   • Convert entry to 768-dim vector
   • Store in ChromaDB
   • Metadata: date, sentiment, skills, user_id
         ↓
5. Update PostgreSQL
   • Add sentiment_score, extracted_insights
         ↓
6. Build Long-term Memory
   • ChromaDB enables semantic search
   • "When did user learn PostgreSQL?" → Retrieves this entry
   • "What challenges did user face?" → Historical patterns
         ↓
═══════════════════════════════════════
    LONG-TERM COMPANION BEHAVIOR
═══════════════════════════════════════
         ↓
[Next Day - User Asks: "I'm struggling with Docker networking"]
         ↓
Journal Agent Queries ChromaDB:
  • Semantic search: "docker challenges"
  • Retrieves past similar struggles
         ↓
LLM Generates Personalized Response:
"""
I remember when you started PostgreSQL, you also found the
concepts challenging at first. But after the hands-on project,
you felt much more confident. 

For Docker networking, I recommend trying a similar approach:
build a small multi-container app to see how networks work
in practice. Based on your learning style, you prefer
hands-on over theory.
"""
         ↓
Result: AI remembers past patterns and adapts guidance
```

**Memory Persistence:**
- **ChromaDB** stores ALL journal entries as vectors
- **Semantic Search** enables contextual memory retrieval
- **LLM** synthesizes insights from historical data
- **Long-term Companion** learns user over weeks/months

***

## 🗄️ Database Architecture

### **Three-Tier Database Strategy**

![Database Strategy](./docs/images/database-SQL - Relational Facts**

**Purpose:** Store structured, transactional data

**Key Tables:**

```sql
-- Authentication
users (id, email, hashed_password, full_name, created_at)

-- Profile
education (user_id, institution, degree, major, start_date, end_date)
experience (user_id, role, company, duration, description)
skills (user_id, skill, category, level, verified)
projects (user_id, title, description, tech_stack, url)

-- Career Planning
career_goals (user_id, target_role, timeline, status)
roadmap_tasks (user_id, task, due_date, status, calendar_event_id)

-- Interview System
interviews (id, user_id, role, difficulty, score, status)
interview_questions (id, interview_id, question_text, audio_path)
interview_responses (id, question_id, answer_text, score, feedback)

-- Opportunities
opportunities (id, title, company, location, salary, source, scraped_at)
user_opportunity_interactions (user_id, opportunity_id, status, applied_at)

-- Cold Email
cold_email_targets (id, user_id, name, email, company, status)
cold_email_history (id, target_id, email_body, sent_at, replied_at)

-- Journal
journal_entries (id, user_id, entry_text, sentiment_score, insights, created_at)

-- Calendar Integration
calendar_events (id, user_id, event_id, title, start_time, synced_at)
```

**Why PostgreSQL?**
- ✅ ACID compliance for transactional data
- ✅ Complex queries with JOINs
- ✅ Strong consistency guarantees
- ✅ Mature ecosystem (Alembic migrations)

***

### **2. Neo4j - Knowledge Graph**

**Purpose:** Model relationships between skills, roles, resources

**Graph Schema:**

```cypher
// Node Types
(:User {id, name, target_role, timeline})
(:Skill {name, category, difficulty, demand_score})
(:Role {title, seniority, industry, avg_salary})
(:Resource {title, type, url, difficulty, duration})
(:Company {name, size, industry, location})
(:Project {title, description, skills_used})

// Relationship Types
(:User)-[:HAS_SKILL {level, verified, acquired_date}]->(:Skill)
(:User)-[:TARGETS {timeline, priority}]->(:Role)
(:User)-[:WORKED_AT {duration, role}]->(:Company)
(:User)-[:COMPLETED]->(:Project)

(:Role)-[:REQUIRES {importance: 1-10, years_exp}]->(:Skill)
(:Skill)-[:PREREQUISITE_FOR {order}]->(:Skill)
(:Resource)-[:TEACHES {effectiveness: 1-10}]->(:Skill)
(:Company)-[:OFFERS]->(:Role)
(:Project)-[:DEMONSTRATES]->(:Skill)
```

**Example Queries:**

```cypher
// Find skill gaps for user targeting "Full Stack Developer"
MATCH (u:User {id: $user_id})-[:HAS_SKILL]->(userSkills:Skill)
MATCH (target:Role {title: "Full Stack Developer"})-[:REQUIRES]->(requiredSkills:Skill)
WHERE NOT (u)-[:HAS_SKILL]->(requiredSkills)
RETURN requiredSkills.name AS skill_gap,
       requiredSkills.importance AS priority
ORDER BY priority DESC

// Find learning path from current skill to target skill
MATCH (current:Skill {name: "React"}),
      (target:Skill {name: "AWS"})
MATCH path = shortestPath((current)-[:PREREQUISITE_FOR*]->(target))
RETURN path, length(path) AS steps

// Recommend resources for skill gap
MATCH (skill:Skill {name: "Docker"})<-[:TEACHES]-(resource:Resource)
RETURN resource.title, resource.url, resource.effectiveness
ORDER BY resource.effectiveness DESC
LIMIT 5
```

**Why Neo4j?**
- ✅ Natural representation of skill relationships
- ✅ Fast graph traversal for pathfinding
- ✅ Flexible schema for evolving ontology
- ✅ Cypher query language optimized for relationships

***

### **3. ChromaDB - Vector Embeddings (Memory)**

**Purpose:** Semantic search and long-term memory retrieval

**Collections:**

```python
# Collection 1: Resume Embeddings
resume_embeddings
  • Documents: Full resume text
  • Embeddings: 1536-dim vectors (OpenAI ada-002)
  • Metadata: user_id, uploaded_at, file_name
  • Use case: Semantic job matching

# Collection 2: User Conversation History
conversation_history
  • Documents: All interview Q&A, journal entries, chat logs
  • Embeddings: 768-dim vectors (Sentence Transformers)
  • Metadata: user_id, timestamp, conversation_type, sentiment
  • Use case: Long-term companion memory

# Collection 3: Job Description Embeddings
job_embeddings
  • Documents: Job descriptions from scraping
  • Embeddings: 1536-dim vectors
  • Metadata: opportunity_id, company, role, posted_date
  • Use case: Vector similarity search for job matching

# Collection 4: Learning Resource Embeddings
resource_embeddings
  • Documents: Course descriptions, tutorial summaries
  • Embeddings: 1536-dim vectors
  • Metadata: resource_id, skill, difficulty, platform
  • Use case: Personalized resource recommendations

# Collection 5: Journal Entry Embeddings
journal_embeddings
  • Documents: Daily journal reflections
  • Embeddings: 768-dim vectors
  • Metadata: user_id, date, sentiment_score, extracted_skills
  • Use case: Semantic memory retrieval (long-term companion)
```

**Example Usage:**

```python
# Job Matching via Vector Search
user_profile_embedding = generate_embedding(
    f"Skills: {user_skills}, Experience: {user_experience}"
)

similar_jobs = chromadb.job_embeddings.query(
    query_embeddings=[user_profile_embedding],
    n_results=50,
    where={"location": {"$eq": "San Francisco"}}
)

# Long-term Memory Retrieval
query = "When did I struggle with React hooks?"
results = chromadb.journal_embeddings.query(
    query_texts=[query],
    n_results=5,
    where={"user_id": {"$eq": user_id}}
)
# Returns: Past journal entries mentioning React hooks struggles
```

**Why ChromaDB?**
- ✅ Lightweight, embedded vector database
- ✅ Fast similarity search (HNSW algorithm)
- ✅ No separate server needed
- ✅ Python-native (easy integration with FastAPI)

***

### **Database Synchronization Flow**

```
User Action (e.g., Update Skills)
         ↓
1. Save to PostgreSQL (Source of Truth)
   • ACID transaction
   • skills table updated
         ↓
2. Background Task: Profile Agent Triggers
         ↓
3. Sync to Neo4j
   • Create/Update (:User)-[:HAS_SKILL]->(:Skill)
   • Update skill levels
         ↓
4. Generate Embeddings
   • Updated profile text → Embedding
   • Store in ChromaDB (resume_embeddings)
         ↓
5. Trigger Dependent Agents
   • Roadmap Agent: Recalculate skill gaps
   • Opportunities Agent: Re-rank job matches
         ↓
All 3 databases now in sync
```

***

## 💻 Technology Stack

### **Backend**

**Core Framework:**
- FastAPI 0.104+ (async API)
- Python 3.11+ (type hints, performance)
- Uvicorn (ASGI server)
- Pydantic 2.0+ (data validation)

**Databases:**
- **PostgreSQL 15** - Relational data (SQLAlchemy ORM)
- **Neo4j 5.0+** - Knowledge graph (py2neo driver)
- **ChromaDB 0.4+** - Vector embeddings (persistent client)

**AI/ML:**
- **Groq API** - LLM (fast inference)
- **LangChain 0.1+** - Agent framework
- **LangGraph** - Multi-agent orchestration
- **Whisper Base** - Speech-to-text (offline, 74M params)
- **Piper TTS** - Text-to-speech (en_US-lessac model)
- **Sentence Transformers** - Embeddings (all-MiniLM-L6-v2)
- **Transformers** - Sentiment analysis (BERT)

**Authentication & Security:**
- JWT (JSON Web Tokens)
- bcrypt (password hashing)
- OAuth 2.0 (Google Calendar/Gmail)

**Background Jobs:**
- APScheduler (cron-like scheduling)
- FastAPI BackgroundTasks

**Web Scraping:**
- BeautifulSoup4 (HTML parsing)
- Selenium (dynamic content)
- aiohttp (async HTTP)

**File Processing:**
- PyPDF2 (PDF parsing)
- python-docx (Word documents)
- python-multipart (file uploads)

**Database Migrations:**
- Alembic (PostgreSQL schema versioning)

***

### **Frontend**

**Core:**
- React 18 (concurrent rendering)
- TypeScript 5 (type safety)
- Vite 5 (fast dev server)

**UI Framework:**
- TailwindCSS 3.4 (utility-first CSS)
- Lucide React (icon library)
- Framer Motion (animations)

**State Management:**
- React Hooks (useState, useEffect, useContext)
- Context API (global state)

**Audio/Video:**
- MediaRecorder API (voice recording)
- Web Audio API (audio processing)
- HTMLAudioElement (playback)

**HTTP Client:**
- Axios (API requests)
- JWT token management

***

### **External Integrations**

**Google APIs:**
- Google Calendar API (OAuth 2.0, event CRUD)
- Gmail API (OAuth 2.0, send emails, read replies)

**Job Boards:**
- LinkedIn Jobs (API + scraping)
- Indeed (web scraping)
- Glassdoor (Selenium automation)

***

## 🚀 Quick Start

### **Prerequisites**

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Neo4j 5.0+ (Neo4j Desktop or Docker)
- Git

***

### **Installation**

**1. Clone Repository**

```bash
git clone https://github.com/Seventie/Anokha-AiVerse.git
cd Anokha-AiVerse
```

***

**2. Backend Setup**

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
pip install -r requirements_opportunities.txt
pip install -r req_interview.txt
pip install -r req_extra.txt
```

***

**3. Download AI Models**

```bash
# Whisper (Speech-to-Text)
python -c "import whisper; whisper.load_model('base')"

# Piper TTS (Text-to-Speech)
# Download from: https://github.com/rhasspy/piper/releases
# Place en_US-lessac-medium.onnx in backend/models/piper/

# Or use setup script (Linux/Mac)
chmod +x setup_local_models.sh
./setup_local_models.sh
```

***

**4. Environment Configuration**

Create `backend/.env`:

```env
# API Keys
OPENAI_API_KEY=your_openai_key_here        # For embeddings
GROQ_API_KEY=your_groq_key_here            # For LLM

# Database URLs
DATABASE_URL=postgresql://user:password@localhost:5432/careerai
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# JWT Secret
SECRET_KEY=your_super_secret_jwt_key_here_min_32_chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ChromaDB
CHROMA_PERSIST_DIRECTORY=./chroma_db

# File Storage
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760  # 10MB

# AI Model Paths
WHISPER_MODEL_PATH=./models/whisper/base.pt
PIPER_MODEL_PATH=./models/piper/en_US-lessac-medium.onnx

# Google APIs (for Calendar & Gmail)
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

# Scheduler
SCHEDULER_ENABLED=true
JOB_SCRAPING_INTERVAL_HOURS=12
COLD_EMAIL_INTERVAL_DAYS=3
```

***

**5. Initialize Databases**

```bash
# PostgreSQL - Create database
createdb careerai

# Run migrations
alembic upgrade head

# Seed with demo data (optional)
python init_db.py

# Neo4j - Start Neo4j Desktop or Docker
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  neo4j:5.0

# Initialize knowledge graph
python app/services/graph_builder.py
```

***

**6. Frontend Setup**

```bash
cd ../frontend

# Install dependencies
npm install

# Create environment file
cat > .env.local << EOF
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
EOF
```

***

**7. Run Application**

**Terminal 1 - Backend:**

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**

```bash
cd frontend
npm run dev
```

**Access Application:**
- 🌐 Frontend: http://localhost:5173
- 🔌 Backend API: http://localhost:8000
- 📚 API Docs: http://localhost:8000/docs
- 🗄️ Neo4j Browser: http://localhost:7474

![Installation Success](./docs/images/installation- ⏰ Automation & Scheduling

### **Background Scheduler Configuration**

CareerAI runs **automated tasks** using APScheduler:

**1. Job Scraping (Every 12 Hours)**

```python
# app/main.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour='0,12')
async def scrape_jobs():
    """Runs at 00:00 and 12:00 daily"""
    logger.info("Starting job scraping...")
    await opportunities_agent.scrape_and_match_all_users()
```

**2. Cold Email Outreach (Every 3 Days)**

```python
@scheduler.scheduled_job('cron', day='*/3', hour='9')
async def send_cold_emails():
    """Runs at 9:00 AM every 3 days"""
    logger.info("Sending cold emails...")
    await cold_email_agent.process_pending_emails()
```

**3. Roadmap Auto-Rescheduling (Daily Check)**

```python
@scheduler.scheduled_job('cron', hour='8')
async def check_delayed_tasks():
    """Runs at 8:00 AM daily"""
    logger.info("Checking delayed roadmap tasks...")
    await roadmap_agent.reschedule_delayed_tasks(delay_threshold_days=10)
```

**4. Dashboard Data Sync (Every 6 Hours)**

```python
@scheduler.scheduled_job('cron', hour='*/6')
async def update_dashboards():
    """Runs every 6 hours"""
    logger.info("Updating user dashboards...")
    await summary_agent.refresh_all_dashboards()
```

***

## 📂 Project Structure

```
Anokha-AiVerse/
│
├── backend/
│   ├── app/
│   │   ├── agents/                     # AI Agent System
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py          # Base agent class
│   │   │   ├── supervisor_agent.py     # Orchestrator
│   │   │   ├── profile_agent.py        # User profile sync
│   │   │   ├── resume_agent.py         # Resume parsing & analysis
│   │   │   ├── interview_agent.py      # Interview conductor
│   │   │   ├── roadmap_agent.py        # Learning path generator
│   │   │   ├── opportunities_agent.py  # Job scraping & matching
│   │   │   ├── journal_agent.py        # Reflection analyzer
│   │   │   └── summary_agent.py        # Dashboard aggregator
│   │   │
│   │   ├── routes/                     # API Endpoints
│   │   │   ├── auth.py                 # Login, register, JWT
│   │   │   ├── profile.py              # User profile CRUD
│   │   │   ├── resume.py               # Resume upload & analysis
│   │   │   ├── interview.py            # Interview sessions
│   │   │   ├── roadmap.py              # Learning roadmap
│   │   │   ├── opportunities.py        # Job search & apply
│   │   │   ├── journal.py              # Journal entries
│   │   │   ├── dashboard.py            # Dashboard data
│   │   │   └── knowledge_graph.py      # Neo4j queries
│   │   │
│   │   ├── services/                   # Business Logic
│   │   │   ├── graph_db.py             # Neo4j connection
│   │   │   ├── vector_db.py            # ChromaDB client
│   │   │   ├── graph_builder.py        # Neo4j initialization
│   │   │   ├── hybrid_graph_service.py # Multi-DB orchestration
│   │   │   ├── user_graph_sync.py      # User → Neo4j sync
│   │   │   ├── llm_service.py          # Groq API wrapper
│   │   │   ├── interview_llm_service.py# Interview-specific LLM
│   │   │   ├── interview_service.py    # Interview logic
│   │   │   ├── stt_service.py          # Whisper STT
│   │   │   ├── tts_service.py          # Piper TTS
│   │   │   ├── resume_parser_service.py# Resume parsing
│   │   │   ├── resume_analyzer_service.py# ATS scoring
│   │   │   ├── job_scraper_service.py  # Job board scraping
│   │   │   ├── opportunities_service.py# Job matching logic
│   │   │   └── journal_service.py      # Journal processing
│   │   │
│   │   ├── models/                     # Database Models (SQLAlchemy)
│   │   │   ├── __init__.py
│   │   │   ├── database.py             # PostgreSQL models
│   │   │   └── graph_models.py         # Neo4j models
│   │   │
│   │   ├── schemas/                    # Pydantic Schemas
│   │   │   ├── user.py                 # User DTOs
│   │   │   ├── graph_schemas.py        # Graph DTOs
│   │   │   └── interview_schemas.py    # Interview DTOs
│   │   │
│   │   ├── config/                     # Configuration
│   │   │   ├── settings.py             # Environment variables
│   │   │   └── database.py             # DB connections
│   │   │
│   │   ├── utils/                      # Utilities
│   │   │   ├── auth.py                 # JWT helpers
│   │   │   ├── graph_queries.py        # Cypher queries
│   │   │   └── graph_validators.py     # Data validation
│   │   │
│   │   ├── knowledgeFiles/             # Static Knowledge
│   │   │   ├── skillCatalog.json
│   │   │   ├── skillOntology.json
│   │   │   ├── jobRoles.json
│   │   │   ├── jobSkill.json
│   │   │   └── resourceSkill.json
│   │   │
│   │   ├── main.py                     # FastAPI app entry
│   │   └── __init__.py
│   │
│   ├── models/                         # AI Models
│   │   ├── whisper/
│   │   │   └── base.pt                 # Whisper Base model
│   │   └── piper/
│   │       ├── en_US-lessac-medium.onnx
│   │       └── en_US-lessac-medium.onnx.json
│   │
│   ├── interview_audio/                # Generated Audio Files
│   │   ├── questions/                  # TTS-generated questions
│   │   └── answers/                    # User answer recordings
│   │
│   ├── interview_recordings/           # Full interview sessions
│   │
│   ├── uploads/                        # User Uploads
│   │   ├── resumes/                    # Resume PDFs/DOCX
│   │   └── temp/                       # Temporary files
│   │
│   ├── alembic/                        # Database Migrations
│   │   ├── versions/                   # Migration scripts
│   │   ├── env.py
│   │   └── script.py.mako
│   │
│   ├── requirements.txt                # Core dependencies
│   ├── requirements_opportunities.txt  # Scraping dependencies
│   ├── req_interview.txt               # Interview dependencies
│   ├── req_extra.txt                   # Additional packages
│   ├── alembic.ini                     # Alembic config
│   ├── init_db.py                      # DB initialization script
│   ├── setup_local_models.sh           # Model download script
│   └── .env                            # Environment variables
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── LandingPage.tsx         # Marketing page
│   │   │   ├── Login.tsx               # Authentication
│   │   │   ├── GetStarted.tsx          # Registration wizard
│   │   │   ├── Navbar.tsx              # Navigation
│   │   │   │
│   │   │   ├── Dashboard/
│   │   │   │   ├── Dashboard.tsx       # Main container
│   │   │   │   ├── DashboardHome.tsx   # Overview page
│   │   │   │   ├── ProfileModule.tsx   # Profile management
│   │   │   │   ├── ResumeModule.tsx    # Resume tools
│   │   │   │   ├── RoadmapModule.tsx   # Learning roadmap
│   │   │   │   ├── OpportunitiesModule.tsx # Job search
│   │   │   │   ├── JournalModule.tsx   # Daily journal
│   │   │   │   └── SummaryModule.tsx   # Progress reports
│   │   │   │
│   │   │   └── Interview/
│   │   │       ├── InterviewModule.tsx # Interview hub
│   │   │       ├── InterviewSetup.tsx  # Configuration
│   │   │       ├── InterviewRoom.tsx   # Live session
│   │   │       ├── InterviewResults.tsx# Results page
│   │   │       └── InterviewAnalytics.tsx # Historical data
│   │   │
│   │   ├── services/                   # API Clients
│   │   │   ├── apiService.ts           # Base HTTP client
│   │   │   ├── authService.ts          # Auth APIs
│   │   │   ├── agentService.ts         # Agent APIs
│   │   │   ├── interviewService.ts     # Interview APIs
│   │   │   ├── resumeService.ts        # Resume APIs
│   │   │   ├── opportunitiesService.ts # Job APIs
│   │   │   ├── journalService.ts       # Journal APIs
│   │   │   ├── profileService.ts       # Profile APIs
│   │   │   └── dashboardService.ts     # Dashboard APIs
│   │   │
│   │   ├── index.css                   # Global styles
│   │   └── App.tsx                     # Root component
│   │
│   ├── index.html                      # HTML entry
│   ├── index.tsx                       # React entry
│   ├── vite.config.ts                  # Vite config
│   ├── tsconfig.json                   # TypeScript config
│   ├── package.json                    # Node dependencies
│   ├── package-lock.json
│   └── .env.local                      # Environment variables
│
├── docs/                               # Documentation & Assets
│   └── images/                         # Screenshots & diagrams
│
├── .gitignore
├── LICENSE
└── README.md                           # This file
```

***

## 📸 Screenshots

### **Landing Page**

![Landing Page](./docs/images Upload & Auto-fill**

![Resume Upload](./docs/images/resume-upload-demod Home**

![Dashboard](./docs/images/dashboard-homeLearning Roadmap with Calendar Sync**

![Roadmap](./docs/images/roadmap-calendar Interview Room**

![Interview](./docs/images/interview-roomJob Matching Results**

![Jobs](./docs/images/job-matchesCold Email Automation**

![Cold Email](./docs/images/cold-email-dashboarDaily Journal & Insights**

![Journal](./docs/ 🗺️ Roadmap

### **Version 1.0 (Current)** ✅

- Multi-agent AI system with LangGraph orchestration
- Resume parsing and auto-fill registration
- Voice-based AI interview simulator (Whisper + Piper TTS)
- Automated learning roadmap with Google Calendar sync
- Job scraping and matching (every 12 hours)
- Cold email automation (every 3 days)
- Daily journal with long-term memory (ChromaDB)
- Multi-database architecture (PostgreSQL + Neo4j + ChromaDB)

***

### **Version 2.0 (Upcoming)** 🚧

- [ ] **Real-time WebSocket Interviews** - Live transcription during answers
- [ ] **Mobile App** (React Native) - Interview practice on-the-go
- [ ] **Advanced Analytics Dashboard** - Skill growth visualization, time-series charts
- [ ] **Mentor Matching** - Connect with industry professionals via knowledge graph
- [ ] **Team Collaboration** - Study groups, peer resume reviews
- [ ] **Gamification** - Badges, streaks, leaderboards
- [ ] **Enhanced Cold Email** - A/B testing, open rate tracking
- [ ] **Multi-language Support** - Whisper multilingual models
- [ ] **Custom Agent Creation** - User-defined specialized agents

***

### **Version 3.0 (Vision)** 🔮

- [ ] **Enterprise Features** - Team dashboards, org-wide skill mapping
- [ ] **Blockchain Credentials** - Verified skill certificates as NFTs
- [ ] **Metaverse Integration** - VR interview practice rooms
- [ ] **AI Video Interviewer** - Deepfake avatar with lip-sync
- [ ] **Salary Negotiation Coach** - Real-time guidance during offers

***

## 🤝 Contributing

We welcome contributions from the community!

### **How to Contribute**

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### **Code Standards**

- **Python:** PEP 8, use type hints, docstrings for functions
- **TypeScript:** Airbnb style guide, functional components, TypeScript strict mode
- **Commits:** Conventional Commits format (`feat:`, `fix:`, `docs:`, etc.)

### **Testing**

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

***

## 📄 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) for details.

***

## 📧 Contact & Support

- 💬 **Discord:** [Join our community](https://discord.gg/careerai)
- 🐦 **Twitter:** [@CareerAI_Dev](https://twitter.com/CareerAI_Dev)
- 📧 **Email:** support@careerai.dev
- 🐛 **Issues:** [GitHub Issues](https://github.com/Seventie/Anokha-AiVerse/issues)

***

## 🙏 Acknowledgments

Special thanks to:

- **OpenAI** - GPT models and embeddings API
- **Groq** - Fast LLM inference
- **Whisper** - Open-source speech recognition
- **Piper** - Neural text-to-speech
- **LangChain & LangGraph** - Agent orchestration framework
- **Neo4j** - Knowledge graph database
- **ChromaDB** - Vector embedding database
- **FastAPI** - Modern Python web framework

***

<div align="center">

**⭐ Star this repo if CareerAI helped you land your dream job!**

Built with ❤️ by the CareerAI Team

![Footer](./docs/images/footer-er 30, 2025

</div>
