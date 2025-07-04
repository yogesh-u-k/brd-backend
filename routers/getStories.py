from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

@router.post("/get-stories")
async def get_stories(request: Request):
    try:
        applications = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if not isinstance(applications, list):
        raise HTTPException(status_code=400, detail="Payload should be a list of applications")

    flattened_stories = []

    for app in applications:
        app_name = app.get("application")
        stories = app.get("stories", [])
        
        if not app_name or not isinstance(stories, list):
            continue  # Skip if structure is wrong

        for story in stories:
            flattened_stories.append({
                "application": app_name,
                "title": story.get("title"),
                "description": story.get("description"),
                "labels": story.get("labels", [])
            })

    print("Flattened Stories:", flattened_stories)
    return {"stories": flattened_stories}
