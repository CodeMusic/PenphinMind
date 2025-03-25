import openai
import os
from typing import Dict, Any

class OpenAIManager:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        openai.api_key = self.api_key
        self.model = "gpt-4"

    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """
        Generate response using OpenAI's API
        """
        try:
            messages = [{"role": "system", "content": "You are PenphinOS, a bicameral AI assistant."}]
            if context:
                messages.append({"role": "system", "content": f"Context: {str(context)}"})
            messages.append({"role": "user", "content": prompt})

            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"OpenAI Error: {str(e)}" 