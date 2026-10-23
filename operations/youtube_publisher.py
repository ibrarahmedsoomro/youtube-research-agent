"""
YouTube Live Publishing Engine.
Handles authenticating and synchronizing video metadata (title, description, tags)
directly to YouTube via Google YouTube Data API v3, with built-in sandbox validation.
"""

import os
import json
from typing import Dict, Any, List, Optional
from database.db import log_system_event

class YouTubePublisher:
    def __init__(self, credentials_path: Optional[str] = None):
        self.credentials_path = credentials_path or os.getenv("YOUTUBE_OAUTH_CREDENTIALS", "youtube_credentials.json")
        self.is_authenticated = self._check_auth_status()

    def _check_auth_status(self) -> bool:
        """Checks if valid OAuth credentials or refresh token exists."""
        # Auto-create credentials file if provided via environment variable (e.g. GitHub Actions / Streamlit Secrets)
        if not os.path.exists(self.credentials_path) and os.getenv("YOUTUBE_CREDENTIALS_JSON"):
            try:
                with open(self.credentials_path, "w", encoding="utf-8") as f:
                    f.write(os.getenv("YOUTUBE_CREDENTIALS_JSON", ""))
            except Exception:
                pass

        if os.path.exists(self.credentials_path):
            try:
                with open(self.credentials_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return bool(data.get("token") or data.get("refresh_token") or data.get("access_token"))
            except Exception:
                return False
        return False

    def update_video_metadata(
        self,
        video_id: str,
        title: str,
        description: str,
        tags: List[str],
        category_id: str = "24",  # Default to Entertainment
        privacy_status: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Publishes updated metadata to YouTube via YouTube Data API v3 videos.update.
        If credentials are not yet linked or in dry_run mode, executes in Verified Sandbox Mode.
        """
        clean_title = title.strip()
        clean_desc = description.strip()
        clean_tags = [t.strip() for t in tags if t.strip()]

        log_system_event(
            "YouTubePublisher",
            f"Syncing video {video_id} - Title: {clean_title[:30]}... ({len(clean_tags)} tags)"
        )

        if dry_run or not self.is_authenticated:
            # Sandbox Simulation Mode with verification checks
            validation_errors = []
            if len(clean_title) > 100:
                validation_errors.append(f"Title exceeds 100 character limit ({len(clean_title)} chars)")
            if len(clean_desc) > 5000:
                validation_errors.append(f"Description exceeds 5000 character limit ({len(clean_desc)} chars)")
            total_tag_chars = sum(len(t) for t in clean_tags)
            if total_tag_chars > 500:
                validation_errors.append(f"Total tags exceed 500 character limit ({total_tag_chars} chars)")

            status = "SANDBOX_SIMULATED_SUCCESS" if not validation_errors else "VALIDATION_FAILED"

            return {
                "status": status,
                "video_id": video_id,
                "is_sandbox": True,
                "authenticated": self.is_authenticated,
                "updated_fields": {
                    "title": clean_title,
                    "description_preview": clean_desc[:120] + "..." if len(clean_desc) > 120 else clean_desc,
                    "tags_count": len(clean_tags),
                    "total_tag_chars": total_tag_chars,
                    "category_id": category_id,
                },
                "validation_errors": validation_errors,
                "message": (
                    "Video metadata validated and simulated successfully in Sandbox Mode. "
                    "Link Google OAuth to enable direct live channel sync."
                    if not validation_errors else "Validation errors found."
                )
            }

        # Real YouTube API execution branch (when OAuth is configured)
        try:
            # Note: Uses googleapiclient if installed and authenticated
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials

            with open(self.credentials_path, "r", encoding="utf-8") as f:
                creds_data = json.load(f)
            
            creds = Credentials.from_authorized_user_info(creds_data)
            youtube = build("youtube", "v3", credentials=creds)

            body = {
                "id": video_id,
                "snippet": {
                    "title": clean_title,
                    "description": clean_desc,
                    "tags": clean_tags,
                    "categoryId": category_id
                }
            }
            if privacy_status:
                body["status"] = {"privacyStatus": privacy_status}

            request = youtube.videos().update(
                part="snippet" + (",status" if privacy_status else ""),
                body=body
            )
            response = request.execute()

            return {
                "status": "PUBLISHED_LIVE",
                "video_id": video_id,
                "is_sandbox": False,
                "authenticated": True,
                "updated_fields": {
                    "title": response.get("snippet", {}).get("title"),
                    "tags_count": len(response.get("snippet", {}).get("tags", [])),
                },
                "message": f"Successfully updated video '{video_id}' live on YouTube!"
            }

        except Exception as e:
            return {
                "status": "ERROR",
                "video_id": video_id,
                "is_sandbox": False,
                "authenticated": True,
                "error": str(e),
                "message": f"Failed to sync with YouTube API: {str(e)}"
            }

    def save_oauth_credentials(self, credentials_data: Dict[str, Any]) -> bool:
        """Saves authorized OAuth tokens for YouTube Data API v3 access."""
        try:
            with open(self.credentials_path, "w", encoding="utf-8") as f:
                json.dump(credentials_data, f, indent=2)
            self.is_authenticated = True
            log_system_event("YouTubePublisher", "OAuth credentials saved successfully.")
            return True
        except Exception as e:
            log_system_event("YouTubePublisher", f"Error saving credentials: {e}")
            return False
