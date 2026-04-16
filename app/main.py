import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from fastapi import FastAPI

from app.api import admin, bundles, consumer, health, metrics, tracking

# Configure logging
def setup_logging():
    """Setup logging to both console and file."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Console handler (INFO level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (DEBUG level) - rotates when 10MB is reached
    file_handler = RotatingFileHandler(
        log_dir / "freshroute.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger

# Initialize logging
setup_logging()

app = FastAPI(
    title="FreshRoute",
    description="AI-powered food bundle recommendations to reduce retail waste",
    version="0.1.0",
)

origins = [
    "http://localhost:3000",    # Next.js/React
    "http://127.0.0.1:3000",
    "http://localhost:3001",    # Alternate local frontend port
    "http://127.0.0.1:3001",
]

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Cho phép các nguồn này truy cập
    allow_credentials=True,
    allow_methods=["*"],         # Cho phép GET, POST, OPTIONS, PUT, DELETE...
    allow_headers=["*"],         # Cho phép tất cả các Headers (Content-Type, Authorization...)
)

app.include_router(health.router, tags=["health"])
app.include_router(bundles.router, tags=["bundles"])
app.include_router(admin.router)
app.include_router(consumer.router)
app.include_router(tracking.router, tags=["tracking"])
app.include_router(metrics.router, tags=["metrics"])
