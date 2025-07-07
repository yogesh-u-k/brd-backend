from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import User
from user_auth import verify_password, create_access_token

router = APIRouter()

@router.post("/login")
async def login(name: str, password: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.name == name))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Invalid credentials",
                "status code": 401
            }
        )

    token = create_access_token(data={"sub": user.name})

    return {
        "message": "user logged in successfully",
        "user": {
            "name": user.name,
            "email": user.email
        },
        "status code": 200
    }
