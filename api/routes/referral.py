import uuid
import aiosqlite
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Response, BackgroundTasks

from ..config import logger
from ..database import get_db_path
from ..utils import get_current_user
from ..services.mamont import generate_mamont_id
from ..services.notifications import handle_visit_background, notify_mamont_visit, send_telegram_message

router = APIRouter()

@router.get("/api/referral/track")
async def api_referral_track(request: Request, background_tasks: BackgroundTasks, response: Response, ref: Optional[str] = None):
    if not ref:
        return {"status": "ignored", "reason": "no_ref"}

    ref_attached = request.cookies.get("ref_attached")
    visitor_id = request.cookies.get("visitor_id") or str(uuid.uuid4())
    
    user = await get_current_user(request)
    
    if user:
        # Authorized user - bind referrer if not already bound
        user_id = user['id']
        db_file = await get_db_path()
        async with aiosqlite.connect(db_file) as db:
            async with db.execute("SELECT referrer_user_id FROM users WHERE id = ?", (user_id,)) as cursor:
                curr_referrer = (await cursor.fetchone())[0]
             
            if not curr_referrer:
                async with db.execute("SELECT id, chat_id FROM users WHERE referral_code = ?", (ref,)) as cursor:
                    owner_row = await cursor.fetchone()
                    if owner_row and owner_row[0] != user_id:
                        await db.execute("UPDATE users SET referrer_user_id = ? WHERE id = ?", (owner_row[0], user_id))
                        await db.commit()
                        logger.info(f"Attach referrer: buyer_id={user_id}, ref_code={ref}, referrer_user_id={owner_row[0]}")
                        background_tasks.add_task(send_telegram_message, owner_row[1], "Новый пользователь привязался по твоей ссылке ✅")
        return {"status": "bound"}

    # Anonymous user - first touch logic
    if ref_attached:
        logger.info(f"Referral already attached: {ref_attached}, ignoring new ref: {ref}")
        return {"status": "ignored", "reason": "already_attached"}
    
    # FIRST VISIT - set cookies, create mamont, and notify
    logger.info(f"First referral visit: ref={ref}, visitor_id={visitor_id}")
    
    response.set_cookie(key="ref_attached", value=ref, max_age=2592000, path="/", samesite="lax")
    response.set_cookie(key="ref_pending", value=ref, max_age=2592000, path="/", samesite="lax")
    if not request.cookies.get("visitor_id"):
        response.set_cookie(key="visitor_id", value=visitor_id, max_age=31536000, path="/", samesite="lax")

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Create mamont record and notify owner
    db_file = await get_db_path()
    async with aiosqlite.connect(db_file) as db:
        # Find referrer
        async with db.execute("SELECT id, chat_id FROM users WHERE referral_code = ?", (ref,)) as cursor:
            owner = await cursor.fetchone()
        
        if owner:
            referrer_user_id = owner[0]
            
            # Check if mamont already exists for this visitor_id
            async with db.execute("SELECT mamont_id FROM mamonts WHERE visitor_id = ?", (visitor_id,)) as cursor:
                existing = await cursor.fetchone()
            
            if not existing:
                # Generate unique mamont_id and create record
                mamont_id = await generate_mamont_id(db)
                await db.execute("""
                    INSERT INTO mamonts (mamont_id, visitor_id, referrer_user_id, referral_code, status, created_at)
                    VALUES (?, ?, ?, ?, 'attached', ?)
                """, (mamont_id, visitor_id, referrer_user_id, ref, datetime.now(timezone.utc).isoformat()))
                await db.commit()
                
                logger.info(f"Mamont created: mamont_id={mamont_id}, visitor_id={visitor_id}, referrer_user_id={referrer_user_id}")
                
                # Send mamont notification instead of generic visit notification
                background_tasks.add_task(notify_mamont_visit, referrer_user_id, mamont_id)
            else:
                # Mamont already exists, just record visit
                background_tasks.add_task(handle_visit_background, ref, client_ip, user_agent, visitor_id)
        else:
            # No owner found, just record visit
            background_tasks.add_task(handle_visit_background, ref, client_ip, user_agent, visitor_id)
    
    return {"status": "tracked"}
