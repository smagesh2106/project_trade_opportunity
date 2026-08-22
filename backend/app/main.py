from fastapi import FastAPI

from app.api.v1.endpoints import countries, health, hs_codes, hs_versions


app = FastAPI(
    title="Trade Opportunity Explorer API",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "application": "Trade Opportunity Explorer",
        "status": "running",
    }


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
    }


app.include_router(
    health.router,
    prefix="/api/v1/health",
    tags=["Health"],
)

app.include_router(
    countries.router,
    prefix="/api/v1",
    tags=["Countries"],
)
app.include_router(
    hs_versions.router,
    prefix="/api/v1",
    tags=["HS Versions"],
)

app.include_router(
    hs_codes.router,
    prefix="/api/v1",
    tags=["HS Codes"],
)
