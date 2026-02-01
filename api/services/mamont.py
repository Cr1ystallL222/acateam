import random

async def generate_mamont_id(db) -> str:
    """Generate unique 5-digit mamont_id (10000-99999)."""
    while True:
        new_id = str(random.randint(10000, 99999))
        async with db.execute("SELECT 1 FROM mamonts WHERE mamont_id = ?", (new_id,)) as cursor:
            if not await cursor.fetchone():
                return new_id

def get_mamont_display(mamont: dict) -> str:
    """
    Format mamont_user for display.
    - If not registered or no name: return mamont_id
    - Otherwise: "{first_name} {last_name} ({tg_name})"
    """
    if not mamont:
        return "Unknown"
    
    status = mamont.get('status', '')
    first_name = mamont.get('first_name') or ""
    last_name = mamont.get('last_name') or ""
    
    if status != 'registered' and status != 'paid':
        return mamont.get('mamont_id', 'Unknown')
    
    if not first_name and not last_name:
        return mamont.get('mamont_id', 'Unknown')
    
    # Build tg_name
    tg_name = mamont.get('tg_name') or ""
    tg_username = mamont.get('tg_username') or ""
    
    if not tg_name:
        if tg_username:
            tg_name = f"@{tg_username}"
        else:
            tg_name = "Telegram"
    
    name_part = f"{first_name} {last_name}".strip()
    return f"{name_part} ({tg_name})"
