# backend/app/services/interview_llm_service.py

from groq import Groq
from typing import List, Dict, Any, Optional
from app.config.settings import settings
import json
import logging

logger = logging.getLogger(__name__)

class InterviewLLMService:
    """
    LLM service for interview intelligence using Groq
    - Question generation
    - Answer evaluation
    - Feedback generation
    """
    
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY_INTERVIEW)
        self.model = "llama3-70b-8192"  # Best for reasoning
        self.fast_model = "llama3-8b-8192"  # For quick evaluations
    
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
        
        # Build system prompt
        system_prompt = self._build_question_prompt(context, round_type, difficulty)
        
        # Format conversation history
        history_text = self._format_history(conversation_history)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""Previous conversation:
{history_text}

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
            logger.info(f"✅ Generated {round_type} question: {result['question'][:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"❌ Question generation error: {e}")
            # Fallback question
            return {
                "question": "Can you tell me about a challenging project you worked on?",
                "category": "behavioral",
                "what_to_look_for": ["Problem description", "Your approach", "Outcome"],
                "sample_answer_points": ["Clear problem", "Systematic solution", "Measurable results"]
            }
    
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
