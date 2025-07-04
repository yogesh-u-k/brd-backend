from fastapi import APIRouter, Request, HTTPException, Header, Body
from typing import List, Optional
from pydantic import BaseModel
import httpx
import re

JIRA_BASE_URL = "https://api.atlassian.com"
ISSUE_ENDPOINT = "/rest/api/3/issue"

router = APIRouter()

@router.post("/get-projects")
async def get_projects(
    cloudid: str = Header(...),
    authorization: str = Header(..., convert_underscores=False),
):
    headers = {
        "Authorization": f"Bearer {authorization}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        projects_url = f"{JIRA_BASE_URL}/ex/jira/{cloudid}/rest/api/3/project"
        projects_response = await client.get(projects_url, headers=headers)
        print(f"Projects response status: {projects_response.status_code}")
        if projects_response.status_code != 200:
            raise HTTPException(status_code=projects_response.status_code, detail="Failed to fetch projects")

        all_projects = projects_response.json()
    return {"projects": all_projects}