from fastapi import FastAPI
from app.api import routes_profile, routes_jobs, routes_applications

app = FastAPI(title="Job Hunter AI Agent API")

@app.get("/")
def read_root():
    return {"message": "Job Hunter AI Agent API is running."}

# Include routers (placeholders for now)
# app.include_router(routes_profile.router)
# app.include_router(routes_jobs.router)
# app.include_router(routes_applications.router)
