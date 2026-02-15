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

def generate_me_image(nickname: str, total_profits: int, avg_profit: int, days_in_team: int) -> "BytesIO":
    from PIL import Image, ImageDraw, ImageFont
    from pathlib import Path
    from io import BytesIO
    
    # Paths (Assuming relative to project root or this file)
    # utils.py is in bots/, images in bots/images, fonts in bots/fonts
    base_path = Path(__file__).parent
    bg_path = base_path / "images" / "me_command.png"
    font_path = base_path / "fonts" / "UIHanky-Bold (1).otf"
    
    # Load Image
    img = Image.open(bg_path)
    draw = ImageDraw.Draw(img)
    
    # Load Font
    try:
        font = ImageFont.truetype(str(font_path), 50)
    except IOError:
        # Fallback if font not found
        font = ImageFont.load_default()
        
    # Text Color (White usually looks good on dark, or Black on light. Assuming White for now)
    text_color = (255, 255, 255)
    
    # Coordinates provided by user
    # 1. Nick - 1150 300
    # 2. Total Profits - 1150 440
    # 3. Avg Profit - 1150 600
    # 4. Days in Team - 1150 740
    
    draw.text((920, 275), f"Ник: {nickname}", font=font, fill=text_color)
    draw.text((920, 425), f"{total_profits} P", font=font, fill=text_color)
    draw.text((920, 570), f"Ср. {avg_profit} P", font=font, fill=text_color)
    draw.text((920, 720), f"Дней в команде: {days_in_team}", font=font, fill=text_color)
    
    bio = BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio
