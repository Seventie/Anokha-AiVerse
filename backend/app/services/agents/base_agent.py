"""Base Agent class for all AI agents"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
from datetime import datetime
import anthropic

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all AI agents using Claude Sonnet"""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize base agent with Anthropic client
        
        Args:
            api_key: Anthropic API key
            model: Model to use (Claude Sonnet by default)
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.agent_name = self.__class__.__name__
        self.logger = logger
    
    def call_claude(self, system_prompt: str, user_message: str, **kwargs) -> str:
        """
        Call Claude Sonnet API with system and user prompts
        
        Args:
            system_prompt: System context for the agent
            user_message: User's query/task
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Claude's response text
        """
        try:
            max_tokens = kwargs.get('max_tokens', 4096)
            temperature = kwargs.get('temperature', 0.7)
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            return message.content[0].text
        except Exception as e:
            self.logger.error(f"Error calling Claude in {self.agent_name}: {str(e)}")
            raise
    
    def call_claude_json(self, system_prompt: str, user_message: str, **kwargs) -> Dict[str, Any]:
        """
        Call Claude Sonnet API and parse JSON response
        
        Args:
            system_prompt: System context for the agent
            user_message: User's query/task
            **kwargs: Additional parameters
            
        Returns:
            Parsed JSON response
        """
        import json
        response_text = self.call_claude(system_prompt, user_message, **kwargs)
        
        try:
            # Try to extract JSON from the response
            json_str = response_text
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            
            return json.loads(json_str.strip())
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse JSON response: {response_text}")
            raise ValueError(f"Invalid JSON response from {self.agent_name}")
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the agent's main task
        
        Args:
            **kwargs: Agent-specific parameters
            
        Returns:
            Agent's output as dictionary
        """
        pass
    
    def log_execution(self, task: str, status: str, details: Optional[Dict] = None):
        """
        Log agent execution for debugging
        
        Args:
            task: Task description
            status: Status (success/error/processing)
            details: Additional details
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'agent': self.agent_name,
            'task': task,
            'status': status,
            'details': details or {}
        }
        self.logger.info(f"{self.agent_name} - {task}: {status}", extra=log_entry)
