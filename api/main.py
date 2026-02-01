from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import logger
from api.database import ensure_schema
from api.utils import global_exception_handler
from api.routes import auth, movies, orders, referral

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Exception Handler
app.add_exception_handler(Exception, global_exception_handler)

# Register Routes
app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(orders.router)
app.include_router(referral.router)

@app.on_event("startup")
async def startup():
    await ensure_schema()

@app.get("/")
async def read_root():
    return {"status": "ok", "message": "API is running. Frontend at http://localhost:3000"}
