from fastapi import APIRouter
from ..config import MOVIES

router = APIRouter()

@router.get("/api/movies")
async def api_movies():
    return MOVIES
