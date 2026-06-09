from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.datasets import router as datasets_router
from app.api.models import router as models_router
from app.config import get_settings
from app.database import Base, engine
from app.db_models import Dataset, DatasetColumn, MLModel, ModelMetric, TrainingRun, User


settings = get_settings()
_ = (Dataset, DatasetColumn, MLModel, ModelMetric, TrainingRun, User)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Backend API for OPNs-SVM/SVR based IgAN research analysis.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(datasets_router)
app.include_router(models_router)


@app.get("/api/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}
