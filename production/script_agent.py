"""
Script Generator Agent (Section 13).
Produces full production scripts with Hook, Intro, Main Content, Pattern Interrupts, CTA, Ending, and Seamless Loop.
Supports: 15s, 30s, 45s, 60s Shorts, and 3m, 5m, 10m, 15m Long-form.
"""

from typing import Dict, Any, Optional
from database.db import get_db, log_system_event
from database.models import Script
from .hook_agent import HookAgent


class ScriptAgent:
    @staticmethod
    def generate_script(
        topic: str,
        title: str,
        video_length: str = "60s",  # '15s', '30s', '45s', '60s', '3m', '5m', '10m', '15m'
        format_type: str = "Shorts",  # 'Shorts' or 'Long-form'
        tone: str = "Fast-Paced & Engaging",
        language: str = "English",
        custom_prompt_notes: str = "",
    ) -> Dict[str, Any]:
        """
        Generates a comprehensive, formatted production script.
        """
        log_system_event("ScriptAgent", f"Generating script for {title} ({video_length})")
        
        # Get tailored hook
        hooks = HookAgent.generate_hooks(topic, video_format=format_type)
        primary_hook = hooks[0]["hook_script"]

        if format_type == "Shorts":
            # Shorts script architecture
            intro = f"Most people waste weeks trying to figure this out on their own."
            main_content = (
                f"Here is the 3-step shortcut for {topic}:\n"
                f"1. First, strip away the bloated libraries. All you need is the core logic.\n"
                f"2. Second, connect your input pipeline directly to the execution loop.\n"
                f"3. Third, run verification checks after every single iteration."
            )
            pattern_interrupt = "[SFX: Record Scratch] But wait, do not make this fatal rookie mistake: never skip error handling!"
            cta = "Comment 'GUIDE' below and I'll send you the exact code template for free."
            ending = "And that is exactly why..."
            loop = "And that is exactly why... [Seamlessly connects back to hook: 'Whatever you do, DO NOT learn...']"
        else:
            # Long-form script architecture
            intro = (
                f"Welcome back. In today's deep dive, we are deconstructing {topic}. "
                f"By the end of this session, you'll have an end-to-end working system ready for deployment."
            )
            main_content = (
                f"SECTION 1: THE FOUNDATIONAL BLUEPRINT (0:45)\n"
                f"Before touching code, understand the architectural data flow. The biggest bottleneck in {topic} "
                f"is improper state persistence.\n\n"
                f"[PATTERN INTERRUPT: Pop sound + On-screen red warning graphic]\n\n"
                f"SECTION 2: STEP-BY-STEP IMPLEMENTATION (3:15)\n"
                f"Let's jump into the core engine. Notice how we decouple the processor from the ingestion layer. "
                f"This single architectural decision reduces runtime errors by 80%.\n\n"
                f"[PATTERN INTERRUPT: Screen zoom + B-Roll Demonstration]\n\n"
                f"SECTION 3: PRODUCTION HARDENING & EDGE CASES (7:20)\n"
                f"Now we test with edge cases. What happens when an external dependency times out? "
                f"Here is our automated retry fallback mechanism."
            )
            pattern_interrupt = "Visual B-roll cutaway every 25–40 seconds with text emphasis overlays and subtle sound whooshes."
            cta = "If you found this technical breakdown valuable, hit the subscribe button and download the repository in the description below."
            ending = "Leave your questions in the comments below, and I'll see you in the next masterclass."
            loop = "N/A (Long-form end screen video cards link to Part 2)"

        full_script = (
            f"=== SCRIPT: {title.upper()} ===\n"
            f"FORMAT: {format_type} ({video_length}) | TONE: {tone}\n\n"
            f"--- [0:00] HOOK ---\n{primary_hook}\n\n"
            f"--- INTRO ---\n{intro}\n\n"
            f"--- MAIN CONTENT ---\n{main_content}\n\n"
            f"--- PATTERN INTERRUPT ---\n{pattern_interrupt}\n\n"
            f"--- CTA ---\n{cta}\n\n"
            f"--- ENDING & LOOP ---\n{ending}\n"
            f"LOOP NOTE: {loop}\n"
        )

        # Persist to database
        try:
            with get_db() as db:
                script_rec = Script(
                    topic=topic,
                    title=title,
                    video_length=video_length,
                    format=format_type,
                    hook=primary_hook,
                    intro=intro,
                    main_content=main_content,
                    pattern_interrupts=pattern_interrupt,
                    cta=cta,
                    ending=ending,
                    loop_instruction=loop,
                    full_text=full_script,
                )
                db.add(script_rec)
        except Exception:
            pass

        return {
            "topic": topic,
            "title": title,
            "video_length": video_length,
            "format": format_type,
            "hook": primary_hook,
            "intro": intro,
            "main_content": main_content,
            "pattern_interrupts": pattern_interrupt,
            "cta": cta,
            "ending": ending,
            "loop_instruction": loop,
            "full_script": full_script,
        }
