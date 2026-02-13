from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from datetime import datetime
import random

from ..config import logger
from ..utils import get_current_user as get_current_user_from_request
from data.db import db

router = APIRouter(prefix="/api/events", tags=["events"])


async def get_referrer_settings_by_visitor_id(visitor_id: str) -> dict:
    """Get referrer's settings (from link or worker) for applying to events.
    Uses visitor_id to find the referrer/link through mamonts table."""
    if not visitor_id:
        return None
    
    # Get mamont info including referral_code
    row = await db.fetchone("""
        SELECT m.referrer_user_id, m.referral_code, u.telegram_user_id as referrer_telegram_id
        FROM mamonts m
        JOIN users u ON m.referrer_user_id = u.id
        WHERE m.visitor_id = ?
    """, (visitor_id,))
    
    if not row:
        logger.debug(f"No mamont found for visitor_id: {visitor_id}")
        return None
    
    referrer_telegram_id = row['referrer_telegram_id']
    referral_code = row['referral_code']
    
    # CHECK IF IT IS A THEATRE LINK
    if referral_code:
        link_row = await db.fetchone("""
            SELECT * FROM theatre_links WHERE link_code = ?
        """, (referral_code,))
        
        if link_row:
            logger.info(f"Found theatre link settings for code {referral_code}: {link_row}")
            return dict(link_row)

    # Fallback to global worker settings
    settings_row = await db.fetchone("""
        SELECT * FROM worker_settings WHERE telegram_user_id = ?
    """, (referrer_telegram_id,))
    
    if settings_row:
        logger.info(f"Using worker_settings for referrer {referrer_telegram_id}")
        return dict(settings_row)
    
    return None

# ... (rest of the file until get_event_photo)

@router.get("/{event_id}/photo")
async def get_event_photo(event_id: int):
    """Get event photo."""
    from fastapi.responses import FileResponse
    import os
    import pathlib
    
    row = await db.fetchone("SELECT photo_path FROM events WHERE id = ?", (event_id,))
    
    if not row or not row['photo_path']:
        # Return default banner if no photo
        current_dir = pathlib.Path(__file__).parent.parent.parent
        default_banner = current_dir / "web" / "public" / "images" / "banner.jpeg"
        if default_banner.exists():
             return FileResponse(str(default_banner))
        raise HTTPException(status_code=404, detail="Photo not found")
    
    photo_path = row['photo_path']
    current_dir = pathlib.Path(__file__).parent.parent.parent
    
    # Resolution logic:
    # 1. If absolute path, try it
    # 2. If relative, try resolving from project root
    
    possible_paths = []
    
    if os.path.isabs(photo_path):
        possible_paths.append(pathlib.Path(photo_path))
    else:
        # Try relative to project root (most common for bots/images/...)
        possible_paths.append(current_dir / photo_path)
        # Try relative to web/public (legacy)
        possible_paths.append(current_dir / "web" / "public" / photo_path.lstrip('/'))
    
    final_path = None
    for p in possible_paths:
        if p.exists():
            final_path = p
            break
            
    if not final_path:
        logger.error(f"Image not found. Tried: {[str(p) for p in possible_paths]}")
        # Return default banner
        default_banner = current_dir / "web" / "public" / "images" / "banner.jpeg"
        if default_banner.exists():
             return FileResponse(str(default_banner))
        raise HTTPException(status_code=404, detail="Image file not found")
    
    return FileResponse(str(final_path))