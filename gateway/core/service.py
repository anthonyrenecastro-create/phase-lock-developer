from typing import Any

from phase_lock_core import DriftEngine

from gateway.core.policy import actions_for_risk, classify_risk
from gateway.core.schemas import StabilizeRequest, StabilizeResponse


class StabilizationService:
    def __init__(self) -> None:
        self.engine = DriftEngine(nx=18, ny=18, n_fields=10, seed=7)

    def stabilize(self, req: StabilizeRequest) -> StabilizeResponse:
        out: dict[str, Any] = self.engine.stabilize(
            metric_window=req.metric_window,
            embedding=req.embedding,
        )

        drift_score = float(out["drift_score"])
        risk = classify_risk(drift_score)
        actions = actions_for_risk(risk)

        return StabilizeResponse(
            request_id=req.request_id,
            stabilized_vector=[float(x) for x in out["stabilized_vector"]],
            drift_score=drift_score,
            risk_level=risk,
            actions=actions,
            diagnostics={
                "euler_chi": float(out.get("euler_chi", 0.0)),
                "genus": float(out.get("genus", 0.0)),
                "beta0": float(out.get("beta0", 0.0)),
                "beta1": float(out.get("beta1", 0.0)),
            },
        )
