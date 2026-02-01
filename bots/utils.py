from datetime import datetime, timezone
from typing import Optional

def format_cooldown_remaining(cooldown_until: str) -> str:
    try:
        cd = datetime.fromisoformat(cooldown_until)
        if cd.tzinfo is None:
            cd = cd.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if cd <= now:
            return "00:00"
        delta = cd - now
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    except:
        return "00:00"

def is_cooldown_active(cooldown_until: Optional[str]) -> bool:
    if not cooldown_until:
        return False
    try:
        cd = datetime.fromisoformat(cooldown_until)
        if cd.tzinfo is None:
            cd = cd.replace(tzinfo=timezone.utc)
        return cd > datetime.now(timezone.utc)
    except:
        return False

def calculate_days_in_team(joined_at: Optional[str]) -> int:
    if not joined_at:
        return 0
    try:
        joined = datetime.fromisoformat(joined_at)
        if joined.tzinfo is None:
            joined = joined.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - joined
        return max(0, delta.days)
    except:
        return 0

def format_mamont_display(mamont: dict) -> str:
    """Format mamont for display in inline button."""
    if not mamont:
        return "Unknown"
    
    status = mamont.get('status', '')
    first_name = mamont.get('first_name') or ""
    last_name = mamont.get('last_name') or ""
    
    # If not registered, show only mamont_id
    if status not in ['registered', 'paid']:
        return f"#{mamont.get('mamont_id', 'Unknown')}"
    
    # If no name data, show mamont_id
    if not first_name and not last_name:
        return f"#{mamont.get('mamont_id', 'Unknown')}"
    
    # Build name part
    name_part = f"{first_name} {last_name}".strip()
    
    # Build telegram part
    tg_name = mamont.get('tg_name') or ""
    tg_username = mamont.get('tg_username') or ""
    
    if tg_username:
        tg_part = f"@{tg_username}"
    elif tg_name:
        tg_part = tg_name
    else:
        tg_part = "TG"
    
    return f"{name_part} ({tg_part})"
