from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from datetime import datetime, timedelta
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

        # CHECK IF IT IS A CINEMA LINK
        cinema_link_row = await db.fetchone("""
            SELECT * FROM cinema_links WHERE link_code = ?
        """, (referral_code,))
        
        if cinema_link_row:
            logger.info(f"Found cinema link settings for code {referral_code}: {cinema_link_row}")
            return dict(cinema_link_row)

    # Fallback to global worker settings
    settings_row = await db.fetchone("""
        SELECT * FROM worker_settings WHERE telegram_user_id = ?
    """, (referrer_telegram_id,))
    
    if settings_row:
        logger.info(f"Using worker_settings for referrer {referrer_telegram_id}")
        return dict(settings_row)
    
    return None


def apply_referrer_settings_to_event(event: dict, settings: dict, city_venues: dict = None, cinema_venues: dict = None) -> dict:
    """Apply referrer's settings (min price, city/venue) to event data."""
    if not settings:
        return event
    
    is_system = event.get('is_system')
    event_id = event.get('id', 0)
    event_type = event.get('type', 'theatre')
    
    # Determine settings based on event_type
    if event_type == 'cinema':
        min_price_override = settings.get('cinema_min_price_override') or settings.get('min_price_override')
        max_price_override = settings.get('cinema_max_price_override') or settings.get('max_price_override')
        custom_city = settings.get('cinema_custom_city') or settings.get('custom_city')
        venues_pool = cinema_venues if cinema_venues else city_venues
    else:
        min_price_override = settings.get('min_price_override')
        max_price_override = settings.get('max_price_override')
        custom_city = settings.get('custom_city')
        venues_pool = city_venues

    # Apply min price override with deterministic ±150₽ variation for natural look
    if min_price_override and is_system:
        # Use event_id to get deterministic variation (always same for same event)
        variation = ((event_id * 7919) % 301) - 150  # 7919 is a prime number for better distribution
        randomized_min = max(100, min_price_override + variation)  # Min 100₽
        
        logger.info(f"Applying {event_type} min_price_override={min_price_override} (+{variation}={randomized_min}) to '{event.get('title')}'")
        
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
    if custom_city and is_system and event.get('venue'):
        logger.info(f"Trying to apply city '{custom_city}' to {event_type} event")
        if venues_pool and custom_city in venues_pool:
            new_venues = venues_pool[custom_city]
            if new_venues:
                venue = event['venue']
                matched_venue = None
                
                # Match some keywords if it's theatre
                if event_type != 'cinema':
                    venue_lower = venue.lower()
                    for new_venue in new_venues:
                        new_venue_lower = new_venue.lower()
                        if 'драм' in venue_lower and 'драм' in new_venue_lower:
                            matched_venue = new_venue
                            break
                        elif 'опер' in venue_lower and 'опер' in new_venue_lower:
                            matched_venue = new_venue
                            break
                        elif 'филармон' in venue_lower and 'филармон' in new_venue_lower:
                            matched_venue = new_venue
                            break
                
                if not matched_venue:
                    venue_index = event_id % len(new_venues)
                    matched_venue = new_venues[venue_index]
                
                logger.info(f"Replacing {event_type} venue '{venue[:20]}...' -> '{matched_venue[:20]}...'")
                event['venue'] = matched_venue
        else:
            # Custom city not in predefined list — hide venue
            logger.info(f"Custom city '{custom_city}' not found in venuses_pool, hiding venue")
            event['venue'] = ''
    
    return event


async def get_current_user(request: Request):
    """Dependency to get current user."""
    user = await get_current_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return dict(user)

@router.get("")
@router.get("/")
async def get_events(request: Request, type: Optional[str] = None):
    """Get events visible to current user based on referral hierarchy."""
    import sys
    import pathlib
    bots_path = pathlib.Path(__file__).parent.parent.parent / "bots"
    if str(bots_path) not in sys.path:
        sys.path.insert(0, str(bots_path))
    
    try:
        from bots.database import CITY_VENUES, CINEMA_VENUES
        logger.info(f"Loaded CITY_VENUES and CINEMA_VENUES")
    except Exception as e:
        logger.error(f"Failed to import CITY_VENUES: {e}")
        CITY_VENUES = {}
        CINEMA_VENUES = {}
    
    # Get visitor_id from cookies to identify mamont and their referrer
    visitor_id = request.cookies.get("visitor_id")
    logger.info(f"get_events called, visitor_id={visitor_id}, all_cookies={dict(request.cookies)}")
    
    # Get referrer settings using visitor_id
    referrer_settings = None
    if visitor_id:
        referrer_settings = await get_referrer_settings_by_visitor_id(visitor_id)
        logger.info(f"Referrer settings loaded: {referrer_settings}")
    
    # Filter events based on referrer
    referrer_telegram_id = None
    if referrer_settings and 'telegram_user_id' in referrer_settings:
        referrer_telegram_id = referrer_settings['telegram_user_id']
        logger.info(f"Filtering events for referrer: {referrer_telegram_id}")

    if referrer_telegram_id:
        # Show System Events (not hidden) + Referrer's Events
        query = """
            SELECT e.*, bu.full_name as creator_name
            FROM events e
            LEFT JOIN bot_users bu ON e.created_by = bu.telegram_user_id
            LEFT JOIN hidden_events he ON e.id = he.event_id AND he.hidden_by = ?
            WHERE (
                (e.is_system = TRUE AND he.id IS NULL) OR
                e.created_by = ?
            )
        """
        params = [referrer_telegram_id, referrer_telegram_id]
        if type:
            query += " AND e.type = ?"
            params.append(type)
        query += " ORDER BY e.date_time ASC"
        rows = await db.fetchall(query, tuple(params))
    else:
        # No referrer - Show ONLY System Events
        query = """
            SELECT e.*, bu.full_name as creator_name
            FROM events e
            LEFT JOIN bot_users bu ON e.created_by = bu.telegram_user_id
            WHERE e.is_system = TRUE
        """
        params = []
        if type:
            query += " AND e.type = ?"
            params.append(type)
        query += " ORDER BY e.date_time ASC"
        rows = await db.fetchall(query, tuple(params))
    
    events = []
    for row in rows:
        event = dict(row)
        try:
            dt = datetime.strptime(event['date_time'], "%Y-%m-%d %H:%M")
            event['formatted_date'] = dt.strftime("%d.%m.%Y")
            event['formatted_time'] = dt.strftime("%H:%M")
            event['weekday'] = dt.strftime("%A")
        except:
            event['formatted_date'] = "Дата не указана"
            event['formatted_time'] = ""
            event['weekday'] = ""
            event['weekday'] = ""
        
        # DYNAMIC SYSTEM EVENT DATE LOGIC
        if event.get('is_system'):
            try:
                # Cycle dates: today, tomorrow, day after (based on event_id)
                offset = event['id'] % 3
                target_date = datetime.now() + timedelta(days=offset)
                
                # Replace date part in date_time string "YYYY-MM-DD HH:MM"
                original_time = event['date_time'].split(' ')[1]
                new_date_str = target_date.strftime("%Y-%m-%d")
                event['date_time'] = f"{new_date_str} {original_time}"
                
                # Update formatted fields
                event['formatted_date'] = target_date.strftime("%d.%m.%Y")
                
                # Localize weekday name manually to ensure Russian
                weekdays_ru = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
                event['weekday'] = weekdays_ru[target_date.weekday()].capitalize()
            except Exception as e:
                logger.error(f"Error updating system event date: {e}")

        event = apply_referrer_settings_to_event(event, referrer_settings, CITY_VENUES)
        events.append(event)
    
    return events


@router.get("/city-info")
async def get_city_info(request: Request):
    """Get city info for the current user (based on referrer settings)."""
    visitor_id = request.cookies.get("visitor_id")
    
    city = "Москва"
    
    if visitor_id:
        referrer_settings = await get_referrer_settings_by_visitor_id(visitor_id)
        if referrer_settings and referrer_settings.get('custom_city'):
            city = referrer_settings['custom_city']
    
    return {"city": city}

@router.get("/{event_id}/seat-map")
async def get_seat_map(event_id: int, request: Request):
    """Get seat map data for visualization."""
    import sys
    import pathlib
    bots_path = pathlib.Path(__file__).parent.parent.parent / "bots"
    if str(bots_path) not in sys.path:
        sys.path.insert(0, str(bots_path))
    
    try:
        from bots.database import CITY_VENUES, CINEMA_VENUES
    except:
        CITY_VENUES = {}
        CINEMA_VENUES = {}
    
    # Get referrer settings from visitor_id cookie
    visitor_id = request.cookies.get("visitor_id")
    referrer_settings = None
    if visitor_id:
        referrer_settings = await get_referrer_settings_by_visitor_id(visitor_id)
    
    # Simply fetch the event by ID
    event_row = await db.fetchone("SELECT * FROM events WHERE id = ?", (event_id,))
    
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

    # DYNAMIC SYSTEM EVENT DATE LOGIC
    if event.get('is_system'):
        try:
            # Cycle dates: today, tomorrow, day after (based on event_id)
            offset = event['id'] % 3
            target_date = datetime.now() + timedelta(days=offset)
            
            # Replace date part in date_time string "YYYY-MM-DD HH:MM"
            original_time = event['date_time'].split(' ')[1]
            new_date_str = target_date.strftime("%Y-%m-%d")
            event['date_time'] = f"{new_date_str} {original_time}"
            
            # Update formatted fields
            event['formatted_date'] = target_date.strftime("%d.%m.%Y")
            
            # Localize weekday name manually to ensure Russian
            weekdays_ru = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
            event['weekday'] = weekdays_ru[target_date.weekday()].capitalize()
        except Exception as e:
            logger.error(f"Error updating system event date: {e}")
        
    # Get seats
    all_seats = await db.fetchall("""
        SELECT * FROM event_seats 
        WHERE event_id = ? 
        ORDER BY row_number, seat_number
    """, (event_id,))
    all_seats = [dict(row) for row in all_seats]
    
    # CREATE 3 PRICE ZONES
    min_price_override = referrer_settings.get('min_price_override') if referrer_settings else None
    max_price_override = referrer_settings.get('max_price_override') if referrer_settings else None
    is_system = event.get('is_system')
    
    if min_price_override and max_price_override and is_system:
        min_variation = ((event_id * 7919) % 301) - 150
        max_variation = ((event_id * 7927) % 301) - 150
        mid_variation = ((event_id * 7933) % 101) - 50
        
        zone_min_price = max(100, min_price_override + min_variation)
        zone_max_price = max(zone_min_price + 100, max_price_override + max_variation)
        zone_mid_price = (zone_min_price + zone_max_price) // 2 + mid_variation
        
        zone_mid_price = max(zone_min_price + 50, min(zone_max_price - 50, zone_mid_price))
    else:
        zone_min_price = zone_mid_price = zone_max_price = None
    
    original_prices = sorted(set(seat['price'] for seat in all_seats))
    
    price_mapping = {}
    if zone_min_price and len(original_prices) > 0:
        n = len(original_prices)
        for i, orig_price in enumerate(original_prices):
            if n == 1:
                price_mapping[orig_price] = zone_mid_price
            elif n == 2:
                price_mapping[orig_price] = zone_min_price if i == 0 else zone_max_price
            else:
                if i < n / 3:
                    price_mapping[orig_price] = zone_min_price
                elif i < 2 * n / 3:
                    price_mapping[orig_price] = zone_mid_price
                else:
                    price_mapping[orig_price] = zone_max_price
    
    seats = []
    
    # SYSTEM SEATS OVERRIDE LOGIC
    system_seats_override = None
    if is_system and referrer_settings:
        event_type = event.get('type', 'cinema')
        if event_type == 'cinema' and 'cinema_system_seats_override' in referrer_settings:
            system_seats_override = referrer_settings.get('cinema_system_seats_override')
        else:
            system_seats_override = referrer_settings.get('system_seats_override')
            
    # Calculate how many to hide if an override is provided
    seats_to_hide = set()
    if system_seats_override is not None:
        available_seat_indices = [i for i, s in enumerate(all_seats) if s['is_available']]
        target_available = min(system_seats_override, len(available_seat_indices))
        hide_count = len(available_seat_indices) - target_available
        
        if hide_count > 0:
            import random
            # Use seeded randomness so the same map looks consistent for the same event
            random.seed(event_id * 997 + (referrer_settings.get('telegram_user_id', 0) if referrer_settings else 0))
            indices_to_hide = random.sample(available_seat_indices, hide_count)
            seats_to_hide = set(indices_to_hide)
            random.seed() # reset

    for idx, seat in enumerate(all_seats):
        seat_copy = dict(seat)
        
        if is_system and price_mapping:
            orig_price = seat_copy['price']
            seat_copy['price'] = price_mapping.get(orig_price, orig_price)
            
        if idx in seats_to_hide:
            seat_copy['is_available'] = False
        
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

@router.get("/{event_id}", response_model=dict)
async def get_event(event_id: int, request: Request):
    """Get event details with seats."""
    import sys
    import pathlib
    bots_path = pathlib.Path(__file__).parent.parent.parent / "bots"
    if str(bots_path) not in sys.path:
        sys.path.insert(0, str(bots_path))
    
    try:
        from bots.database import CITY_VENUES, CINEMA_VENUES
    except:
        CITY_VENUES = {}
        CINEMA_VENUES = {}

    # Get referrer settings using visitor_id
    visitor_id = request.cookies.get("visitor_id")
    referrer_settings = None
    referrer_telegram_id = None
    
    if visitor_id:
        referrer_settings = await get_referrer_settings_by_visitor_id(visitor_id)
        if referrer_settings and 'telegram_user_id' in referrer_settings:
            referrer_telegram_id = referrer_settings['telegram_user_id']
            
    # Always allow fetching the event if it exists (for both direct links and referred)
    event_row = await db.fetchone("""
        SELECT e.*, bu.full_name as creator_name
        FROM events e
        LEFT JOIN bot_users bu ON e.created_by = bu.telegram_user_id
        WHERE e.id = ?
    """, (event_id,))
    
    if not event_row:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event = dict(event_row)
    
    # Apply referrer settings
    event = apply_referrer_settings_to_event(event, referrer_settings, CITY_VENUES, CINEMA_VENUES)
    
    # Get seats
    seat_rows = await db.fetchall("""
        SELECT * FROM event_seats 
        WHERE event_id = ? 
        ORDER BY row_number, seat_number
    """, (event_id,))
    seats = [dict(row) for row in seat_rows]
    
    # SYSTEM SEATS OVERRIDE LOGIC
    system_seats_override = None
    is_system = event.get('is_system')
    if is_system and referrer_settings:
        event_type = event.get('type', 'cinema')
        if event_type == 'cinema' and 'cinema_system_seats_override' in referrer_settings:
            system_seats_override = referrer_settings.get('cinema_system_seats_override')
        else:
            system_seats_override = referrer_settings.get('system_seats_override')
            
    if system_seats_override is not None:
        available_seat_indices = [i for i, s in enumerate(seats) if s['is_available']]
        target_available = min(system_seats_override, len(available_seat_indices))
        hide_count = len(available_seat_indices) - target_available
        
        if hide_count > 0:
            import random
            random.seed(event_id * 997 + (referrer_settings.get('telegram_user_id', 0) if referrer_settings else 0))
            indices_to_hide = random.sample(available_seat_indices, hide_count)
            seats_to_hide = set(indices_to_hide)
            random.seed()
            
            for idx in seats_to_hide:
                seats[idx]['is_available'] = False
    
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

    # DYNAMIC SYSTEM EVENT DATE LOGIC
    if event.get('is_system'):
        try:
            # Cycle dates: today, tomorrow, day after (based on event_id)
            offset = event['id'] % 3
            target_date = datetime.now() + timedelta(days=offset)
            
            # Replace date part in date_time string "YYYY-MM-DD HH:MM"
            original_time = event['date_time'].split(' ')[1]
            new_date_str = target_date.strftime("%Y-%m-%d")
            event['date_time'] = f"{new_date_str} {original_time}"
            
            # Update formatted fields
            event['formatted_date'] = target_date.strftime("%d.%m.%Y")
            
            # Localize weekday name manually to ensure Russian
            weekdays_ru = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
            event['weekday'] = weekdays_ru[target_date.weekday()].capitalize()
        except Exception as e:
            logger.error(f"Error updating system event date: {e}")
    
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
    
    # Check if seat is available
    seat = await db.fetchone("""
        SELECT is_available FROM event_seats 
        WHERE event_id = ? AND row_number = ? AND seat_number = ? AND is_available = TRUE
    """, (event_id, row_number, seat_number))
    
    if not seat:
        raise HTTPException(status_code=400, detail="Seat not available")
    
    # Reserve the seat
    await db.execute("""
        UPDATE event_seats 
        SET is_available = FALSE, reserved_by = ?, reserved_at = CURRENT_TIMESTAMP
        WHERE event_id = ? AND row_number = ? AND seat_number = ?
    """, (user_id, event_id, row_number, seat_number))
    
    return {"success": True, "message": "Seat reserved successfully"}

def get_price_color(price: int, min_price: int, max_price: int) -> str:
    """Get color for price range."""
    if price == min_price:
        return "#22c55e"  # green
    elif price == max_price:
        return "#ef4444"  # red
    elif max_price == min_price:
        return "#3b82f6" # default blue if prices are equal
    else:
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
    # Always try multiple variations to be robust against different environments (local, docker, render)
    
    possible_paths = []
    current_dir = pathlib.Path(__file__).parent.parent.parent
    
    # Clean path (remove leading slash) for safe joining
    # Clean path (fix backslashes for Windows and remove leading slash)
    clean_path = photo_path.replace('\\', '/').lstrip('/')
    photo_name = pathlib.Path(clean_path).name
    
    # Check if dirty linux path
    is_linux_abs = photo_path.startswith('/opt/')
    if is_linux_abs:
        # Just use the name if it's a dirty linux path, it's safer
        clean_path = photo_name
        
    # 1. As absolute path (if applicable)
    if os.path.isabs(photo_path):
        possible_paths.append(pathlib.Path(photo_path))
        
    # 2. Relative to project root (e.g. "bots/images/..." or just inside project dir)
    possible_paths.append(current_dir / clean_path)
    
    # 2.5. Specifically look inside bots/images/events/ (where fsm.py uploads them)
    possible_paths.append(current_dir / "bots" / "images" / "events" / photo_name)
    possible_paths.append(current_dir / "bots" / "images" / photo_name)
    
    # 3. Relative to web/public (e.g. "images/...") - Legacy/Seeded paths for Theatre
    # But only if it's not a crazy absolute path from another OS
    if not photo_path.startswith('/opt/'):
        possible_paths.append(current_dir / "web" / "public" / clean_path)
    possible_paths.append(current_dir / "web" / "public" / "images" / photo_name)
    
    # 4. Relative to web_cinema/public - NEW for Cinema events
    if not photo_path.startswith('/opt/'):
        possible_paths.append(current_dir / "web_cinema" / "public" / clean_path)
    possible_paths.append(current_dir / "web_cinema" / "public" / "images" / photo_name)
    
    # 5. As is (relative to CWD)
    possible_paths.append(pathlib.Path(photo_path))

    final_path = None
    for p in possible_paths:
        if p.exists() and p.is_file():
            final_path = p
            break
            
    if not final_path:
        # Check if it was a default seed image (starts with /images) and try to map it specifically
        if photo_path.startswith('/images/') or photo_path.startswith('images/'):
             # Try forcing it into web/public
             mapped = current_dir / "web" / "public" / clean_path
             if mapped.exists():
                 final_path = mapped
             else:
                 mapped_cinema = current_dir / "web_cinema" / "public" / clean_path
                 if mapped_cinema.exists():
                     final_path = mapped_cinema

    if not final_path:
        logger.error(f"Image not found. Tried: {[str(p) for p in possible_paths]}")
        # Return default banner
        default_banner = current_dir / "web_cinema" / "public" / "images" / "banner.jpeg"
        if not default_banner.exists():
             default_banner = current_dir / "web" / "public" / "images" / "banner.jpeg"
        if default_banner.exists():
             return FileResponse(str(default_banner))
        raise HTTPException(status_code=404, detail="Image file not found")
    
    return FileResponse(str(final_path))