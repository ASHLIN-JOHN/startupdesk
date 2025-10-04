import os
import requests
import json
from typing import Dict, Any


class GroqClient:
    """Client for interacting with Groq API."""
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key if api_key else os.getenv("GROQ_API_KEY", "")
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "mixtral-8x7b-32768"
    
    def generate_score(self, category: str, text: str, context: str = "") -> Dict[str, Any]:
        """Generate a score for a specific category using Groq API."""
        
        prompt = f"""You are a VC analyst evaluating startup pitch decks.

Category: {category}
{f"Context: {context}" if context else ""}

Analyze the following pitch deck content and provide:
1. A score from 1-10 (decimals allowed)
2. Brief evaluation notes (2-3 sentences)

Pitch deck content:
{text}

Respond in JSON format:
{{
    "score": <number between 1-10>,
    "notes": "<brief evaluation>"
}}
"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a VC analyst. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Extract JSON from response
            try:
                # Try to parse as JSON directly
                score_data = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                    score_data = json.loads(json_str)
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                    score_data = json.loads(json_str)
                else:
                    # Fallback: return default values
                    score_data = {"score": 5.0, "notes": content[:200]}
            
            return {
                "score": float(score_data.get("score", 5.0)),
                "notes": score_data.get("notes", "")
            }
            
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return {
                "score": 0.0,
                "notes": f"Error during evaluation: {str(e)}"
            }
    
    def generate_investibility_decision(self, scores: Dict[str, float], notes: Dict[str, str]) -> Dict[str, Any]:
        """Generate final investibility decision based on scores."""
        
        prompt = f"""Based on the following evaluation scores, determine if this startup is investible.

Scores:
- Market Size: {scores.get('market_size', 0)}/10
- Team: {scores.get('team', 0)}/10
- Product: {scores.get('product', 0)}/10
- Traction: {scores.get('traction', 0)}/10
- Financials: {scores.get('financials', 0)}/10

Evaluation Notes:
{json.dumps(notes, indent=2)}

Provide a final decision in JSON format:
{{
    "investible": "Yes" or "No",
    "summary": "<1-2 sentence summary>",
    "key_strengths": ["strength1", "strength2"],
    "key_concerns": ["concern1", "concern2"]
}}
"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a VC analyst. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Extract JSON from response
            try:
                decision_data = json.loads(content)
            except json.JSONDecodeError:
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                    decision_data = json.loads(json_str)
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                    decision_data = json.loads(json_str)
                else:
                    decision_data = {
                        "investible": "No",
                        "summary": "Unable to generate decision",
                        "key_strengths": [],
                        "key_concerns": ["Evaluation error"]
                    }
            
            return decision_data
            
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return {
                "investible": "No",
                "summary": f"Error during evaluation: {str(e)}",
                "key_strengths": [],
                "key_concerns": ["API error"]
            }
