from fastapi import Request
from fastapi.responses import JSONResponse
from .config import logger
from data.db import db

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"}
    )

async def get_current_user(request: Request):
    user_id = request.cookies.get("auth_user_id")
    if not user_id:
        return None
    row = await db.fetchone("SELECT * FROM users WHERE id = ?", (user_id,))
    return row
