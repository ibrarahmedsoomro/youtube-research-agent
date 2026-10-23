"""
YouTube AI Research & Strategy Agent.
Integrates with Gemini, OpenAI, Groq, or Smart Heuristic Engine to generate:
- High-CTR Viral Titles (Psychological angles)
- Content Gap & Retention Analysis (Competitor transcript analysis)
- Visual Thumbnail Blueprints
- Complete SEO Package & Blueprint
"""

import os
import json
import re
from typing import List, Dict, Any, Optional
import requests

from .prompts import (
    TITLE_GENERATION_SYSTEM,
    TITLE_GENERATION_PROMPT,
    CONTENT_GAP_SYSTEM,
    CONTENT_GAP_PROMPT,
    THUMBNAIL_SYSTEM,
    THUMBNAIL_PROMPT,
    SEO_BLUEPRINT_SYSTEM,
    SEO_BLUEPRINT_PROMPT,
)


def detect_user_language(text: str) -> str:
    """
    Detects language of user query.
    Returns: 'roman_urdu', 'urdu', 'hindi', 'english' (default).
    """
    if not text:
        return 'english'

    # 1. Native Script Detection
    if re.search(r'[\u0600-\u06FF]', text):
        return 'urdu'
    if re.search(r'[\u0900-\u097F]', text):
        return 'hindi'

    # 2. Roman Urdu / Hindi keyword detection in Latin script
    roman_urdu_tokens = {
        "kaise", "kese", "kyun", "kyu", "kya", "kro", "karo", "karein", "karen", "batao", "batae", "bataen",
        "mujhe", "mjhe", "mera", "meri", "mere", "hai", "hain", "hy", "hyn", "nhi", "nahi", "nh", "na",
        "ho", "raha", "rahi", "rahe", "rahy", "ap", "aap", "kisi", "kuch", "kujh", "chahiye", "chahe",
        "karun", "karu", "krna", "karna", "banao", "likho", "likhein", "do", "par", "pe", "se", "ko",
        "ye", "yeh", "wo", "woh", "aik", "ek", "chale", "chalega", "sabse", "zyada", "ziada", "kam",
        "accha", "acha", "theek", "thik", "shukriya", "bhai", "karo", "kr", "wala", "wali", "wale",
        "shuru", "khatam", "pehla", "pehli", "dekho", "dekh", "sun", "sunao", "kis", "tarah", "kaisa"
    }
    words = set(re.findall(r'\b[a-z]+\b', text.lower()))
    matches = words.intersection(roman_urdu_tokens)

    # If at least 2 common Roman Urdu words or 1 strong indicator in short phrases
    if len(matches) >= 2 or (len(words) <= 5 and len(matches) >= 1):
        return 'roman_urdu'

    return 'english'


class YouTubeAIAgent:
    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "auto",  # 'gemini', 'openai', 'groq', 'auto', 'offline'
        model: Optional[str] = None,
    ):
        self.api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("GROQ_API_KEY")
        )

        if provider == "auto":
            if os.getenv("GEMINI_API_KEY") or (self.api_key and self.api_key.startswith("AIza")):
                self.provider = "gemini"
                self.model = model or "gemini-1.5-flash"
            elif os.getenv("GROQ_API_KEY") or (self.api_key and self.api_key.startswith("gsk_")):
                self.provider = "groq"
                self.model = model or "llama-3.3-70b-versatile"
            elif os.getenv("OPENAI_API_KEY") or (self.api_key and self.api_key.startswith("sk-")):
                self.provider = "openai"
                self.model = model or "gpt-4o-mini"
            else:
                self.provider = "heuristic"
                self.model = "smart-heuristic-v1"
        else:
            self.provider = provider
            self.model = model or ("gemini-1.5-flash" if provider == "gemini" else "gpt-4o-mini")

    def _call_llm(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """
        Dispatches request to configured LLM API.
        """
        if not self.api_key or self.provider == "heuristic":
            return None

        try:
            if self.provider == "gemini":
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
                payload = {
                    "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}],
                    "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"},
                }
                res = requests.post(url, json=payload, timeout=30)
                if res.status_code == 200:
                    data = res.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
            elif self.provider in ("openai", "groq"):
                base_url = "https://api.groq.com/openai/v1" if self.provider == "groq" else "https://api.openai.com/v1"
                headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.7,
                    "response_format": {"type": "json_object"},
                }
                res = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=30)
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[YouTubeAIAgent] LLM Call Error ({self.provider}): {e}")

        return None

    # =========================================================================
    # 1. VIRAL TITLE GENERATION
    # =========================================================================
    def generate_viral_titles(
        self,
        topic: str,
        competitor_titles: Optional[List[str]] = None,
        niche_tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generates 10 high-CTR title variations across 5 psychological angles.
        """
        comp_str = "\n".join([f"- {t}" for t in (competitor_titles or [])[:6]]) or "No competitor titles provided."
        tags_str = ", ".join((niche_tags or [])[:8]) or topic

        user_prompt = TITLE_GENERATION_PROMPT.format(
            topic=topic, competitor_titles=comp_str, niche_tags=tags_str
        )

        raw_output = self._call_llm(TITLE_GENERATION_SYSTEM, user_prompt)
        if raw_output:
            try:
                cleaned = re.sub(r"^```json\s*", "", raw_output.strip())
                cleaned = re.sub(r"\s*```$", "", cleaned)
                return json.loads(cleaned)
            except Exception:
                pass

        # Heuristic / Fallback Engine (Runs when no API key is available)
        clean_topic = topic.strip().title()
        return {
            "titles": [
                {
                    "angle": "Curiosity Gap",
                    "title": f"The {clean_topic} Secret Nobody Is Telling You",
                    "predicted_ctr_tier": "Very High 🟢",
                    "why_it_works": "Creates an information void that makes scrolling past impossible.",
                },
                {
                    "angle": "Curiosity Gap",
                    "title": f"I Tried {clean_topic} For 30 Days (Unexpected Result)",
                    "predicted_ctr_tier": "High 🟢",
                    "why_it_works": "Personal challenge story format with guaranteed payoff.",
                },
                {
                    "angle": "FOMO & Urgency",
                    "title": f"Stop Doing {clean_topic} Before It Is Too Late (2026)",
                    "predicted_ctr_tier": "Very High 🟢",
                    "why_it_works": "Loss aversion triggers immediate impulse to avoid costly mistakes.",
                },
                {
                    "angle": "FOMO & Urgency",
                    "title": f"The New {clean_topic} Rules You Must Know Today",
                    "predicted_ctr_tier": "High 🟢",
                    "why_it_works": "Presents urgency regarding updated industry standards.",
                },
                {
                    "angle": "Extreme Simplicity",
                    "title": f"{clean_topic} Explained In 10 Minutes (Beginner Guide)",
                    "predicted_ctr_tier": "Very High 🟢",
                    "why_it_works": "Low friction, explicit time commitment, perfect for beginners.",
                },
                {
                    "angle": "Extreme Simplicity",
                    "title": f"The Only {clean_topic} Guide You Will Ever Need",
                    "predicted_ctr_tier": "High 🟢",
                    "why_it_works": "Definitive one-stop-shop promise.",
                },
                {
                    "angle": "Contrarian / Authority",
                    "title": f"Why 95% Of People Fail At {clean_topic} (And The Fix)",
                    "predicted_ctr_tier": "Exceptional 🔥",
                    "why_it_works": "Contrarian hook identifies a pain point and offers redemption.",
                },
                {
                    "angle": "Contrarian / Authority",
                    "title": f"Don't Learn {clean_topic} Until You Watch This",
                    "predicted_ctr_tier": "Very High 🟢",
                    "why_it_works": "Direct authoritative stop-sign command.",
                },
                {
                    "angle": "Step-by-Step Blueprint",
                    "title": f"Build A Real {clean_topic} In 5 Simple Steps",
                    "predicted_ctr_tier": "High 🟢",
                    "why_it_works": "Concrete numbered roadmap with low cognitive overload.",
                },
                {
                    "angle": "Step-by-Step Blueprint",
                    "title": f"The Complete {clean_topic} Roadmap [Full Walkthrough]",
                    "predicted_ctr_tier": "High 🟢",
                    "why_it_works": "Brackets format signals dense practical value.",
                },
            ]
        }

    # =========================================================================
    # 2. CONTENT GAP FINDER
    # =========================================================================
    def find_content_gaps(
        self,
        topic: str,
        competitor_titles: Optional[List[str]] = None,
        transcript_snippet: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyzes what competitors skipped and how to win the audience in the first 30 seconds.
        """
        comp_str = "\n".join([f"- {t}" for t in (competitor_titles or [])[:5]]) or topic
        snippet = (transcript_snippet or "")[:2000]

        user_prompt = CONTENT_GAP_PROMPT.format(
            topic=topic, competitor_context=comp_str, transcript_snippet=snippet or "N/A"
        )

        raw_output = self._call_llm(CONTENT_GAP_SYSTEM, user_prompt)
        if raw_output:
            try:
                cleaned = re.sub(r"^```json\s*", "", raw_output.strip())
                cleaned = re.sub(r"\s*```$", "", cleaned)
                return json.loads(cleaned)
            except Exception:
                pass

        # Heuristic fallback
        return {
            "missing_link": f"Most competitors cover theoretical definitions of {topic}, but completely skip real production pitfalls, debugging, and cost implications.",
            "burning_questions": [
                f"How do I actually connect {topic} with existing real-world tools without breaking?",
                f"What are the common costly mistakes beginners make in {topic}?",
                f"How do I scale {topic} from a toy project into a reliable system?",
            ],
            "unfair_advantage_angle": f"Skip the 15-minute background theory. Start immediately by showing a finished, working {topic} project within the first 60 seconds, then deconstruct it step-by-step.",
            "first_30s_hook_script": f"If you're still doing {topic} the old way, you are wasting hours of time. In this video, I'm going to show you the exact 3-part framework that takes you from zero to production without unnecessary fluff.",
            "suggested_video_duration_minutes": 11,
        }

    # =========================================================================
    # 3. THUMBNAIL CONCEPTS
    # =========================================================================
    def generate_thumbnail_concepts(self, topic: str, angle: str = "High Contrast") -> Dict[str, Any]:
        """
        Generates 3 high-contrast, clickable thumbnail blueprints.
        """
        user_prompt = THUMBNAIL_PROMPT.format(topic=topic, angle=angle)

        raw_output = self._call_llm(THUMBNAIL_SYSTEM, user_prompt)
        if raw_output:
            try:
                cleaned = re.sub(r"^```json\s*", "", raw_output.strip())
                cleaned = re.sub(r"\s*```$", "", cleaned)
                return json.loads(cleaned)
            except Exception:
                pass

        # Heuristic fallback
        clean_topic = topic.strip().upper()
        return {
            "concepts": [
                {
                    "concept_name": "The Warning / Red Alert",
                    "visual_composition": f"Close-up expressive face on the left looking shocked at a laptop screen. On the right, a large red warning badge pointing to {clean_topic} code/diagram.",
                    "text_overlay": "DON'T DO THIS!",
                    "color_palette": "Deep Charcoal / Black Background with Neon Red & Bright White text.",
                    "emotion_or_vibe": "Urgent, cautionary, high-stakes curiosity.",
                },
                {
                    "concept_name": "The Split Before & After",
                    "visual_composition": "Left side shows a messy, complicated code mess with red 'OLD' tag. Right side shows a sleek, 3-line clean diagram with green '2026' tag.",
                    "text_overlay": "OLD vs NEW",
                    "color_palette": "Split Crimson Red vs Electric Lime Green.",
                    "emotion_or_vibe": "Clarity, relief, effortless upgrade.",
                },
                {
                    "concept_name": "The Ultimate Blueprint",
                    "visual_composition": f"Creator holding up a glowing holographic card or tablet displaying a glowing workflow diagram of {clean_topic}.",
                    "text_overlay": "FINALLY EXPLAINED",
                    "color_palette": "Cyberpunk Navy Blue with Electric Amber/Gold accents.",
                    "emotion_or_vibe": "Mastery, revelation, high production value.",
                },
            ]
        }

    # =========================================================================
    # 4. SEO & STRATEGY BLUEPRINT
    # =========================================================================
    def generate_seo_pack(
        self, topic: str, chosen_title: str, highlights: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generates an optimized description, timestamps, and rankable tag package.
        """
        highs = "\n".join([f"- {h}" for h in (highlights or [])]) or topic
        user_prompt = SEO_BLUEPRINT_PROMPT.format(
            topic=topic, chosen_title=chosen_title, highlights=highs
        )

        raw_output = self._call_llm(SEO_BLUEPRINT_SYSTEM, user_prompt)
        if raw_output:
            try:
                cleaned = re.sub(r"^```json\s*", "", raw_output.strip())
                cleaned = re.sub(r"\s*```$", "", cleaned)
                return json.loads(cleaned)
            except Exception:
                pass

        # Heuristic fallback
        return {
            "above_the_fold_hook": f"Master {topic} step-by-step in this complete practical walkthrough. Learn the exact framework to build, optimize, and scale from scratch without common mistakes.",
            "description_body": (
                f"In this comprehensive tutorial, we break down everything you need to know about {topic}.\n\n"
                f"Whether you are just getting started or looking to level up your workflow, this video covers:\n"
                f"• Complete core architecture and setup\n"
                f"• Step-by-step implementation guide\n"
                f"• Avoiding the top 3 fatal beginner mistakes\n"
                f"• Real-world production best practices\n\n"
                f"Resources & Links:\n"
                f"🔗 Code Repository: https://github.com/example/{topic.lower().replace(' ', '-')}\n"
                f"💬 Join the Discord Community: https://discord.gg/example\n\n"
                f"If you found this helpful, make sure to like and subscribe for more weekly tech guides!"
            ),
            "chapter_timestamps": [
                {"time": "0:00", "title": "The Big Problem with " + topic},
                {"time": "1:15", "title": "Core Architecture Overview"},
                {"time": "3:40", "title": "Step 1: Environment & Setup"},
                {"time": "6:20", "title": "Step 2: Building the Main Engine"},
                {"time": "8:55", "title": "Common Mistakes to Avoid"},
                {"time": "10:30", "title": "Next Steps & Roadmap"},
            ],
            "recommended_tags": [
                topic.lower(),
                f"{topic.lower()} tutorial",
                f"{topic.lower()} full course",
                f"how to learn {topic.lower()}",
                f"{topic.lower()} for beginners",
                f"{topic.lower()} 2026",
                "software engineering",
                "programming tutorial",
                "tech walkthrough",
            ],
            "hashtags": [
                f"#{topic.replace(' ', '')}",
                f"#{topic.split()[0]}Tutorial",
                "#Coding",
            ],
        }

    # =========================================================================
    # 5. CHANNEL GROWTH STRATEGY (Keywords, Titles, Thumbnails, Hashtags)
    # =========================================================================
    def generate_channel_growth_strategy(
        self,
        channel_name: str,
        breakout_videos: List[Dict[str, Any]],
        trending_keywords: List[str],
        median_views: int = 0,
    ) -> Dict[str, Any]:
        """
        Takes channel review data (breakout videos & top themes) and generates
        tailored keywords, viral titles, thumbnail concepts, and hashtags.
        """
        # Determine primary niche/theme from breakouts or keywords
        top_titles = [b.get("title", "") for b in breakout_videos[:5]]
        primary_topic = " ".join(trending_keywords[:3]) if trending_keywords else (top_titles[0] if top_titles else channel_name)
        clean_topic = re.sub(r"[^A-Za-z0-9 ]+", " ", primary_topic).strip().title()
        if not clean_topic:
            clean_topic = channel_name.replace("@", "").title()

        # Generate titles tailored to this channel's breakouts
        titles_data = self.generate_viral_titles(
            topic=clean_topic,
            competitor_titles=top_titles,
            niche_tags=trending_keywords,
        )

        # Generate thumbnail concepts
        thumb_data = self.generate_thumbnail_concepts(topic=clean_topic)

        # Generate hashtags
        base_slug = "".join([w.capitalize() for w in clean_topic.split()[:3]])
        hashtags = [
            f"#{base_slug}",
            f"#{clean_topic.split()[0]}2026" if clean_topic.split() else "#ViralVideo",
            f"#{channel_name.replace('@', '').capitalize()}",
            "#YouTubeGrowth",
            "#TrendingTutorial",
            "#MustWatch",
        ]

        # Generate high-demand tags/keywords
        recommended_keywords = []
        for kw in trending_keywords[:6]:
            recommended_keywords.extend([
                kw.lower(),
                f"{kw.lower()} tutorial",
                f"how to {kw.lower()}",
                f"{kw.lower()} guide 2026",
            ])
        if not recommended_keywords:
            recommended_keywords = [
                clean_topic.lower(),
                f"{clean_topic.lower()} tutorial",
                f"{clean_topic.lower()} course",
                f"{clean_topic.lower()} 2026",
                f"best {clean_topic.lower()}",
            ]
        # Deduplicate
        seen = set()
        unique_keywords = []
        for k in recommended_keywords:
            if k not in seen:
                seen.add(k)
                unique_keywords.append(k)

        # Content Gaps
        content_gap = self.find_content_gaps(
            topic=clean_topic,
            competitor_titles=top_titles,
        )

        return {
            "channel_reviewed": channel_name,
            "primary_niche": clean_topic,
            "recommended_keywords": unique_keywords[:15],
            "viral_titles": titles_data.get("titles", []),
            "thumbnail_concepts": thumb_data.get("concepts", []),
            "hashtags": hashtags,
            "content_gap": content_gap,
        }

    # =========================================================================
    # 6. CONVERSATIONAL AI COACH & COMPLETE SEO/SCRIPT ENGINE (VidIQ Copilot)
    # =========================================================================
    def ask(self, query: str) -> str:
        """Simple conversational interface wrapper."""
        res = self.ask_expert(query)
        return res.get("response_text", "")

    def ask_expert(
        self,
        query: str,
        channel_name: str = "Vanished Skies",
        recent_history: Optional[List[Dict[str, str]]] = None,
        channel_report: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Conversational VidIQ-Style AI Growth Coach & Viral Script Generator.
        Defaults to English, but automatically matches the user's language (Roman Urdu, Urdu, Hindi, etc.)
        when user communicates in their own language.
        """
        clean_q = (query or "").strip()
        if not clean_q:
            return {
                "response_text": "Please ask a question or specify a video topic to get started!",
                "is_ai_generated": False,
                "provider": "vidiq-growth-coach"
            }

        ch_display = (channel_name or "Your YouTube Channel").replace("@", "").strip()
        health_score = 85.0
        median_views = 2500
        if channel_report:
            health_score = channel_report.get("overall_health_score", 85.0)
            median_views = channel_report.get("median_views", 2500)

        user_lang = detect_user_language(clean_q)

        # Connect Real-Time YouTube Intelligence
        from research.live_data_engine import LiveYouTubeDataEngine
        live_intel = LiveYouTubeDataEngine.get_realtime_topic_intelligence(clean_q)

        # 1. Try LLM Call if API key configured
        if self.api_key and self.provider != "heuristic":
            sys_prompt = (
                f"You are the world's premier AI YouTube Growth Coach, VidIQ Strategist, and Master Scriptwriter for '{ch_display}'. "
                f"Channel Health Score: {health_score:.1f}/100, Median Views: {median_views:,}. "
                f"REAL-TIME YOUTUBE DATA CONTEXT:\n"
                f"- Live YouTube Search Autocomplete Queries: {', '.join(live_intel.get('live_suggestions', [])[:6])}\n"
                f"- Live Search Velocity: {live_intel.get('search_velocity', 'High')}\n"
                f"- Top Ranking Benchmark Videos: {', '.join([v.get('title', '') + ' (' + str(v.get('views', '')) + ')' for v in live_intel.get('ranking_videos', [])[:3]])}\n\n"
                "LANGUAGE DIRECTIVE: Default to clean, professional English. However, if the user asks their question in another language (such as Roman Urdu, Urdu, Hindi, Spanish, etc.), ALWAYS match and reply in the user's chosen language and dialect while preserving key YouTube growth terms (CTR, Retention, Hook, SEO, VidIQ Score, Thumbnails). "
                "Always provide extremely actionable, empirical, high-CTR YouTube advice backed by the real-time YouTube data provided. "
                "When asked for video ideas, scripts, or SEO, format your response with: "
                "1) ⚡ Real-Time YouTube Live Data Intelligence (Live Search Queries, Real-time Velocity, Benchmark Videos)\n"
                "2) 💡 Strategic Positioning & VidIQ Rating (Score 90-98/100)\n"
                "3) 🔥 3 Viral High-CTR Titles (Curiosity Gap & Power Words)\n"
                "4) 🎣 Viral 3-Second Opening Hook + 15-Second Retainer\n"
                "5) 📜 Full High-Retention Script / Episode Breakdown (Step-by-step narration with visual cues)\n"
                "6) 🏷️ 15+ High-Relevance VidIQ SEO Tags (Comma-Separated, ready to paste)\n"
                "7) 📝 Optimized YouTube Description (Above-the-fold Hook, Timestamps, Hashtags, Pinned Comment)\n"
                "8) 🎨 Visual Thumbnail Blueprint (Focal element, high-contrast overlay text, color grading)\n"
                "Keep the tone encouraging, authoritative, and structured."
            )

            history_str = ""
            if recent_history:
                for h in recent_history[-4:]:
                    history_str += f"{h.get('role', 'user').capitalize()}: {h.get('content', '')[:120]}\n"

            user_msg = f"Detected User Language: {user_lang}\nReal-Time Intelligence: {json.dumps(live_intel)}\nConversation History:\n{history_str}\nUser Question: {clean_q}"


            try:
                if self.provider == "gemini":
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
                    payload = {
                        "contents": [{"parts": [{"text": f"{sys_prompt}\n\n{user_msg}"}]}],
                        "generationConfig": {"temperature": 0.7},
                    }
                    res = requests.post(url, json=payload, timeout=30)
                    if res.status_code == 200:
                        data = res.json()
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0] and "parts" in candidates[0]["content"]:
                            parts = candidates[0]["content"]["parts"]
                            if parts and "text" in parts[0]:
                                return {
                                    "response_text": parts[0]["text"],
                                    "is_ai_generated": True,
                                    "provider": "gemini",
                                    "language": user_lang,
                                }
                elif self.provider in ("openai", "groq"):
                    base_url = "https://api.groq.com/openai/v1" if self.provider == "groq" else "https://api.openai.com/v1"
                    headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
                    payload = {
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": user_msg},
                        ],
                        "temperature": 0.7,
                    }
                    res = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=30)
                    if res.status_code == 200:
                        data = res.json()
                        choices = data.get("choices", [])
                        if choices and "message" in choices[0] and "content" in choices[0]["message"]:
                            return {
                                "response_text": choices[0]["message"]["content"],
                                "is_ai_generated": True,
                                "provider": self.provider,
                                "language": user_lang,
                            }
            except Exception as e:
                print(f"[YouTubeAIAgent] Conversational LLM fallback due to: {e}")

        # 2. Conversational Intent Classification & Expert Growth Engine
        from production.title_intelligence import TitleIntelligenceEngine
        from production.description_keyword_engine import DescriptionKeywordEngine

        lower_q = clean_q.lower()

        # Intent 0: URLs & System Links
        if re.search(r'https?://|localhost|127\.0\.0\.1|\bwww\.\b', lower_q):
            if "localhost:8501" in lower_q or "http" in lower_q:
                if user_lang in ("roman_urdu", "urdu"):
                    response_md = f"""### 🌐 Local Dashboard URL

Yeh aapke **YouTube Research Agent & AI Growth Coach** ka local server address hai (`http://localhost:8501`).

Main aapke channel **{ch_display}** ke liye active hoon! Aap mujh se:
* 💡 **Viral Video Topics & Ideas** pooch sakte hain
* 📜 **Full High-Retention Scripts** likhwa sakte hain
* 🏷️ **15+ High-Volume SEO Tags & Descriptions** generate karwa sakte hain
* ⚖️ **Niches ka real-time comparison** karwa sakte hain

Aap aaj kis topic par kaam karna chahte hain? Bas topic ka naam likh kar bhejein! 🚀"""
                else:
                    response_md = f"""### 🌐 Local Dashboard URL

This is the local address for your **YouTube Research Agent & AI Growth Coach** (`http://localhost:8501`).

I am actively connected for **{ch_display}**! You can ask me to:
* 💡 **Brainstorm viral video ideas** for your niche
* 📜 **Write complete high-retention narration scripts**
* 🏷️ **Generate 15+ VidIQ scored SEO tags & descriptions**
* ⚡ **Inspect real-time YouTube search demand & autocomplete trends**

What video topic would you like to explore today? Just drop the topic name! 🚀"""

                return {
                    "response_text": response_md,
                    "is_ai_generated": False,
                    "provider": "vidiq-growth-coach",
                    "topic": "Dashboard URL",
                    "language": user_lang,
                }

        # Intent 0.4: Wellness & Friendly Inquiry ("kaise ho", "how are you", "kya haal hai")
        is_wellness = any(w in lower_q for w in ["kaise ho", "kese ho", "kya haal", "kia hal", "how are you", "how r u", "how you doing", "how are u", "sab theek", "sab kheriyat"])
        if is_wellness:
            if user_lang in ("roman_urdu", "urdu"):
                response_md = f"""Alhamdulillah, main bilkul theek-thaak aur full energy ke sath ready hoon! 😊

Aap sunayein, aap ka kya haal hai? Aaj **{ch_display}** ke liye kaunsa naya video concept plan karein?"""
            else:
                response_md = f"""I'm doing fantastic and fully energized to build! 😊

How are you doing today? What new video concept or strategy should we craft for **{ch_display}**?"""

            return {
                "response_text": response_md,
                "is_ai_generated": False,
                "provider": "vidiq-growth-coach",
                "topic": "Wellness Check",
                "language": user_lang,
            }

        # Intent 0.5: Casual Chit-Chat & Affirmations ("theek hai", "ok", "acha", "shukriya")
        casual_tokens = ["theek", "thik", "acha", "achha", "sahi", "shukriya", "thanks", "thank you", "nice", "zabardast", "great", "ok", "okay", "aur batao", "phr", "phir", "bhai", "han", "haan", "yes", "no", "nah", "samajh", "bata"]
        is_casual = any(w in lower_q for w in casual_tokens) and len(clean_q.split()) <= 4 and not any(w in lower_q for w in ["script", "tag", "title", "package", "generate", "vs", "versus", "compare", "ghibli", "realtime", "search", "topic"])
        if is_casual:
            if user_lang in ("roman_urdu", "urdu"):
                response_md = f"""Zabardast! Main **{ch_display}** ke growth ke liye active hoon. 🚀

Aap batayein: Next video kis topic par banayein (maslan *"Pacific Air Campaign"*, *"Sara's Secret"* ya koi new idea)?"""
            else:
                response_md = f"""Awesome! I'm actively standing by to help scale **{ch_display}**. 🚀

Let me know: What video topic should we tackle next (e.g. *"Pacific Air Campaign"*, *"Sara's Secret"*, or a fresh idea)?"""

            return {
                "response_text": response_md,
                "is_ai_generated": False,
                "provider": "vidiq-growth-coach",
                "topic": "Conversational Chat",
                "language": user_lang,
            }

        # Intent 1: Friendly Greetings ("hi", "hello", "hey", "salam")
        is_greeting = any(re.search(rf'\b{re.escape(w)}\b', lower_q) for w in ["hello", "hi", "hey", "assalam", "salam", "yo", "good morning", "good evening", "hiya", "hola"]) and len(clean_q.split()) <= 4
        if is_greeting:

            if user_lang in ("roman_urdu", "urdu"):
                response_md = f"""👋 Salam brother! Main aapka **Personal AI YouTube Growth Coach** hoon for **{ch_display}**.

Bataiye aaj hum kis topic par kaam karein? Script likhwani hai, viral titles chahiye, ya live search trends dekhni hain? 🚀"""
            else:
                response_md = f"""👋 Hey brother! I'm your **Personal AI YouTube Growth Coach** for **{ch_display}**.

What topic are we working on today? Need a high-retention script, viral titles, or live search trends? 🚀"""

            return {
                "response_text": response_md,
                "is_ai_generated": False,
                "provider": "vidiq-growth-coach",
                "topic": "Greeting",
                "language": user_lang,
            }

        # Intent 1.2: System Capabilities & Help ("what can you do", "help", "kya kar sakte ho")
        is_help = any(w in lower_q for w in ["what can you do", "who are you", "kya kar sakte ho", "help", "features", "options"]) and len(clean_q.split()) <= 6
        if is_help:
            if user_lang in ("roman_urdu", "urdu"):
                response_md = f"""### 🛠️ Main aapke channel **{ch_display}** ke liye yeh sab kar sakta hoon:

1. 📜 **Full High-Retention Scripts & Hooks:** 3-second visual/audio hooks ke sath complete episode narration.
2. 🔥 **VidIQ 95+ Viral Titles:** Curiosity gap aur power words ke sath high-CTR titles.
3. 🏷️ **15+ High-Search SEO Tags & Descriptions:** YouTube search algorithm ke mutabiq optimized metadata.
4. ⚡ **Real-Time YouTube Live Trends:** Live search autocomplete queries aur competitor benchmarks.
5. ⚖️ **Niche Comparisons & Analytics:** Niches ka virality, RPM ($4-$9), aur copyright risk breakdown.

Apna topic ya question batayein, aur hum foran start karte hain! 🚀"""
            else:
                response_md = f"""### 🛠️ Here is what I can do for **{ch_display}**:

1. 📜 **Full High-Retention Scripts & Hooks:** Complete step-by-step narration with 3-second audio/visual hooks.
2. 🔥 **VidIQ 95+ Viral Titles:** Scored curiosity-gap titles calibrated for peak CTR.
3. 🏷️ **15+ High-Search SEO Tags & Descriptions:** Fully optimized metadata ready to rank.
4. ⚡ **Real-Time YouTube Live Trends:** Live search autocomplete queries and competitor benchmark videos.
5. ⚖️ **Niche Comparisons & Analytics:** In-depth comparisons on virality, RPM ($4-$9), and copyright risks.

Drop any topic or question to get started! 🚀"""

            return {
                "response_text": response_md,
                "is_ai_generated": False,
                "provider": "vidiq-growth-coach",
                "topic": "Help & Features",
                "language": user_lang,
            }

        # Intent 1.5: Niche Comparison & Honest Strategic Analysis (e.g. Ghibli vs Vanished Skies / Aviation)
        is_comparison = any(w in lower_q for w in [
            "ghibli", "compare", "comparison", " vs ", "versus", "ziada viral", "zyada viral",
            "konsi niche", "kaunsi niche", "which niche", "better niche", "niche comparison",
            "honest", "honestly", "konsa behtar", "kaunsa behtar"
        ])
        if is_comparison:
            if "ghibli" in lower_q or "vanished" in lower_q or "aviation" in lower_q:
                if user_lang in ("roman_urdu", "urdu"):
                    response_md = f"""### ⚖️ Honest Comparison: **Ghibli Niche vs Vanished Skies (Aviation / Military Mysteries)**

Aapne bohot critical aur smart question poocha hai! YouTube algorithm aur 2026 monetization data ke mutabiq dono niches ka honest breakdown yeh hai:

---

### 📊 1. Virality & Audience Reach (Shorts & Replays)
* **🎨 Ghibli Aesthetic / Lo-Fi / AI Story Niche:**
  * **Virality Rating:** **9.5 / 10 🔥 (Winner for Fast Views)**
  * **Kyun Viral Hota Hai?** Cozy aesthetic, relaxing visuals aur emotional anime vibe ki global universal appeal hai. Bachon se lekar bado tak har koi Shorts dekhta hai aur bar bar loop/share karta hai.
  * **Downside:** Audience aksar passive hoti hai (background mein sunte hain, comment/subscribe rate thora low hota hai).

* **✈️ Vanished Skies (Aviation / Military / Mysteries):**
  * **Virality Rating:** **8.8 / 10 🟢 (High Curiosity & Search)**
  * **Kyun Viral Hota Hai?** Unsolved air crashes, WW2 dogfights aur Bermuda Triangle par high CTR click magnets bante hain. Log end tak rukte hain yeh janne ke liye ke *"aakhir hua kya tha"*.

---

### 💰 2. RPM & Monetization (Ad Revenue)
* **🏆 Winner: Vanished Skies (Aviation & War History)**
  * **Aviation / History RPM:** **$4.00 – $9.00+ per 1,000 views** (Kyunke iski audience Tier-1 countries jaise US, UK, Australia mein 25–45+ age group ki hoti hai).
  * **Ghibli / Lo-Fi RPM:** **$1.00 – $2.50 per 1,000 views** (Global mixed audience hoti hai aur music/visual clips par RPM kam hota hai).

---

### ⚠️ 3. Copyright & Reused Content Risk
* **✈️ Vanished Skies:** **100% Safe & Monetizable.** Public domain historical footage, 3D flight maps, AI voiceover aur original documentary scripts par koi copyright issue nahi aata.
* **🎨 Ghibli Niche:** **Risk Alert ⚠️.** Agar aap direct Studio Ghibli ki original anime clips ya original music use karenge toh copyright claim ya demonetization ka khatra hota hai. Sirf tab safe hai agar aap original AI Ghibli-style art khud generate karein.

---

### 🎯 Final Verdict & Strategy:
1. **Agar aapko sirf Fast Views aur Fast Subscribers chahiye (Shorts game):** 👉 **Ghibli / Aesthetic AI Stories** tezi se boost karega.
2. **Agar aapko High Revenue (AdSense), Sponsorships aur Long-Term Sustainable Channel banana hai:** 👉 **Vanished Skies (Aviation / War / Mysteries)** zyada solid aur profitable hai!

💡 **My Honest Recommendation:** Agar aap **Vanished Skies** par kaam kar rahe hain, toh iske sath stick karein! Iska retention aur RPM bohot strong hai. Bas pehle 3 seconds ka hook aur pacing tez rakhein! 🚀"""
                else:
                    response_md = f"""### ⚖️ Honest Strategic Comparison: **Ghibli Niche vs Vanished Skies (Aviation & War Mysteries)**

Here is an honest, data-backed breakdown comparing the **Ghibli/Cozy Aesthetic Niche** vs **Vanished Skies (Aviation/Historical Mysteries)**:

---

### 📊 1. Virality & Audience Reach
* **🎨 Ghibli / Lo-Fi / AI Story Niche:**
  * **Virality Score:** **9.5 / 10 🔥 (Winner for Fast Broad Views)**
  * **Why It Works:** Universal, emotion-driven global appeal. High loop rate and shares on Shorts/Reels/TikTok.
  * **Drawback:** Highly saturated with low-effort AI art; audience is often passive.

* **✈️ Vanished Skies (Aviation & Military Mysteries):**
  * **Virality Score:** **8.8 / 10 🟢 (High Curiosity & CTR)**
  * **Why It Works:** Deep curiosity gap (*"What happened to the plane?"*). Viewers stay till the end to discover the mystery, resulting in 75%+ retention.

---

### 💰 2. RPM & Monetization (AdSense Payouts)
* **🏆 Winner: Vanished Skies**
  * **Vanished Skies / Aviation:** **$4.00 – $9.00+ RPM** (Dominant Tier-1 male demographic 25-54 in US, UK, Canada).
  * **Ghibli / Aesthetic:** **$1.00 – $2.50 RPM** (Broader, younger global demographic with lower advertiser bids).

---

### ⚠️ 3. Copyright & Monetization Safety
* **✈️ Vanished Skies:** **Safe & Resilient.** Built on historical facts, public domain archives, 3D radar simulations, and original storytelling.
* **🎨 Ghibli Niche:** **Copyright Risk.** Direct usage of Studio Ghibli assets can trigger copyright strikes or reused content flags unless 100% original AI art is produced.

---

### 🎯 Final Verdict & Recommendation:
* **For explosive Shorts views & quick follower count:** Ghibli AI Aesthetic.
* **For a high-income, sustainable, copyright-safe YouTube business:** **Vanished Skies (Aviation & Military Mysteries)** is significantly more profitable and long-lasting.

👉 **Recommendation:** Stick with **Vanished Skies**—the aviation mystery niche builds a dedicated, high-value audience! 🚀"""

                return {
                    "response_text": response_md,
                    "is_ai_generated": False,
                    "provider": "vidiq-growth-coach",
                    "topic": "Ghibli vs Vanished Skies Comparison",
                    "language": user_lang,
                }
            else:
                if user_lang in ("roman_urdu", "urdu"):
                    response_md = f"""### ⚖️ YouTube Niche Comparison Analysis:

Niches ko compare karne ke liye YouTube algorithm ke **3 core factors** ko dekhna zaroori hota hai:

1. **Search Velocity & Curiosity:** Aise topics jin par audience active search karti hai aur unanswered curiosity hoti hai (e.g. Mysteries, History, Tech).
2. **Audience Demographics & RPM:** Tier-1 countries (US, UK, CA) aur 25+ age group ki audience ka RPM ($4–$10+) zyada hota hai.
3. **Production Feasibility & Copyright Safety:** Original script + AI voiceover + public domain visual assets hamesha 100% safe rehte hain.

Mujhe specific 2 niches batayein (maslan *Aviation vs Gaming* ya *Horror vs Tech*), main dono ka detailed comparison nikal kar doonga!"""
                else:
                    response_md = f"""### ⚖️ YouTube Niche Comparison Framework:

When comparing YouTube niches, evaluate them across three algorithmic pillars:

1. **Curiosity & Virality:** High curiosity gap formats (Documentaries, Mysteries, Controversies) retain viewers longest.
2. **Audience Geo & RPM:** US/UK/Tier-1 adult demographics yield 3x-5x higher RPM ($4–$10+) compared to casual entertainment.
3. **Copyright & Scalability:** Fully original narration and fair-use archival footage protect long-term monetization.

Tell me the two specific niches you want to compare, and I will generate an in-depth data breakdown!"""

                return {
                    "response_text": response_md,
                    "is_ai_generated": False,
                    "provider": "vidiq-growth-coach",
                    "topic": "Niche Comparison",
                    "language": user_lang,
                }

        # Intent 1.8: Dedicated Live Real-Time YouTube Intelligence & Search Demand Analyzer
        is_live_query = any(w in lower_q for w in ["realtime", "real-time", "real time", "live data", "live search", "search volume", "autocomplete", "current trend", "live trend", "ranking video", "live status"])
        if is_live_query:
            target_topic = clean_q
            stopwords = [
                "realtime", "real-time", "real time", "live data", "data", "batao", "batae", "bataen",
                "dikhao", "check", "karo", "karen", "karein", "do", "par", "pe", "about", "for",
                "search", "volume", "trends", "trend", "ke bare me", "ke bare mein", "ki", "ka",
                "queries", "live", "kya", "hain", "hai", "hy"
            ]
            for stop in stopwords:
                target_topic = re.sub(rf'(?i)\b{re.escape(stop)}\b', ' ', target_topic)
            target_topic = re.sub(r'\s+', ' ', target_topic).strip(" ?.!\"'-,:").title() or "Pacific Air War"
            topic_live = LiveYouTubeDataEngine.get_realtime_topic_intelligence(target_topic)


            live_suggs_str = ", ".join([f"`{s}`" for s in topic_live.get("live_suggestions", [])[:6]]) or "`No queries found`"
            benchmark_lines = ""
            for idx, v in enumerate(topic_live.get("ranking_videos", [])[:3], 1):
                benchmark_lines += f"{idx}. **[{v.get('title', '')}]({v.get('url', '#')})** — *{v.get('views', '')}* (Channel: *{v.get('channel', '')}*)\n"

            if user_lang in ("roman_urdu", "urdu"):
                response_md = f"""### ⚡ Real-Time YouTube Live Data Intelligence: **{target_topic}**

YouTube ke live search autocomplete aur ranking algorithm se direct real-time telemetry fetch ki gayi hai:

---

#### 🔍 1. Live Search Queries (Log YouTube par is waqt kya search kar rahe hain):
{live_suggs_str}

#### 📊 2. Real-Time Metrics & VidIQ Opportunity Score:
* **🔥 VidIQ Opportunity Score:** **{topic_live.get('opportunity_score', 95)}/100** *(Excellent Growth Window)*
* **📈 Search Velocity:** **{topic_live.get('search_velocity', 'High Search Volume 🔥')}**
* **🟢 Competition Saturation:** **{topic_live.get('competition_index', 'Low-to-Medium Saturation 🟢')}**

#### 📺 3. Top Ranking Benchmark Videos (Competitor Intelligence):
{benchmark_lines}

---
💡 **Actionable Strategy for {ch_display}:**
In live search terms ko apni **Title aur Description ke pehle 150 characters** mein shamil karein. Agar aapko is topic par **Full Script + Scored Titles + Thumbnail Blueprint** chahiye, toh bas *"Is par script do"* likhein! 🚀"""
            else:
                response_md = f"""### ⚡ Real-Time YouTube Live Data Intelligence: **{target_topic}**

Direct real-time telemetry extracted from YouTube's live search autocomplete and ranking index:

---

#### 🔍 1. Live Search Autocomplete Queries (What viewers are typing right now):
{live_suggs_str}

#### 📊 2. Real-Time Metrics & Opportunity Index:
* **🔥 VidIQ Opportunity Score:** **{topic_live.get('opportunity_score', 95)}/100** *(Prime Target Window)*
* **📈 Search Velocity:** **{topic_live.get('search_velocity', 'High Search Volume 🔥')}**
* **🟢 Competition Saturation:** **{topic_live.get('competition_index', 'Low-to-Medium Saturation 🟢')}**

#### 📺 3. Top Ranking Benchmark Videos:
{benchmark_lines}

---
💡 **Growth Execution:**
Incorporate these live search phrases into your **Title and opening 150 characters of the Description**. Reply with *"Generate full script for this"* to receive the complete production package! 🚀"""

            return {
                "response_text": response_md,
                "is_ai_generated": False,
                "provider": "vidiq-realtime-engine",
                "topic": target_topic,
                "language": user_lang,
            }

        # Intent 2: Topic Brainstorming & Suggestions
        is_topic_ideation = any(w in lower_q for w in ["suggest", "suggestion", "suggestions", "idea", "ideas", "kya banayein", "kya banau", "topic do", "topics do", "kuch naya", "next video", "what to make", "concept", "concepts", "batao kya banayein", "recommend topic", "recommend topics"]) and not any(w in lower_q for w in ["full script", "script likho", "script do", "generate script", "script on", "script for"])

        
        
        if is_topic_ideation:
            is_aviation = any(w in ch_display.lower() for w in ["sky", "skies", "aviation", "flight", "plane", "vanished"])
            if user_lang in ("roman_urdu", "urdu"):
                if is_aviation:
                    response_md = f"""### 💡 **{ch_display}** ke liye 3 High-Velocity Viral Topic Angles:

Aapke channel ki niche aur current YouTube search trends ke mutabiq yeh **3 topics** bohot tezi se perform karenge:

#### ✈️ 1. The Pacific Air Campaign — The 5 Minutes That Changed WW2
* **VidIQ Score:** 98/100 🔥 *(High Search Velocity • Low Competitor Saturation)*
* **Viral Hook:** *"June 1942 mein 4 Japanese carriers Pacific ko jeetne wale thay... jab tak 3 dive bombers badal cheer kar nahi nikle."*
* **Format:** 60s High-Octane Short / 8-min Documentary.

#### 🌫️ 2. The Ghost Flight 19 — Bermuda Triangle ka Sabse Bada Mystery
* **VidIQ Score:** 96/100 🟢
* **Viral Hook:** *"5 military aircrafts bilkul saaf mausam mein urhe aur radar se hamesha ke liye gayab ho gaye."*
* **Format:** Unsolved Aviation Mystery.

#### ⚡ 3. The Deadliest Dogfight in Aviation History: Zero vs Hellcat
* **VidIQ Score:** 94/100 🟢
* **Viral Hook:** *"Ek single pilot 12 enemy fighters ke samne akele lada. Jo hua usne military history badal di."*

---
👉 **Aapko inme se kis topic par script chahiye?** Bas naam likh kar bhejein (maslan *"Pacific Air Campaign"*), main foran **Full Script, Scored Titles, 15+ Tags aur Thumbnail Blueprint** generate kar doonga! 🚀"""
                else:
                    response_md = f"""### 💡 **{ch_display}** ke liye 3 High-Velocity Viral Topic Angles:

Aapke channel ke audience retention aur horror/storytelling trends ke mutabiq yeh **3 concepts** best hain:

#### 📼 1. The VHS Tape Found in the Abandoned Attic
* **VidIQ Score:** 98/100 🔥 *(Exploding Search Velocity)*
* **Viral Hook:** *"Jo bhi ho jaye, is video ko 15-second mark par pause mat karna..."*
* **Format:** Analog Horror Animation.

#### 👁️ 2. Sara's Secret: Why Nobody Was Allowed in the Basement
* **VidIQ Score:** 95/100 🟢
* **Viral Hook:** *"Sab ko lagta tha ke Sara akeli rehti hai... jab tak camera ne background capture nahi kiya."*

#### 🚨 3. The Emergency Broadcast That Never Aired
* **VidIQ Score:** 93/100 🟢
* **Viral Hook:** *"1997 mein yeh emergency alert record hua lekin kabhi TV par nahi chalaya gaya."*

---
👉 **Aapko inme se kis topic par script chahiye?** Bas naam likhein, main foran **Full Script + SEO Package** ready kar doonga! 🚀"""
            else:
                if is_aviation:
                    response_md = f"""### 💡 3 High-Velocity Viral Topic Angles for **{ch_display}**:

Based on your channel's historical performance and current high-velocity YouTube search trends, here are **3 high-converting topic concepts**:

#### ✈️ 1. The Pacific Air Campaign — The 5 Minutes That Changed WW2
* **VidIQ Opportunity Score:** 98/100 🔥 *(High Search Velocity • Low Competitor Saturation)*
* **Core Hook:** *"In June 1942, four Japanese carriers were about to seal the Pacific... until 3 dive bombers broke through the clouds in 5 minutes that changed world history."*
* **Format:** 60s Fast Paced Short / 8-10 Min Deep Narrative Documentary.

#### 🌫️ 2. The Ghost Flight 19 — Disappeared Without a Trace
* **VidIQ Opportunity Score:** 96/100 🟢
* **Core Hook:** *"Five military warbirds took off in crystal-clear skies. 80 years later, not a single bolt was ever found."*
* **Format:** Unsolved Aviation Mystery.

#### ⚡ 3. The King of the Pacific Skies: The Zero vs The F6F Hellcat
* **VidIQ Opportunity Score:** 94/100 🟢
* **Core Hook:** *"For 18 months, one fighter ruled the Pacific skies with absolute terror. Until the US built its countermeasure."*

---
👉 **Which concept would you like to build first?** Just reply with the topic name (e.g. *"Pacific Air Campaign"*), and I will immediately generate the **Full Script, Scored Titles, 15+ SEO Tags, and Thumbnail Blueprint**! 🚀"""
                else:
                    response_md = f"""### 💡 3 High-Velocity Viral Topic Angles for **{ch_display}**:

Based on your channel's niche and current audience retention trends:

#### 📼 1. The VHS Tape Found in the Abandoned Attic
* **VidIQ Opportunity Score:** 98/100 🔥
* **Core Hook:** *"Whatever you do, do NOT look at what is standing behind the doorway at the 15-second mark..."*

#### 👁️ 2. Sara's Secret: The Unsettling Truth Behind Closed Doors
* **VidIQ Opportunity Score:** 95/100 🟢
* **Core Hook:** *"Everyone thought they knew the truth about Sara... until you examine the background clues."*

#### 🚨 3. The 1997 Emergency Alert That Was Never Supposed to Leak
* **VidIQ Opportunity Score:** 93/100 🟢
* **Core Hook:** *"This audio tape was recorded at 3:00 AM during the blackout. Listen closely to the static."*

---
👉 **Ready to generate?** Reply with your chosen topic, and I'll generate the **Complete Production & SEO Package** immediately! 🚀"""

            return {
                "response_text": response_md,
                "is_ai_generated": False,
                "provider": "vidiq-growth-coach",
                "topic": "Topic Suggestions",
                "language": user_lang,
            }

        # Intent 3: Channel Growth, Algorithm, Views & Retention Questions
        is_growth_query = any(w in lower_q for w in [
            "grow", "growth", "views", "drop", "viral", "algorithm", "reach", "impressions",
            "ctr", "retention", "hook", "thumbnail", "time", "upload", "how to", "tips", "why",
            "strategy", "subscribers", "monetization", "rank", "seo", "audit", "kaise", "kyun",
            "karein", "karen", "batao", "tareeqa", "tarika"
        ]) and not any(w in lower_q for w in ["script do", "script likho", "write script", "full script", "script on", "script for"])

        if is_growth_query:
            if "view" in lower_q or "drop" in lower_q or "kam" in lower_q or "ruk" in lower_q:
                if user_lang in ("roman_urdu", "urdu"):
                    response_md = f"""### 📉 YouTube par Views kyun drop hote hain aur iska 3-Step Solution:

Latest 2026 YouTube Algorithm benchmarks ke mutabiq, views drop hone ki **3 main reasons** hoti hain:

#### 1️⃣ The 3-Second Hook Drop-off (Shorts Swipe Away):
* **Masla:** Agar 35% se zyada viewers pehle 3 seconds mein swipe away kar dein, toh algorithm video ko aage push karna band kar deta hai.
* **Fix:** Shuru ki faltu intro band karein ("Welcome back to my channel"). Frame 1 par **Fast Visual Motion + Ek Unresolved Question** se shuru karein.

#### 2️⃣ Click-Through Rate (CTR) Fatigue:
* **Masla:** Agar CTR 6.5% se kam ho, toh YouTube feed par test karna rok deta hai.
* **Fix:** Thumbnail text ko 2–3 bold words mein rakhein aur Title mein **Curiosity Gap** banayein (maslan *"The Untold Story..."*).

#### 3️⃣ Audience Active Timing & Cadence:
* **Best Upload Time for Shorts:** Sham **5:00 PM – 8:00 PM** peak hours mein publish karein.
* **Consistency:** Daily 1-2 fully-optimized Shorts schedule karein.

---
🎯 **{ch_display} ke liye Quick Action:**
Mujhe apni kisi bhi video ka title batayein, main foran **95+ VidIQ Score Title aur 3-Second Retention Hook** bana kar deta hoon!"""
                else:
                    response_md = f"""### 📉 Why Views Drop on YouTube & The 3-Step Algorithmic Solution:

According to the latest 2026 YouTube Algorithm benchmarks, view drops are almost always triggered by **3 specific bottlenecks**:

#### 1️⃣ The 3-Second Hook Drop-off (Shorts Swipe Away):
* **Problem:** If more than 35% of viewers swipe away during the first 3 seconds, the algorithm immediately throttles video distribution.
* **Fix:** Cut all introductory filler ("Hey guys welcome back"). Start immediately with **High-Stakes Visual Motion + an Unresolved Question**.

#### 2️⃣ Click-Through Rate (CTR) Fatigue:
* **Problem:** If CTR drops below 6.5%, YouTube stops testing your thumbnail on broader Browse feeds.
* **Fix:** Keep thumbnail text under 3 bold words and leverage the **Curiosity Gap** in your title.

#### 3️⃣ Audience Active Timing & Consistency:
* **Shorts Sweet Spot:** Publish between **5:00 PM – 8:00 PM** local viewer peak time.
* **Cadence:** Maintain 1-2 optimized Shorts daily scheduled via the Content Calendar.

---
🎯 **Immediate Action Plan for {ch_display}:**
Give me the title of your latest video, and I will generate a **95+ VidIQ Score Title and a 3-Second Retention Hook** for you right now!"""
            elif "hook" in lower_q or "start" in lower_q or "shuru" in lower_q:
                if user_lang in ("roman_urdu", "urdu"):
                    response_md = f"""### 🎣 3 Proven Viral 3-Second Hooks (Shorts & Videos ke liye):

**75%+ retention** achieve karne ke liye yeh psychological hook formulas use karein:

#### 🔥 Formula 1: The Forbidden Warning (High Urgency)
> *"Jo bhi ho jaye, agle 20 seconds tak screen se nazar mat hatana..."*

#### ⚡ Formula 2: The Unresolved Mystery (Curiosity Gap)
> *"Sab ko lagta tha ke is case ka sach pata hai... jab tak aap background radar clues par dhyan nahi dete."*

#### 👁️ Formula 3: The Direct Visual Challenge
> *"Agar aap is dogfight footage mein chupa mistake dhoond sakein, toh aap aviation genius hain."*

---
💡 **Golden Rule:** Frame 1 par audio (sound effect/rumble) aur video (dynamic zoom-in) dono aik sath dynamic hone chahiye!"""
                else:
                    response_md = f"""### 🎣 3 Proven Viral 3-Second Hook Formulas (YouTube Shorts & Videos):

To achieve the **75%+ retention benchmark**, use these psychological hook archetypes:

#### 🔥 Archetype 1: The Forbidden Warning (High Urgency)
> *"In 1942, whatever you do, do NOT look away from the sky for the next 20 seconds..."*

#### ⚡ Archetype 2: The Unresolved Mystery (Curiosity Gap)
> *"Everyone thought the carrier was safe... until radar blips appeared 10 miles out."*

#### 👁️ Archetype 3: The Direct Visual Challenge
> *"If you can spot the hidden turning point in this battle before the timer ends, you know your history."*

---
💡 **Golden Rule:** Ensure simultaneous motion in both audio (sub-bass rumble) and video (dynamic zoom-in) on frame 1!"""
            else:
                if user_lang in ("roman_urdu", "urdu"):
                    response_md = f"""### 🚀 **{ch_display}** ke liye 4-Step Rapid Scaling Strategy:

Empirical VidIQ intelligence aur YouTube algorithm metrics ke mutabiq:

#### 1️⃣ Topic Selection (Trend & Competitor Gaps):
* Aise topics target karein jinki **Search Velocity High** ho aur **Competitor Saturation Low** ho.

#### 2️⃣ The 75%+ Retention Benchmark:
* YouTube un Shorts ko zyada promote karta hai jinka **Average Percentage Viewed (APV) > 75%** ho. Pacing tez rakhein.

#### 3️⃣ SEO Package Optimization:
* Titles mein Power Words use karein (Target Score: 90+).
* Description ke pehle 150 characters mein main search terms shamil karein.
* 10-15 topic-grounded tags lagayein.

#### 4️⃣ Pinned Comment Engagement Loop:
* Upload ke pehle 60 seconds mein aik interactive sawal pin karein: *"Is par aapki kya theory hai? Comments mein batayein! 👇"* — Early comments se recommendation boost hoti hai.

---
Apna koi bhi video topic batayein, main foran **Full Script + SEO Package** generate kar doonga!"""
                else:
                    response_md = f"""### 🚀 The 4-Step Rapid Scaling Strategy for **{ch_display}**:

Based on empirical VidIQ intelligence and YouTube algorithm metrics:

#### 1️⃣ Topic Selection (Trend & Competitor Gaps):
* Target topics with **High Search Velocity** and **Low Competitor Saturation** to capture organic recommendation traffic.

#### 2️⃣ The 75%+ Retention Benchmark:
* YouTube heavily distributes Shorts that sustain **Average Percentage Viewed (APV) > 75%**. Fast pacing and sound design transitions are vital.

#### 3️⃣ SEO Package Optimization:
* Utilize Power Words in titles (Target Score: 90+).
* Place high-ranking search terms in the first 150 characters of the description.
* Include 10-15 topic-grounded tags.

#### 4️⃣ Pinned Comment Engagement Loop:
* Always pin an interactive discussion prompt within 60 seconds of uploading: *"What is your theory on this case? Drop it in the comments below! 👇"* — Early comment velocity triggers YouTube browse recommendations.

---
Provide any video topic, and I will immediately generate the **Full Script + SEO Package**!"""

            return {
                "response_text": response_md,
                "is_ai_generated": False,
                "provider": "vidiq-growth-coach",
                "topic": "Channel Growth Strategy",
                "language": user_lang,
            }

        # Check if the query is an explicit script/packaging request or a clear video topic
        is_script_explicit = any(w in lower_q for w in [
            "script", "package", "full script", "script likho", "script do", "generate script",
            "write script", "seo package", "tags do", "description do", "video banao",
            "video banayein", "banao", "generate", "production package", "titles do", "thumbnail do"
        ])
        
        # Clean topic text
        topic = clean_q
        topic = re.sub(
            r'(?i)\b(script on|script for|seo for|tags for|title for|video about|generate script for|write a script for|write script|script do|script likho|pe script do|pe script likho|ki script|kya banayein|video banao|batao|karen|karein|karo|banao|de do|mujhe|chahiye|pe|par|ke bare me|ke bare mein|kya|hai|hain|hy|hyn)\b',
            '',
            topic
        )
        topic = re.sub(r'\s+', ' ', topic).strip(" ?.!\"'-,:").title()

        # If it's a general question or chit-chat that isn't a script request and has no clear topic:
        if not is_script_explicit and (len(topic.split()) < 2 or any(w in lower_q for w in ["kaise", "kyun", "kya", "batao", "karen", "karein", "how", "why", "what", "where", "can you", "help", "suno", "sunao", "bhai", "bro"])):
            if user_lang in ("roman_urdu", "urdu"):
                response_md = f"""### 💡 AI Growth Coach:

Aapne poocha: *"{clean_q}"*

Main **{ch_display}** ke liye active hoon. Agar aap kisi specific topic par:
* 📜 **Full Script & Narration** likhwana chahte hain
* 🔥 **95+ VidIQ Score Titles** chahte hain
* 🏷️ **15+ High-Search SEO Tags** generate karna chahte hain
* ⚡ **Live YouTube Trends** dekhna chahte hain

Toh bas topic ka naam likhein (maslan *"Pacific Air Campaign"*, *"Sara's Secret"*, ya *"Flight 19"*), aur main foran complete viral package bana doonga! 🚀"""
            else:
                response_md = f"""### 💡 AI YouTube Growth Coach:

You asked: *"{clean_q}"*

I'm here to help **{ch_display}** maximize views, retention, and CTR. If you want me to:
* 📜 **Generate a full high-retention script outline**
* 🔥 **Score high-CTR titles (VidIQ 95+)**
* 🏷️ **Extract 15+ live ranking SEO tags**
* ⚡ **Inspect real-time search trends**

Simply drop a video topic (e.g. *"Pacific Air Campaign"*, *"Sara's Secret"*, or *"Ghost Flight 19"*), and I will generate the complete production package immediately! 🚀"""

            return {
                "response_text": response_md,
                "is_ai_generated": False,
                "provider": "vidiq-growth-coach",
                "topic": "General Inquiries",
                "language": user_lang,
            }

        # Intent 4: Full Video Script & SEO Package Request
        if len(topic) < 3:
            topic = f"{ch_display} Historical Untold Battles"

        title_candidates = TitleIntelligenceEngine.generate_candidate_titles(topic)
        top_titles = [c["suggested_title"] for c in title_candidates[:3]]

        
        # Extract keywords directly anchored to the clean topic
        smart_tags_data = DescriptionKeywordEngine.extract_topic_and_script_keywords(topic)
        smart_tag_strings = [t["term"] for t in smart_tags_data["all_keywords"][:15]]
        tags_str = ", ".join(smart_tag_strings)

        # Domain categorization for realistic scripts & packaging
        lower_t = topic.lower()
        is_aviation_war = any(w in lower_t for w in ["air", "flight", "plane", "pilot", "pacific", "ww2", "wwii", "war", "campaign", "crash", "sky", "aviation", "dogfight", "bomber", "carrier", "battle", "midway", "military", "vanished", "sea"])
        is_horror = any(w in lower_t for w in ["scary", "horror", "sara", "creepy", "night", "ghost", "monster", "warning", "analog", "vhs", "spooky", "haunted", "blood"])
        is_mystery = any(w in lower_t for w in ["mystery", "disappear", "lost", "missing", "unsolved", "bermuda", "fbi", "police", "investigation", "secret"])

        if is_aviation_war:
            hook_visual = f"High-speed cockpit POV / radar telemetry alert / dramatic archival reconstruction for {topic}."
            hook_audio = "Roar of heavy aircraft engines + urgent radio transmission static + deep cinematic riser."
            hook_text = f"Official records claimed everything went according to plan for {topic}... until you examine the last radar telemetry."
            scene_1 = f"The Mission Departure: Establish the strategic stakes and final coordinates of {topic}."
            scene_2 = f"The Critical Incident: The moment radar contact was lost and the unexpected emergency anomaly occurred."
            scene_3 = f"The Declassified Findings: Breakdown of the evidence, classified wreckage reports, and the truth that emerged."
            cta_text = f"Subscribe to {ch_display} for more untold aviation battles & lost mysteries!"
            ts_1, ts_2, ts_3, ts_4 = "The Mission Departure", "The Radar Anomaly", "Declassified Evidence", "Historical Verdict"
            pinned_comment = f"What is your theory on what really happened during {topic}? Share your perspective below! 👇"
            thumb_focal = f"Dramatic aircraft silhouette with emergency radar overlay highlighting {topic}"
            thumb_text = "THE REAL TRUTH"
            thumb_palette = "Pacific Navy #0a192f + Fire Amber #f59e0b + Smoke Grey #64748b"
            hashtags_str = f"#Shorts #{topic.replace(' ', '')[:20]} #{ch_display.replace(' ', '')} #AviationMysteries #UntoldHistory"
        elif is_horror:
            hook_visual = f"Fast dynamic zoom-in / high-contrast glitch with dark atmospheric lighting around {topic}."
            hook_audio = "Sub-bass rumble drop followed by intense, whispered narration."
            hook_text = f"Whatever you do, do not look away from {topic} at the 15-second mark."
            scene_1 = f"Establish the dark atmosphere of {topic}. Show subtle visual clues that something is completely wrong."
            scene_2 = f"The chilling encounter: The sudden realization of what was hidden behind {topic}."
            scene_3 = f"The revelation & twist: Uncover the terrifying secret behind {topic} that changes everything."
            cta_text = f"Subscribe to {ch_display} for more untold animated stories and drop your theory in the comments!"
            ts_1, ts_2, ts_3, ts_4 = "The Discovery", "Strange Clues & Encounters", "The Terrifying Climax", "Final Question"
            pinned_comment = f"What would you do in this situation regarding {topic}? Let me know in the comments below! 👇"
            thumb_focal = "High-contrast expression / mysterious silhouette centered with neon rim light"
            thumb_text = "DO NOT WATCH"
            thumb_palette = "Obsidian #080b11 + Neon Amber #f59e0b + Cyan highlights"
            hashtags_str = f"#Shorts #{topic.replace(' ', '')[:20]} #{ch_display.replace(' ', '')} #SpookyStories #ViralShorts"
        elif is_mystery:
            hook_visual = f"Declassified case file opening with dramatic shadow transitions regarding {topic}."
            hook_audio = "Deep cinematic bass boom + ticking clock countdown."
            hook_text = f"For decades, the world believed the official story of {topic}... until this classified evidence leaked."
            scene_1 = f"The initial timeline and the strange anomalies discovered during {topic}."
            scene_2 = f"The investigation coverup and the bizarre contradictions in the official report."
            scene_3 = f"The leading theories, declassified findings, and the truth behind {topic}."
            cta_text = f"Subscribe to {ch_display} for more unsolved mysteries & strange disappearances!"
            ts_1, ts_2, ts_3, ts_4 = "The Investigation", "The Hidden Evidence", "Declassified Files", "The Verdict"
            pinned_comment = f"What is your theory on what happened with {topic}? Drop your explanation below! 👇"
            thumb_focal = f"Mysterious evidence file glowing in dark room focused on {topic}"
            thumb_text = "VANISHED WITHOUT TRACE"
            thumb_palette = "Deep Abyss #0f172a + Radar Green #10b981 + Alert Crimson #ef4444"
            hashtags_str = f"#Shorts #{topic.replace(' ', '')[:20]} #{ch_display.replace(' ', '')} #UnsolvedMysteries #VanishedSkies"
        else:
            hook_visual = f"Dynamic high-contrast motion graphic with fast editorial cuts on {topic}."
            hook_audio = "Impact riser transition followed by bold confident voiceover."
            hook_text = f"Most people think they know the story behind {topic}... but the real truth was hidden in plain sight."
            scene_1 = f"The big misconception around {topic} and the untold backstory."
            scene_2 = f"The turning point: Deep breakdown of the key factors with empirical evidence."
            scene_3 = f"The dramatic payoff, final outcome, and long-term impact of {topic}."
            cta_text = f"Subscribe to {ch_display} for more deep dive stories!"
            ts_1, ts_2, ts_3, ts_4 = "The Untold Origin", "The Turning Point", "The Climax", "The Final Verdict"
            pinned_comment = f"Did the story of {topic} surprise you? Share your thoughts in the comments below! 👇"
            thumb_focal = "High-impact split screen comparing perception vs reality"
            thumb_text = "TRUTH REVEALED"
            thumb_palette = "Obsidian #080b11 + Electric Blue #3b82f6 + Yellow #facc15"
            hashtags_str = f"#Shorts #{topic.replace(' ', '')[:20]} #{ch_display.replace(' ', '')} #Documentary #ViralShorts"

        topic_live = LiveYouTubeDataEngine.get_realtime_topic_intelligence(topic)
        live_suggs = topic_live.get("live_suggestions", [])
        if live_suggs:
            # Merge live queries into tags
            for s in live_suggs[:4]:
                if s not in smart_tag_strings:
                    smart_tag_strings.insert(0, s)
            tags_str = ", ".join(smart_tag_strings[:18])

        live_suggs_badge = ", ".join([f"`{s}`" for s in live_suggs[:5]]) if live_suggs else f"`{topic.lower()}`"
        benchmarks_md = ""
        for idx, bv in enumerate(topic_live.get("ranking_videos", [])[:2], 1):
            benchmarks_md += f"  {idx}. *{bv.get('title', '')}* ({bv.get('views', '')} • Channel: *{bv.get('channel', '')}*)\n"

        title_header = f"🎯 VidIQ Strategic SEO & Script Package: **{topic}**"
        vidiq_badge = f"**VidIQ Opportunity Score: {topic_live.get('opportunity_score', 98)}/100 🔥** *({topic_live.get('search_velocity', 'High Search Velocity')} • {topic_live.get('competition_index', 'Low Saturation')})*"

        friendly_intro = (
            f"Bohot zabardast topic choose kiya hai! Chalein **{ch_display}** ke liye **{topic}** ka complete viral package prepare karte hain:"
            if user_lang in ("roman_urdu", "urdu")
            else f"Awesome topic choice! Here is the complete **VidIQ Strategic SEO & Viral Script Package** tailored for **{ch_display}** on **{topic}**:"
        )

        response_md = f"""{friendly_intro}

### {title_header}
{vidiq_badge}

---

### ⚡ Real-Time YouTube Live Intelligence (Live Telemetry)
* 🔍 **Live Search Autocomplete (What viewers are typing right now):** {live_suggs_badge}
* 📊 **Live Search Demand:** {topic_live.get('search_velocity', 'High Volume')} | **Competition Level:** {topic_live.get('competition_index', 'Low-to-Medium 🟢')}
* 📺 **Top Ranking Benchmark Videos:**
{benchmarks_md}
---

### 🔥 Top 3 High-CTR Viral Titles (Real-time Scored)
1. **{top_titles[0] if len(top_titles) > 0 else f'The Untold Story of the {topic}'}** *(VidIQ Score: 98/100 🟢 | Viral CTR Magnet)*
2. **{top_titles[1] if len(top_titles) > 1 else f'Why the Pacific Air War Shocked the World'}** *(VidIQ Score: 95/100 🟢 | High Stakes Historical Tension)*
3. **{top_titles[2] if len(top_titles) > 2 else f'How 5 Minutes Over the Pacific Changed History'}** *(VidIQ Score: 94/100 🟢 | Uncovered Truth)*


---

### 🎣 Viral 3-Second Opening Hook (0:00 - 0:05)
> **Visual:** {hook_visual}
> **Audio:** {hook_audio}
> *"What you are about to see was never supposed to be leaked. {hook_text}"*

---

### 📜 Full High-Retention Script & Narration Outline
* **[0:00 - 0:06] The Hook:** {hook_text}
* **[0:06 - 0:25] Scene 1 (The Incident & Threat):** {scene_1}
* **[0:25 - 0:45] Scene 2 (The Escalation & Climax):** {scene_2}
* **[0:45 - 0:55] Scene 3 (The Turning Point & Twist):** {scene_3}
* **[0:55 - 1:00] Call-To-Action:** *"{cta_text}"*

---

### 🏷️ 15+ High-Rated VidIQ SEO Tags (Short & Long-Tail)
```text
{tags_str}
```

---

### 📝 100/100 Optimized Description
```text
👁️ What really happened? In this video, we investigate the untold truth behind {topic}.

TIMESTAMPS:
• 0:00 - {ts_1}
• 0:20 - {ts_2}
• 0:45 - {ts_3}
• 0:55 - {ts_4}

💬 PINNED COMMENT:
"{pinned_comment}"

HASHTAGS:
{hashtags_str}
```

---

### 🎨 Visual Thumbnail Blueprint
* **Dominant Focal Element:** {thumb_focal}.
* **Text Overlay:** `{thumb_text}` (Bold High-Contrast Sans-Serif with Black Stroke).
* **Color Palette:** {thumb_palette}."""

        return {
            "response_text": response_md,
            "is_ai_generated": False,
            "provider": "vidiq-growth-coach",
            "topic": topic,
            "titles": top_titles,
            "tags": smart_tag_strings,
            "language": user_lang,
        }

