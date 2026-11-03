
from datetime import date
from typing import Optional
from app.core.init_db import create_tables
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.services.quote_aggregator import (
    find_vehicle,
    get_insurance_quotes,
)
from app.api.selections import router as selections_router

# Create the application FIRST
app = FastAPI(
    title="AutoCover API",
    description="Vehicle insurance quote comparison API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers AFTER creating app
app.include_router(selections_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "AutoCover API",
    }


@app.get("/api/providers")
def get_providers():
    return {
        "providers": [
            {"id": "A", "name": "Provider A"},
            {"id": "B", "name": "Provider B"},
            {"id": "C", "name": "Provider C"},
            {"id": "D", "name": "Provider D"},
        ]
    }


@app.get("/api/vehicles/{registration}")
def get_vehicle(registration: str):
    vehicle = find_vehicle(registration)

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found in registry",
        )

    return vehicle.model_dump(mode="json")


@app.get("/api/quotes/{registration}")
def get_quotes(
    registration: str,
    quote_date: Optional[date] = Query(default=None),
):
    try:
        result = get_insurance_quotes(
            registration,
            quote_date=quote_date,
        )
        return result.model_dump(mode="json")

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

@app.on_event("startup")
def startup_event():
    create_tables()