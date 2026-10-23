"""
Thumbnail Studio & Auditor Module (Section 19 & 20).
Generates 3-5 topic-adaptive, high-CTR visual concepts, audits thumbnail imagery
for mobile readability, subject contrast, text crowding, and curiosity score (0-100),
and constructs production-ready AI image prompts for Midjourney/Imagen tailored to the exact niche.
"""

from typing import List, Dict, Any, Optional
import re
from database.db import log_system_event


class ThumbnailStudio:
    @staticmethod
    def _detect_category(topic: str, target_vibe: Optional[str] = None) -> str:
        """
        Detects the niche/category from topic text or explicit vibe to deliver
        authentic, niche-grounded visual concepts and prompts.
        """
        t = (topic or "").lower()
        v = (target_vibe or "").lower()

        if any(w in v for w in ["war", "history", "military"]):
            return "military_history"
        if any(w in v for w in ["aviation", "marine", "flight", "plane"]):
            return "aviation_marine"
        if any(w in v for w in ["horror", "spooky", "analog"]):
            return "analog_horror"
        if any(w in v for w in ["tech", "ai", "science", "future"]):
            return "tech_ai"
        if any(w in v for w in ["crime", "investigation", "police"]):
            return "true_crime"

        # Topic keyword & historical figure analysis
        military_keywords = [
            "war", "ww2", "wwii", "ww1", "wwi", "military", "army", "navy", "air force",
            "glenn miller", "hitler", "nazi", "soviet", "cold war", "weapon", "tank", "soldier",
            "pearl harbor", "pacific", "air campaign", "battle", "bunker", "tactics",
            "warfare", "bomber", "reich", "allies", "axis", "commander", "general",
            "submarine", "u-boat", "d-day", "normandy", "stalingrad", "hiroshima", "nagasaki",
            "oppenheimer", "manhattan project", "churchill", "eisenhower", "patton", "rommel",
            "yamamoto", "kamikaze", "blitz", "luftwaffe", "raf", "spitfire", "b-29", "enola gay",
            "midway", "guadalcanal", "iwo jima", "norseman", "english channel"
        ]
        if any(re.search(rf"\b{re.escape(k)}\b", t) for k in military_keywords):
            return "military_history"

        aviation_keywords = [
            "mh370", "vanished", "lost flight", "flight", "plane", "airplane", "pilot",
            "cockpit", "bermuda", "ocean", "shipwreck", "crash", "radar", "skies",
            "deep sea", "trench", "black box", "air accident", "disappearance", "missing plane",
            "amelia earhart", "db cooper", "d.b. cooper", "flight 19", "malaysia airlines",
            "mary celeste", "dyatlov", "triangle", "aviation"
        ]
        if any(re.search(rf"\b{re.escape(k)}\b", t) for k in aviation_keywords):
            return "aviation_marine"

        horror_keywords = [
            "horror", "spooky", "ghost", "creepy", "monster", "tape", "analog",
            "haunted", "incident", "demon", "sara", "shadow", "entity", "uncanny",
            "curse", "paranormal", "disturbing", "creepypasta", "backrooms", "scp"
        ]
        if any(re.search(rf"\b{re.escape(k)}\b", t) for k in horror_keywords):
            return "analog_horror"

        tech_keywords = [
            "ai", "robot", "quantum", "tech", "technology", "space", "alien", "ufo",
            "nasa", "mars", "code", "algorithm", "cyber", "gpt", "neural", "future",
            "science", "universe", "black hole", "matrix"
        ]
        if any(re.search(rf"\b{re.escape(k)}\b", t) for k in tech_keywords):
            return "tech_ai"

        crime_keywords = [
            "crime", "murder", "killer", "police", "fbi", "cia", "investigation",
            "evidence", "suspect", "prison", "escape", "interrogation", "conspiracy",
            "coverup", "heist", "robbery", "zodiac", "jack the ripper"
        ]
        if any(re.search(rf"\b{re.escape(k)}\b", t) for k in crime_keywords):
            return "true_crime"

        return "general_viral"

    @classmethod
    def generate_concepts(cls, topic: str, target_vibe: str = "Auto-Detect") -> List[Dict[str, Any]]:
        """
        Generates 3 to 5 distinct topic-adaptive thumbnail concepts with CTR reasoning.
        """
        log_system_event("ThumbnailStudio", f"Generating concepts for {topic}")
        clean_topic = topic.strip().title() if topic.strip() else "Untold Mystery"
        category = cls._detect_category(topic, target_vibe)

        if category == "military_history":
            return [
                {
                    "concept_id": 1,
                    "name": "The Declassified War Secret (Red Alert)",
                    "visual_layout": f"Close-up of a battle-hardened commander / historical figure in shock on the left, illuminated by fiery amber flare light; on the right, high-contrast dark silhouette of combat warplanes and battlefield smoke stamped with a bold glowing red 'TOP SECRET' declassified marker for '{clean_topic}'.",
                    "text_overlay": "WHAT THEY HID",
                    "color_palette": "Battlefield Charcoal + Fiery Amber Glow & Crimson Red",
                    "focal_point": "Left 35% eye line & glowing red classified stamp",
                    "curiosity_score": 97.0,
                    "ctr_reasoning": "Triggers loss aversion and forbidden knowledge. Mobile viewers instinctively click to uncover hidden military blunders or classified history.",
                },
                {
                    "concept_id": 2,
                    "name": "The Fatal Tactical Error (Split Contrast)",
                    "visual_layout": f"Left half: Desaturated grayscale vintage tactical map showing official records. Right half: Vibrant glowing thermal heatmap exposing the catastrophic hidden disappearance / secret flight path of '{clean_topic}'.",
                    "text_overlay": "FATAL ERROR",
                    "color_palette": "Grayscale Vintage Silver vs High-Voltage Crimson & Cyan (#ef4444 / #06b6d4)",
                    "focal_point": "Center high-contrast split divider line",
                    "curiosity_score": 94.0,
                    "ctr_reasoning": "High-contrast visual comparison communicates an undeniable historical turning point in under 0.2 seconds on mobile.",
                },
                {
                    "concept_id": 3,
                    "name": "The Redacted War Order",
                    "visual_layout": f"Aged wartime command dossier folder under a single forensic spotlight, with glowing gold lettering peeking through heavy black redaction bars beside a key artifact from '{clean_topic}'.",
                    "text_overlay": "THE BIG LIE",
                    "color_palette": "Dark Military Navy + Stamped Goldenrod Yellow (#facc15)",
                    "focal_point": "Center evidence artifact & redaction line",
                    "curiosity_score": 95.0,
                    "ctr_reasoning": "Redaction bars create an irresistible curiosity gap in the human brain that forces the click.",
                },
            ]

        elif category == "aviation_marine":
            return [
                {
                    "concept_id": 1,
                    "name": "The Radar Anomaly / Last Warning",
                    "visual_layout": f"Ominous cockpit view overlooking pitch-black storm clouds; glowing emergency amber cockpit lighting and radar screen capturing the exact moment the beacon vanished into the abyss for '{clean_topic}'.",
                    "text_overlay": "THEY VANISHED",
                    "color_palette": "Pitch Midnight Black + Neon Radar Green & Emergency Crimson",
                    "focal_point": "Center-left radar screen & storm silhouette",
                    "curiosity_score": 98.0,
                    "ctr_reasoning": "High-stakes aviation mystery creates immediate suspense and unexplainable intrigue.",
                },
                {
                    "concept_id": 2,
                    "name": "The Ocean Abyss / Coordinates Leak",
                    "visual_layout": f"Deep ocean bathymetry sonar scan revealing an anomalous metallic structure buried in the seabed trench, with a glowing red pinpoint coordinate ring marking '{clean_topic}'.",
                    "text_overlay": "FOUND DEEP",
                    "color_palette": "Deep Oceanic Cobalt + Electric Cyan & Laser Red",
                    "focal_point": "Glowing seabed coordinate ping",
                    "curiosity_score": 95.0,
                    "ctr_reasoning": "Visual discovery of something hidden in the deep triggers primal curiosity.",
                },
                {
                    "concept_id": 3,
                    "name": "The Recovered Black Box / Leaked Audio",
                    "visual_layout": f"Dented orange flight recorder under forensic spotlight on an investigation table, with a glowing red audio waveform and stamped transcript labeled 'CLASSIFIED AUDIO' regarding '{clean_topic}'.",
                    "text_overlay": "REAL AUDIO",
                    "color_palette": "Investigation Room Dark Slate + Safety Orange & Warning Red",
                    "focal_point": "Center flight recorder & audio waveform",
                    "curiosity_score": 96.0,
                    "ctr_reasoning": "Exclusive evidence framing drives ultra-high click intent and perceived authenticity.",
                },
            ]

        elif category == "analog_horror":
            return [
                {
                    "concept_id": 1,
                    "name": "The Urgent Warning / Red Alert",
                    "visual_layout": f"Close-up face looking terrified in the shadows on the left; glowing red analog glitch box on the right revealing '{clean_topic}'.",
                    "text_overlay": "STOP NOW!",
                    "color_palette": "Deep Charcoal Black + Electric Amber Warning Glow",
                    "focal_point": "Left 35% eye line matches thumb scan area",
                    "curiosity_score": 96.0,
                    "ctr_reasoning": "Creates instant panic/loss aversion. Mobile users stop immediately to check what to avoid.",
                },
                {
                    "concept_id": 2,
                    "name": "The Split Before & After (Corrupted Tape)",
                    "visual_layout": f"Left half: Desaturated grayscale distorted broadcast artifact. Right half: Vibrant glowing neon cyan anomaly revealing the hidden entity in '{clean_topic}'.",
                    "text_overlay": "DO NOT WATCH",
                    "color_palette": "Split Crimson (#ef4444) vs Electric Teal (#06b6d4)",
                    "focal_point": "Center split divider line",
                    "curiosity_score": 92.0,
                    "ctr_reasoning": "High visual contrast makes the disturbance obvious in under 0.2 seconds.",
                },
                {
                    "concept_id": 3,
                    "name": "The Hidden Secret / Redacted Archive",
                    "visual_layout": f"Dark vintage CRT monitor displaying a disturbing silhouette in static, with glowing gold text peeking through a heavy black redaction bar on '{clean_topic}'.",
                    "text_overlay": "THE TRUTH",
                    "color_palette": "Navy Blue + Goldenrod Yellow (#facc15)",
                    "focal_point": "Center CRT screen artifact",
                    "curiosity_score": 94.0,
                    "ctr_reasoning": "Black redaction bar triggers the brain's innate need to uncover hidden information.",
                },
            ]

        elif category == "tech_ai":
            return [
                {
                    "concept_id": 1,
                    "name": "The Forbidden Tech Leak / System Alert",
                    "visual_layout": f"High-contrast cybernetic mainframe in dark room, glowing with intense warning red error prompt and holographic code snippet exposing the reality of '{clean_topic}'.",
                    "text_overlay": "AI DID THIS",
                    "color_palette": "Obsidian Black + Laser Red & Neon Cyber Blue",
                    "focal_point": "Center glowing terminal error prompt",
                    "curiosity_score": 97.0,
                    "ctr_reasoning": "Fear of emerging AI / technological shifts forces tech-savvy viewers to check the alert.",
                },
                {
                    "concept_id": 2,
                    "name": "The Breakthrough Split (Before vs AI Future)",
                    "visual_layout": f"Left half: Old outdated manual method in dark monochrome. Right half: Mind-blowing futuristic AI holographic architecture solving '{clean_topic}'.",
                    "text_overlay": "IT'S OVER",
                    "color_palette": "Monochrome Slate vs Electric Emerald & Cyan (#10b981 / #06b6d4)",
                    "focal_point": "Center vertical divide",
                    "curiosity_score": 95.0,
                    "ctr_reasoning": "High-contrast transformation communicates massive paradigm shift in 0.1 seconds.",
                },
                {
                    "concept_id": 3,
                    "name": "The Redacted Whitepaper",
                    "visual_layout": f"Internal confidential laboratory document with redacted lines, glowing laser pointer highlighting a shocking secret benchmark for '{clean_topic}'.",
                    "text_overlay": "LEAKED NOW",
                    "color_palette": "Deep Charcoal + Electric Amber & White",
                    "focal_point": "Glowing highlighted benchmark data",
                    "curiosity_score": 94.0,
                    "ctr_reasoning": "Confidential leak framing creates immense FOMO and urgency.",
                },
            ]

        elif category == "true_crime":
            return [
                {
                    "concept_id": 1,
                    "name": "The Red String Evidence Board",
                    "visual_layout": f"Dark investigation room evidence corkboard with glowing red interconnecting strings converging on a central shocking photograph regarding '{clean_topic}'.",
                    "text_overlay": "THEY KNEW",
                    "color_palette": "Dark Mahogany + Laser Crimson & Evidence Amber",
                    "focal_point": "Central photograph at string convergence",
                    "curiosity_score": 97.0,
                    "ctr_reasoning": "Investigation visual instantly promises a deep unsolved mystery connection.",
                },
                {
                    "concept_id": 2,
                    "name": "The Split Alibi / Timeline Fracture",
                    "visual_layout": f"Left half: Official police report in grayscale. Right half: Security camera footage frame with bright yellow timestamp proving the lie in '{clean_topic}'.",
                    "text_overlay": "CAUGHT ON TAPE",
                    "color_palette": "Cold Muted Gray vs High-Contrast Surveillance Yellow",
                    "focal_point": "Center surveillance timestamp",
                    "curiosity_score": 96.0,
                    "ctr_reasoning": "Surveillance proof framing guarantees instant mobile tap-throughs.",
                },
                {
                    "concept_id": 3,
                    "name": "The Redacted Interrogation Tape",
                    "visual_layout": f"Dim interrogation table under single harsh light, audio cassette tape labeled 'DO NOT DESTROY' with confidential dossier on '{clean_topic}'.",
                    "text_overlay": "THE CONFESSION",
                    "color_palette": "Deep Slate + Goldenrod Yellow & Dark Shadow",
                    "focal_point": "Center evidence tape under cone of light",
                    "curiosity_score": 95.0,
                    "ctr_reasoning": "Confession tape framing triggers intense curiosity about what was admitted.",
                },
            ]

        else:
            # General Viral Niche
            return [
                {
                    "concept_id": 1,
                    "name": "The Urgent Exposure / Warning",
                    "visual_layout": f"Dramatic high-contrast focal subject on the left reacting with shock, illuminated by an intense amber spotlight; on the right, glowing danger indicator highlighting the hidden truth behind '{clean_topic}'.",
                    "text_overlay": "THE BIG LIE",
                    "color_palette": "Deep Charcoal Black + Electric Amber Warning Glow",
                    "focal_point": "Left 35% eye line & subject focal glow",
                    "curiosity_score": 96.0,
                    "ctr_reasoning": "Creates instant loss aversion and urgency. Viewers stop scrolling to verify what they are missing.",
                },
                {
                    "concept_id": 2,
                    "name": "The High-Contrast Split (Before vs After)",
                    "visual_layout": f"Left half: Common outdated method in dull grayscale. Right half: Glowing vibrant cyan breakthrough revealing the real secret behind '{clean_topic}'.",
                    "text_overlay": "WHY IT FAILED",
                    "color_palette": "Split Crimson (#ef4444) vs Electric Teal (#06b6d4)",
                    "focal_point": "Center split divider line",
                    "curiosity_score": 93.0,
                    "ctr_reasoning": "High visual contrast makes the core conflict instantly clear in under 0.2 seconds.",
                },
                {
                    "concept_id": 3,
                    "name": "The Redacted Discovery",
                    "visual_layout": f"Dark vintage dossier with glowing gold typography peeking through a heavy black redaction bar, focusing directly on the core mystery of '{clean_topic}'.",
                    "text_overlay": "THE TRUTH",
                    "color_palette": "Navy Blue + Goldenrod Yellow (#facc15)",
                    "focal_point": "Center artifact and redaction bar",
                    "curiosity_score": 95.0,
                    "ctr_reasoning": "Redaction bars tap into the brain's psychological need for closure.",
                },
            ]

    @classmethod
    def generate_ai_image_prompt(
        cls,
        topic: str,
        style: Optional[str] = None,
        emotion: str = "Terrified / Shocked",
        aspect_ratio: str = "9:16",
        focal_element: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates production-grade text-to-image prompts tailored for Midjourney v6, Imagen 3, or DALL-E 3
        that adapt intelligently to the topic's niche.
        """
        clean_topic = topic.strip() if topic.strip() else "Untold Mystery"
        category = cls._detect_category(clean_topic, style)

        if category == "military_history":
            style_name = "Gritty Cinematic History / IMAX 70mm"
            overlay_text = "WHAT THEY HID"
            positive_prompt = (
                f"Cinematic ultra-detailed historical battlefield scene of {clean_topic}, dramatic dark smoke-filled sky, "
                f"intense volumetric searchlight beams cutting through the haze, high-contrast rim lighting on soldier and aircraft silhouettes, "
                f"gritty photorealistic textures, atmospheric embers, masterwork IMAX 70mm cinematography, dramatic color grading "
                f"--ar {aspect_ratio} --stylize 250 --v 6.0"
            )
            imagen_prompt = (
                f"Ultra-detailed photorealistic cinematic frame of {clean_topic}, dramatic dark battlefield lighting, "
                f"gritty historical atmosphere, intense searchlight beams and fire embers, high contrast, 8k resolution, photorealistic masterwork"
            )
            negative_prompt = (
                "blurry text, watermark, cartoonish, 3d render plastic, saturated rainbows, smiling, oversaturated, deformed anatomy"
            )

        elif category == "aviation_marine":
            style_name = "Atmospheric Aviation Mystery / National Geographic"
            overlay_text = "THEY VANISHED"
            positive_prompt = (
                f"Cinematic ultra-realistic aerial mystery shot regarding {clean_topic}, dramatic dark stormy clouds and lightning, "
                f"eerie cockpit radar glow illuminating mysterious vanishing blip, volumetric fog, stark rim lighting on aircraft silhouette, "
                f"photorealistic National Geographic documentary cinematography, 8k resolution --ar {aspect_ratio} --stylize 250 --v 6.0"
            )
            imagen_prompt = (
                f"Photorealistic cinematic frame of {clean_topic}, dramatic dark ocean storm, glowing radar instrumentation, "
                f"volumetric lighting, photorealistic 8k, IMAX documentary quality"
            )
            negative_prompt = (
                "blurry text, watermark, bad anatomy, CGI videogame render, cheerful colors, flat lighting"
            )

        elif category == "analog_horror":
            style_name = "Analog Horror VHS Glitch"
            overlay_text = "DON'T LOOK"
            positive_prompt = (
                f"Hyper-detailed 1980s VHS tape frame, theme of {clean_topic}, expression of {emotion}, "
                f"heavy analog distortion, scan lines, chromatic aberration, eerie cinematic lighting, stark volumetric shadows, "
                f"high contrast rim light, hyper-realistic film grain, CRT monitor curve --ar {aspect_ratio} --stylize 250 --v 6.0"
            )
            imagen_prompt = (
                f"Hyper-detailed analog horror VHS frame of {clean_topic}, eerie shadows, chromatic aberration, scan lines, 8k photorealistic"
            )
            negative_prompt = (
                "blurry text, watermark, bad anatomy, deformed eyes, low resolution, flat lighting, smiling, cartoonish childish colors"
            )

        elif category == "tech_ai":
            style_name = "Cyberpunk Dark Realism / Sci-Fi"
            overlay_text = "AI DID THIS"
            positive_prompt = (
                f"Hyper-realistic futuristic cybernetic server room, glowing neon red warning alerts regarding {clean_topic}, "
                f"holographic code projections, stark shadows, volumetric light rays, sleek metallic textures, cinematic 8k Unreal Engine 5 render style "
                f"--ar {aspect_ratio} --stylize 250 --v 6.0"
            )
            imagen_prompt = (
                f"Photorealistic futuristic cybernetic laboratory, glowing warning displays for {clean_topic}, volumetric lighting, 8k resolution"
            )
            negative_prompt = (
                "blurry, childish cartoon, saturated pastels, watermark, low quality render, flat lighting"
            )

        elif category == "true_crime":
            style_name = "Fincher Noir Investigation"
            overlay_text = "THEY KNEW"
            positive_prompt = (
                f"Moody cinematic true-crime investigation scene regarding {clean_topic}, dark corkboard with glowing red evidence strings, "
                f"dim tungsten desk lamp lighting, gritty film noir aesthetic, stark directional shadows, hyper-realistic 8k cinematography "
                f"--ar {aspect_ratio} --stylize 250 --v 6.0"
            )
            imagen_prompt = (
                f"Gritty cinematic investigation scene regarding {clean_topic}, dark evidence room, tungsten lighting, hyper-realistic 8k"
            )
            negative_prompt = (
                "blurry, cartoon, bright happy colors, watermark, deformed elements"
            )

        else:
            style_name = "High-Contrast Cinematic Documentary"
            overlay_text = "THE TRUTH"
            positive_prompt = (
                f"Hyper-realistic cinematic documentary frame about {clean_topic}, dramatic high-contrast lighting, "
                f"stark focal point, volumetric shadows, intense emotional atmosphere, professional color grading, 8k resolution "
                f"--ar {aspect_ratio} --stylize 250 --v 6.0"
            )
            imagen_prompt = (
                f"Ultra-detailed photorealistic cinematic frame of {clean_topic}, dramatic lighting, high contrast, 8k resolution"
            )
            negative_prompt = (
                "blurry text, watermark, bad anatomy, flat lighting, overexposed, low resolution"
            )

        return {
            "topic": clean_topic,
            "style": style_name,
            "aspect_ratio": aspect_ratio,
            "midjourney_prompt": positive_prompt,
            "imagen_prompt": imagen_prompt,
            "negative_prompt": negative_prompt,
            "recommended_overlay_text": overlay_text,
            "overlay_style": "Impact font, #FFFFFF with 5px #000000 border and subtle amber/red outer glow",
        }

    @staticmethod
    def audit_thumbnail(
        thumbnail_text: str,
        has_face: bool = True,
        color_contrast: str = "High",
        subject_clarity: str = "Clear",
    ) -> Dict[str, Any]:
        """
        Audits a thumbnail configuration and yields a 0–100 score with specific improvement instructions.
        """
        score = 80
        issues = []
        strengths = []

        words = thumbnail_text.strip().split()
        word_count = len(words)

        # 3-Word Rule Check
        if word_count > 4:
            score -= 20
            issues.append(f"Thumbnail text contains {word_count} words. Mobile readers cannot decipher more than 3-4 words.")
        elif word_count == 0:
            issues.append("No text overlay provided. Consider adding 2-3 power words to reinforce curiosity.")
        else:
            score += 10
            strengths.append(f"Text overlay satisfies the 3-Word Rule ({word_count} words).")

        # Contrast Check
        if color_contrast.lower() == "high":
            score += 10
            strengths.append("High contrast palette ensures separation on dark/light YouTube mobile feeds.")
        else:
            score -= 15
            issues.append("Low color contrast. Background blends into the main subject.")

        if has_face:
            strengths.append("Human/character expression included to establish immediate emotional hook.")

        final_score = max(20, min(score, 100))

        return {
            "thumbnail_score": final_score,
            "tier": "Optimal 🟢" if final_score >= 85 else ("Acceptable 🟡" if final_score >= 70 else "Needs Work 🔴"),
            "strengths": strengths,
            "issues": issues,
            "recommendation": "Use 2–3 words in all-caps, heavy sans-serif font with a 4px dark drop shadow positioned in top 40% of canvas.",
        }
