# backend/app/services/interview_llm_service.py

from groq import Groq
from typing import List, Dict, Any, Optional
from app.config.settings import settings
import json
import logging
import re

logger = logging.getLogger(__name__)

class InterviewLLMService:
    """
    LLM service for interview intelligence using Groq
    - Question generation
    - Answer evaluation
    - Feedback generation
    """
    
    def __init__(self):
        self.client = None
        if settings.GROQ_API_KEY_INTERVIEW:
            try:
                self.client = Groq(api_key=settings.GROQ_API_KEY_INTERVIEW)
            except Exception as e:
                logger.warning(f"Could not initialize Groq client for interviews: {e}")
        self.model = "llama3-70b-8192"  # Best for reasoning
        self.fast_model = "llama3-8b-8192"  # For quick evaluations

    def _extract_keywords(self, text: str, limit: int = 8) -> List[str]:
        if not text:
            return []
        cleaned = re.sub(r"[^a-zA-Z0-9+.#\s]", " ", text.lower())
        tokens = [t for t in cleaned.split() if 2 <= len(t) <= 24]
        stop = {
            "the","and","for","with","you","your","are","our","this","that","will","have","from","into","role",
            "years","year","experience","work","team","teams","using","use","able","must","should","skills","skill",
            "we","they","them","their","what","when","where","how","why","who","a","an","to","of","in","on","as"
        }
        tokens = [t for t in tokens if t not in stop]
        freq: Dict[str, int] = {}
        for t in tokens:
            freq[t] = freq.get(t, 0) + 1
        ranked = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
        return [k for k, _ in ranked[:limit]]

    def _fallback_question(self, context: Dict[str, Any], round_type: str, difficulty: str, forbidden: List[str]) -> Dict[str, Any]:
        jd = (context.get("job_description") or "").strip()
        topics = context.get("custom_topics") or []
        company = context.get("company_name") or "the role"
        keywords = self._extract_keywords(jd)
        focus = keywords[:3] or [t for t in topics[:3] if isinstance(t, str)]
        focus_text = ", ".join(focus) if focus else "the job requirements"

        if round_type == "technical":
            pool = [
                f"Walk me through how you would design and implement a solution for {focus_text} mentioned in the job description.",
                f"The role mentions {focus_text}. What trade-offs would you consider when building this in production?",
                f"Pick one requirement from the job description (e.g., {focus_text}) and explain your approach end-to-end, including testing and deployment.",
                f"What are the biggest performance or reliability risks you anticipate for {focus_text}, and how would you mitigate them?"
            ]
            category = "technical"
            look_for = ["Clear approach", "Trade-offs", "Real-world considerations"]
        elif round_type == "hr":
            pool = [
                f"Why are you interested in this position at {company}, and which part of the job description aligns best with your experience?",
                "Tell me about a time you handled conflicting priorities. How did you decide what to do first?",
                "Describe a situation where you received critical feedback. What did you change afterwards?",
                "Tell me about a time you influenced a decision without formal authority."
            ]
            category = "behavioral"
            look_for = ["Specific examples", "Ownership", "Reflection and learning"]
        else:
            pool = [
                f"Explain a complex concept from your past work (related to {focus_text}) to a non-technical stakeholder.",
                "When you don't know an answer in an interview, how do you communicate and proceed?",
                "How do you structure your answers to be clear and concise under time pressure?",
                "Describe how you collaborate with teammates to resolve misunderstandings and keep alignment."
            ]
            category = "communication"
            look_for = ["Clarity", "Structure", "Stakeholder awareness"]

        for q in pool:
            if q not in forbidden:
                return {
                    "question": q,
                    "category": category,
                    "what_to_look_for": look_for,
                    "sample_answer_points": []
                }

        return {
            "question": f"What would you prioritize first in the first 30 days for this role, based on the job description?",
            "category": "general",
            "what_to_look_for": ["Prioritization", "Clarity", "Alignment to role"],
            "sample_answer_points": []
        }
    
    async def generate_interview_question(
        self,
        context: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        round_type: str,
        difficulty: str
    ) -> Dict[str, Any]:
        """
        Generate contextual interview question
        
        Args:
            context: Interview context (company, role, JD, topics)
            conversation_history: Previous Q&A pairs
            round_type: "technical" | "hr" | "communication"
            difficulty: "easy" | "medium" | "hard"
        
        Returns:
            {
                "question": "What is your approach to...",
                "category": "problem_solving",
                "what_to_look_for": ["key point 1", "key point 2"],
                "sample_answer_points": ["expected 1", "expected 2"],
                "follow_up_hints": ["probe deeper on X"]
            }
        """
        
        forbidden_questions = [
            msg.get("message", "")
            for msg in conversation_history
            if msg.get("speaker") == "ai" and msg.get("message")
        ]

        if not self.client:
            return self._fallback_question(context, round_type, difficulty, forbidden_questions)

        # Build system prompt
        system_prompt = self._build_question_prompt(context, round_type, difficulty)
        
        # Format conversation history
        history_text = self._format_history(conversation_history)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""Previous conversation:
{history_text}

Do NOT repeat any of these previously asked questions (exact text):
{json.dumps(forbidden_questions[-12:], ensure_ascii=False)}

Generate the NEXT interview question that naturally follows this conversation.
Return ONLY valid JSON, no markdown."""}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)

            q = (result.get("question") or "").strip()
            if not q or q in forbidden_questions:
                return self._fallback_question(context, round_type, difficulty, forbidden_questions)

            if "category" not in result:
                result["category"] = "general"
            if "what_to_look_for" not in result or not isinstance(result.get("what_to_look_for"), list):
                result["what_to_look_for"] = []
            if "sample_answer_points" not in result or not isinstance(result.get("sample_answer_points"), list):
                result["sample_answer_points"] = []

            logger.info(f"✅ Generated {round_type} question: {q[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"❌ Question generation error: {e}")
            return self._fallback_question(context, round_type, difficulty, forbidden_questions)
    
    async def evaluate_answer(
        self,
        question: str,
        answer: str,
        expected_points: List[str],
        round_type: str
    ) -> Dict[str, Any]:
        """
        Evaluate candidate's answer
        
        Returns:
            {
                "score": 85,  // 0-100
                "content_score": 80,
                "clarity_score": 90,
                "depth_score": 85,
                "strengths": ["Good examples", "Clear structure"],
                "improvements": ["Add more technical depth", "Explain X better"],
                "feedback": "Detailed feedback paragraph",
                "pass": true,
                "confidence_level": "high"
            }
        """
        
        system_prompt = f"""You are an expert interview evaluator for {round_type} interviews.

Question: {question}

Expected key points to cover:
{chr(10).join([f"- {point}" for point in expected_points])}

Candidate's answer: {answer}

Evaluate comprehensively on:
1. Content accuracy and completeness
2. Communication clarity
3. Technical depth (if applicable)
4. Real-world understanding
5. Confidence indicators

Return JSON:
{{
    "score": 85,
    "content_score": 80,
    "clarity_score": 90,
    "depth_score": 85,
    "strengths": ["strength 1", "strength 2"],
    "improvements": ["improvement 1", "improvement 2"],
    "feedback": "Detailed paragraph of constructive feedback",
    "pass": true,
    "confidence_level": "high"
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.fast_model,  # Fast evaluation
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Evaluate this answer."}
                ],
                temperature=0.3,  # Low for consistency
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"✅ Answer evaluated: {result['score']}/100")
            return result
            
        except Exception as e:
            logger.error(f"❌ Answer evaluation error: {e}")
            return {
                "score": 50,
                "content_score": 50,
                "clarity_score": 50,
                "depth_score": 50,
                "strengths": ["Answer provided"],
                "improvements": ["Could not evaluate - please try again"],
                "feedback": "Evaluation unavailable",
                "pass": False
            }
    
    async def generate_final_evaluation(
        self,
        all_conversations: List[Dict[str, Any]],
        round_scores: List[float],
        interview_type: str,
        company_name: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive interview report
        
        Returns:
            {
                "overall_score": 82,
                "technical_score": 85,
                "communication_score": 88,
                "problem_solving_score": 75,
                "confidence_score": 80,
                "strengths": ["Strong technical foundation", "Clear communicator"],
                "weaknesses": ["Needs more system design practice"],
                "recommendations": ["Study distributed systems", "Practice mock interviews"],
                "next_steps": "Ready for real interviews at mid-level positions",
                "pass": true
            }
        """
        
        # Summarize conversation
        conversation_summary = self._summarize_conversations(all_conversations)
        
        system_prompt = f"""You are a senior technical recruiter providing final interview feedback.

Interview Type: {interview_type}
Company: {company_name}

Round Scores: {round_scores}
Average: {sum(round_scores)/len(round_scores):.1f}

Full Conversation Summary:
{conversation_summary}

Provide comprehensive evaluation in JSON:
{{
    "overall_score": 82,
    "technical_score": 85,
    "communication_score": 88,
    "problem_solving_score": 75,
    "confidence_score": 80,
    "strengths": ["2-3 key strengths"],
    "weaknesses": ["2-3 areas to improve"],
    "recommendations": ["Specific actionable steps"],
    "next_steps": "What candidate should do next",
    "pass": true,
    "readiness_level": "mid-level"
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,  # Use powerful model for final eval
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate final evaluation."}
                ],
                temperature=0.5,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"✅ Final evaluation: {result['overall_score']}/100")
            return result
            
        except Exception as e:
            logger.error(f"❌ Final evaluation error: {e}")
            return {"error": str(e)}
    
    def _build_question_prompt(self, context: Dict, round_type: str, difficulty: str) -> str:
        """Build system prompt for question generation"""
        
        base_prompt = f"""You are an expert {round_type} interviewer at {difficulty} difficulty level.

Context:
- Company: {context.get('company_name', 'General Tech Company')}
- Role: {context.get('job_title', 'Software Engineer')}
- Job Description: {context.get('job_description', 'N/A')[:500]}
- Focus Topics: {', '.join(context.get('custom_topics', []))}

Your goal: Generate realistic interview questions that:
1. Match {round_type} interview style
2. Are appropriate for {difficulty} level
3. Follow naturally from previous conversation
4. Test real-world understanding
5. Allow for in-depth discussion

Return JSON format:
{{
    "question": "Clear, specific question",
    "category": "behavioral|technical|problem_solving",
    "what_to_look_for": ["key point 1", "key point 2", "key point 3"],
    "sample_answer_points": ["expected element 1", "expected element 2"],
    "follow_up_hints": ["Probe on X if they mention it"]
}}"""
        
        return base_prompt
    
    def _format_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history"""
        if not history:
            return "No previous conversation (this is the first question)."
        
        formatted = []
        for msg in history[-6:]:  # Last 6 exchanges (3 Q&A pairs)
            speaker = "Interviewer" if msg["speaker"] == "ai" else "Candidate"
            formatted.append(f"{speaker}: {msg['message']}")
        
        return "\n".join(formatted)
    
    def _summarize_conversations(self, conversations: List[Dict]) -> str:
        """Summarize all conversations for final eval"""
        summary = []
        for i, conv in enumerate(conversations):
            if conv["speaker"] == "ai":
                summary.append(f"\nQ{i//2 + 1}: {conv['message']}")
            else:
                summary.append(f"A{i//2 + 1}: {conv['message'][:200]}...")  # Truncate long answers
        
        return "\n".join(summary)

# Singleton
interview_llm = InterviewLLMService()
