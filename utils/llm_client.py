"""
LLM Client with OpenRouter support and model fallback.
Uses direct HTTP requests to avoid langchain version issues.
"""

import os
import json
import requests
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenRouter models with fallback (without openrouter/ prefix)
# Original free models with :free suffix
LT_MODELS = [
    'xiaomi/mimo-v2-flash:free',  # Primary fallback
    'mistralai/devstral-2512:free',
    'tngtech/deepseek-r1t2-chimera:free',
    'tngtech/deepseek-r1t-chimera:free',
    'deepseek/deepseek-r1-0528:free'
]


class OpenRouterLLM:
    """OpenRouter LLM client with automatic fallback."""
    
    def __init__(self, models: Optional[List[str]] = None, temperature: float = 0.1):
        """
        Initialize OpenRouter LLM client.
        
        Args:
            models: List of model names to try (with fallback)
            temperature: Temperature for generation
        """
        self.models = models or LT_MODELS
        self.temperature = temperature
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables. Please add it to .env file.")
        
        # Initialize with first model
        self.current_model_index = 0
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def invoke(self, prompt: str) -> str:
        """
        Invoke LLM with automatic fallback on errors.
        
        Args:
            prompt: Input prompt (string)
            
        Returns:
            LLM response (string)
        """
        last_error = None
        
        # Try current model first, then fallback to others
        models_to_try = [self.models[self.current_model_index]] + [
            m for i, m in enumerate(self.models) if i != self.current_model_index
        ]
        
        for model_name in models_to_try:
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/omni-retail-orchestrator",  # Optional
                    "X-Title": "Omni-Retail Orchestrator"  # Optional
                }
                
                payload = {
                    "model": model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": self.temperature,
                    "max_tokens": 512  # Limit tokens to reduce cost and avoid credit issues
                }
                
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                # Check for errors and log details
                if response.status_code != 200:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = json.dumps(error_json, indent=2)
                    except:
                        pass
                    raise Exception(f"HTTP {response.status_code}: {error_detail}")
                
                result = response.json()
                
                # Extract content from response
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0].get("message", {}).get("content", "")
                    if content:
                        self.current_model_index = self.models.index(model_name)
                        return content.strip()
                    else:
                        raise ValueError("Empty response from model")
                else:
                    raise ValueError("Invalid response format")
                    
            except Exception as e:
                last_error = e
                error_msg = str(e)[:100]
                print(f"[LLM] Model {model_name} failed: {error_msg}. Trying next model...")
                continue
        
        # If all models failed, raise the last error
        raise Exception(f"All models failed. Last error: {str(last_error)}")
    
    def __call__(self, prompt: str) -> str:
        """Make the client callable."""
        return self.invoke(prompt)
