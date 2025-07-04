from fastapi import APIRouter, Request, HTTPException, Header, Body
from typing import List, Optional
from pydantic import BaseModel
import httpx
import re
# JIRA_BASE_URL = "https://api.atlassian.com"
# JIRA_API_URL = "https://your-domain.atlassian.net/rest/api/3"
ISSUE_ENDPOINT = "/issue"
router = APIRouter()

class Story(BaseModel):
    title: str
    description: Optional[str]
    labels: Optional[List[str]] = []

class ApplicationStories(BaseModel):
    application: str
    stories: List[Story]

class WrappedStories(BaseModel):
    flattened_stories: List[ApplicationStories]


JIRA_BASE_URL = "https://api.atlassian.com"
ISSUE_ENDPOINT = "/rest/api/3/issue"

@router.post("/create-stories")
async def create_stories(
    cloudid: str = Header(...),
    authorization: str = Header(..., convert_underscores=False),
    payload: WrappedStories = Body(...)
):
    flattened_stories = payload.flattened_stories
    token = authorization.replace("Bearer ", "")
    headers = {
        "Authorization": f"Bearer {token}",
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
        project_key_map = {proj["name"].lower(): proj["key"] for proj in all_projects}
        created_issues = []

        def sanitize_label(label: str):
            cleaned = label.lower().replace(" ", "-")
            return re.sub(r"[^a-z0-9-_]", "", cleaned)

        for app in flattened_stories:
            app_name = app.application.lower()
            stories = app.stories

            matched_key = None
            for project_name, key in project_key_map.items():
                if app_name in project_name:
                    matched_key = key
                    break

            if not matched_key:
                continue

            for story in stories:
                issue_payload = {
                    "fields": {
                        "project": {"key": matched_key},
                        "summary": story.title or "Untitled Story",
                        "description": {
                            "type": "doc",
                            "version": 1,
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": story.description or "No description provided"
                                        }
                                    ]
                                }
                            ]
                        },
                        "labels": [
                            sanitize_label(label)
                            for label in story.labels or []
                            if label and label.strip()
                        ],
                        "issuetype": {"name": "Story"}
                    }
                }

                issue_url = f"{JIRA_BASE_URL}/ex/jira/{cloudid}{ISSUE_ENDPOINT}"
                issue_resp = await client.post(issue_url, headers=headers, json=issue_payload)

                if issue_resp.status_code in [200, 201]:
                    created_issues.append(issue_resp.json())
                else:
                    created_issues.append({
                        "error": f"Failed to create issue for {story.title}",
                        "status": issue_resp.status_code,
                        "details": issue_resp.json()
                    })

    return {
        "created": created_issues,
        "total": len(created_issues)
    }

# @router.post("/create-stories")
# async def create_stories(
#     cloudid: str = Header(...),
#     authorization: str = Header(..., convert_underscores=False),
#     flattened_stories: List[ApplicationStories] = Body(...)
# ):
#     token = authorization.replace("Bearer ", "")

#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Accept": "application/json",
#         "Content-Type": "application/json"
#     }

#     # return {"message": "Headers received successfully"}
#     # You provided the flattened stories manually

#     flattened_stories=[
#   {
#     "application": "Radar (Radar Admin Tools)",
#     "stories": [
#       {
#         "title": "Limit Access to Data in Dashboards Across Your System",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=869051",
#         "labels": ["Required Reading", "Required", "Moderate"]
#       },
#       {
#         "title": "A Centralized, Flexible Way to Limit Access to Data in Dashboards",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=894447",
#         "labels": ["Includes Automatic Changes", "Required", "Moderate"]
#       },
#       {
#         "title": "Verify That Server Names Match Certificates to Ensure Cogito SQL, Radar SQL, and HopStart Continue to Run",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=906454",
#         "labels": ["Includes Automatic Changes", "Required", "Minimal"]
#       }
#     ]
#   },
#   {
#     "application": "MyChart (Appointments and Admissions), Referrals (Miscellaneous)",
#     "stories": [
#       {
#         "title": "A Fresh New Look for Referrals in MyChart",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=872759",
#         "labels": ["Includes Automatic Changes", "Required", "Minimal"]
#       }
#     ]
#   },
#   {
#     "application": "Healthy Planet (Risk Adjustment)",
#     "stories": [
#       {
#         "title": "Take Risk Adjustment Tools to the Next Level",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=881428",
#         "labels": ["None", "Staying Current", "Considerable"]
#       },
#       {
#         "title": "Take Pre-Visit Risk Adjustment Review to the Next Level",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=896017",
#         "labels": ["None", "Staying Current", "Moderate"]
#       },
#       {
#         "title": "Setup Required to Deprecate CMS-HCC V24 Model for Reporting Period 2025",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=896509",
#         "labels": [
#           "Build Wizard",
#           "Required Reading - Fix Requiring Setup",
#           "Required",
#           "Moderate"
#         ]
#       },
#       {
#         "title": "Introducing the RxHCC Model: Enhancing Accuracy in Healthcare Risk Adjustment",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=897040",
#         "labels": [
#           "Required Reading",
#           "Turbocharger Package",
#           "Required",
#           "Moderate"
#         ]
#       },
#       {
#         "title": "Setup Required to Configure the Number of Conditions Shown in Risk Adjustment Advisories",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=898780",
#         "labels": [
#           "Required Reading - Fix Requiring Setup",
#           "Required",
#           "Minimal"
#         ]
#       },
#       {
#         "title": "Facilitate Risk Adjustment Workflows With New Print Groups",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=900198",
#         "labels": ["Includes Automatic Changes", "Required", "Minimal"]
#       },
#       {
#         "title": "Risk Adjustment Models Updated to Align with 2025 CMS and HHS Specifications",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=900401",
#         "labels": ["Includes Automatic Changes", "Required", "Minimal"]
#       },
#       {
#         "title": "Setup Required to Fix CDI Reviews Appearing in the HCC Advisory",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=901023",
#         "labels": [
#           "Required Reading - Fix Requiring Setup",
#           "Required",
#           "Minimal"
#         ]
#       },
#       {
#         "title": "CMS and HHS Risk Adjustment Registries Updated for 2025",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=902132",
#         "labels": ["Includes Automatic Changes", "Required", "Minimal"]
#       },
#       {
#         "title": "Setup Required to Fix Inaccuracies in a Patient's Most Recent Risk Adjustment Review",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=903559",
#         "labels": [
#           "Required Reading - Fix Requiring Setup",
#           "Required",
#           "Minimal"
#         ]
#       }
#     ]
#   },
#   {
#     "application": "EpicCare Ambulatory (OurPractice Advisories)",
#     "stories": [
#       {
#         "title": "Take OurPractice Advisories to the Next Level with a New Design That Simplifies Clinician Workflows",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=881659",
#         "labels": ["None", "Staying Current", "Moderate"]
#       },
#       {
#         "title": "Update Multiple OurPractice Advisories at Once with the Bulk Update Action",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=898511",
#         "labels": ["Includes Automatic Changes", "Required", "None"]
#       },
#       {
#         "title": "Setup Required to Fix OurPractice Advisories Using Pediatric BMI Percentile Extension Criteria",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=898895",
#         "labels": [
#           "Required Reading - Fix Requiring Setup",
#           "Required",
#           "Minimal"
#         ]
#       },
#       {
#         "title": "Setup Required to Disable Data Courier and EMFI Tracking for an OurPractice Advisory Web Service Item",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=902831",
#         "labels": [
#           "Required Reading - Fix Requiring Setup",
#           "Required",
#           "Moderate"
#         ]
#       },
#       {
#         "title": "Limit the Data Sent to Web Services Through CDS Hooks OurPractice Advisories by Not Sending FHIR Access Tokens",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=903251",
#         "labels": ["Includes Automatic Changes", "Required", "Minimal"]
#       }
#     ]
#   },
#   {
#     "application": "MyChart (Appointments and Admissions)",
#     "stories": [
#       {
#         "title": "Other Preferences Transitions to the React Framework and Caregiver Information Says Farewell",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=883560",
#         "labels": ["Includes Automatic Changes", "Required", "Minimal"]
#       },
#       {
#         "title": "MyChart's Search for Provider Activity Is Now Retired",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=893782",
#         "labels": ["Includes Automatic Changes", "Required", "None"]
#       },
#       {
#         "title": "Goodbye to the Scheduling Tickets Activity",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=900313",
#         "labels": ["Includes Automatic Changes", "Required", "Minimal"]
#       },
#       {
#         "title": "Patients See a Friendlier List of Specialties for Providers in Provider Finder",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=902106",
#         "labels": ["Includes Automatic Changes", "Required", "None"]
#       },
#       {
#         "title": "Farewell to the Provider Selection Dropdown",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=902718",
#         "labels": ["Includes Automatic Changes", "Required", "None"]
#       }
#     ]
#   },
#   {
#     "application": "MyChart (MyChart Care Companion)",
#     "stories": [
#       {
#         "title": "Reimagining Diabetes Care: A New Plan for Type 2 Diabetes Management",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=883984",
#         "labels": [
#           "Foundation Content",
#           "Required Reading",
#           "Turbocharger Package",
#           "Required",
#           "Moderate"
#         ]
#       },
#       {
#         "title": "Provide a Healthy Start for Kids with the Early Childhood Development Care Plan",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=900806",
#         "labels": [
#           "Foundation Content",
#           "Turbocharger Package",
#           "Staying Current",
#           "Moderate"
#         ]
#       },
#       {
#         "title": "Buckle Up for the Car Seat Safety Care Plan",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=902384",
#         "labels": [
#           "Foundation Content",
#           "Required Reading",
#           "Turbocharger Package",
#           "Required",
#           "Minimal"
#         ]
#       },
#       {
#         "title": "Setup Required to Fix Daily Digest Notifications",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=902426",
#         "labels": [
#           "Required Reading - Fix Requiring Setup",
#           "Required",
#           "Minimal"
#         ]
#       }
#     ]
#   },
#   {
#     "application": "SlicerDicer (Miscellaneous)",
#     "stories": [
#       {
#         "title": "Introducing Tutorial Builder: Create SlicerDicer Tutorials with Ease",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=884618",
#         "labels": ["Required Reading", "Required", "None"]
#       }
#     ]
#   },
#   {
#     "application": "MyChart (Telehealth)",
#     "stories": [
#       {
#         "title": "Click, Connect, Care! Simplified On-Demand Video Visits in MyChart",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=884699",
#         "labels": ["Includes Automatic Changes", "Staying Current", "Moderate"]
#       }
#     ]
#   },
#   {
#     "application": "EpicCare Ambulatory (Problem List)",
#     "stories": [
#       {
#         "title": "Update Custom Multiple Myeloma Staging Forms to Include Additional Options",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=885073",
#         "labels": ["Includes Automatic Changes", "Required", "Minimal"]
#       },
#       {
#         "title": "More Discrete Disease Documentation with Rheumatoid Arthritis Phenotype SmartForm Updates",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=896722",
#         "labels": ["Includes Automatic Changes", "Required", "Minimal"]
#       },
#       {
#         "title": "Updated AJCC Version 9 Staging Forms for Lung, Thymus, Diffuse Pleural Mesothelioma, and Nasopharynx",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=898563",
#         "labels": ["Includes Automatic Changes", "Required", "Minimal"]
#       },
#       {
#         "title": "Document Mutation Status on Breast Cancer AJCC 8th Edition Staging Forms",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=901092",
#         "labels": ["Includes Automatic Changes", "Required", "Minimal"]
#       },
#       {
#         "title": "Document Myometrial Thickness and Extent of Myometrial Invasion on AJCC 8th Edition Corpus Uteri Carcinoma and Carcinosarcoma Staging Forms",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=903086",
#         "labels": ["Includes Automatic Changes", "Required", "Minimal"]
#       }
#     ]
#   },
#   {
#     "application": "Analytics (Generative AI), Healthy Planet (Risk Adjustment), Resolute Professional Billing (Charge Entry and Review)",
#     "stories": [
#       {
#         "title": "AI Coding Assistant for Post-Visit Risk Adjustment",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=886712",
#         "labels": ["None", "Staying Current", "Moderate"]
#       }
#     ]
#   },
#   {
#     "application": "Wisdom (Dental Treatment Plan)",
#     "stories": [
#       {
#         "title": "Allow Dental Residents to Complete Pre-Approved Procedures Without Supervisor Signoff",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=887843",
#         "labels": ["Build Wizard", "Required Reading", "Required", "Moderate"]
#       },
#       {
#         "title": "Dental Students and Residents Can Now Add Additional Procedures to Today's Visit",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=890382",
#         "labels": ["Includes Automatic Changes", "Required", "None"]
#       },
#       {
#         "title": "Speed Up Dental Scheduling with Automatic Requested Visit Types",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=899869",
#         "labels": ["Build Wizard", "Staying Current", "Moderate"]
#       },
#       {
#         "title": "Quickly Add Additional Procedures in the Sidebar",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=902512",
#         "labels": ["Includes Automatic Changes", "Required", "None"]
#       }
#     ]
#   },
#   {
#     "application": "Cadence (Appointment Scheduling)",
#     "stories": [
#       {
#         "title": "Provider Search Terms Help Schedulers Find the Best Fit",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=889836",
#         "labels": ["Build Wizard", "Staying Current", "Considerable"]
#       },
#       {
#         "title": "Setup Required to Fix Unsafe HTML in Patient Scheduling Items",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=898113",
#         "labels": [
#           "Includes Automatic Changes",
#           "Required Reading - Fix Requiring Setup",
#           "Required",
#           "Minimal"
#         ]
#       },
#       {
#         "title": "Smarter Appointment Notes and Messages Have Arrived",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=898752",
#         "labels": ["Includes Automatic Changes", "Required", "None"]
#       },
#       {
#         "title": "Tinkering with Time: Override Visit Length Is Now More Visible in Book It",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=902161",
#         "labels": ["Includes Automatic Changes", "Required", "None"]
#       }
#     ]
#   },
#   {
#     "application": "Cadence (Appointment Scheduling), Referrals (Order Entry and Order Composer)",
#     "stories": [
#       {
#         "title": "Take Me to the Specialist: Focus on Patients' Clinical Needs in Referrals with Provider Search Terms",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=890038",
#         "labels": ["Build Wizard", "Staying Current", "Considerable"]
#       }
#     ]
#   },
#   {
#     "application": "Charge Router (Miscellaneous)",
#     "stories": [
#       {
#         "title": "Got It: Filter Action History in Charge Router Charge Detail",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=890541",
#         "labels": ["Includes Automatic Changes", "Required", "None"]
#       }
#     ]
#   },
#   {
#     "application": "Resolute Professional Claims (Claim Error Management)",
#     "stories": [
#       {
#         "title": "Setup Required to Fix Claim Definition Files So Extension 70093 Applies to CMS Only",
#         "description": "https://nova.epic.com/Select.aspx?CstID=1434&RnID=891167",
#         "labels": [
#           "Required Reading - Fix Requiring Setup",
#           "Required",
#           "Minimal"
#         ]
#       }
#     ]
#   },
# ]


#     # Setup headers
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Accept": "application/json",
#         "Content-Type": "application/json"
#     }

#     async with httpx.AsyncClient() as client:
#         # Fetch all JIRA projects
#         projects_url = f"{JIRA_BASE_URL}/ex/jira/{cloudid}/rest/api/3/project"
#         projects_response = await client.get(projects_url, headers=headers)
#         print(f"Projects response status: {projects_response.status_code}")
#         if projects_response.status_code != 200:
#             raise HTTPException(status_code=projects_response.status_code, detail="Failed to fetch projects")

#         all_projects = projects_response.json()
#         project_key_map = {proj["name"].lower(): proj["key"] for proj in all_projects}

#         created_issues = []

#         for app in flattened_stories:
#             app_name = app["application"].lower()
#             stories = app.get("stories", [])

#             # Try to match the project
#             matched_key = None
#             for project_name, key in project_key_map.items():
#                 if app_name in project_name:
#                     matched_key = key
#                     break

#             if not matched_key:
#                 continue  # Skip if no project matched
#             import re

#             def sanitize_label(label: str):
#                 cleaned = label.lower().replace(" ", "-")
#                 return re.sub(r"[^a-z0-9-_]", "", cleaned)  # remove invalid characters

#             for story in stories:
#                 issue_payload = {
#                     "fields": {
#                         "project": {"key": matched_key},
#                         "summary": story["title"] or "Untitled Story",
#                         "description": {
#                             "type": "doc",
#                             "version": 1,
#                             "content": [
#                                 {
#                                     "type": "paragraph",
#                                     "content": [
#                                         {
#                                             "type": "text",
#                                             "text": story["description"] or "No description provided"
#                                         }
#                                     ]
#                                 }
#                             ]
#                         },
#                         "labels": [
#                             sanitize_label(label)
#                             for label in story.get("labels", [])
#                             if label and label.strip()
#                         ],
#                         "issuetype": {"name": "Story"} 
#                     }
#                 }

#                 issue_url = f"{JIRA_BASE_URL}/ex/jira/{cloudid}{ISSUE_ENDPOINT}"
#                 issue_resp = await client.post(issue_url, headers=headers, json=issue_payload)

#                 if issue_resp.status_code in [200, 201]:
#                     created_issues.append(issue_resp.json())
#                 else:
#                     created_issues.append({
#                         "error": f"Failed to create issue for {story['title']}",
#                         "status": issue_resp.status_code,
#                         "details": issue_resp.json()
#                     })

#     return {
#         "created": created_issues,
#         "total": len(created_issues)
#     }