# phase-lock-rag-api-llm-data-drift-preventer

An API gateway that helps reduce LLM/data drift by stabilizing noisy metric streams into a bounded 24-D representation.

## MVP Architecture

- Rust core (`phase_lock_core`): deterministic 24-D stabilization engine with drift scoring and topology-inspired diagnostics.
- Python FastAPI gateway: `/v1/stabilize`, `/v1/feedback`, `/v1/telemetry`, `/v1/health`.

## Repository Layout

```text
gateway/
  main.py
  api/routes_stabilize.py
  core/{schemas.py,policy.py,service.py}
rust/
  Cargo.toml
  pyproject.toml
  src/{lib.rs,engine.rs}
```

## Quickstart

### 1) Build and install Rust extension

```bash
cd rust
python -m pip install -U pip maturin
maturin develop --release
cd ..
```

### 2) Install Python dependencies

```bash
python -m pip install -r requirements-dev.txt
```

### 3) Run API

```bash
uvicorn gateway.main:app --reload --port 8000
```

## Example request

```bash
curl -X POST "http://127.0.0.1:8000/v1/stabilize" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id":"acme",
    "request_id":"req-001",
    "metric_window":[0.1,0.2,0.12,0.25,0.4,0.33,0.29,0.31,0.28,0.35,0.37,0.34,0.3,0.27,0.26,0.24,0.22,0.2,0.19,0.18,0.21,0.23,0.25,0.2],
    "embedding":[0.01,-0.02,0.03,0.04],
    "metadata":{"source":"mvp-test"}
  }'
```

Expected response shape:

```json
{
  "request_id": "req-001",
  "stabilized_vector": [0.0, 0.0, 0.0],
  "drift_score": 0.0,
  "risk_level": "green",
  "actions": ["pass"],
  "diagnostics": {
    "euler_chi": 0.0,
    "genus": 0.0,
    "beta0": 1.0,
    "beta1": 0.0
  }
}
```

## Notes

- `metric_window` must contain at least 24 values.
- Output vector is always bounded in `[-1, 1]` and length 24.
- Drift score is bounded in `[0, 1]`.
