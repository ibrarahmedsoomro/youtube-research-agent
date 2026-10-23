"""
YouTube Authentication Script.
Uses client_secret.json to authenticate your Google/YouTube account via OAuth 2.0
and saves credentials to youtube_credentials.json.
"""

import os
import sys
import json

def authenticate():
    client_secret_file = "client_secret.json"
    credentials_file = "youtube_credentials.json"

    if not os.path.exists(client_secret_file):
        print(f"[ERROR] '{client_secret_file}' not found.")
        print("Please paste your Google OAuth client secret JSON into 'client_secret.json'.")
        return False

    with open(client_secret_file, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if "PASTE_YOUR_CLIENT_ID_HERE" in str(data):
                print("[ERROR] Please replace the placeholder values in 'client_secret.json' with your actual Google Cloud OAuth credentials.")
                return False
        except Exception as e:
            print(f"[ERROR] Failed to parse {client_secret_file}: {e}")
            return False

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        print("[ERROR] Missing required packages. Installing them now...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "google-api-python-client", "google-auth-oauthlib"])
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

    SCOPES = [
        "https://www.googleapis.com/auth/youtube.force-ssl",
        "https://www.googleapis.com/auth/youtube.readonly"
    ]

    print("\n=======================================================")
    print("      Starting YouTube OAuth 2.0 Authorization")
    print("=======================================================")
    print("Opening browser for you to sign in to your YouTube channel...")

    try:
        flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
        creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")

        # Save authorized credentials
        creds_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes
        }

        with open(credentials_file, "w", encoding="utf-8") as f:
            json.dump(creds_data, f, indent=2)

        print(f"\n[SUCCESS] Authentication successful!")
        print(f"Credentials saved to: {credentials_file}")

        # Test Channel Connection
        youtube = build("youtube", "v3", credentials=creds)
        channels_response = youtube.channels().list(mine=True, part="snippet,statistics").execute()

        items = channels_response.get("items", [])
        if items:
            channel = items[0]
            title = channel.get("snippet", {}).get("title", "Unknown")
            subscribers = channel.get("statistics", {}).get("subscriberCount", "0")
            videos = channel.get("statistics", {}).get("videoCount", "0")
            print("\n-------------------------------------------------------")
            print(f" Connected Channel: {title}")
            print(f" Subscribers:       {subscribers}")
            print(f" Total Videos:      {videos}")
            print("-------------------------------------------------------")
        else:
            print("\n[INFO] Connected Google Account has no primary YouTube channel created yet.")

        return True

    except Exception as e:
        print(f"\n[ERROR] Authentication failed: {e}")
        return False

if __name__ == "__main__":
    authenticate()
