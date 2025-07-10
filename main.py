from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import base, auth, issues,load,getStories,createStories,getProjects,uselogin,registration, agent,Documentagent
import uvicorn
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://brd-to-jira.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# No prefix applied to routers
app.include_router(base.router, tags=["Base"])
app.include_router(auth.router, tags=["Auth"])
app.include_router(issues.router, tags=["Issues"])
app.include_router(load.router, tags=["load"]) 
app.include_router(getStories.router, tags=["getStories"])  
app.include_router(createStories.router, tags=["createStories"])  
app.include_router(getProjects.router,  tags=["getProjects"])
app.include_router(uselogin.router, tags=["uselogin"])
app.include_router(registration.router, tags=["registration"])
app.include_router(agent.router, tags=["agent"])
app.include_router(Documentagent.router, tags=["agent"])


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
