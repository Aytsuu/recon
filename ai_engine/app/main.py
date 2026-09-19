import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not (settings.supabase_url and settings.supabase_service_role_key):
        logger.warning(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are not set. "
            "The web app writes cases to Supabase, so transcription/process endpoints "
            "will return 404 case_not_found until Supabase is configured. "
            "Copy values from ai_engine/.env.example or run `supabase status`."
        )
    yield


app = FastAPI(
    title="Recon AI Engine",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
