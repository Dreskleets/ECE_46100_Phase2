"""
Main Application Entry Point.

Configures and launches the FastAPI application, middleware, and routers.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from src.api.experiment import router as experiment_router
from src.api.routes import router

# Trigger deploy
app = FastAPI(title="Trustworthy Model Registry", version="1.0.0", root_path="/default")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log Request
    # print(f"DEBUG: Request: {request.method} {request.url}") 
    
    response = await call_next(request)
    
    # Consuming response body in middleware is risky if not needed.
    # I'll enable standard logging without body capture to avoid bugs.
    # print(f"DEBUG: Response Status: {response.status_code}")
    
    return response

app.include_router(router)
app.include_router(experiment_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Lambda Handler
handler = Mangum(app)
