# utils/jira_api.py
import requests
from token_store import token_data
from utils.jira_auth import refresh_jira_token

def make_jira_request(url: str, method="get", data=None):
    if not token_data["access_token"]:
        raise Exception("No access token available")

    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    request_method = getattr(requests, method)

    res = request_method(url, headers=headers, json=data)

    if res.status_code == 401:
        # Access token expired
        new_token = refresh_jira_token()
        headers["Authorization"] = f"Bearer {new_token}"
        res = request_method(url, headers=headers, json=data)

    return res
