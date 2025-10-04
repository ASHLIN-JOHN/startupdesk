from crewai import Agent, Task, Crew, Process
from typing import Dict, Any
from groq_client import GroqClient
import json


class PitchDeckEvaluationCrew:
    """CrewAI orchestration for pitch deck evaluation."""
    
    def __init__(self, groq_api_key: str):
        self.groq_client = GroqClient(groq_api_key)
        
    def evaluate_pitch_deck(self, deck_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a pitch deck using multiple specialized agents."""
        
        company_name = deck_data.get("company_name", "Unknown")
        sector = deck_data.get("sector", "Unknown")
        stage = deck_data.get("stage", "Unknown")
        content = deck_data.get("content", "")
        funding_ask = deck_data.get("funding_ask", "")
        
        scores = {}
        notes = {}
        
        market_result = self.groq_client.generate_score(
            category="Market Size and Opportunity",
            text=content,
            context=f"Sector: {sector}, Stage: {stage}"
        )
        scores["market_size"] = market_result["score"]
        notes["market_size"] = market_result["notes"]
        
        team_result = self.groq_client.generate_score(
            category="Team Quality and Experience",
            text=content,
            context=f"Company: {company_name}, Stage: {stage}"
        )
        scores["team"] = team_result["score"]
        notes["team"] = team_result["notes"]
        
        product_result = self.groq_client.generate_score(
            category="Product Differentiation and Innovation",
            text=content,
            context=f"Sector: {sector}"
        )
        scores["product"] = product_result["score"]
        notes["product"] = product_result["notes"]
        
        traction_result = self.groq_client.generate_score(
            category="Traction and Growth Metrics",
            text=content,
            context=f"Stage: {stage}"
        )
        scores["traction"] = traction_result["score"]
        notes["traction"] = traction_result["notes"]
        
        financial_result = self.groq_client.generate_score(
            category="Financials and Runway",
            text=content,
            context=f"Funding Ask: {funding_ask}"
        )
        scores["financials"] = financial_result["score"]
        notes["financials"] = financial_result["notes"]
        
        overall_score = sum(scores.values()) / len(scores)
        
        decision = self.groq_client.generate_investibility_decision(scores, notes)
        
        evaluation_result = {
            "company_name": company_name,
            "sector": sector,
            "stage": stage,
            "funding_ask": funding_ask,
            "scores": {
                "market_size": round(scores["market_size"], 2),
                "team": round(scores["team"], 2),
                "product": round(scores["product"], 2),
                "traction": round(scores["traction"], 2),
                "financials": round(scores["financials"], 2),
                "overall": round(overall_score, 2)
            },
            "investible": decision.get("investible", "No"),
            "evaluation_notes": {
                "market_size": notes["market_size"],
                "team": notes["team"],
                "product": notes["product"],
                "traction": notes["traction"],
                "financials": notes["financials"]
            },
            "summary": decision.get("summary", ""),
            "key_strengths": decision.get("key_strengths", []),
            "key_concerns": decision.get("key_concerns", [])
        }
        
        return evaluation_result
