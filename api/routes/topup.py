from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import aiosqlite

from ..config import logger
from ..database import get_db_path
from ..utils import get_current_user

router = APIRouter()


class TopUpCreateRequest(BaseModel):
    amount: int


class TopUpStatusRequest(BaseModel):
    deposit_id: int


@router.post("/api/topup/create")
async def api_topup_create(payload: TopUpCreateRequest, request: Request, background_tasks: BackgroundTasks):
    """Create a new top-up request."""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if payload.amount < 2000:
        raise HTTPException(status_code=400, detail="Минимальная сумма пополнения — 2000₽")
    
    db_file = await get_db_path()
    
    async with aiosqlite.connect(db_file) as db:
        db.row_factory = aiosqlite.Row
        
        # Check for existing pending deposit
        async with db.execute("""
            SELECT id FROM deposits 
            WHERE user_id = ? AND status IN ('pending', 'awaiting_requisites', 'requisites_sent')
        """, (user['id'],)) as cursor:
            existing = await cursor.fetchone()
            if existing:
                raise HTTPException(status_code=400, detail="У вас уже есть активная заявка на пополнение")
        
        # Create deposit
        cursor = await db.execute("""
            INSERT INTO deposits (user_id, amount, status)
            VALUES (?, ?, 'pending')
        """, (user['id'], payload.amount))
        deposit_id = cursor.lastrowid
        await db.commit()
    
    # Send notification to Telegram group (will be handled by bot)
    # Import here to avoid circular imports
    from .topup_notify import send_topup_notification
    # Convert user to dict in case it's sqlite3.Row
    user_dict = dict(user) if hasattr(user, 'keys') else user
    background_tasks.add_task(send_topup_notification, deposit_id, user_dict, payload.amount)
    
    logger.info(f"Deposit created: id={deposit_id}, user_id={user['id']}, amount={payload.amount}")
    
    return {"status": "ok", "deposit_id": deposit_id}


@router.get("/api/topup/status")
async def api_topup_status(deposit_id: int, request: Request):
    """Get status of a top-up request."""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    db_file = await get_db_path()
    
    async with aiosqlite.connect(db_file) as db:
        db.row_factory = aiosqlite.Row
        
        async with db.execute("""
            SELECT * FROM deposits WHERE id = ? AND user_id = ?
        """, (deposit_id, user['id'])) as cursor:
            deposit = await cursor.fetchone()
        
        if not deposit:
            raise HTTPException(status_code=404, detail="Заявка не найдена")
        
        deposit = dict(deposit)
        
        # Check if expired
        if deposit['status'] == 'requisites_sent' and deposit['expires_at']:
            expires_at = datetime.fromisoformat(str(deposit['expires_at']))
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if datetime.now(timezone.utc) > expires_at:
                # Mark as expired
                await db.execute("UPDATE deposits SET status = 'expired' WHERE id = ?", (deposit_id,))
                await db.commit()
                deposit['status'] = 'expired'
        
        return {
            "deposit_id": deposit['id'],
            "status": deposit['status'],
            "amount": deposit['amount'],
            "requisites": deposit['requisites'],
            "bank_name": deposit['bank_name'],
            "exact_amount": deposit['exact_amount'],
            "expires_at": deposit['expires_at']
        }


@router.post("/api/topup/cancel")
async def api_topup_cancel(deposit_id: int, request: Request, background_tasks: BackgroundTasks):
    """Cancel a top-up request."""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    db_file = await get_db_path()
    
    async with aiosqlite.connect(db_file) as db:
        db.row_factory = aiosqlite.Row
        
        async with db.execute("""
            SELECT * FROM deposits WHERE id = ? AND user_id = ?
        """, (deposit_id, user['id'])) as cursor:
            deposit = await cursor.fetchone()
        
        if not deposit:
            raise HTTPException(status_code=404, detail="Заявка не найдена")
        
        deposit = dict(deposit)
        
        if deposit['status'] in ('completed', 'expired', 'cancelled'):
            raise HTTPException(status_code=400, detail="Заявка уже завершена")
        
        # Cancel the deposit
        await db.execute("UPDATE deposits SET status = 'cancelled' WHERE id = ?", (deposit_id,))
        await db.commit()
    
    # Notify group about cancellation
    from .topup_notify import send_cancel_notification
    user_dict = dict(user) if hasattr(user, 'keys') else user
    background_tasks.add_task(send_cancel_notification, deposit, user_dict)
    
    logger.info(f"Deposit cancelled: id={deposit_id}, user_id={user['id']}")
    
    return {"status": "ok"}


@router.post("/api/topup/paid")
async def api_topup_paid(deposit_id: int, request: Request, background_tasks: BackgroundTasks):
    """User clicked 'I paid' button."""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    db_file = await get_db_path()
    
    async with aiosqlite.connect(db_file) as db:
        db.row_factory = aiosqlite.Row
        
        async with db.execute("""
            SELECT * FROM deposits WHERE id = ? AND user_id = ?
        """, (deposit_id, user['id'])) as cursor:
            deposit = await cursor.fetchone()
        
        if not deposit:
            raise HTTPException(status_code=404, detail="Заявка не найдена")
        
        deposit = dict(deposit)
        
        if deposit['status'] != 'requisites_sent':
            raise HTTPException(status_code=400, detail="Невозможно подтвердить оплату")
        
        # Update status to awaiting_confirmation
        await db.execute("UPDATE deposits SET status = 'awaiting_confirmation' WHERE id = ?", (deposit_id,))
        await db.commit()
    
    # Notify group about payment
    from .topup_notify import send_paid_notification
    user_dict = dict(user) if hasattr(user, 'keys') else user
    background_tasks.add_task(send_paid_notification, deposit, user_dict)
    
    logger.info(f"Deposit paid clicked: id={deposit_id}, user_id={user['id']}")
    
    return {"status": "ok"}
