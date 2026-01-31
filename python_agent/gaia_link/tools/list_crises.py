"""
ListCrisesTool - Lists humanitarian crises from multiple real-time sources.

Data Sources:
1. NASA EONET - Natural disasters (earthquakes, wildfires, storms, etc.)
2. GDELT - Conflict/humanitarian crisis news activity
3. Local JSON - Curated crisis database (fallback)
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

import aiohttp

from spoon_ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

# API endpoints
NASA_EONET_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"
GDELT_GEO_URL = "https://api.gdeltproject.org/api/v2/geo/geo"

# Top humanitarian crisis regions with optimized GDELT queries
# Use broader terms for better API response
HUMANITARIAN_CRISES = [
    {"query": "ukraine", "name": "Ukraine Humanitarian Crisis", "region": "Ukraine", "type": "Armed Conflict"},
    {"query": "gaza", "name": "Gaza Humanitarian Crisis", "region": "Gaza Strip", "type": "Armed Conflict"},
    {"query": "sudan conflict", "name": "Sudan Civil War & Famine", "region": "Sudan", "type": "Armed Conflict"},
    {"query": "syria", "name": "Syria Humanitarian Crisis", "region": "Syria", "type": "Armed Conflict"},
    {"query": "yemen", "name": "Yemen Humanitarian Crisis", "region": "Yemen", "type": "Armed Conflict"},
    {"query": "myanmar", "name": "Myanmar Civil Conflict", "region": "Myanmar", "type": "Armed Conflict"},
    {"query": "haiti crisis", "name": "Haiti Humanitarian Crisis", "region": "Haiti", "type": "Armed Conflict"},
]

# EONET category mappings
EONET_SEVERITY_MAP = {
    "severeStorms": "CRITICAL",
    "wildfires": "HIGH",
    "volcanoes": "CRITICAL",
    "earthquakes": "CRITICAL",
    "floods": "HIGH",
}

EONET_CATEGORY_NAMES = {
    "severeStorms": "Severe Storm",
    "wildfires": "Wildfire",
    "volcanoes": "Volcanic Activity",
    "earthquakes": "Earthquake",
    "floods": "Flood",
}

# Filters for natural disasters (exclude non-emergency events)
EONET_EXCLUDE_KEYWORDS = [
    "prescribed",  # Prescribed burns (controlled, not emergencies)
    " rx ",        # Rx = Prescribed (common abbreviation)
    " rx,",
    "rx ",         # Starts with Rx
    "controlled burn",
    "planned burn",
]

# Timeouts (in seconds)
SINGLE_REQUEST_TIMEOUT = 5
TOTAL_API_TIMEOUT = 12


class ListCrisesTool(BaseTool):
    """
    Lists humanitarian crises from multiple real-time sources.
    """

    name: str = "list_crises"
    description: str = (
        "Retrieve a list of active humanitarian crises including armed conflicts "
        "and natural disasters from NASA EONET and GDELT news activity."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "crisis_type": {
                "type": "string",
                "enum": ["all", "natural", "conflict"],
                "description": "Type of crises to list (default: all)"
            },
            "severity_filter": {
                "type": "string",
                "enum": ["CRITICAL", "HIGH", "MODERATE", "LOW"],
                "description": "Optional filter by severity level."
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of crises to return (default 10)",
                "default": 10
            }
        },
        "required": [],
    }

    async def execute(
        self,
        crisis_type: str = "all",
        severity_filter: Optional[str] = None,
        limit: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executes the tool with overall timeout protection.
        """
        try:
            return await asyncio.wait_for(
                self._execute_with_apis(crisis_type, severity_filter, limit),
                timeout=TOTAL_API_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.warning("API requests timed out, using local data")
            return await self._get_local_crises(severity_filter, limit)
        except Exception as e:
            logger.error(f"Unexpected error: {e}, using local data")
            return await self._get_local_crises(severity_filter, limit)

    async def _execute_with_apis(
        self,
        crisis_type: str,
        severity_filter: Optional[str],
        limit: int
    ) -> Dict[str, Any]:
        """Execute API calls with parallel requests."""
        all_crises = []
        sources_used = []

        # Run API calls in parallel
        tasks = []
        if crisis_type in ["all", "conflict"]:
            tasks.append(("gdelt", self._get_gdelt_crises(severity_filter)))
        if crisis_type in ["all", "natural"]:
            tasks.append(("eonet", self._get_eonet_crises(severity_filter, limit)))

        if not tasks:
            return await self._get_local_crises(severity_filter, limit)

        # Execute all tasks in parallel
        results = await asyncio.gather(
            *[task[1] for task in tasks],
            return_exceptions=True
        )

        for i, result in enumerate(results):
            task_name = tasks[i][0]
            if isinstance(result, Exception):
                logger.warning(f"{task_name} failed: {result}")
                continue
            if result:
                all_crises.extend(result)
                if task_name == "gdelt":
                    sources_used.append("GDELT (Conflicts)")
                else:
                    sources_used.append("NASA EONET (Natural)")

        # If no API data, use local
        if not all_crises:
            return await self._get_local_crises(severity_filter, limit)

        # Sort by severity
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2, "LOW": 3}
        all_crises.sort(key=lambda x: (
            severity_order.get(x.get("severity", "LOW"), 4),
            -x.get("news_count", 0)
        ))

        return {
            "count": min(len(all_crises), limit),
            "crises": all_crises[:limit],
            "sources": sources_used,
            "note": "Real-time data from verified sources."
        }

    async def _get_gdelt_crises(
        self,
        severity_filter: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Fetch humanitarian crisis activity from GDELT (parallel requests)."""

        async def fetch_single(session: aiohttp.ClientSession, crisis_info: dict) -> Optional[Dict]:
            try:
                params = {
                    "query": crisis_info["query"],
                    "mode": "PointData",
                    "format": "GeoJSON",
                    "maxpoints": 3
                }
                async with session.get(
                    GDELT_GEO_URL,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=SINGLE_REQUEST_TIMEOUT)
                ) as response:
                    if response.status != 200:
                        return None
                    data = await response.json()

                features = data.get("features", [])
                if not features:
                    return None

                total_count = sum(
                    f.get("properties", {}).get("count", 0)
                    for f in features
                )

                # Lower thresholds for conflicts to appear more prominently
                # Armed conflicts with any significant news activity are important
                if total_count > 500:
                    severity = "CRITICAL"
                elif total_count > 100:
                    severity = "HIGH"
                elif total_count > 20:
                    severity = "MODERATE"
                else:
                    # Still show even with low activity (ongoing conflicts)
                    severity = "LOW" if total_count > 0 else None

                if severity is None:
                    return None

                if severity_filter and severity != severity_filter:
                    return None

                return {
                    "id": f"gdelt_{crisis_info['region'].lower().replace(' ', '_')}",
                    "title": crisis_info["name"],
                    "location": crisis_info["region"],
                    "severity": severity,
                    "verification": "VERIFIED",
                    "type": crisis_info["type"],
                    "news_count": total_count,
                    "source": "GDELT News"
                }
            except Exception:
                return None

        crises = []
        async with aiohttp.ClientSession() as session:
            results = await asyncio.gather(
                *[fetch_single(session, c) for c in HUMANITARIAN_CRISES],
                return_exceptions=True
            )
            for r in results:
                if r and not isinstance(r, Exception):
                    crises.append(r)

        return crises

    async def _get_eonet_crises(
        self,
        severity_filter: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch natural disasters from NASA EONET."""
        # Request more events to compensate for filtering
        params = {"status": "open", "limit": min(limit * 3, 50)}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                NASA_EONET_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=SINGLE_REQUEST_TIMEOUT)
            ) as response:
                if response.status != 200:
                    return []
                data = await response.json()

        crises = []
        for event in data.get("events", []):
            title = event.get("title", "")
            title_lower = title.lower()

            # Filter out non-emergency events (prescribed burns, etc.)
            is_excluded = any(kw in title_lower for kw in EONET_EXCLUDE_KEYWORDS)
            if is_excluded:
                continue

            categories = event.get("categories", [])
            category_id = categories[0].get("id") if categories else "unknown"
            category_name = EONET_CATEGORY_NAMES.get(category_id, "Natural Event")
            severity = EONET_SEVERITY_MAP.get(category_id, "HIGH")

            if severity_filter and severity != severity_filter:
                continue

            geometry = event.get("geometry", [])
            location = "Unknown"
            if geometry:
                coords = geometry[-1].get("coordinates", [])
                if len(coords) >= 2:
                    location = self._coords_to_region(coords[1], coords[0])

            crises.append({
                "id": event.get("id", "unknown"),
                "title": title or "Unknown Event",
                "location": location,
                "severity": severity,
                "verification": "VERIFIED",
                "type": category_name,
                "news_count": 0,
                "source": "NASA EONET"
            })

        return crises

    def _coords_to_region(self, lat: float, lon: float) -> str:
        """Convert coordinates to region name."""
        if lat > 60:
            ns = "Arctic"
        elif lat > 23.5:
            ns = "Northern"
        elif lat > -23.5:
            ns = "Equatorial"
        else:
            ns = "Southern"

        if lon < -100:
            ew = "Pacific Americas"
        elif lon < -30:
            ew = "Americas"
        elif lon < 30:
            ew = "Africa/Europe"
        elif lon < 100:
            ew = "Asia"
        else:
            ew = "Pacific Asia"

        return f"{ns} {ew}"

    async def _get_local_crises(
        self,
        severity_filter: Optional[str],
        limit: int
    ) -> Dict[str, Any]:
        """Fetch crises from local JSON file (fast fallback)."""
        current_file = Path(__file__).resolve()
        project_root = current_file.parents[3]
        data_path = project_root / "backend_data" / "data.json"

        if not data_path.exists():
            return {"count": 0, "crises": [], "note": "No data available"}

        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            crises = data.get("crises", [])

            if severity_filter:
                crises = [c for c in crises if c.get("severity") == severity_filter]

            severity_order = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2, "LOW": 3}
            crises.sort(key=lambda x: severity_order.get(x.get("severity", "LOW"), 4))
            crises = crises[:limit]

            simplified = [{
                "id": c.get("id"),
                "title": c.get("title"),
                "location": c.get("location", {}).get("region"),
                "severity": c.get("severity"),
                "verification": c.get("verification", {}).get("status"),
                "type": "Humanitarian",
                "news_count": 0,
                "source": "GaiaLink Database"
            } for c in crises]

            return {
                "count": len(simplified),
                "crises": simplified,
                "sources": ["Local Database"],
                "note": "Cached crisis data."
            }

        except Exception as e:
            return {"count": 0, "crises": [], "error": str(e)}
