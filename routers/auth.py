
from fastapi.responses import RedirectResponse
import requests
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
import pandas as pd
from io import BytesIO
import traceback
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
router = APIRouter()
import datetime
from datetime import datetime, timedelta

@router.get("/jira-connect")
def connect_jira():
    scope = f"read%3Ajira-work%20manage%3Ajira-project%20manage%3Ajira-configuration%20read%3Ajira-user%20write%3Ajira-work%20manage%3Ajira-webhook%20manage%3Ajira-data-provider"
    state = CLIENT_SECRET
    auth_url = (
        # f"https://auth.atlassian.com/authorize?audience=api.atlassian.com&client_id=PFQ5sV4ckENP6BezRXHNWXYw7aTG44eV&scope=read%3Ajira-work%20manage%3Ajira-project%20manage%3Ajira-configuration%20read%3Ajira-user%20write%3Ajira-work%20manage%3Ajira-webhook%20manage%3Ajira-data-provider&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fjira-callback&state=${state}&response_type=code&prompt=consent"
        f"https://auth.atlassian.com/authorize?audience=api.atlassian.com&client_id={CLIENT_ID}&scope={scope}&redirect_uri=https%3A%2F%2Fbrd-backend-8iup.onrender.com%2Fjira-callback&state={state}&response_type=code&prompt=consent"
    )
    return RedirectResponse(auth_url)

from token_store import token_data

# @router.get("/jira-callback")
# def jira_callback(code: str):
#     token_url = "https://auth.atlassian.com/oauth/token"
#     payload = {
#         "grant_type": "authorization_code",
#         "client_id": CLIENT_ID,
#         "client_secret": CLIENT_SECRET,
#         "code": code,
#         "redirect_uri": REDIRECT_URI,
#     }
    

#     response = requests.post(token_url, json=payload)
#     print(response.json())
#     if response.status_code == 200:
#         data= response.json()
#         token_data["access_token"] = data["access_token"]
#         token_data["refresh_token"] = data.get("refresh_token")
#         token_data["expires_at"] = datetime.utcnow() + timedelta(seconds=data["expires_in"])
#         print(f"Access Token: {token_data['expires_at']}")

#         resource_res = requests.get(
#         "https://api.atlassian.com/oauth/token/accessible-resources",
#         headers={"Authorization": f"Bearer {data['access_token']}"},
#         )
#         resources = resource_res.json()
#         print(resources)
#         if not resources:
#             raise HTTPException(status_code=400, detail="Unable to get cloudId")

#         CLOUD_ID = resources[0]["id"]
#         print(f"Using CLOUD_ID: {CLOUD_ID}")
#         print(f"Access Token: {data['access_token']}")
#         base_url = f"https://brd-to-jira.netlify.app/"
#         #base_url = f"http://localhost:5173/"
#         redirect_url = f"{base_url}jira-success?token={data['access_token']}&cloudId={CLOUD_ID}"
#         return RedirectResponse(redirect_url)
#     else:
#         raise HTTPException(status_code=500, detail="Token exchange failed")

@router.get("/jira-callback")
def jira_callback(code: str):
    token_url = "https://auth.atlassian.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    

    response = requests.post(token_url, json=payload)
    print(response.json())
    if response.status_code == 200:
        access_token = response.json().get("access_token")
        resource_res = requests.get(
        "https://api.atlassian.com/oauth/token/accessible-resources",
        headers={"Authorization": f"Bearer {access_token}"},
        )
        resources = resource_res.json()
        print(resources)
        if not resources:
            raise HTTPException(status_code=400, detail="Unable to get cloudId")

        CLOUD_ID = resources[0]["id"]
        print(f"Using CLOUD_ID: {CLOUD_ID}")
        print(f"Access Token: {access_token}")
        base_url = f"https://brd-to-jira.netlify.app/"
        # base_url = f"http://localhost:5173/"
        redirect_url = f"{base_url}jira-success?token={access_token}&cloudId={CLOUD_ID}"
        return RedirectResponse(redirect_url)
    else:
        raise HTTPException(status_code=500, detail="Token exchange failed")


#when jira is connected i want to create a project in jira will upload a excel file with the project details create a api to upload the file and create the project in the jira provide me the overall code for this

# Step 4: Upload Excel and create project




def get_current_user_account_id(token: str, cloudId: str):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://api.atlassian.com/ex/jira/{cloudId}/rest/api/3/myself"
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        return res.json()["accountId"]
    except Exception as e:
        print("Error fetching accountId:", e)
        raise HTTPException(status_code=500, detail=f"Error fetching accountId: {e}")


import random
import string

# At the top of your function
generated_keys = set()

def generate_unique_project_key(name: str) -> str:
    base = "".join([c for c in name if c.isalnum()])[:3].upper()
    key = base
    while key in generated_keys:
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=2))
        key = (base + suffix)[:10]  # Max 10 chars allowed by Jira
    generated_keys.add(key)
    return key

# @router.post("/upload-excel-create-project")
# def upload_excel_create_project(
#     file: UploadFile = File(...),
#     token: str = Form(...),
#     cloudId: str = Form(...)
# ):
#     try:
#         token = token.replace("Bearer ", "")
#         print(f"Received token: {token[:10]}..., cloudId: {cloudId}")
#         print(f"Uploaded file: {file.filename}")

#         file_content = file.file.read()
#         if not file_content:
#             raise HTTPException(status_code=400, detail="Uploaded file is empty")

#         df = pd.read_excel(BytesIO(file_content))
#         print("Excel DataFrame preview:")
#         print(df.head())

#         if 'project_name' not in df.columns:
#             raise HTTPException(status_code=400, detail="Missing 'project_name' column in Excel")

#         lead_account_id = get_current_user_account_id(token, cloudId)

#         headers = {
#             "Authorization": f"Bearer {token}",
#             "Accept": "application/json",
#             "Content-Type": "application/json"
#         }

#         created_projects = []
#         failed_projects = []

#         for index, row in df.iterrows():
#             project_name = str(row['project_name']).strip()
#             if not project_name:
#                 failed_projects.append({"row": index + 2, "error": "Empty project name"})
#                 continue

#             project_key = generate_unique_project_key(project_name)
#             payload = {
#                 "key": project_key,
#                 "name": project_name,
#                 "projectTypeKey": "software",
#                 "projectTemplateKey": "com.pyxis.greenhopper.jira:gh-simplified-scrum-classic",
#                 "description": "Created via API",
#                 "leadAccountId": lead_account_id,
#             }

#             url = f"https://api.atlassian.com/ex/jira/{cloudId}/rest/api/3/project"
#             response = requests.post(url, json=payload, headers=headers)

#             if response.status_code in [200, 201]:
#                 created_projects.append(project_name)
#                 print(f"✅ Created: {project_name} ({project_key})")
#             else:
#                 error = response.json() if response.text else "Unknown error"
#                 failed_projects.append({"project": project_name, "error": error})
#                 print(f"❌ Failed: {project_name} → {error}")

#         return {
#             "created": created_projects,
#             "failed": failed_projects,
#         }

#     except Exception as e:
#         tb = traceback.format_exc()
#         print("Unhandled Exception:\n", tb)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=tb
#         )



@router.post("/upload-excel-create-project")
def upload_excel_create_project(
    file: UploadFile = File(...),
    token: str = Form(...),
    cloudId: str = Form(...)
):
    try:
        token = token.replace("Bearer ", "")
        print(f"Received token: {token[:10]}..., cloudId: {cloudId}")
        print(f"Uploaded file: {file.filename}")

        file_content = file.file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        df = pd.read_excel(BytesIO(file_content))
        print("Excel DataFrame preview:")
        print(df.head())

        if 'project_name' not in df.columns:
            raise HTTPException(status_code=400, detail="Missing 'project_name' column in Excel")

        lead_account_id = get_current_user_account_id(token, cloudId)

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        created_projects = []
        updated_projects = []
        failed_projects = []

        # Fetch all existing projects (or optimize by name search if supported)
        get_projects_url = f"https://api.atlassian.com/ex/jira/{cloudId}/rest/api/3/project/search"
        existing_projects_resp = requests.get(get_projects_url, headers=headers)
        existing_projects = existing_projects_resp.json().get("values", []) if existing_projects_resp.status_code == 200 else []

        project_name_to_key = {p['name']: p['key'] for p in existing_projects}

        for index, row in df.iterrows():
            project_name = str(row['project_name']).strip()
            if not project_name:
                failed_projects.append({"row": index + 2, "error": "Empty project name"})
                continue

            if project_name in project_name_to_key:
                # Update existing project
                project_key = project_name_to_key[project_name]
                update_url = f"https://api.atlassian.com/ex/jira/{cloudId}/rest/api/3/project/{project_key}"

                update_payload = {
                    "name": project_name,
                    "description": f"Updated via API",
                    "leadAccountId": lead_account_id,
                }

                response = requests.put(update_url, json=update_payload, headers=headers)

                if response.status_code == 204:
                    updated_projects.append(project_name)
                    print(f"📝 Updated: {project_name} ({project_key})")
                else:
                    error = response.json() if response.text else "Unknown update error"
                    failed_projects.append({"project": project_name, "error": error})
                    print(f"❌ Failed to update: {project_name} → {error}")

            else:
                # Create new project
                project_key = generate_unique_project_key(project_name)
                create_url = f"https://api.atlassian.com/ex/jira/{cloudId}/rest/api/3/project"

                create_payload = {
                    "key": project_key,
                    "name": project_name,
                    "projectTypeKey": "software",
                    "projectTemplateKey": "com.pyxis.greenhopper.jira:gh-simplified-scrum-classic",
                    "description": "Created via API",
                    "leadAccountId": lead_account_id,
                }

                response = requests.post(create_url, json=create_payload, headers=headers)

                if response.status_code in [200, 201]:
                    created_projects.append(project_name)
                    print(f"✅ Created: {project_name} ({project_key})")
                else:
                    error = response.json() if response.text else "Unknown create error"
                    failed_projects.append({"project": project_name, "error": error})
                    print(f"❌ Failed to create: {project_name} → {error}")

        return {
            "created": created_projects,
            "updated": updated_projects,
            "failed": failed_projects,
        }

    except Exception as e:
        tb = traceback.format_exc()
        print("Unhandled Exception:\n", tb)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=tb
        )
    



    
def get_current_user_account_id(token: str, cloudId: str):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.atlassian.com/ex/jira/{cloudId}/rest/api/3/myself"
    res = requests.get(url, headers=headers)

    print(f"GET /myself response status: {res.status_code}")
    print(f"Response text: {res.text}")

    if res.status_code != 200:
        raise HTTPException(
            status_code=401,
            detail=f"Failed to fetch accountId. Status: {res.status_code}, Body: {res.text}"
        )

    try:
        return res.json().get("accountId")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error decoding JSON response: {res.text}"
        )


@router.delete("/delete-all-projects")
def delete_all_projects(
    token: str = Form(...),
    cloudId: str = Form(...)
):
    try:
        token = token.replace("Bearer ", "")
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        # 1. Get list of all projects
        url = f"https://api.atlassian.com/ex/jira/{cloudId}/rest/api/3/project/search"
        project_list = []
        start_at = 0
        max_results = 100

        while True:
            paged_url = f"{url}?startAt={start_at}&maxResults={max_results}"
            res = requests.get(paged_url, headers=headers)
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail=res.text)

            data = res.json()
            projects = data.get("values", [])
            project_list.extend(projects)

            if start_at + max_results >= data.get("total", 0):
                break
            start_at += max_results

        print(f"Found {len(project_list)} projects.")

        # 2. Delete each project
        deleted = []
        failed = []

        for project in project_list:
            key = project["key"]
            name = project["name"]
            delete_url = f"https://api.atlassian.com/ex/jira/{cloudId}/rest/api/3/project/{key}"

            del_res = requests.delete(delete_url, headers=headers)
            if del_res.status_code == 204:
                print(f"✅ Deleted: {key} - {name}")
                deleted.append(key)
            else:
                print(f"❌ Failed: {key} - {name} → {del_res.status_code}")
                failed.append({
                    "key": key,
                    "name": name,
                    "error": del_res.text
                })

        return {
            "total": len(project_list),
            "deleted": deleted,
            "failed": failed
        }

    except Exception as e:
        tb = traceback.format_exc()
        print("Unhandled Exception:\n", tb)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=tb
        )


@router.delete("/delete-project")
def delete_project(
    token: str = Form(...),
    cloudId: str = Form(...),
    projectKey: str = Form(...)

):

    try:

        token = token.replace("Bearer ", "")

        headers = {

            "Authorization": f"Bearer {token}",

            "Accept": "application/json"

        }
 
        delete_url = f"https://api.atlassian.com/ex/jira/{cloudId}/rest/api/3/project/{projectKey}"

        response = requests.delete(delete_url, headers=headers)
 
        if response.status_code == 204:

            return {"message": f"✅ Project {projectKey} deleted successfully."}

        else:

            raise HTTPException(

                status_code=response.status_code,

                detail=f"❌ Failed to delete project {projectKey}: {response.text}"

            )
 
    except Exception as e:

        tb = traceback.format_exc()

        print("Unhandled Exception:\n", tb)

        raise HTTPException(

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=tb

        )
 