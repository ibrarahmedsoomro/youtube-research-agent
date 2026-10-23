"""
Structured Transcript Intelligence Engine (Tier 2 - Decision Layer).
Converts raw transcripts into structured narrative anatomy:
- Hook (0-15s): Type, Duration, Opening Line
- Promise & Setup (15-60s)
- Pattern Interrupts (Pacing & Reset Markers)
- Open Loops & Narrative Tension
- Key Claims & Named Entities
- Payoff & CTA Delivery
Aggregates cross-video patterns across top outliers.
"""

import re
from typing import Dict, Any, List, Optional
from scraper.models import VideoTranscript, VideoMetadata


class TranscriptIntelligenceEngine:
    """
    Decomposes raw subtitles and transcripts into narrative beats and retention levers.
    """

    @staticmethod
    def analyze_transcript(transcript: VideoTranscript, duration_seconds: int = 600) -> Dict[str, Any]:
        """
        Extracts structural anatomy and retention patterns from a single video transcript.
        """
        full_text = transcript.full_text or ""
        segments = transcript.segments or []
        
        if not full_text:
            return {
                "has_transcript": False,
                "confidence": "INSUFFICIENT",
                "hook": None,
                "promise": None,
                "pattern_interrupts_count": 0,
                "open_loops": [],
                "key_claims": [],
                "payoff": None,
            }

        # 1. Segment extraction by timestamp
        hook_segments = [s for s in segments if s.start < 15.0]
        promise_segments = [s for s in segments if 15.0 <= s.start < 60.0]
        end_threshold = max(0.0, float(duration_seconds) - 45.0) if duration_seconds > 60 else 45.0
        payoff_segments = [s for s in segments if s.start >= end_threshold]

        hook_text = " ".join([s.text for s in hook_segments]).strip() if hook_segments else full_text[:200]
        promise_text = " ".join([s.text for s in promise_segments]).strip() if promise_segments else full_text[200:600]
        payoff_text = " ".join([s.text for s in payoff_segments]).strip() if payoff_segments else full_text[-300:]

        # 2. Hook Classification
        hook_type, hook_explanation = TranscriptIntelligenceEngine._classify_hook(hook_text)

        # 3. Pattern Interrupt Detection
        interrupt_patterns = [
            r"\b(but here('?s| is) the (twist|thing|catch))\b",
            r"\b(what nobody (tells|told) you)\b",
            r"\b(look at this|watch this|notice this)\b",
            r"\b(suddenly|unexpectedly|without warning)\b",
            r"\b(however|in reality|the truth is)\b",
            r"\b(wait until you see|this is where it gets crazy)\b",
            r"\b(let me explain|here is why)\b",
        ]
        total_interrupts = 0
        found_interrupt_examples = []
        for pat in interrupt_patterns:
            matches = re.findall(pat, full_text, re.IGNORECASE)
            if matches:
                total_interrupts += len(matches)
                found_interrupt_examples.append(matches[0][0] if isinstance(matches[0], tuple) else matches[0])

        # 4. Open Loops Extraction (Questions & Unresolved Tension)
        open_loops = []
        sentences = re.split(r"[.!?]+", full_text[:1500])
        for s in sentences:
            s_clean = s.strip()
            if any(s_clean.lower().startswith(q) for q in ["why", "how", "what happened to", "who was", "where did"]):
                if len(s_clean) > 15:
                    open_loops.append(s_clean + "?")
            if len(open_loops) >= 3:
                break

        # 5. Key Claims & Dates Extraction
        key_claims = []
        date_matches = re.findall(r"\b(19\d{2}|20\d{2}|january|february|march|april|may|june|july|august|september|october|november|december)\b", full_text, re.IGNORECASE)
        stat_matches = re.findall(r"\b(\d+[%kKmMbB]?|\$\d+)\b", full_text)
        
        if date_matches:
            key_claims.append(f"Temporal Anchors: {', '.join(set(date_matches[:4]))}")
        if stat_matches:
            key_claims.append(f"Quantitative Data Points: {', '.join(set(stat_matches[:5]))}")

        return {
            "has_transcript": True,
            "confidence": "HIGH" if len(segments) > 10 else "MEDIUM",
            "hook": {
                "text": hook_text[:250],
                "type": hook_type,
                "duration_seconds": min(15.0, sum(s.duration for s in hook_segments)) if hook_segments else 12.0,
                "explanation": hook_explanation,
            },
            "promise": {
                "text": promise_text[:300],
            },
            "pattern_interrupts": {
                "count": total_interrupts,
                "pacing_rating": "Dynamic / Fast" if total_interrupts >= 5 else "Moderate" if total_interrupts >= 2 else "Linear / Steady",
                "sample_markers": found_interrupt_examples[:3],
            },
            "open_loops": open_loops,
            "key_claims": key_claims,
            "payoff_and_cta": {
                "text": payoff_text[:300],
            },
        }

    @staticmethod
    def _classify_hook(hook_text: str) -> (str, str):
        """Classifies the opening hook style."""
        h_lower = hook_text.lower()
        if any(h_lower.startswith(q) for q in ["why", "how", "what if", "have you ever"]):
            return "Curiosity Question Hook", "Opens with a provocative inquiry driving the viewer to seek the answer."
        elif any(w in h_lower for w in ["never", "impossible", "biggest mistake", "shocking", "banned", "secret"]):
            return "Bold Paradox / High-Stakes Claim", "Leverages contrast, controversy, or extreme stakes to freeze scrolling."
        elif any(w in h_lower for w in ["in 19", "in 20", "at 3am", "it was a quiet", "flight", "deep in"]):
            return "Story In Media Res", "Throws the viewer directly into the middle of an escalating scene or narrative."
        elif any(w in h_lower for w in ["in this video", "today i will show", "welcome back"]):
            return "Direct Proposition / Agenda", "Standard informational opening declaring the video's explicit agenda."
        return "Thematic Hook", "Sets an immediate thematic atmosphere before elaborating on the premise."

    @staticmethod
    def aggregate_outlier_patterns(transcript_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synthesizes common structural patterns across multiple high-performing outlier videos.
        """
        valid = [t for t in transcript_analyses if t.get("has_transcript")]
        if not valid:
            return {
                "analyzed_count": 0,
                "dominant_hook_type": "Insufficient Data",
                "avg_interrupts": 0.0,
                "top_recurring_themes": [],
            }

        hook_types = [t["hook"]["type"] for t in valid if t.get("hook")]
        dominant_hook = max(set(hook_types), key=hook_types.count) if hook_types else "Bold Claim"
        avg_interrupts = round(sum(t["pattern_interrupts"]["count"] for t in valid) / len(valid), 1)

        all_open_loops = []
        for t in valid:
            all_open_loops.extend(t.get("open_loops", []))

        return {
            "analyzed_count": len(valid),
            "dominant_hook_type": dominant_hook,
            "avg_pattern_interrupts": avg_interrupts,
            "common_open_loops": all_open_loops[:5],
            "structural_takeaway": f"Top outliers in this niche consistently rely on '{dominant_hook}' openings paired with ~{avg_interrupts} retention pattern interrupts.",
        }
