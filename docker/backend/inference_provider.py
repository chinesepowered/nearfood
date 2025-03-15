import os
import google.generativeai as genai
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GeminiFlashProvider:
    """Gemini Flash 2.0 inference provider"""
    
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        # Configure API
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-flash-2.0')
    
    def get_completion(self, prompt: str) -> str:
        """Get completion from Gemini Flash 2.0"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error getting completion: {e}")
            return f"Error: {str(e)}"

def get_inference_provider() -> Optional[GeminiFlashProvider]:
    """Get the configured inference provider"""
    try:
        return GeminiFlashProvider()
    except Exception as e:
        print(f"Failed to initialize inference provider: {e}")
        return None