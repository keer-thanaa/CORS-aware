import time
import uuid

import jwt
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ---- Task 1 config (Metrics API) ----
ALLOWED_ORIGIN = "https://dash-n818qz.example.com"
EMAIL = "24f2003019@ds.study.iitm.ac.in"

# ---- Task 2 config (Token Verification) ----
ISSUER = "https://idp.exam.local"
AUDIENCE = "tds-vtxbjojl.apps.exam.local"
PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""

app = FastAPI(title="OAuth/CORS Combined API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
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


# ---------------- Task 1: /stats ----------------

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


# ---------------- Task 2: /verify ----------------

class VerifyRequest(BaseModel):
    token: str


@app.post("/verify")
async def verify_token(body: VerifyRequest):
    try:
        claims = jwt.decode(
            body.token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            audience=AUDIENCE,
            issuer=ISSUER,
            options={"require": ["exp", "iss", "aud"]},
        )
    except jwt.PyJWTError:
        return JSONResponse(status_code=401, content={"valid": False})

    return {
        "valid": True,
        "email": claims.get("email"),
        "sub": claims.get("sub"),
        "aud": claims.get("aud"),
    }


@app.get("/")
async def root():
    return {"status": "ok", "service": "oauth-cors-combined-api"}
