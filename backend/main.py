import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# load_dotenv populates os.environ for libraries that read it directly.
# config.Settings (pydantic-settings) also reads .env independently.
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up cached loaders at startup
    from services.conversation_service import init_db
    from services.matcher_service import load_products
    from services.realtime_cv_service import load_reference_templates
    from services.scoring_service import load_rules
    from services.ocr_service import get_reader

    logger.info("========================================")
    logger.info("Loading products and rules into cache...")
    logger.info("========================================")
    init_db()
    load_products()
    load_rules()
    load_reference_templates()
    logger.info("Warming EasyOCR reader...")
    get_reader()
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

# Configure CORS for production
import os
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000")
allowed_origins_list = [origin.strip() for origin in allowed_origins_str.split(",")]

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


@app.get("/api/health")
def health():
    return {"status": "Verimed API ie healthy..."}
