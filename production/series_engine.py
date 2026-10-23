"""
Series & Lore Engine (Section 45 & 46).
Maintains episodic continuity, recurring character bibles, recurring locations,
and visual aesthetics (specifically optimized for Analog Horror, SpookyToons, Sci-Fi, and Web Series).
"""

import json
from typing import Dict, Any, List, Optional
from database.db import get_db, log_system_event
from database.models import SeriesLore


class SeriesEngine:
    @staticmethod
    def get_or_create_series(
        series_name: str,
        genre: str = "Analog Horror",
        lore_bible: str = "",
        characters: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        visual_style: str = "Creepy 1990s VHS cassette artifacts, scanlines, analog noise, eerie low-light lighting",
    ) -> Dict[str, Any]:
        """
        Retrieves existing series lore or registers a new story universe.
        """
        log_system_event("SeriesEngine", f"Loading series lore for {series_name}")
        
        with get_db() as db:
            existing = db.query(SeriesLore).filter(SeriesLore.series_name == series_name).first()
            if existing:
                return {
                    "id": existing.id,
                    "series_name": existing.series_name,
                    "genre": existing.genre,
                    "lore_bible": existing.lore_bible,
                    "characters": json.loads(existing.characters_json or "[]"),
                    "locations": json.loads(existing.locations_json or "[]"),
                    "visual_style": existing.visual_style,
                }

            # Create new series lore
            new_series = SeriesLore(
                series_name=series_name,
                genre=genre,
                lore_bible=lore_bible or f"The official continuous story bible for {series_name}.",
                characters_json=json.dumps(characters or ["Protagonist", "Antagonist / Entity"]),
                locations_json=json.dumps(locations or ["Main Setting", "Secret Chamber"]),
                visual_style=visual_style,
                rules_json=json.dumps(["Maintain chronological consistency", "End each episode with an unsolved question"]),
            )
            db.add(new_series)
            db.flush()

            return {
                "id": new_series.id,
                "series_name": new_series.series_name,
                "genre": new_series.genre,
                "lore_bible": new_series.lore_bible,
                "characters": characters or ["Protagonist", "Antagonist / Entity"],
                "locations": locations or ["Main Setting", "Secret Chamber"],
                "visual_style": visual_style,
            }

    @staticmethod
    def generate_episode_outline(
        series_name: str,
        episode_number: int,
        episode_title: str,
    ) -> Dict[str, Any]:
        """
        Generates an episode outline that strictly respects the series continuity and lore.
        """
        series_info = SeriesEngine.get_or_create_series(series_name)
        
        return {
            "series": series_name,
            "episode_number": episode_number,
            "episode_title": f"Episode {episode_number}: {episode_title}",
            "genre": series_info["genre"],
            "visual_style": series_info["visual_style"],
            "active_characters": series_info["characters"],
            "featured_location": series_info["locations"][0] if series_info["locations"] else "Primary Setting",
            "opening_hook": f"[EMERGENCY BROADCAST CHIME] This is a mandated warning regarding the events of Episode {episode_number - 1 if episode_number > 1 else 1}.",
            "narrative_twist": "The transmission breaks down halfway through to reveal a hidden coordinates message.",
            "cliffhanger": "A radio frequency suddenly matches the protagonist's personal voice recording.",
        }
