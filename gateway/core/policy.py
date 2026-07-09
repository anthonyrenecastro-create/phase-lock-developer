from typing import Literal

RiskLevel = Literal["green", "yellow", "red"]
ActionType = Literal["pass", "clamp", "retry", "fallback_model", "human_review"]


def classify_risk(drift_score: float) -> RiskLevel:
    if drift_score < 0.20:
        return "green"
    if drift_score < 0.45:
        return "yellow"
    return "red"


def actions_for_risk(risk: RiskLevel) -> list[ActionType]:
    if risk == "green":
        return ["pass"]
    if risk == "yellow":
        return ["clamp", "retry"]
    return ["fallback_model", "human_review"]
