from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from gateway.core.auth import require_api_key
from gateway.core.schemas import FeedbackRequest, StabilizeRequest, StabilizeResponse
from gateway.core.service import StabilizationService
from gateway.core.telemetry import telemetry_store

router = APIRouter(prefix="/v1", tags=["stabilization"])
service = StabilizationService()


@router.post("/stabilize", response_model=StabilizeResponse)
def stabilize(req: StabilizeRequest, _: None = Depends(require_api_key)) -> StabilizeResponse:
    started_at = telemetry_store.start_timer()

    if req.text is None and req.embedding is None:
        telemetry_store.observe_stabilize(started_at=started_at, success=False, prevented_incident=False)
        raise HTTPException(status_code=400, detail="Provide at least one of: text, embedding")

    try:
        out = service.stabilize(req)
        prevented = "fallback-model" in out.actions or "human-review" in out.actions
        telemetry_store.observe_stabilize(started_at=started_at, success=True, prevented_incident=prevented)
        return out
    except ValueError as e:
        telemetry_store.observe_stabilize(started_at=started_at, success=False, prevented_incident=False)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        telemetry_store.observe_stabilize(started_at=started_at, success=False, prevented_incident=False)
        raise HTTPException(status_code=500, detail="Internal stabilization error")


@router.post("/feedback")
def feedback(req: FeedbackRequest, _: None = Depends(require_api_key)) -> dict[str, str]:
    telemetry_store.observe_feedback(corrected=req.corrected, risk_level=req.observed_risk_level)
    return {"status": "accepted", "request_id": req.request_id}


@router.get("/telemetry", response_model=None)
def telemetry(format: str = "json", _: None = Depends(require_api_key)) -> object:
    if format == "prometheus":
        return PlainTextResponse(telemetry_store.as_prometheus(), media_type="text/plain; version=0.0.4")

    return {
        "status": "ok",
        "metrics": telemetry_store.as_json(),
    }
