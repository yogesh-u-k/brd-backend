from fastapi import APIRouter

router = APIRouter()

@router.get("/",tags=["Base"])
def jira_home():
    return {"message": "Welcome to the Jira routes"}
