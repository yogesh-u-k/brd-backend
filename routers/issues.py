from fastapi import APIRouter, Request, Header, HTTPException
import requests
import json

router = APIRouter()
CLOUD_ID = "b574c564-8337-4c3b-8e84-786d837d294b"  # In-memory store (can use database/session in prod)

@router.get("/jira-issues")
def get_issues(authorization: str = Header(None)):
    print(authorization)
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Jira access token")
    token = authorization.split(" ")[1]

    global CLOUD_ID
    resource_res = requests.get(
        "https://api.atlassian.com/oauth/token/accessible-resources",
        headers={"Authorization": f"Bearer {token}"},
    )
    resources = resource_res.json()
    print(resources)
    if not resources:
        raise HTTPException(status_code=400, detail="Unable to get cloudId")

    CLOUD_ID = resources[0]["id"]

    jira_res = requests.get(
        f"https://api.atlassian.com/ex/jira/{CLOUD_ID}/rest/api/3/search?jql=project=project-1",
        headers={"Authorization": f"Bearer {token}"},
    )
    if not jira_res.ok:
        raise HTTPException(status_code=jira_res.status_code, detail=jira_res.text)

    return jira_res.json().get("issues", [])


@router.post("/create-issue")
async def create_issue(request: Request, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Jira access token")
    token = authorization.split(" ")[1]
    body = await request.json()

    summary = body.get("summary")
    description = body.get("description")
    issueType = body.get("issueType")
    projectKey = body.get("projectKey")
    labels = body.get("labels", [])
    acceptance_criteria = body.get("acceptance_criteria", [])

    if not CLOUD_ID:
        raise HTTPException(status_code=500, detail="Jira cloudId not configured")

    formatted_description = {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": description}]}
        ] + (
            [{"type": "paragraph", "content": [{"type": "text", "text": "Acceptance Criteria:"}]}] +
            [{"type": "paragraph", "content": [{"type": "text", "text": f"- {item}"}]} for item in acceptance_criteria]
            if acceptance_criteria else []
        )
    }

    issue_payload = {
        "fields": {
            "summary": summary,
            "description": formatted_description,
            "issuetype": {"name": issueType},
            "project": {"key": projectKey},
            "labels": labels,
        }
    }

    response = requests.post(
        f"https://api.atlassian.com/ex/jira/{CLOUD_ID}/rest/api/3/issue",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        json=issue_payload,
    )

    if response.ok:
        return {"message": "Issue created", "issue": response.json()}
    else:
        raise HTTPException(status_code=response.status_code, detail=response.json())
