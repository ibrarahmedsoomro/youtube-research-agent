"""
Multi-Account YouTube OAuth & Channel Authentication Manager.
Allows users to connect, authenticate, switch, and manage multiple YouTube channels
seamlessly via Google OAuth 2.0 and YouTube Data API v3.
"""

import os
import json
from typing import Dict, Any, List, Optional
from database import (
    save_or_update_connected_account,
    get_connected_accounts,
    get_active_account,
    set_active_account,
    delete_connected_account,
    log_system_event,
)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

class YouTubeAuthManager:
    def __init__(self, client_secrets_file: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.client_secrets_file = client_secrets_file or os.path.join(base_dir, "client_secret.json")
        self._ensure_default_seed()

    def _ensure_default_seed(self):
        """Ensures at least the default SpookyToonStories channel exists in database."""
        accounts = get_connected_accounts()
        if not accounts:
            save_or_update_connected_account(
                channel_id="UC_SpookyToon_Demo_01",
                channel_handle="@SpookyToonStories",
                channel_name="Spooky Toon Stories",
                email="taqisoomro333@gmail.com",
                avatar_url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=100&auto=format&fit=crop&q=60",
                subscriber_count=18400,
                video_count=42,
                credentials_data=None,
                set_active=True,
            )

    def get_auth_url(self, redirect_uri: str = "http://localhost:8501") -> Optional[str]:
        """Generates the Google OAuth 2.0 Authorization URL for connecting a new YouTube account."""
        if not os.path.exists(self.client_secrets_file):
            return None
        
        try:
            from google_auth_oauthlib.flow import Flow
            flow = Flow.from_client_secrets_file(
                self.client_secrets_file,
                scopes=SCOPES,
                redirect_uri=redirect_uri,
            )
            auth_url, _ = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                prompt="consent",
            )
            return auth_url
        except Exception as e:
            log_system_event("YouTubeAuthManager", f"Error generating auth URL: {e}", "ERROR")
            return None

    def exchange_code_for_channel(self, auth_code: str, redirect_uri: str = "http://localhost:8501") -> Dict[str, Any]:
        """Exchanges authorization code for tokens and registers channel."""
        if not os.path.exists(self.client_secrets_file):
            return {"success": False, "error": "client_secret.json not found on server."}

        try:
            from google_auth_oauthlib.flow import Flow
            from googleapiclient.discovery import build

            flow = Flow.from_client_secrets_file(
                self.client_secrets_file,
                scopes=SCOPES,
                redirect_uri=redirect_uri,
            )
            flow.fetch_token(code=auth_code)
            credentials = flow.credentials

            # Convert credentials to serializable dict
            creds_data = {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes,
            }

            # Fetch channel metadata from YouTube Data API v3
            youtube = build("youtube", "v3", credentials=credentials)
            ch_request = youtube.channels().list(
                mine=True,
                part="snippet,statistics"
            )
            ch_response = ch_request.execute()

            items = ch_response.get("items", [])
            if not items:
                return {"success": False, "error": "No YouTube channel found associated with this Google Account."}

            ch_item = items[0]
            ch_id = ch_item.get("id")
            snippet = ch_item.get("snippet", {})
            stats = ch_item.get("statistics", {})

            ch_title = snippet.get("title", "YouTube Channel")
            ch_handle = snippet.get("customUrl", f"@{ch_title.replace(' ', '')}")
            if not ch_handle.startswith("@"):
                ch_handle = f"@{ch_handle}"

            avatar = snippet.get("thumbnails", {}).get("default", {}).get("url", "")
            subs = int(stats.get("subscriberCount", 0))
            v_count = int(stats.get("videoCount", 0))

            # Fetch user email if available
            user_email = ""
            try:
                from googleapiclient.discovery import build as oauth_build
                oauth_service = oauth_build("oauth2", "v2", credentials=credentials)
                user_info = oauth_service.userinfo().get().execute()
                user_email = user_info.get("email", "")
            except Exception:
                pass

            # Save in database
            save_or_update_connected_account(
                channel_id=ch_id,
                channel_handle=ch_handle,
                channel_name=ch_title,
                email=user_email,
                avatar_url=avatar,
                subscriber_count=subs,
                video_count=v_count,
                credentials_data=creds_data,
                set_active=True,
            )

            # Also update local credentials json for publisher compatibility
            with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "youtube_credentials.json"), "w", encoding="utf-8") as f:
                json.dump(creds_data, f, indent=2)

            log_system_event("YouTubeAuthManager", f"Connected new channel: {ch_title} ({ch_handle})", "SUCCESS")

            return {
                "success": True,
                "channel_id": ch_id,
                "channel_name": ch_title,
                "channel_handle": ch_handle,
                "email": user_email,
                "subscriber_count": subs,
                "avatar_url": avatar,
            }

        except Exception as e:
            log_system_event("YouTubeAuthManager", f"Auth code exchange failed: {e}", "ERROR")
            return {"success": False, "error": str(e)}

    def list_accounts(self) -> List[Dict[str, Any]]:
        """Returns all registered channels."""
        return get_connected_accounts()

    def get_current_active(self) -> Optional[Dict[str, Any]]:
        """Returns active channel details."""
        return get_active_account()

    def switch_channel(self, channel_identifier: str) -> bool:
        """Switches active channel."""
        success = set_active_account(channel_identifier)
        if success:
            acc = get_active_account()
            if acc and acc.get("credentials_json"):
                try:
                    creds_data = json.loads(acc["credentials_json"])
                    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "youtube_credentials.json"), "w", encoding="utf-8") as f:
                        json.dump(creds_data, f, indent=2)
                except Exception:
                    pass
            log_system_event("YouTubeAuthManager", f"Switched active channel to {channel_identifier}", "SUCCESS")
        return success

    def remove_account(self, channel_identifier: str) -> bool:
        """Removes a connected channel."""
        return delete_connected_account(channel_identifier)
