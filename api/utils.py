import aiosqlite
from fastapi import Request
from fastapi.responses import JSONResponse
from .config import logger
from .database import get_db_path

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
    db_file = await get_db_path()
    async with aiosqlite.connect(db_file) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row
