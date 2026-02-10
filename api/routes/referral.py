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
async def api_referral_track(
    request: Request,
    background_tasks: BackgroundTasks,
    response: Response,
    ref: Optional[str] = None,
    cl: Optional[str] = None  # New: theatre link code
):
    # Determine which parameter to use
    link_code = cl  # Theatre link
    ref_code = ref  # Classic referral
    
    if not link_code and not ref_code:
        return {"status": "ignored", "reason": "no_ref"}

    ref_attached = request.cookies.get("ref_attached")
    visitor_id = request.cookies.get("visitor_id") or str(uuid.uuid4())
    
    user = await get_current_user(request)
    db_file = await get_db_path()
    
    # Resolve the referrer - either from theatre_links (cl=) or users (ref=)
    referrer_info = None  # (referrer_user_id, chat_id, link_settings)
    
    async with aiosqlite.connect(db_file) as db:
        if link_code:
            # Look up theatre link by link_code
            async with db.execute("""
                SELECT tl.telegram_user_id, bu.chat_id, tl.custom_city, tl.min_price_override, tl.max_price_override
                FROM theatre_links tl
                JOIN bot_users bu ON bu.telegram_user_id = tl.telegram_user_id
                WHERE tl.link_code = ?
            """, (link_code,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    # Get the user.id for this telegram_user_id
                    async with db.execute("SELECT id FROM users WHERE telegram_user_id = ?", (row[0],)) as cur2:
                        user_row = await cur2.fetchone()
                        if user_row:
                            referrer_info = {
                                "user_id": user_row[0],
                                "telegram_user_id": row[0],
                                "chat_id": row[1],
                                "link_settings": {
                                    "custom_city": row[2],
                                    "min_price_override": row[3],
                                    "max_price_override": row[4]
                                }
                            }
        elif ref_code:
            # Classic referral code lookup
            async with db.execute("SELECT id, telegram_user_id, chat_id FROM users WHERE referral_code = ?", (ref_code,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    referrer_info = {
                        "user_id": row[0],
                        "telegram_user_id": row[1],
                        "chat_id": row[2],
                        "link_settings": None
                    }
    
    # Use link_code or ref_code as the tracking identifier
    tracking_code = link_code or ref_code
    
    if user:
        # Authorized user - bind referrer if not already bound
        user_id = user['id']
        async with aiosqlite.connect(db_file) as db:
            async with db.execute("SELECT referrer_user_id FROM users WHERE id = ?", (user_id,)) as cursor:
                curr_referrer = (await cursor.fetchone())[0]
             
            if not curr_referrer and referrer_info and referrer_info["user_id"] != user_id:
                await db.execute("UPDATE users SET referrer_user_id = ? WHERE id = ?", (referrer_info["user_id"], user_id))
                await db.commit()
                logger.info(f"Attach referrer: buyer_id={user_id}, code={tracking_code}, referrer_user_id={referrer_info['user_id']}")
                if referrer_info.get("chat_id"):
                    background_tasks.add_task(send_telegram_message, referrer_info["chat_id"], "Новый пользователь привязался по твоей ссылке ✅")
        return {"status": "bound"}

    # Anonymous user - first touch logic
    if ref_attached:
        logger.info(f"Referral already attached: {ref_attached}, ignoring new code: {tracking_code}")
        return {"status": "ignored", "reason": "already_attached"}
    
    # FIRST VISIT - set cookies, create mamont, and notify
    logger.info(f"First referral visit: code={tracking_code}, visitor_id={visitor_id}")
    
    # Store the tracking code (use cl prefix for theatre links)
    cookie_value = f"cl:{link_code}" if link_code else ref_code
    response.set_cookie(key="ref_attached", value=cookie_value, max_age=2592000, path="/", samesite="lax")
    response.set_cookie(key="ref_pending", value=cookie_value, max_age=2592000, path="/", samesite="lax")
    if not request.cookies.get("visitor_id"):
        response.set_cookie(key="visitor_id", value=visitor_id, max_age=31536000, path="/", samesite="lax")

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Create mamont record and notify owner
    if referrer_info:
        async with aiosqlite.connect(db_file) as db:
            referrer_user_id = referrer_info["user_id"]
            
            # Check if mamont already exists for this visitor_id
            async with db.execute("SELECT mamont_id FROM mamonts WHERE visitor_id = ?", (visitor_id,)) as cursor:
                existing = await cursor.fetchone()
            
            if not existing:
                # Generate unique mamont_id and create record
                mamont_id = await generate_mamont_id(db)
                await db.execute("""
                    INSERT INTO mamonts (mamont_id, visitor_id, referrer_user_id, referral_code, status, created_at)
                    VALUES (?, ?, ?, ?, 'attached', ?)
                """, (mamont_id, visitor_id, referrer_user_id, tracking_code, datetime.now(timezone.utc).isoformat()))
                await db.commit()
                
                logger.info(f"Mamont created: mamont_id={mamont_id}, visitor_id={visitor_id}, referrer_user_id={referrer_user_id}")
                
                # Send mamont notification
                background_tasks.add_task(notify_mamont_visit, referrer_user_id, mamont_id)
            else:
                # Mamont already exists, just record visit
                background_tasks.add_task(handle_visit_background, tracking_code, client_ip, user_agent, visitor_id)
    else:
        # No owner found, just record visit
        background_tasks.add_task(handle_visit_background, tracking_code, client_ip, user_agent, visitor_id)
    
    return {"status": "tracked", "link_type": "theatre" if link_code else "classic"}

