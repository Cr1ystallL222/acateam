import uuid
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Response, BackgroundTasks

from ..config import logger
from ..utils import get_current_user
from ..services.mamont import generate_mamont_id
from ..services.notifications import handle_visit_background, notify_mamont_visit, send_telegram_message
from data.db import db

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
    link_code = cl  # Theatre/Cinema link
    ref_code = ref  # Classic referral
    
    if not link_code and not ref_code:
        return {"status": "ignored", "reason": "no_ref"}

    ref_attached = request.cookies.get("ref_attached")
    visitor_id = request.cookies.get("visitor_id") or str(uuid.uuid4())
    
    user = await get_current_user(request)
    
    # Resolve the referrer - either from theatre_links/cinema_links (cl=) or users (ref=)
    referrer_info = None  # (referrer_user_id, chat_id, link_settings)
    service_name = "Театр"  # Default service name for notification
    
    if link_code:
        # Look up theatre link by link_code
        row = await db.fetchone("""
            SELECT tl.telegram_user_id, bu.chat_id, tl.custom_city, tl.min_price_override, tl.max_price_override
            FROM theatre_links tl
            JOIN bot_users bu ON bu.telegram_user_id = tl.telegram_user_id
            WHERE tl.link_code = ?
        """, (link_code,))
        if row:
            # Get the user.id for this telegram_user_id (sync if needed)
            from ..utils import ensure_global_user
            user_row = await ensure_global_user(row['telegram_user_id'])
            
            if user_row:
                service_name = "Театр"
                referrer_info = {
                    "user_id": user_row['id'],
                    "telegram_user_id": row['telegram_user_id'],
                    "chat_id": row['chat_id'],
                    "link_settings": {
                        "custom_city": row['custom_city'],
                        "min_price_override": row['min_price_override'],
                        "max_price_override": row['max_price_override']
                    }
                }
        else:
            # Check cinema links
            row = await db.fetchone("""
                SELECT cl.telegram_user_id, bu.chat_id, cl.custom_city, cl.min_price_override, cl.max_price_override
                FROM cinema_links cl
                JOIN bot_users bu ON bu.telegram_user_id = cl.telegram_user_id
                WHERE cl.link_code = ?
            """, (link_code,))
            if row:
                from ..utils import ensure_global_user
                user_row = await ensure_global_user(row['telegram_user_id'])
                if user_row:
                    service_name = "Кино"
                    referrer_info = {
                        "user_id": user_row['id'],
                        "telegram_user_id": row['telegram_user_id'],
                        "chat_id": row['chat_id'],
                        "link_settings": {
                            "custom_city": row['custom_city'],
                            "min_price_override": row['min_price_override'],
                            "max_price_override": row['max_price_override']
                        }
                    }
    elif ref_code:
        # Classic referral code lookup
        row = await db.fetchone("SELECT id, telegram_user_id, chat_id FROM users WHERE referral_code = ?", (ref_code,))
        if row:
            referrer_info = {
                "user_id": row['id'],
                "telegram_user_id": row['telegram_user_id'],
                "chat_id": row['chat_id'],
                "link_settings": None
            }
    
    # Use link_code or ref_code as the tracking identifier
    tracking_code = link_code or ref_code
    
    if user:
        # Authorized user - bind referrer if not already bound
        user_id = user['id']
        ref_row = await db.fetchone("SELECT referrer_user_id FROM users WHERE id = ?", (user_id,))
        curr_referrer = ref_row['referrer_user_id'] if ref_row else None
             
        if not curr_referrer and referrer_info and referrer_info["user_id"] != user_id:
            await db.execute("UPDATE users SET referrer_user_id = ? WHERE id = ?", (referrer_info["user_id"], user_id))
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
        referrer_user_id = referrer_info["user_id"]
        
        # Check if mamont already exists for this visitor_id
        existing = await db.fetchone("SELECT mamont_id FROM mamonts WHERE visitor_id = ?", (visitor_id,))
        
        if not existing:
            # Generate unique mamont_id and create record
            mamont_id = await generate_mamont_id()
            await db.execute("""
                INSERT INTO mamonts (mamont_id, visitor_id, referrer_user_id, referral_code, status, created_at)
                VALUES (?, ?, ?, ?, 'attached', ?)
            """, (mamont_id, visitor_id, referrer_user_id, tracking_code, datetime.utcnow()))
            
            logger.info(f"Mamont created: mamont_id={mamont_id}, visitor_id={visitor_id}, referrer_user_id={referrer_user_id}, service={service_name}")
            
            # Send mamont notification with service type
            background_tasks.add_task(notify_mamont_visit, referrer_user_id, mamont_id, service_name, client_ip, user_agent)
        else:
            # Mamont already exists, just record visit
            background_tasks.add_task(handle_visit_background, tracking_code, client_ip, user_agent, visitor_id, referrer_user_id)
    else:
        # No owner found, look it up in background (will likely fail based on current logic, but keeps behavior)
        background_tasks.add_task(handle_visit_background, tracking_code, client_ip, user_agent, visitor_id)
    
    return {"status": "tracked", "link_type": "theatre" if link_code else "classic"}
