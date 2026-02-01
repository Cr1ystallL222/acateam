from fastapi import APIRouter, Request, BackgroundTasks
import aiosqlite

from ..config import logger
from ..database import get_db_path
from ..models import PaymentRequest
from ..utils import get_current_user
from ..services.notifications import notification_purchase, notify_mamont_purchase

router = APIRouter()

@router.post("/api/orders/pay")
async def api_orders_pay(payload: PaymentRequest, request: Request, background_tasks: BackgroundTasks):
    price_per_ticket = 500
    total_price = payload.qty * price_per_ticket
    
    user = await get_current_user(request)
    user_id = user['id'] if user else None
    
    logger.info(f"Pay: starting, user_id={user_id}, movie={payload.movie}, qty={payload.qty}")
    
    if not user_id:
        logger.warning("Pay: No auth cookie - buyer is anonymous")
    
    db_file = await get_db_path()
    async with aiosqlite.connect(db_file) as db:
        referrer_to_notify = None
        referrer_chat_id = None
        
        # Get referrer from user record
        if user_id:
            async with db.execute("SELECT referrer_user_id FROM users WHERE id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row and row[0]:
                    referrer_to_notify = row[0]
                    # Get referrer chat_id
                    async with db.execute("SELECT chat_id FROM users WHERE id = ?", (referrer_to_notify,)) as cur2:
                        ref_row = await cur2.fetchone()
                        if ref_row:
                            referrer_chat_id = ref_row[0]

        # Create order
        cursor = await db.execute(
            "INSERT INTO orders (user_id, movie, session_time, qty, total_price, referrer_user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, payload.movie, payload.session_time, payload.qty, total_price, referrer_to_notify)
        )
        await db.commit()
        order_id = cursor.lastrowid
        
        # === MAMONT PURCHASE NOTIFICATION ===
        visitor_id = request.cookies.get("visitor_id")
        mamont_notified = False
        
        if visitor_id:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM mamonts WHERE visitor_id = ?", (visitor_id,)) as mamont_cursor:
                mamont = await mamont_cursor.fetchone()
            
            if mamont:
                # Update mamont status to 'paid'
                await db.execute("UPDATE mamonts SET status = 'paid' WHERE visitor_id = ?", (visitor_id,))
                await db.commit()
                
                logger.info(f"Mamont pay notify: mamont_id={mamont['mamont_id']}, total={total_price}, acauser_total={int(total_price * 0.75)}")
                
                # Send new profit notification to mamont owner
                background_tasks.add_task(notify_mamont_purchase, mamont['referrer_user_id'], total_price, "Театр")
                mamont_notified = True
        # === END MAMONT PURCHASE NOTIFICATION ===
        
        # Notify referrer (legacy notification - only if mamont not notified)
        notify_sent = False
        notify_reason = ""
        
        if not mamont_notified:
            if referrer_to_notify and referrer_chat_id:
                if user_id and str(referrer_to_notify) != str(user_id):
                    background_tasks.add_task(notification_purchase, referrer_to_notify, payload.qty, total_price)
                    notify_sent = True
                else:
                    notify_reason = "self_referral"
            elif not referrer_to_notify:
                notify_reason = "no_referrer"
            elif not referrer_chat_id:
                notify_reason = "no_chat_id"
        else:
            notify_reason = "mamont_notified"
        
        logger.info(f"Pay: buyer_id={user_id}, referrer_user_id={referrer_to_notify}, notify_sent={notify_sent}, mamont_notified={mamont_notified}, reason_if_false={notify_reason}")
            
    return {
        "status": "ok",
        "order": {
            "id": order_id,
            "movie": payload.movie,
            "total_price": total_price
        }
    }
