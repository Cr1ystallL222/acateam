from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
import aiosqlite
from datetime import datetime
import random

from ..config import DB_PATH, logger
from ..utils import get_current_user as get_current_user_from_request

router = APIRouter(prefix="/api/events", tags=["events"])

# Bot uses the same database as API (data/app.db)
# Both worker_settings and mamonts are in the same DB
BOT_DB_PATH = DB_PATH


async def get_referrer_settings_by_visitor_id(visitor_id: str) -> dict:
    """Get referrer's worker settings for applying to events shown to mamont.
    Uses visitor_id to find the referrer through mamonts table."""
    if not visitor_id:
        return None
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Get referrer_user_id from mamonts table (in API DB)
        async with db.execute("""
            SELECT m.referrer_user_id, u.telegram_user_id as referrer_telegram_id
            FROM mamonts m
            JOIN users u ON m.referrer_user_id = u.id
            WHERE m.visitor_id = ?
        """, (visitor_id,)) as cursor:
            row = await cursor.fetchone()
        
        if not row:
            logger.debug(f"No mamont found for visitor_id: {visitor_id}")
            return None  # No referrer found
        
        referrer_telegram_id = row['referrer_telegram_id']
        logger.info(f"Found referrer for visitor {visitor_id}: telegram_id={referrer_telegram_id}")
    
    # Now query bot database for worker_settings
    if not BOT_DB_PATH.exists():
        logger.warning(f"Bot database not found at {BOT_DB_PATH}")
        return None
    
    async with aiosqlite.connect(BOT_DB_PATH) as bot_db:
        bot_db.row_factory = aiosqlite.Row
        
        async with bot_db.execute("""
            SELECT * FROM worker_settings WHERE telegram_user_id = ?
        """, (referrer_telegram_id,)) as cursor:
            settings_row = await cursor.fetchone()
        
        if settings_row:
            settings = dict(settings_row)
            logger.info(f"Found worker_settings: city={settings.get('custom_city')}, min_price={settings.get('min_price_override')}")
            return settings
    
    logger.debug(f"No worker_settings found for referrer telegram_id: {referrer_telegram_id}")
    return None


def apply_referrer_settings_to_event(event: dict, settings: dict, city_venues: dict = None) -> dict:
    """Apply referrer's settings (min price, city/venue) to event data."""
    if not settings:
        return event
    
    is_system = event.get('is_system')
    event_id = event.get('id', 0)
    
    # Apply min price override with deterministic ±150₽ variation for natural look
    min_price_override = settings.get('min_price_override')
    max_price_override = settings.get('max_price_override')
    
    if min_price_override and is_system:
        # Use event_id to get deterministic variation (always same for same event)
        # Hash event_id to get a value between -150 and 150
        variation = ((event_id * 7919) % 301) - 150  # 7919 is a prime number for better distribution
        randomized_min = max(100, min_price_override + variation)  # Min 100₽
        
        logger.info(f"Applying min_price_override={min_price_override} (+{variation}={randomized_min}) to event '{event.get('title')}'")
        
        # Set minimum price with variation
        if event['min_price'] < randomized_min:
            event['min_price'] = randomized_min
        
        # Also adjust max price if needed
        if event['max_price'] < randomized_min:
            event['max_price'] = randomized_min + 1500  # Keep a reasonable spread
    
    # Apply max price override
    if max_price_override and is_system:
        if event['max_price'] > max_price_override:
            event['max_price'] = max_price_override
        # Ensure min <= max
        if event['min_price'] > event['max_price']:
            event['min_price'] = event['max_price']
    
    # Apply city override - change venue name
    custom_city = settings.get('custom_city')
    event_id = event.get('id', 0)  # Get event_id for deterministic selection
    
    if custom_city and is_system and event.get('venue'):
        logger.info(f"Trying to apply city '{custom_city}' to event, city_venues available: {bool(city_venues)}, cities: {list(city_venues.keys()) if city_venues else []}")
        # Get venues for the new city
        if city_venues and custom_city in city_venues:
            new_venues = city_venues[custom_city]
            logger.info(f"Found {len(new_venues)} venues for city '{custom_city}'")
            if new_venues:
                # Pick a venue from the new city that matches the "type" of venue
                venue = event['venue']
                
                # Try to match venue type
                matched_venue = None
                venue_lower = venue.lower()
                
                for new_venue in new_venues:
                    new_venue_lower = new_venue.lower()
                    # Match by keywords
                    if 'театр драмы' in venue_lower and 'драм' in new_venue_lower:
                        matched_venue = new_venue
                        break
                    elif 'опер' in venue_lower and 'опер' in new_venue_lower:
                        matched_venue = new_venue
                        break
                    elif 'филармон' in venue_lower and 'филармон' in new_venue_lower:
                        matched_venue = new_venue
                        break
                    elif 'кукол' in venue_lower and 'кукол' in new_venue_lower:
                        matched_venue = new_venue
                        break
                    elif 'дом культуры' in venue_lower and 'дом культуры' in new_venue_lower:
                        matched_venue = new_venue
                        break
                    elif 'библиотек' in venue_lower and 'библиотек' in new_venue_lower:
                        matched_venue = new_venue
                        break
                
                # If no match, pick DETERMINISTICALLY based on event_id
                if not matched_venue:
                    # Use event_id to always get the same venue for the same event
                    venue_index = event_id % len(new_venues)
                    matched_venue = new_venues[venue_index]
                
                logger.info(f"Replacing venue '{venue[:50]}...' -> '{matched_venue[:50]}...'")
                event['venue'] = matched_venue
    
    return event

async def get_current_user(request: Request):
    """Dependency to get current user."""
    user = await get_current_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return dict(user)

@router.get("")
@router.get("/")
async def get_events(request: Request):
    """Get events visible to current user based on referral hierarchy."""
    # Import city venues for venue replacement
    import sys
    import pathlib
    bots_path = pathlib.Path(__file__).parent.parent.parent / "bots"
    if str(bots_path) not in sys.path:
        sys.path.insert(0, str(bots_path))
    
    try:
        from bots.database import CITY_VENUES
        logger.info(f"Loaded CITY_VENUES with {len(CITY_VENUES)} cities: {list(CITY_VENUES.keys())}")
    except Exception as e:
        logger.error(f"Failed to import CITY_VENUES: {e}")
        CITY_VENUES = {}
    
    # Get visitor_id from cookies to identify mamont and their referrer
    visitor_id = request.cookies.get("visitor_id")
    logger.info(f"get_events called, visitor_id={visitor_id}, all_cookies={dict(request.cookies)}")
    
    # Get referrer settings using visitor_id
    referrer_settings = None
    if visitor_id:
        referrer_settings = await get_referrer_settings_by_visitor_id(visitor_id)
        logger.info(f"Referrer settings loaded: {referrer_settings}")
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Show ALL events to match Bot behavior
        async with db.execute("""
            SELECT e.*, bu.full_name as creator_name
            FROM events e
            LEFT JOIN bot_users bu ON e.created_by = bu.telegram_user_id
            ORDER BY e.date_time ASC
        """) as cursor:
            rows = await cursor.fetchall()
        
        events = []
        for row in rows:
            event = dict(row)
            # Format date for frontend
            try:
                dt = datetime.strptime(event['date_time'], "%Y-%m-%d %H:%M")
                event['formatted_date'] = dt.strftime("%d.%m.%Y")
                event['formatted_time'] = dt.strftime("%H:%M")
                event['weekday'] = dt.strftime("%A")
            except:
                event['formatted_date'] = "Дата не указана"
                event['formatted_time'] = ""
                event['weekday'] = ""
            
            # Apply referrer settings (min price, venue replacement)
            event = apply_referrer_settings_to_event(event, referrer_settings, CITY_VENUES)
            
            events.append(event)
        
        return events


@router.get("/city-info")
async def get_city_info(request: Request):
    """Get city info for the current user (based on referrer settings)."""
    # Get visitor_id from cookies
    visitor_id = request.cookies.get("visitor_id")
    
    # Default city
    city = "Москва"
    
    if visitor_id:
        referrer_settings = await get_referrer_settings_by_visitor_id(visitor_id)
        if referrer_settings and referrer_settings.get('custom_city'):
            city = referrer_settings['custom_city']
    
    return {"city": city}

@router.get("/{event_id}", response_model=dict)
async def get_event(event_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    """Get event details with seats - only if user has access to this event."""
    import sys
    import pathlib
    bots_path = pathlib.Path(__file__).parent.parent.parent / "bots"
    if str(bots_path) not in sys.path:
        sys.path.insert(0, str(bots_path))
    
    try:
        from bots.database import CITY_VENUES
    except:
        CITY_VENUES = {}

    user_telegram_id = current_user['telegram_user_id']
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Check if user has access to this event
        # Get user's referrer
        async with db.execute("""
            SELECT u.referrer_user_id, bu.telegram_user_id as referrer_telegram_id
            FROM users u
            LEFT JOIN users ref_u ON u.referrer_user_id = ref_u.id
            LEFT JOIN bot_users bu ON ref_u.telegram_user_id = bu.telegram_user_id
            WHERE u.telegram_user_id = ?
        """, (user_telegram_id,)) as cursor:
            user_row = await cursor.fetchone()
        
        referrer_telegram_id = user_row['referrer_telegram_id'] if user_row else None
        
        # Get referrer settings
        referrer_settings = None
        if referrer_telegram_id:
            try:
                async with aiosqlite.connect(BOT_DB_PATH) as bot_db:
                    bot_db.row_factory = aiosqlite.Row
                    async with bot_db.execute("SELECT * FROM worker_settings WHERE telegram_user_id = ?", (referrer_telegram_id,)) as cursor:
                        row = await cursor.fetchone()
                        if row:
                            referrer_settings = dict(row)
            except Exception as e:
                logger.error(f"Error fetching worker settings: {e}")

        # Get event and check access
        if not referrer_telegram_id:
            # User has no referrer - can access system events + their own events
            async with db.execute("""
                SELECT e.*, bu.full_name as creator_name
                FROM events e
                LEFT JOIN bot_users bu ON e.created_by = bu.telegram_user_id
                WHERE e.id = ? AND (e.is_system = 1 OR e.created_by = ?)
            """, (event_id, user_telegram_id)) as cursor:
                event_row = await cursor.fetchone()
        else:
            # User has referrer - check referrer's settings
            async with db.execute("""
                SELECT e.*, bu.full_name as creator_name
                FROM events e
                LEFT JOIN bot_users bu ON e.created_by = bu.telegram_user_id
                LEFT JOIN hidden_events he ON e.id = he.event_id AND he.hidden_by = ?
                WHERE e.id = ? AND (
                    (e.is_system = 1 AND he.id IS NULL) OR  -- System events not hidden by referrer
                    e.created_by = ? OR                      -- Events created by referrer
                    e.created_by = ?                         -- User's own events
                )
            """, (referrer_telegram_id, event_id, referrer_telegram_id, user_telegram_id)) as cursor:
                event_row = await cursor.fetchone()
        
        if not event_row:
            raise HTTPException(status_code=404, detail="Event not found or access denied")
        
        event = dict(event_row)
        
        # Apply referrer settings
        event = apply_referrer_settings_to_event(event, referrer_settings, CITY_VENUES)
        
        # Get seats
        async with db.execute("""
            SELECT * FROM event_seats 
            WHERE event_id = ? 
            ORDER BY row_number, seat_number
        """, (event_id,)) as cursor:
            seat_rows = await cursor.fetchall()
            seats = [dict(row) for row in seat_rows]
        
        # Format date
        try:
            dt = datetime.strptime(event['date_time'], "%Y-%m-%d %H:%M")
            event['formatted_date'] = dt.strftime("%d.%m.%Y")
            event['formatted_time'] = dt.strftime("%H:%M")
            event['weekday'] = dt.strftime("%A")
        except:
            event['formatted_date'] = "Дата не указана"
            event['formatted_time'] = ""
            event['weekday'] = ""
        
        # Group seats by rows
        rows = {}
        for seat in seats:
            row_num = seat['row_number']
            if row_num not in rows:
                rows[row_num] = []
            rows[row_num].append(seat)
        
        # Calculate statistics
        total_seats = len(seats)
        available_seats = len([s for s in seats if s['is_available']])
        
        event['seats'] = seats
        event['rows'] = rows
        event['total_seats'] = total_seats
        event['available_seats'] = available_seats
        
        return event

@router.post("/{event_id}/reserve")
async def reserve_seat(event_id: int, row_number: int, seat_number: int, request: Request, current_user: dict = Depends(get_current_user)):
    """Reserve a seat for the current user."""
    user_id = current_user['telegram_user_id']
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if seat is available
        async with db.execute("""
            SELECT is_available FROM event_seats 
            WHERE event_id = ? AND row_number = ? AND seat_number = ? AND is_available = 1
        """, (event_id, row_number, seat_number)) as cursor:
            if not await cursor.fetchone():
                raise HTTPException(status_code=400, detail="Seat not available")
        
        # Reserve the seat
        await db.execute("""
            UPDATE event_seats 
            SET is_available = 0, reserved_by = ?, reserved_at = CURRENT_TIMESTAMP
            WHERE event_id = ? AND row_number = ? AND seat_number = ?
        """, (user_id, event_id, row_number, seat_number))
        
        await db.commit()
        
        return {"success": True, "message": "Seat reserved successfully"}

@router.get("/{event_id}/seat-map")
async def get_seat_map(event_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    """Get seat map data for visualization - requires authentication."""
    # Auth is checked by Depends(get_current_user)
    # No complex access checks - any authenticated user can view any event
    
    # Import city venues for venue replacement
    import sys
    import pathlib
    bots_path = pathlib.Path(__file__).parent.parent.parent / "bots"
    if str(bots_path) not in sys.path:
        sys.path.insert(0, str(bots_path))
    
    try:
        from bots.database import CITY_VENUES
    except:
        CITY_VENUES = {}
    
    # Get referrer settings from visitor_id cookie
    visitor_id = request.cookies.get("visitor_id")
    referrer_settings = None
    if visitor_id:
        referrer_settings = await get_referrer_settings_by_visitor_id(visitor_id)
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Simply fetch the event by ID
        async with db.execute("SELECT * FROM events WHERE id = ?", (event_id,)) as cursor:
            event_row = await cursor.fetchone()
        
        if not event_row:
            raise HTTPException(status_code=404, detail="Event not found")
        
        event = dict(event_row)
        
        # Apply referrer settings to event (venue replacement, price adjustment)
        event = apply_referrer_settings_to_event(event, referrer_settings, CITY_VENUES)
        
        # Format date
        try:
            dt = datetime.strptime(event['date_time'], "%Y-%m-%d %H:%M")
            event['formatted_date'] = dt.strftime("%d.%m.%Y")
            event['formatted_time'] = dt.strftime("%H:%M")
            event['weekday'] = dt.strftime("%A")
        except:
            event['formatted_date'] = "Дата не указана"
            event['formatted_time'] = ""
            event['weekday'] = ""
            
        # Get seats
        async with db.execute("""
            SELECT * FROM event_seats 
            WHERE event_id = ? 
            ORDER BY row_number, seat_number
        """, (event_id,)) as cursor:
            seat_rows = await cursor.fetchall()
            all_seats = [dict(row) for row in seat_rows]
        
        # CREATE 3 PRICE ZONES: min, middle, max
        # Each zone gets deterministic variation ±150₽
        min_price_override = referrer_settings.get('min_price_override') if referrer_settings else None
        max_price_override = referrer_settings.get('max_price_override') if referrer_settings else None
        is_system = event.get('is_system')
        
        # Calculate 3 zone prices with deterministic variations
        if min_price_override and max_price_override and is_system:
            # Use event_id for deterministic variations
            min_variation = ((event_id * 7919) % 301) - 150  # -150 to +150
            max_variation = ((event_id * 7927) % 301) - 150  # Different prime for different variation
            mid_variation = ((event_id * 7933) % 101) - 50   # Smaller variation for middle
            
            zone_min_price = max(100, min_price_override + min_variation)
            zone_max_price = max(zone_min_price + 100, max_price_override + max_variation)
            zone_mid_price = (zone_min_price + zone_max_price) // 2 + mid_variation
            
            # Ensure proper ordering: min < mid < max
            zone_mid_price = max(zone_min_price + 50, min(zone_max_price - 50, zone_mid_price))
        else:
            zone_min_price = zone_mid_price = zone_max_price = None
        
        # Get unique original prices and sort them
        original_prices = sorted(set(seat['price'] for seat in all_seats))
        
        # Map original prices to 3 zones (cheap -> min, medium -> mid, expensive -> max)
        price_mapping = {}
        if zone_min_price and len(original_prices) > 0:
            n = len(original_prices)
            for i, orig_price in enumerate(original_prices):
                if n == 1:
                    # Only one price tier - use middle
                    price_mapping[orig_price] = zone_mid_price
                elif n == 2:
                    # Two tiers - use min and max
                    price_mapping[orig_price] = zone_min_price if i == 0 else zone_max_price
                else:
                    # Three or more tiers - split into thirds
                    if i < n / 3:
                        price_mapping[orig_price] = zone_min_price
                    elif i < 2 * n / 3:
                        price_mapping[orig_price] = zone_mid_price
                    else:
                        price_mapping[orig_price] = zone_max_price
        
        seats = []
        for seat in all_seats:
            seat_copy = dict(seat)
            
            if is_system and price_mapping:
                # Map to one of 3 zone prices
                orig_price = seat_copy['price']
                seat_copy['price'] = price_mapping.get(orig_price, orig_price)
            
            seats.append(seat_copy)
        
        # Group by price for color coding
        price_groups = {}
        for seat in seats:
            price = seat['price']
            if price not in price_groups:
                price_groups[price] = {
                    'price': price,
                    'seats': [],
                    'color': get_price_color(price, event['min_price'], event['max_price'])
                }
            price_groups[price]['seats'].append(seat)
        
        # Group seats by rows
        rows = {}
        for seat in seats:
            row_num = seat['row_number']
            if row_num not in rows:
                rows[row_num] = {
                    'row_number': row_num,
                    'seats': [],
                    'available_count': 0,
                    'total_count': 0
                }
            rows[row_num]['seats'].append(seat)
            rows[row_num]['total_count'] += 1
            if seat['is_available']:
                rows[row_num]['available_count'] += 1
        
        return {
            'event': event,
            'rows': list(rows.values()),
            'price_groups': list(price_groups.values()),
            'total_seats': len(seats),
            'available_seats': len([s for s in seats if s['is_available']])
        }

def get_price_color(price: int, min_price: int, max_price: int) -> str:
    """Get color for price range."""
    if price == min_price:
        return "#22c55e"  # green
    elif price == max_price:
        return "#ef4444"  # red
    elif max_price == min_price:
        return "#3b82f6" # default blue if prices are equal
    else:
        # Calculate percentage and assign color
        percentage = (price - min_price) / (max_price - min_price)
        if percentage < 0.3:
            return "#3b82f6"  # blue
        elif percentage < 0.5:
            return "#06b6d4"  # cyan
        elif percentage < 0.7:
            return "#f59e0b"  # amber
        else:
            return "#8b5cf6"  # purple
@router.get("/{event_id}/photo")
async def get_event_photo(event_id: int):
    """Get event photo."""
    from fastapi.responses import FileResponse
    import os
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT photo_path FROM events WHERE id = ?", (event_id,)) as cursor:
            row = await cursor.fetchone()
            
            if not row or not row[0]:
                raise HTTPException(status_code=404, detail="Photo not found")
            
            photo_path = row[0]
            
            # Handle relative paths from seeding (starts with /images/)
            # We assume images are in web/public
            if photo_path.startswith('/'):
                # Get project root (parent of api)
                import pathlib
                current_dir = pathlib.Path(__file__).parent.parent.parent
                # web/public + path (e.g. /images/foo.jpg)
                full_path = current_dir / "web" / "public" / photo_path.lstrip('/')
            else:
                full_path = photo_path
            
            full_path_str = str(full_path)
            
            if not os.path.exists(full_path_str):
                # Fallback to absolute check if needed
                if os.path.exists(photo_path):
                    full_path_str = photo_path
                else:
                    logger.error(f"Image not found: {full_path_str}")
                    return FileResponse(os.path.join("web", "public", "images", "banner.jpeg")) # Fallback image
            
            return FileResponse(full_path_str)