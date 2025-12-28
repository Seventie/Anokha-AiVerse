# backend/app/services/journal_service.py

from app.services.llm_service import llm_service
from app.services.vector_db import get_vector_db
from typing import Dict, Any, List
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class JournalAnalyzerService:
    """AI-powered journal analysis with vector DB context storage"""
    
    def __init__(self):
        try:
            self.vector_db = get_vector_db()
        except Exception as e:
            logger.warning(f"Vector DB not available: {e}")
            self.vector_db = None
    
    async def analyze_entry(
        self,
        content: str,
        title: str = None,
        user_id: str = None,
        entry_id: str = None
    ) -> Dict[str, Any]:
        """
        Analyze journal entry + Store in vector DB for LLM context
        """
        
        try:
            logger.info(f"🤖 Analyzing journal entry ({len(content)} chars)")
            
            # Get user context from vector DB for personalized response
            user_context = ""
            if user_id and self.vector_db:
                try:
                    past_entries = self.vector_db.query_context(
                        user_id=user_id,
                        query="recent experiences learning career progress",
                        n_results=3,
                        filter={"source": "journal_entry"}
                    )
                    if past_entries:
                        user_context = "\n\nRecent context from your journey:\n" + "\n".join([
                            f"- {entry.get('metadata', {}).get('title', 'Entry')}: {entry.get('text', '')[:150]}"
                            for entry in past_entries[:2]
                        ])
                except Exception as e:
                    logger.debug(f"Could not fetch user context: {e}")
            
            # Create personalized prompt
            prompt = f"""You are a supportive career coach analyzing a journal entry from someone on their career journey.

Title: {title or 'Untitled'}

Entry:
{content}
{user_context}

Provide a warm, personalized response as JSON with:
{{
  "summary": "A 2-3 sentence conversational response that shows you understand their situation and progress",
  "key_insights": ["insight about their growth", "pattern you noticed", "strength they demonstrated"],
  "sentiment_score": 0.5,
  "topics_detected": ["learning", "career", "project", etc.],
  "mood_detected": "motivated/frustrated/accomplished/confused/happy",
  "suggestions": ["Specific actionable next step", "Another concrete suggestion", "One more practical tip"]
}}

Be conversational, encouraging, and specific. Reference what they wrote. Don't be generic."""
            
            system_prompt = """You are an empathetic career coach who deeply understands the tech industry. 
You provide personalized insights that show you're paying attention to their journey.
Your tone is warm, supportive, and constructive - like a mentor who genuinely cares."""
            
            # Use LLM service to generate analysis
            response = await llm_service.generate_json(
                prompt=prompt,
                system_prompt=system_prompt,
                model="llama3-70b-8192"
            )
            
            # Ensure all required fields
            response.setdefault("summary", "Thanks for sharing your thoughts! Keep reflecting on your journey.")
            response.setdefault("key_insights", ["You're making progress", "Keep documenting your growth"])
            response.setdefault("sentiment_score", 0.0)
            response.setdefault("topics_detected", ["reflection"])
            response.setdefault("mood_detected", "neutral")
            response.setdefault("suggestions", [
                "Continue documenting your learning",
                "Reflect on your progress weekly"
            ])
            
            # 🔥 STORE IN VECTOR DB FOR CONTEXT
            if user_id and entry_id and self.vector_db:
                await self._store_in_vector_db(
                    user_id=user_id,
                    entry_id=entry_id,
                    title=title,
                    content=content,
                    analysis=response
                )
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Journal analysis failed: {e}", exc_info=True)
            return self._get_default_analysis()
    
    async def _store_in_vector_db(
        self,
        user_id: str,
        entry_id: str,
        title: str,
        content: str,
        analysis: Dict[str, Any]
    ):
        """Store journal entry in ChromaDB for semantic search and LLM context"""
        try:
            if not self.vector_db:
                logger.debug("Vector DB not available, skipping storage")
                return
                
            # Combine title, content, and insights for rich context
            full_text = f"""Journal Entry: {title or 'Untitled'}

Content:
{content}

Key Insights:
{chr(10).join(f'- {insight}' for insight in analysis.get('key_insights', []))}

AI Summary: {analysis.get('summary', '')}"""
            
            # Store in vector DB
            self.vector_db.add_context(
                user_id=user_id,
                text=full_text,
                metadata={
                    "source": "journal_entry",
                    "entry_id": entry_id,
                    "title": title or "Untitled",
                    "timestamp": datetime.utcnow().isoformat(),
                    "mood": analysis.get("mood_detected"),
                    "sentiment_score": analysis.get("sentiment_score", 0.0),
                    "topics": analysis.get("topics_detected", []),
                    "word_count": len(content.split())
                }
            )
            
            logger.info(f"✅ Journal entry {entry_id} stored in vector DB")
            
        except Exception as e:
            logger.error(f"❌ Failed to store in vector DB: {e}")
    
    async def get_context_for_query(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant journal entries for a query"""
        try:
            if not self.vector_db:
                return []
                
            results = self.vector_db.query_context(
                user_id=user_id,
                query=query,
                n_results=limit,
                filter={"source": "journal_entry"}
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Context query failed: {e}")
            return []
    
    async def generate_weekly_summary(
        self,
        entries: List[Dict[str, Any]],
        user_id: str = None
    ) -> Dict[str, Any]:
        """Generate weekly summary with vector DB context"""
        
        if not entries:
            return {
                "summary": "No entries this week. Let's change that!",
                "themes": [],
                "progress_highlights": [],
                "recommendations": ["Start journaling daily to track your progress"]
            }
        
        try:
            # Get additional context from vector DB
            context = ""
            if user_id and self.vector_db:
                past_context = await self.get_context_for_query(
                    user_id=user_id,
                    query="weekly progress learning achievements challenges",
                    limit=3
                )
                if past_context:
                    context = "\n\nContext from previous weeks:\n" + "\n".join([
                        f"- {ctx.get('text', '')[:150]}" for ctx in past_context
                    ])
            
            # Combine entries
            combined_content = "\n\n".join([
                f"Entry {i+1}: {entry.get('title', 'Untitled')}\n{entry.get('content', '')[:400]}"
                for i, entry in enumerate(entries[:7])
            ])
            
            prompt = f"""Analyze this week's journal entries and provide an insightful, personalized summary.

This Week's Entries:
{combined_content[:3500]}
{context}

Provide as JSON:
{{
  "summary": "A warm, conversational 3-4 sentence reflection on their week, highlighting patterns and growth you noticed",
  "themes": ["specific theme 1", "specific theme 2", "specific theme 3"],
  "progress_highlights": ["Specific thing they accomplished", "Another achievement you noticed"],
  "challenges_faced": ["Challenge they mentioned", "Another difficulty"],
  "mood_trend": "improving/steady/struggling",
  "recommendations": ["Specific actionable step", "Another concrete suggestion", "Third practical tip"]
}}

Be specific, encouraging, and reference actual things they wrote about."""
            
            system_prompt = "You are a supportive career coach providing a weekly reflection. Be warm, specific, and constructive."
            
            response = await llm_service.generate_json(
                prompt=prompt,
                system_prompt=system_prompt,
                model="llama3-70b-8192"
            )
            
            # Store weekly summary
            if user_id and self.vector_db:
                summary_text = f"""Weekly Summary ({datetime.utcnow().strftime('%B %d, %Y')})

{response.get('summary', '')}

Key Themes: {', '.join(response.get('themes', []))}
Progress: {', '.join(response.get('progress_highlights', []))}
Recommendations: {', '.join(response.get('recommendations', []))}"""
                
                self.vector_db.add_context(
                    user_id=user_id,
                    text=summary_text,
                    metadata={
                        "source": "weekly_summary",
                        "timestamp": datetime.utcnow().isoformat(),
                        "entry_count": len(entries)
                    }
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Weekly summary failed: {e}")
            return {
                "summary": f"You made {len(entries)} journal entries this week - that's great progress!",
                "themes": ["reflection", "learning"],
                "progress_highlights": ["Consistent journaling"],
                "recommendations": ["Keep documenting your journey"]
            }
    
    def get_daily_prompts(self, category: str = None) -> List[str]:
        """Get random journal prompts"""
        
        prompts = {
            "reflection": [
                "What did I learn today that surprised me?",
                "What challenged me today, and how did I respond?",
                "What am I grateful for in my career journey right now?",
                "If I could redo today, what would I change and why?",
                "What's one skill I'm improving, and how can I tell?"
            ],
            "learning": [
                "What new concept did I grasp today? How will I apply it?",
                "What's still confusing me, and what's my plan to understand it?",
                "What project or tutorial helped me learn the most today?",
                "How did my understanding evolve this week?",
                "What mistake did I make that taught me something valuable?"
            ],
            "career": [
                "What step did I take toward my career goal today?",
                "Who inspired me this week, and what did I learn from them?",
                "What skills do I need to develop for my dream role?",
                "What's one professional connection I could strengthen?",
                "How did I add value today?"
            ],
            "project": [
                "What feature or bug did I tackle today? What did I learn?",
                "What's blocking my progress, and how can I get unstuck?",
                "What's the most interesting technical decision I made today?",
                "How can I improve the code I wrote today?",
                "What would I show in my portfolio from today's work?"
            ]
        }
        
        if category and category in prompts:
            import random
            return random.sample(prompts[category], min(3, len(prompts[category])))
        
        # Return mixed prompts
        import random
        all_prompts = [p for category_prompts in prompts.values() for p in category_prompts]
        return random.sample(all_prompts, 5)
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """Fallback analysis"""
        return {
            "summary": "Thanks for sharing your thoughts! Your reflection shows you're thinking deeply about your journey.",
            "key_insights": ["You're taking time to reflect on your progress", "Keep documenting your learning journey"],
            "sentiment_score": 0.0,
            "topics_detected": ["reflection"],
            "mood_detected": "motivated",
            "suggestions": [
                "Continue documenting your learning experiences",
                "Reflect on your progress weekly to see patterns",
                "Set one specific, achievable goal for tomorrow"
            ]
        }

# Singleton
journal_analyzer = JournalAnalyzerService()
