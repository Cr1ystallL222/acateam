from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel
from ..config import logger
from bots.services.logger_service import log_action

router = APIRouter()

class LogRequest(BaseModel):
    message: str
    level: str = "INFO"
    data: dict = {}

@router.post("/api/log/action")
async def api_log_action(payload: LogRequest, request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint for frontend to send logs to Telegram.
    """
    # client_ip = request.client.host
    # basic info
    
    formatted_msg = f"{payload.message}\n\nData: {payload.data}"
    
    # Use background task to not block response
    background_tasks.add_task(log_action, formatted_msg, payload.level)
    
    return {"status": "ok"}
