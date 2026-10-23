"""
Storyboard Engine (Section 14).
Converts scripts into precise scene-by-scene production instructions including camera angles,
audio/SFX timing, transitions, and AI video generation prompts.
"""

from typing import List, Dict, Any
from database.db import log_system_event


class StoryboardAgent:
    @staticmethod
    def generate_storyboard(
        script_data: Dict[str, Any],
        visual_style: str = "Cinematic 4K, high contrast lighting, subtle motion blur",
    ) -> List[Dict[str, Any]]:
        """
        Deconstructs script into sequential production scenes.
        """
        title = script_data.get("title", "Video Project")
        hook = script_data.get("hook", "")
        main_content = script_data.get("main_content", "")
        cta = script_data.get("cta", "")
        format_type = script_data.get("format", "Shorts")

        log_system_event("StoryboardAgent", f"Generating storyboard scenes for {title}")

        if format_type == "Shorts":
            scenes = [
                {
                    "scene_number": 1,
                    "duration": 3,
                    "visual_description": "Extreme close-up of host's expressive eyes reacting in disbelief to glowing screen.",
                    "camera": "Dynamic Push-In / Crash Zoom",
                    "character": "Lead Creator (focused, serious expression)",
                    "action": "Pointing aggressively at glowing floating holographic text.",
                    "dialogue_or_vo": hook,
                    "sfx": "Deep sub bass drop + subtle whoosh",
                    "music": "Fast-tempo mysterious synthwave intro",
                    "transition": "Quick Whip Pan",
                    "ai_video_prompt": f"Close-up intense cinematic portrait of a tech creator reacting to a glowing terminal screen, {visual_style}, 9:16 aspect ratio.",
                },
                {
                    "scene_number": 2,
                    "duration": 12,
                    "visual_description": "Clean split screen displaying step-by-step modular blocks snapping into place.",
                    "camera": "Medium Shot, fixed framing with moving digital overlays",
                    "character": "Host in bottom-right corner narrating",
                    "action": "Hands animating code structures that turn from red error state to green verified.",
                    "dialogue_or_vo": "Step 1: Strip away bloat. Step 2: Connect the ingestion pipeline directly.",
                    "sfx": "Mechanical click sounds on each block lock",
                    "music": "Driving rhythmic electronic beat",
                    "transition": "Digital Glitch Cut",
                    "ai_video_prompt": f"Futuristic UI interface elements snapping into place with glowing neon lines, {visual_style}, 9:16 vertical video.",
                },
                {
                    "scene_number": 3,
                    "duration": 8,
                    "visual_description": "Bold amber warning siren flashing as an animated barrier prevents a system crash.",
                    "camera": "Slight low-angle shot, rapid shake effect",
                    "character": "Host holding up stop-hand gesture",
                    "action": "Pointing at red alert sign labeled 'FATAL MISTAKE'",
                    "dialogue_or_vo": "Never deploy without automated fallback handling.",
                    "sfx": "Warning alarm beep + record scratch",
                    "music": "Bassline drops out briefly for dramatic silence",
                    "transition": "Hard Cut",
                    "ai_video_prompt": f"Dramatic amber warning lights pulsating across a high-tech studio workstation, {visual_style}, vertical framing.",
                },
                {
                    "scene_number": 4,
                    "duration": 7,
                    "visual_description": "Host smiling, pointing downward at comment section as prompt card pulses.",
                    "camera": "Medium Close-up, warm friendly lighting",
                    "character": "Lead Creator",
                    "action": "Tapping virtual floating button labeled 'TEMPLATE'",
                    "dialogue_or_vo": cta,
                    "sfx": "Sparkle chime + subscription notification bell",
                    "music": "Uplifting conclusion beat that loops seamlessly",
                    "transition": "Continuous Zoom into center to connect loop",
                    "ai_video_prompt": f"Charismatic creator pointing downwards in modern creator studio with soft backlighting, {visual_style}.",
                },
            ]
        else:
            # Long-form scenes
            scenes = [
                {
                    "scene_number": 1,
                    "duration": 15,
                    "visual_description": "Establish high production value studio. Host stands before large 85-inch digital blueprint display.",
                    "camera": "Slow cinematic dolly-in, 16:9 widescreen",
                    "character": "Lead Technical Presenter",
                    "action": "Walking into frame, touching display to activate complex architectural diagram.",
                    "dialogue_or_vo": hook,
                    "sfx": "High-tech hologram power-up hum",
                    "music": "Inspirational tech documentary ambient orchestral soundtrack",
                    "transition": "Smooth dissolve to screen share",
                    "ai_video_prompt": f"Cinematic wide shot of tech engineer presenting before a massive glowing digital workflow wall, {visual_style}, 16:9.",
                },
                {
                    "scene_number": 2,
                    "duration": 45,
                    "visual_description": "Direct screen capture with animated highlights and PiP host camera.",
                    "camera": "Screen recording with smooth zooms into critical lines of architecture",
                    "character": "Host in circular PiP frame in top-right corner",
                    "action": "Live demonstration of database initialization and metric tracking",
                    "dialogue_or_vo": "Notice how each module operates in total isolation from external API throttles.",
                    "sfx": "Soft keyboard clicks + subtle UI swooshes",
                    "music": "Muted background lo-fi focus beats",
                    "transition": "Slide Left",
                    "ai_video_prompt": f"Clean dark-mode software interface with glowing cyan data pipelines, {visual_style}.",
                },
            ]

        return scenes
