"""
Hook Generator Module (Section 12).
Generates high-retention opening hooks:
- Shorts: First 1-3 seconds curiosity triggers.
- Long-form: First 5-30 seconds open loops, stakes, and reasons to keep watching.
"""

from typing import List, Dict, Any


class HookAgent:
    @staticmethod
    def generate_hooks(
        topic: str,
        video_format: str = "Shorts",  # 'Shorts' or 'Long-form'
        tone: str = "Curiosity & High Stakes",
    ) -> List[Dict[str, Any]]:
        """
        Produces multi-angle retention hooks tailored to video format length.
        """
        clean_topic = topic.strip().title()

        if video_format == "Shorts":
            # 1-3 seconds hooks
            return [
                {
                    "angle": "The Immediate Stopping Shock",
                    "timing": "0:00 - 0:02",
                    "hook_script": f"Whatever you do, DO NOT learn {clean_topic} until you see this.",
                    "visual_action": "Violent zoom-in on face or sudden red warning badge on screen.",
                    "retention_score": 94.0,
                },
                {
                    "angle": "The Open Loop Question",
                    "timing": "0:00 - 0:03",
                    "hook_script": f"Why is nobody talking about this hidden trick in {clean_topic}?",
                    "visual_action": "Holding phone/screen partially obscured to force curiosity.",
                    "retention_score": 91.0,
                },
                {
                    "angle": "The Instant Proof Demonstration",
                    "timing": "0:00 - 0:02",
                    "hook_script": f"Watch this: in 3 seconds, {clean_topic} just did this...",
                    "visual_action": "Immediate before/after result screen before speaking.",
                    "retention_score": 96.0,
                },
                {
                    "angle": "The Costly Mistake Callout",
                    "timing": "0:00 - 0:03",
                    "hook_script": f"If your {clean_topic} looks like this, you are wasting 90% of your time.",
                    "visual_action": "Pointing at ugly/messy example with an animated red X.",
                    "retention_score": 89.0,
                },
            ]
        else:
            # Long-form 5-30 seconds hooks
            return [
                {
                    "angle": "The Stakes & Open Loop (Recommended)",
                    "timing": "0:00 - 0:15",
                    "hook_script": (
                        f"By the time you finish this video, you will be able to build a complete {clean_topic} "
                        f"from scratch. But if you skip step number two, your entire setup will fail within 48 hours. "
                        f"Here is the exact truth nobody wants to share..."
                    ),
                    "visual_action": "Show finished working production project immediately for 4 seconds, cut back to host.",
                    "retention_score": 95.0,
                },
                {
                    "angle": "The Contrarian Revelation",
                    "timing": "0:00 - 0:20",
                    "hook_script": (
                        f"95% of tutorials on {clean_topic} teach you methods that are completely obsolete in 2026. "
                        f"Today, I'm going to throw out the old playbook and show you the modern streamlined framework "
                        f"that actually works in production."
                    ),
                    "visual_action": "Tossing old papers/guides off screen, bringing up sleek modern diagram.",
                    "retention_score": 92.0,
                },
                {
                    "angle": "The 'I Failed So You Don't Have To' Story Hook",
                    "timing": "0:00 - 0:25",
                    "hook_script": (
                        f"Last month, I spent 120 hours attempting {clean_topic}. It was a total disaster until I discovered "
                        f"one counter-intuitive adjustment. In this video, I will save you weeks of frustration..."
                    ),
                    "visual_action": "Quick montage of failed attempts/terminal errors ending on glowing victory checkmark.",
                    "retention_score": 90.0,
                },
            ]
