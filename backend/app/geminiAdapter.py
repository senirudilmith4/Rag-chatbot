import os
from google import genai
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class GeminiAdapter: 

    def __init__(self):   # Initialize the Gemini client with API key and model configuration
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.client = genai.Client(api_key=api_key)
        
    def generate(self, prompt: str) -> str:
         response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )
         return response.text
