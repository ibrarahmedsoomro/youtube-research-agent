"""
Provider Abstraction Architecture (Section 15 & 35).
Defines swappable adapter interfaces for Video Generation (Veo, Seedance, Mock)
and Voice/Audio Synthesis (ElevenLabs, EdgeTTS, System).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os


class BaseVideoProvider(ABC):
    @abstractmethod
    def generate_video_clip(self, prompt: str, duration_sec: int = 5, aspect_ratio: str = "16:9") -> Dict[str, Any]:
        pass


class VeoVideoProvider(BaseVideoProvider):
    """Google Veo Video Generation Provider Adapter."""
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("VEO_API_KEY") or os.getenv("GEMINI_API_KEY")

    def generate_video_clip(self, prompt: str, duration_sec: int = 5, aspect_ratio: str = "16:9") -> Dict[str, Any]:
        if not self.api_key:
            return {
                "status": "CONFIG_REQUIRED",
                "provider": "Google Veo",
                "message": "Veo API key not detected. Operating in simulated rendering preview mode.",
                "rendered_preview_url": f"https://placehold.co/1280x720/000/fff.png?text=Veo+Preview:+{prompt[:25]}...",
                "prompt": prompt,
                "duration": duration_sec,
            }
        # Production API invocation stub
        return {
            "status": "DISPATCHED",
            "provider": "Google Veo",
            "job_id": "veo_job_9921",
            "prompt": prompt,
            "duration": duration_sec,
        }


class SeedanceVideoProvider(BaseVideoProvider):
    """Seedance Video Generation Provider Adapter."""
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SEEDANCE_API_KEY")

    def generate_video_clip(self, prompt: str, duration_sec: int = 5, aspect_ratio: str = "16:9") -> Dict[str, Any]:
        return {
            "status": "READY_STUB",
            "provider": "Seedance AI",
            "message": "Seedance generation adapter initialized.",
            "prompt": prompt,
            "duration": duration_sec,
        }


class LocalMockVideoProvider(BaseVideoProvider):
    """Zero-cost local sandbox video provider for offline prototyping."""
    def generate_video_clip(self, prompt: str, duration_sec: int = 5, aspect_ratio: str = "16:9") -> Dict[str, Any]:
        return {
            "status": "SUCCESS",
            "provider": "Local Sandbox Mock",
            "rendered_preview_url": f"https://placehold.co/1280x720/1e293b/38bdf8.png?text=Local+Mock:+{prompt[:25]}...",
            "prompt": prompt,
            "duration": duration_sec,
            "aspect_ratio": aspect_ratio,
        }


class VideoProviderFactory:
    @staticmethod
    def get_provider(provider_name: str = "veo") -> BaseVideoProvider:
        name = provider_name.lower()
        if "veo" in name:
            return VeoVideoProvider()
        elif "seedance" in name:
            return SeedanceVideoProvider()
        else:
            return LocalMockVideoProvider()
