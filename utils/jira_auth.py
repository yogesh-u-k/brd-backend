# utils/jira_auth.py
import requests
from datetime import datetime, timedelta
from token_store import token_data
from config import CLIENT_ID, CLIENT_SECRET  # Or from .env

def refresh_jira_token():
    if not token_data["refresh_token"]:
        raise Exception("No refresh token available")

    payload = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": token_data["refresh_token"],
    }

    response = requests.post("https://auth.atlassian.com/oauth/token", json=payload)
    if response.status_code == 200:
        data = response.json()
        token_data["access_token"] = data["access_token"]
        token_data["refresh_token"] = data["refresh_token"]
        token_data["expires_at"] = datetime.utcnow() + timedelta(seconds=data["expires_in"])
        print("🔁 Token refreshed")
        return token_data["access_token"]
    else:
        raise Exception("Failed to refresh token")
