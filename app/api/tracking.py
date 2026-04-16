from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.db.postgres import get_db_session
from app.core.models.bundle import BundleEvent
from app.core.pipeline.p8_tracking import log_event

router = APIRouter()


@router.post("/events", status_code=202)
async def post_event(
    event: BundleEvent,
    background_tasks: BackgroundTasks,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Log user interaction event. Returns 202 immediately."""
    background_tasks.add_task(log_event, event, db_session)
    return {"status": "accepted"}
