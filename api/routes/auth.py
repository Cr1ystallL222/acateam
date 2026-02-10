import uuid
import hashlib
import aiosqlite
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Request, Response, BackgroundTasks, HTTPException

from ..config import logger, BOT_USERNAME
from ..database import get_db_path
from ..models import AuthVerifyRequest, AuthDraftRequest, RegisterRequest, AuthStartRequest
from ..utils import get_current_user
from ..services.mamont import get_mamont_display
from ..services.notifications import notify_mamont_registration

router = APIRouter()

@router.get("/api/me")
async def api_me(request: Request):
    user = await get_current_user(request)
    if user:
        # Build display_name with proper fallback
        first_name = user['first_name'] or ""
        last_name = user['last_name'] or ""
        
        if first_name and last_name:
            display_name = f"{first_name} {last_name}"
        elif first_name:
            display_name = first_name
        elif user['telegram_display_name']:
            display_name = user['telegram_display_name']
        elif user['telegram_username']:
            display_name = f"@{user['telegram_username']}"
        else:
            display_name = f"ID: {user['id']}"
             
        return {
            "id": user['id'],
            "first_name": first_name,
            "last_name": last_name,
            "display_name": display_name,
            "telegram_display_name": user['telegram_display_name'],
            "telegram_username": user['telegram_username'],
            "telegram_username": user['telegram_username'],
            "email": user['email'],
            "balance": user['balance'] or 0
        }
    raise HTTPException(status_code=401, detail="Not authenticated")

@router.post("/api/auth/telegram/start")
async def api_auth_start(payload: AuthStartRequest = None):
    session_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    intent = payload.intent if payload else "login"
    
    db_file = await get_db_path()
    async with aiosqlite.connect(db_file) as db:
        await db.execute(
            "INSERT INTO registration_sessions (session_id, status, session_expires_at, intent) VALUES (?, 'created', ?, ?)",
            (session_id, expires_at, intent)
        )
        await db.commit()
    
    prefix = "auth" if intent == "login" else "reg"
    bot_link = f"https://t.me/{BOT_USERNAME}?start={prefix}_{session_id}"
    return {"session_id": session_id, "bot_link": bot_link}

@router.post("/api/auth/telegram/verify")
async def api_auth_verify(payload: AuthVerifyRequest, request: Request, response: Response, background_tasks: BackgroundTasks):
    session_id = payload.session_id
    code = payload.code
    
    masked_code = code[:1] + "**" + code[-1:] if len(code) > 1 else "***"
    logger.info(f"API Verify: session_id={session_id}, code={masked_code}")

    db_file = await get_db_path()
    async with aiosqlite.connect(db_file) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM registration_sessions WHERE session_id = ?", (session_id,)) as cursor:
            session = await cursor.fetchone()
            
        if not session:
            raise HTTPException(400, "Сессия не найдена")
        
        logger.info(f"Session data: {dict(session) if session else None}")
        logger.info(f"Session visitor_id: {session['visitor_id'] if 'visitor_id' in session else 'NOT FOUND'}")
            
        if session['status'] != 'code_issued':
             if session['status'] in ['verified', 'used', 'completed']:
                  pass
             raise HTTPException(400, "Сначала получите код в боте")
            
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        now = datetime.now(timezone.utc)
        
        # Date parsing logic
        try:
             sess_exp = datetime.fromisoformat(str(session['session_expires_at']))
             code_exp = datetime.fromisoformat(str(session['code_expires_at']))
        except ValueError:
             try:
                sess_exp = datetime.strptime(str(session['session_expires_at']), "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
                code_exp = datetime.strptime(str(session['code_expires_at']), "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
             except:
                raise HTTPException(500, "Ошибка времени")
        
        if sess_exp.tzinfo is None: sess_exp = sess_exp.replace(tzinfo=timezone.utc)
        if code_exp.tzinfo is None: code_exp = code_exp.replace(tzinfo=timezone.utc)

        if now > sess_exp: raise HTTPException(400, "Сессия истекла")
        if now > code_exp: raise HTTPException(400, "Код истек")
             
        if session['code_hash'] != code_hash:
             await db.execute("UPDATE registration_sessions SET attempts = attempts + 1 WHERE session_id = ?", (session_id,))
             await db.commit()
             raise HTTPException(400, "Неверный код")
             
        telegram_user_id = session['telegram_user_id']
        async with db.execute("SELECT * FROM users WHERE telegram_user_id = ?", (telegram_user_id,)) as cursor:
            existing_user = await cursor.fetchone()
        
        # Get draft data
        draft_first_name = session['reg_first_name'] or ""
        draft_last_name = session['reg_last_name'] or ""
        draft_phone = session['reg_phone'] or session['contact_phone'] or ""
        draft_email = session['reg_email'] or ""
        draft_consent_pd = session['consent_pd'] or 0
        draft_consent_marketing = session['consent_marketing'] or 0
        
        # Get referrer from cookie
        ref_pending = request.cookies.get("ref_pending")
        referrer_id = None
        referrer_chat_id = None
        
        if ref_pending:
            async with db.execute("SELECT id, chat_id FROM users WHERE referral_code = ?", (ref_pending,)) as cursor:
                owner = await cursor.fetchone()
                if owner:
                    referrer_id = owner['id']
                    referrer_chat_id = owner['chat_id']
            
        if existing_user:
            # UPDATE existing user with draft data if fields are empty
            user_id = existing_user['id']
            updates = []
            params = []
            
            if not existing_user['first_name'] and draft_first_name:
                updates.append("first_name = ?")
                params.append(draft_first_name)
            if not existing_user['last_name'] and draft_last_name:
                updates.append("last_name = ?")
                params.append(draft_last_name)
            if not existing_user['phone'] and draft_phone:
                updates.append("phone = ?")
                params.append(draft_phone)
            if not existing_user['email'] and draft_email:
                updates.append("email = ?")
                params.append(draft_email)
            if not existing_user['consent_pd'] and draft_consent_pd:
                updates.append("consent_pd = ?")
                params.append(draft_consent_pd)
            if not existing_user['referrer_user_id'] and referrer_id and referrer_id != user_id:
                updates.append("referrer_user_id = ?")
                params.append(referrer_id)
                logger.info(f"Attach referrer: buyer_id={user_id}, ref_code={ref_pending}, referrer_user_id={referrer_id}")
                # Clear cookie
                response.delete_cookie("ref_pending", path="/")
            
            if updates:
                updates.append("consent_at = ?")
                params.append(datetime.now(timezone.utc).isoformat())
                params.append(user_id)
                await db.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
                await db.commit()
                logger.info(f"User updated id={user_id}, first_name={draft_first_name}, last_name={draft_last_name}, phone={draft_phone}, email={draft_email}")
            
            await db.execute("UPDATE registration_sessions SET status = 'used' WHERE session_id = ?", (session_id,))
            await db.commit()
            
            # === MAMONT UPDATE LOGIC FOR EXISTING USER ===
            # Get visitor_id from session (saved during draft creation)
            visitor_id = session['visitor_id'] if session and 'visitor_id' in session.keys() else None
            logger.info(f"Checking mamont for existing user, visitor_id: {visitor_id}")
            logger.info(f"Session keys: {list(session.keys()) if session else 'No session'}")
            
            if visitor_id:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM mamonts WHERE visitor_id = ?", (visitor_id,)) as mamont_cursor:
                    mamont = await mamont_cursor.fetchone()
                
                logger.info(f"Found mamont for existing user: {dict(mamont) if mamont else None}")
                
                if mamont and mamont['status'] == 'attached':
                    # Get telegram data from session
                    tg_name = session['telegram_display_name'] or ""
                    tg_username = session['telegram_username'] or ""
                    
                    logger.info(f"Updating mamont {mamont['mamont_id']} with registration data for existing user")
                    
                    # Update mamont record
                    await db.execute("""
                        UPDATE mamonts SET 
                            status = 'registered',
                            first_name = ?,
                            last_name = ?,
                            phone = ?,
                            email = ?,
                            tg_name = ?,
                            tg_username = ?
                        WHERE visitor_id = ?
                    """, (draft_first_name, draft_last_name, draft_phone, draft_email, tg_name, tg_username, visitor_id))
                    await db.commit()
                    
                    # Build mamont display and notify
                    mamont_data = {
                        'mamont_id': mamont['mamont_id'],
                        'status': 'registered',
                        'first_name': draft_first_name,
                        'last_name': draft_last_name,
                        'tg_name': tg_name,
                        'tg_username': tg_username
                    }
                    mamont_display = get_mamont_display(mamont_data)
                    
                    logger.info(f"Mamont registered (existing user): mamont_id={mamont['mamont_id']}, name={draft_first_name} {draft_last_name}, tg_name={tg_name}, referrer_user_id={mamont['referrer_user_id']}")
                    
                    # Send detailed mamont registration notification
                    background_tasks.add_task(
                        notify_mamont_registration, 
                        mamont['referrer_user_id'], 
                        mamont_display,
                        draft_first_name,
                        draft_last_name,
                        draft_phone,
                        draft_email
                    )
                else:
                    logger.warning(f"Mamont not found or not in 'attached' status for existing user, visitor_id={visitor_id}. Mamont status: {mamont['status'] if mamont else 'None'}")
            else:
                logger.warning(f"No visitor_id in session {session_id} for existing user mamont notification")
            # === END MAMONT UPDATE LOGIC FOR EXISTING USER ===
            
            # Set Cookie
            response.set_cookie(
                key="auth_user_id", 
                value=str(user_id), 
                max_age=2592000, 
                httponly=True, 
                path="/",
                samesite="lax"
            )
            
            # Build display name
            fn = draft_first_name or existing_user['first_name'] or ""
            ln = draft_last_name or existing_user['last_name'] or ""
            if fn and ln:
                display_name = f"{fn} {ln}"
            elif existing_user['telegram_username']:
                display_name = f"@{existing_user['telegram_username']}"
            else:
                display_name = existing_user['telegram_display_name'] or f"ID: {user_id}"

            return {
                "status": "login",
                "user": {
                    "id": user_id,
                    "first_name": fn,
                    "last_name": ln,
                    "display_name": display_name
                }
            }
        else:
            # CREATE NEW USER from draft
            try:
                # Check self-referral
                if referrer_id:
                    logger.info(f"Attach referrer: new_user telegram_id={telegram_user_id}, ref_code={ref_pending}, referrer_user_id={referrer_id}")
                
                cursor = await db.execute("""
                    INSERT INTO users (
                        telegram_user_id, chat_id, telegram_username, telegram_display_name,
                        first_name, last_name, phone, email, 
                        consent_terms, consent_pd, consent_marketing, consent_at, 
                        referrer_user_id, referral_code
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
                """, (
                    session['telegram_user_id'], 
                    session['chat_id'], 
                    session['telegram_username'], 
                    session['telegram_display_name'],
                    draft_first_name, 
                    draft_last_name, 
                    draft_phone, 
                    draft_email,
                    draft_consent_pd, 
                    draft_consent_marketing,
                    datetime.now(timezone.utc).isoformat(), 
                    referrer_id, 
                    str(uuid.uuid4())[:12]
                ))
                new_user_id = cursor.lastrowid
                
                logger.info(f"User created id={new_user_id}, first_name={draft_first_name}, last_name={draft_last_name}, phone={draft_phone}, email={draft_email}, telegram_username={session['telegram_username']}, telegram_display_name={session['telegram_display_name']}")
                
                await db.execute("UPDATE registration_sessions SET status = 'completed' WHERE session_id = ?", (session_id,))
                await db.commit()
                
                # === MAMONT UPDATE LOGIC ===
                # Get visitor_id from session (saved during draft creation)
                visitor_id = session['visitor_id'] if session and 'visitor_id' in session.keys() else None
                logger.info(f"Checking mamont for visitor_id: {visitor_id}")
                logger.info(f"Session keys: {list(session.keys()) if session else 'No session'}")
                
                if visitor_id:
                    db.row_factory = aiosqlite.Row
                    async with db.execute("SELECT * FROM mamonts WHERE visitor_id = ?", (visitor_id,)) as mamont_cursor:
                        mamont = await mamont_cursor.fetchone()
                    
                    logger.info(f"Found mamont: {dict(mamont) if mamont else None}")
                    
                    if mamont and mamont['status'] == 'attached':
                        # Get telegram data from session
                        tg_name = session['telegram_display_name'] or ""
                        tg_username = session['telegram_username'] or ""
                        
                        logger.info(f"Updating mamont {mamont['mamont_id']} with registration data")
                        
                        # Update mamont record
                        await db.execute("""
                            UPDATE mamonts SET 
                                status = 'registered',
                                first_name = ?,
                                last_name = ?,
                                phone = ?,
                                email = ?,
                                tg_name = ?,
                                tg_username = ?
                            WHERE visitor_id = ?
                        """, (draft_first_name, draft_last_name, draft_phone, draft_email, tg_name, tg_username, visitor_id))
                        await db.commit()
                        
                        # Build mamont display and notify
                        mamont_data = {
                            'mamont_id': mamont['mamont_id'],
                            'status': 'registered',
                            'first_name': draft_first_name,
                            'last_name': draft_last_name,
                            'tg_name': tg_name,
                            'tg_username': tg_username
                        }
                        mamont_display = get_mamont_display(mamont_data)
                        
                        logger.info(f"Mamont registered: mamont_id={mamont['mamont_id']}, name={draft_first_name} {draft_last_name}, tg_name={tg_name}, referrer_user_id={mamont['referrer_user_id']}")
                        
                        # Send detailed mamont registration notification
                        background_tasks.add_task(
                            notify_mamont_registration, 
                            mamont['referrer_user_id'], 
                            mamont_display,
                            draft_first_name,
                            draft_last_name,
                            draft_phone,
                            draft_email
                        )
                    else:
                        logger.warning(f"Mamont not found or not in 'attached' status for visitor_id={visitor_id}. Mamont status: {mamont['status'] if mamont else 'None'}")
                else:
                    logger.warning(f"No visitor_id in session {session_id} for mamont notification")
                # === END MAMONT UPDATE LOGIC ===
                
                # Clear ref_pending cookie
                if ref_pending:
                    response.delete_cookie("ref_pending", path="/")

                # Set Cookie
                response.set_cookie(
                    key="auth_user_id", 
                    value=str(new_user_id), 
                    max_age=2592000, 
                    httponly=True, 
                    path="/",
                    samesite="lax"
                )
                
                # Build display name
                if draft_first_name and draft_last_name:
                    dname = f"{draft_first_name} {draft_last_name}"
                elif draft_first_name:
                    dname = draft_first_name
                else:
                    dname = session['telegram_display_name'] or f"ID: {new_user_id}"
                
                return {
                    "status": "verified",
                    "user": {
                        "id": new_user_id,
                        "first_name": draft_first_name,
                        "last_name": draft_last_name,
                        "display_name": dname
                    }
                }
            except aiosqlite.IntegrityError:
                 raise HTTPException(400, "Пользователь уже существует")

# Alias for /api/register/verify
@router.post("/api/register/verify")
async def api_register_verify(payload: AuthVerifyRequest, request: Request, response: Response, background_tasks: BackgroundTasks):
    return await api_auth_verify(payload, request, response, background_tasks)

@router.post("/api/register/draft")
async def api_register_draft(payload: AuthDraftRequest, request: Request):
    if not payload.consent_pd:
        raise HTTPException(400, "Consent PD required")

    session_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    # Get visitor_id from cookies to link with mamont
    visitor_id = request.cookies.get("visitor_id")
    logger.info(f"Saving draft with visitor_id from cookies: {visitor_id}")
    
    db_file = await get_db_path()
    async with aiosqlite.connect(db_file) as db:
        await db.execute("""
            INSERT INTO registration_sessions (
                session_id, status, session_expires_at,
                reg_first_name, reg_last_name, reg_phone, reg_email,
                consent_pd, consent_marketing, consent_at, visitor_id
            ) VALUES (?, 'draft', ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, expires_at,
            payload.first_name, payload.last_name, payload.phone, payload.email,
            payload.consent_pd, payload.consent_marketing, datetime.now(timezone.utc).isoformat(),
            visitor_id
        ))
        await db.commit()
    
    logger.info(f"Draft saved: session_id={session_id}, first_name={payload.first_name}, last_name={payload.last_name}, phone={payload.phone}, email={payload.email}, visitor_id={visitor_id}")
    
    # Verify that visitor_id was saved correctly
    async with aiosqlite.connect(db_file) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT visitor_id FROM registration_sessions WHERE session_id = ?", (session_id,)) as cursor:
            check_row = await cursor.fetchone()
            logger.info(f"Verification: saved visitor_id = {check_row['visitor_id'] if check_row else 'NOT FOUND'}")
        
    bot_link = f"https://t.me/{BOT_USERNAME}?start=reg_{session_id}"
    return {"session_id": session_id, "bot_link": bot_link}

@router.post("/api/auth/register")
async def api_auth_register(payload: RegisterRequest, background_tasks: BackgroundTasks, request: Request, response: Response):
    if not payload.consent_terms or not payload.consent_pd:
        raise HTTPException(400, "Consent required")

    db_file = await get_db_path()
    async with aiosqlite.connect(db_file) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM registration_sessions WHERE session_id = ?", (payload.session_id,)) as cursor:
            session = await cursor.fetchone()
            
        if not session or session['status'] != 'verified':
             raise HTTPException(400, "Invalid session state")

        referrer_id = None
        ref_pending = request.cookies.get("ref_pending")
        if ref_pending:
             async with db.execute("SELECT id, chat_id FROM users WHERE referral_code = ?", (ref_pending,)) as cursor:
                 owner = await cursor.fetchone()
                 if owner:
                     referrer_id = owner['id']
                     
        try:
            cursor = await db.execute("""
                INSERT INTO users (
                    telegram_user_id, chat_id, telegram_username, telegram_display_name,
                    first_name, last_name, phone, email, 
                    consent_terms, consent_pd, consent_at, referrer_user_id, referral_code
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session['telegram_user_id'], session['chat_id'], session['telegram_username'], session['telegram_display_name'],
                payload.first_name, payload.last_name, payload.phone, payload.email,
                True, True, datetime.now(timezone.utc).isoformat(), referrer_id, str(uuid.uuid4())[:12]
            ))
            new_user_id = cursor.lastrowid
            
            logger.info(f"User created id={new_user_id}, first_name={payload.first_name}, last_name={payload.last_name}")
            
            await db.execute("UPDATE registration_sessions SET status = 'used' WHERE session_id = ?", (payload.session_id,))
            await db.commit()

            response.set_cookie(
                key="auth_user_id", 
                value=str(new_user_id), 
                max_age=2592000, 
                httponly=True, 
                path="/",
                samesite="lax"
            )
            response.delete_cookie("ref_pending", path="/")
            return {"status": "ok", "user_id": new_user_id}
            
        except aiosqlite.IntegrityError:
             raise HTTPException(400, "Пользователь уже существует")

@router.get("/api/auth/login-token")
async def verify_login_token(token: str, response: Response):
    """Verify one-time login token and log the user in."""
    db_file = await get_db_path()
    
    async with aiosqlite.connect(db_file) as db:
        db.row_factory = aiosqlite.Row
        
        # Find session with this token
        async with db.execute("""
            SELECT session_id, login_user_id, login_token_expires_at, status 
            FROM registration_sessions 
            WHERE login_token = ? AND status = 'login_ready'
        """, (token,)) as cursor:
            session = await cursor.fetchone()
        
        if not session:
            raise HTTPException(400, "Недействительная или использованная ссылка")
        
        # Check expiration
        try:
            expires_at = datetime.fromisoformat(str(session['login_token_expires_at']))
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
        except:
            raise HTTPException(500, "Ошибка времени")
        
        if datetime.now(timezone.utc) > expires_at:
            raise HTTPException(400, "Ссылка для входа истекла")
        
        user_id = session['login_user_id']
        
        # Mark token as used
        await db.execute("""
            UPDATE registration_sessions 
            SET status = 'login_used', login_token = NULL 
            WHERE session_id = ?
        """, (session['session_id'],))
        await db.commit()
        
        # Set auth cookie
        response.set_cookie(
            key="auth_user_id", 
            value=str(user_id), 
            max_age=2592000, 
            httponly=True, 
            path="/",
            samesite="lax"
        )
        
        logger.info(f"User logged in via token: user_id={user_id}")
        
        return {"status": "ok", "user_id": user_id}
