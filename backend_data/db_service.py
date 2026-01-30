import json
import os
from typing import List, Optional, Dict, Any

class MockDatabaseService:
    """
    GaiaLink Mock Database Service
    
    Reads from 'backend_data/data.json' on init.
    Supports in-memory updates (Optimistic UI for Hackathon).
    """

    def __init__(self, data_path: str = "backend_data/data.json"):
        self.data_path = data_path
        self.data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        """Load data from JSON file"""
        if not os.path.exists(self.data_path):
            # Fallback default data if file missing
            return {"crises": [], "proposals": []}
        
        with open(self.data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def search_crises(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for crises based on keyword matching in title, description, or keywords.
        """
        query = query.lower()
        results = []
        
        for crisis in self.data.get("crises", []):
            # 1. Check ID
            if query in crisis["id"].lower():
                results.append(crisis)
                continue
                
            # 2. Check Title/Desc
            if query in crisis["title"].lower() or query in crisis["description"].lower():
                results.append(crisis)
                continue

            # 3. Check Keywords
            for keyword in crisis.get("keywords", []):
                if keyword.lower() in query:
                    results.append(crisis)
                    break
        
        return results

    def get_crisis_by_id(self, crisis_id: str) -> Optional[Dict[str, Any]]:
        """Get specific crisis by ID"""
        for crisis in self.data.get("crises", []):
            if crisis["id"] == crisis_id:
                return crisis
        return None

    def create_proposal(self, crisis_id: str, target_amount: float, token: str) -> Dict[str, Any]:
        """
        Simulate creating a Layer 2 Proposal (Optimistic In-Memory Write)
        """
        new_proposal = {
            "id": f"prop_{len(self.data.get('proposals', [])) + 1}_{crisis_id}",
            "crisis_id": crisis_id,
            "target_amount": target_amount,
            "current_amount": 0.0,
            "token": token,
            "status": "active",
            "created_at": "Just now"
        }
        
        self.data.setdefault("proposals", []).append(new_proposal)
        return new_proposal

    def get_proposals(self, crisis_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get proposals, optionally filtered by crisis_id"""
        all_props = self.data.get("proposals", [])
        if not crisis_id:
            return all_props
        
        return [p for p in all_props if p["crisis_id"] == crisis_id]

# Singleton Instance
db_service = MockDatabaseService()
