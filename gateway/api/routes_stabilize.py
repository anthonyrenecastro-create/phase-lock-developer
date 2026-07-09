from fastapi import APIRouter, HTTPException

from gateway.core.schemas import FeedbackRequest, StabilizeRequest, StabilizeResponse
from gateway.core.service import StabilizationService

router = APIRouter(prefix="/v1", tags=["stabilization"])
service = StabilizationService()


@router.post("/stabilize", response_model=StabilizeResponse)
def stabilize(req: StabilizeRequest) -> StabilizeResponse:
    if req.text is None and req.embedding is None:
        raise HTTPException(status_code=400, detail="Provide at least one of: text, embedding")

    try:
        return service.stabilize(req)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal stabilization error")


@router.post("/feedback")
def feedback(req: FeedbackRequest) -> dict[str, str]:
    # Stub for MVP; wire to storage/event bus later.
    return {"status": "accepted", "request_id": req.request_id}


@router.get("/telemetry")
def telemetry() -> dict[str, object]:
    # Placeholder endpoint for Prometheus/OpenTelemetry integration.
    return {"status": "ok", "metrics": {}}
