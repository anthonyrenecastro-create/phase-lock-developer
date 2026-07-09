from fastapi import FastAPI

from gateway.api.routes_stabilize import router as stabilize_router

app = FastAPI(title="Phase-Lock Drift Prevention Gateway", version="0.1.0")
app.include_router(stabilize_router)


@app.get("/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
