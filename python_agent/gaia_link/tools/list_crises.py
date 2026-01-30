"""
ListCrisesTool - Lists available crises from the backend data file.
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any

from spoon_ai.tools.base import BaseTool

class ListCrisesTool(BaseTool):
    """
    Lists available crises and their status.
    
    Use this tool when the user asks "what crises are there?", "list all disasters", 
    or wants to know what they can help with.
    """
    
    name: str = "list_crises"
    description: str = (
        "Retrieve a list of active humanitarian crises, including their location, "
        "severity, and verification status. Use this to help users find a cause to donate to."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "severity_filter": {
                "type": "string",
                "enum": ["CRITICAL", "HIGH", "MODERATE", "LOW"],
                "description": "Optional filter to only show crises of a certain severity."
            },
            "limit": {
                "type": "integer", 
                "description": "Maximum number of crises to return (default 5)",
                "default": 10
            }
        },
        "required": [],
    }

    def execute(self, severity_filter: str = None, limit: int = 10) -> Dict[str, Any]:
        """
        Executes the tool to list crises.
        """
        # Resolve path to backend_data/data.json
        # Assuming we are running from python_agent/ directory or root
        # Base path: python_agent/gaia_link/tools/list_crises.py
        # Data path: backend_data/data.json
        
        # Determine the project root based on this file's location
        current_file = Path(__file__).resolve()
        # Go up 3 levels: tools -> gaia_link -> python_agent -> keys (root of python_agent, need one more for project root)
        # Actually:
        # current: .../GaiaLink/python_agent/gaia_link/tools/list_crises.py
        # parents[0]: tools
        # parents[1]: gaia_link
        # parents[2]: python_agent
        # parents[3]: GaiaLink (Project Root)
        
        project_root = current_file.parents[3]
        data_path = project_root / "backend_data" / "data.json"
        
        if not data_path.exists():
            return {"error": f"Data file not found at {data_path}"}
            
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            crises = data.get("crises", [])
            
            # Filter
            if severity_filter:
                crises = [c for c in crises if c.get("severity") == severity_filter]
                
            # Sort by severity (CRITICAL first) logic could be added, but for now just list
            
            # Limit
            crises = crises[:limit]
            
            # Simplify output for LLM
            simplified_list = []
            for c in crises:
                simplified_list.append({
                    "id": c.get("id"),
                    "title": c.get("title"),
                    "location": c.get("location", {}).get("region"),
                    "severity": c.get("severity"),
                    "verification": c.get("verification", {}).get("status")
                })
                
            return {
                "count": len(simplified_list),
                "crises": simplified_list,
                "note": "These are the currently tracked crises available directly from the GaiaLink database."
            }
            
        except Exception as e:
            return {"error": f"Failed to read crisis data: {str(e)}"}
