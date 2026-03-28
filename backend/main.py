import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pythonjsonlogger import jsonlogger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import settings
from limiter import limiter

load_dotenv()


def _setup_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    handler = logging.StreamHandler()
    # JSON in production (Render sets PORT), human-readable locally
    if os.getenv("PORT"):
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
    else:
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    root.addHandler(handler)


_setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from services.conversation_service import init_db
    from services.matcher_service import load_products
    from services.realtime_cv_service import load_reference_templates
    from services.scoring_service import load_rules

    logger.info("========================================")
    logger.info("Loading products and rules into cache...")
    logger.info("========================================")
    init_db()
    load_products()
    load_rules()
    load_reference_templates()

    # Always warm the OCR engine at startup so the first real request
    # doesn't pay the model-load cost. RapidOCR downloads its ONNX models
    # on first construction; subsequent calls are instant.
    from services.ocr_service import get_engine
    logger.info("Warming RapidOCR engine...")
    get_engine()

    logger.info("Startup complete.")
    yield
    logger.info("Shutting down.")
    logger.info("========================================")


app = FastAPI(
    title="VeriMed API",
    description="Medicine authenticity risk assessment via OCR, barcode, and deterministic scoring.",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins_list = [o.strip() for o in settings.allowed_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routes.verify import router as verify_router
from routes.conversation import router as conversation_router
from routes.realtime_detect import router as realtime_detect_router

app.include_router(verify_router, prefix="/api")
app.include_router(conversation_router, prefix="/api")
app.include_router(realtime_detect_router, prefix="/api")


@app.get("/")
def root():
    return {"status": "VeriMed API running..."}


@app.get("/health")
def health():
    return {"status": "ok"}
