from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from data.db import db
from api.utils import get_current_user
from api.config import logger
from datetime import datetime

router = APIRouter()

class ActivateCouponRequest(BaseModel):
    code: str

@router.post("/api/coupons/activate")
async def api_activate_coupon(payload: ActivateCouponRequest, request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    code = payload.code.strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Код не должен быть пустым")
        
    coupon = await db.fetchone("SELECT * FROM coupons WHERE code = ?", (code,))
    if not coupon:
        raise HTTPException(status_code=404, detail="Купон не найден")
        
    # Check max activations
    if coupon['max_activations'] is not None and coupon['current_activations'] >= coupon['max_activations']:
        raise HTTPException(status_code=400, detail="Лимит использования купона по количеству активаций исчерпан")
        
    # Check if already activated by this user
    existing = await db.fetchone("SELECT id FROM coupon_activations WHERE coupon_id = ? AND user_id = ?", (coupon['id'], user['id']))
    if existing:
        raise HTTPException(status_code=400, detail="Вы уже активировали этот купон ранее")
        
    # Check ownership
    # The coupon was created by a worker `telegram_user_id`
    # The user was referred by `referrer_user_id` (this is `users.id` of the worker)
    if not user.get('referrer_user_id'):
        raise HTTPException(status_code=400, detail="Этот купон недействителен для вашего аккаунта")
        
    worker_user = await db.fetchone("SELECT telegram_user_id FROM users WHERE id = ?", (user['referrer_user_id'],))
    if not worker_user or worker_user['telegram_user_id'] != coupon['telegram_user_id']:
        raise HTTPException(status_code=400, detail="Этот купон недействителен для вашего аккаунта")
        
    # Apply reward
    if coupon['type'] == 'balance':
        await db.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (coupon['value'], user['id']))
        msg = f"Ваш баланс успешно пополнен на {coupon['value']}₽!"
    else:
        await db.execute("UPDATE users SET active_discount = ? WHERE id = ?", (coupon['value'], user['id']))
        msg = f"Установлена скидка {coupon['value']}"
        if coupon['value'] <= 100:
            msg += "%!"
        else:
            msg += "₽!"
            
    # Record activation
    await db.execute("INSERT INTO coupon_activations (coupon_id, user_id) VALUES (?, ?)", (coupon['id'], user['id']))
    await db.execute("UPDATE coupons SET current_activations = current_activations + 1 WHERE id = ?", (coupon['id'],))
    
    logger.info(f"User {user['id']} activated coupon {code}")
    
    return {"status": "ok", "message": msg}
