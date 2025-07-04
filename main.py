from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import base, auth, issues,load,getStories
import uvicorn
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# No prefix applied to routers
app.include_router(base.router, tags=["Base"])
app.include_router(auth.router, tags=["Auth"])
app.include_router(issues.router, tags=["Issues"])
app.include_router(load.router, tags=["load"]) 
app.include_router(getStories.router, tags=["getStories"])  

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
