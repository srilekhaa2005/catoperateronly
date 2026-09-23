from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .routers.health import router as health_router
from .routers.operators import router as operators_router
from .routers.tasks import router as tasks_router
from .routers.machines import router as machines_router
from .routers.alerts import router as alerts_router
from .routers.training import router as training_router
from .routers.incidents import router as incidents_router

app = FastAPI(title="CAT Operator Copilot API", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
for router in [health_router, operators_router, tasks_router, machines_router, alerts_router, training_router, incidents_router]:
    app.include_router(router, prefix="/api")

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"error": {"code": "BAD_REQUEST", "message": str(exc)}})

@app.get("/")
def root():
    return {"name": "CAT Operator Copilot API", "status": "running"}
