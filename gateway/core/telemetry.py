from dataclasses import asdict, dataclass
from threading import Lock
from time import perf_counter


@dataclass
class TelemetrySnapshot:
    requests_total: int
    stabilize_success_total: int
    stabilize_error_total: int
    drift_incidents_prevented: int
    feedback_total: int
    false_positive_total: int
    p95_latency_ms: float


class TelemetryStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._requests_total = 0
        self._stabilize_success_total = 0
        self._stabilize_error_total = 0
        self._drift_incidents_prevented = 0
        self._feedback_total = 0
        self._false_positive_total = 0
        self._latencies_ms: list[float] = []

    def start_timer(self) -> float:
        return perf_counter()

    def observe_stabilize(self, started_at: float, success: bool, prevented_incident: bool) -> None:
        elapsed_ms = (perf_counter() - started_at) * 1000.0
        with self._lock:
            self._requests_total += 1
            if success:
                self._stabilize_success_total += 1
            else:
                self._stabilize_error_total += 1
            if prevented_incident:
                self._drift_incidents_prevented += 1
            self._latencies_ms.append(elapsed_ms)
            if len(self._latencies_ms) > 5000:
                self._latencies_ms = self._latencies_ms[-5000:]

    def observe_feedback(self, corrected: bool, risk_level: str | None) -> None:
        with self._lock:
            self._feedback_total += 1
            if corrected and risk_level == "green":
                self._false_positive_total += 1

    def snapshot(self) -> TelemetrySnapshot:
        with self._lock:
            latencies = sorted(self._latencies_ms)
            if not latencies:
                p95 = 0.0
            else:
                index = max(0, min(len(latencies) - 1, int(0.95 * (len(latencies) - 1))))
                p95 = float(latencies[index])

            return TelemetrySnapshot(
                requests_total=self._requests_total,
                stabilize_success_total=self._stabilize_success_total,
                stabilize_error_total=self._stabilize_error_total,
                drift_incidents_prevented=self._drift_incidents_prevented,
                feedback_total=self._feedback_total,
                false_positive_total=self._false_positive_total,
                p95_latency_ms=p95,
            )

    def as_json(self) -> dict[str, float | int]:
        return asdict(self.snapshot())

    def reset(self) -> None:
        with self._lock:
            self._requests_total = 0
            self._stabilize_success_total = 0
            self._stabilize_error_total = 0
            self._drift_incidents_prevented = 0
            self._feedback_total = 0
            self._false_positive_total = 0
            self._latencies_ms = []

    def as_prometheus(self) -> str:
        s = self.snapshot()
        lines = [
            "# TYPE gateway_requests_total counter",
            f"gateway_requests_total {s.requests_total}",
            "# TYPE gateway_stabilize_success_total counter",
            f"gateway_stabilize_success_total {s.stabilize_success_total}",
            "# TYPE gateway_stabilize_error_total counter",
            f"gateway_stabilize_error_total {s.stabilize_error_total}",
            "# TYPE gateway_drift_incidents_prevented_total counter",
            f"gateway_drift_incidents_prevented_total {s.drift_incidents_prevented}",
            "# TYPE gateway_feedback_total counter",
            f"gateway_feedback_total {s.feedback_total}",
            "# TYPE gateway_false_positive_total counter",
            f"gateway_false_positive_total {s.false_positive_total}",
            "# TYPE gateway_stabilize_latency_p95_ms gauge",
            f"gateway_stabilize_latency_p95_ms {s.p95_latency_ms:.3f}",
        ]
        return "\n".join(lines) + "\n"


telemetry_store = TelemetryStore()
