import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ---- Assigned config ----
ALLOWED_ORIGIN = "https://dash-n818qz.example.com"
EMAIL = "REPLACE_WITH_YOUR_LOGIN_EMAIL"  # <-- put your exact logged-in email here

app = FastAPI(title="CORS-Aware Metrics API")

# Strict per-origin CORS: only ALLOWED_ORIGIN ever gets the ACAO header.
# Starlette's CORSMiddleware handles preflight (OPTIONS) automatically:
# - allowed origin -> Access-Control-Allow-Origin echoed back
# - any other origin -> no ACORS headers added (request still gets a response,
#   but without ACAO, so the browser/grader treats it as rejected)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    start = time.perf_counter()
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{elapsed:.6f}"
    return response


@app.get("/stats")
async def get_stats(values: str):
    try:
        nums = [int(v.strip()) for v in values.split(",") if v.strip() != ""]
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={"error": "values must be a comma-separated list of integers"},
        )

    if not nums:
        return JSONResponse(
            status_code=400,
            content={"error": "no integers provided in 'values'"},
        )

    count = len(nums)
    total = sum(nums)
    mean = total / count

    return {
        "email": EMAIL,
        "count": count,
        "sum": total,
        "min": min(nums),
        "max": max(nums),
        "mean": mean,
    }


@app.get("/")
async def root():
    return {"status": "ok", "service": "cors-aware-metrics-api"}
