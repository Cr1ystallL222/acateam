from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.copy_text_button import CopyTextButton

def get_profile_keyboard(balance: int = 0, is_admin: bool = False) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="Театр", callback_data="menu_theatre"),
            InlineKeyboardButton(text="Кино", callback_data="menu_cinema")
        ]
    ]
    
    if balance > 0:
        keyboard.insert(0, [InlineKeyboardButton(text="💸 Вывод", callback_data="menu_withdraw")])
    
    if is_admin:
        # Add Admin Panel button in a new row or same row? Let's add new row for visibility
        keyboard.append([InlineKeyboardButton(text="Админ панель", callback_data="menu_admin")])
        
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_theatre_keyboard(ref_link: str, link_id: int = None) -> InlineKeyboardMarkup:
    # If link_id is present, settings should be for that link
    settings_callback = f"menu_settings:{link_id}" if link_id else "menu_settings"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Скопировать реф. ссылку", copy_text=CopyTextButton(text=ref_link))],
        [
            InlineKeyboardButton(text="Клиенты", callback_data="menu_clients"),
            InlineKeyboardButton(text="События", callback_data="menu_events")
        ],
        [InlineKeyboardButton(text="Настройки", callback_data=settings_callback)],
        [InlineKeyboardButton(text="Назад", callback_data="menu_back_links")]
    ])

def get_links_management_keyboard(links: list) -> InlineKeyboardMarkup:
    """Generate keyboard for links management menu.
    
    Button numbers (1, 2, 3...) are visual order in the list,
    callback_data contains internal id for lookup.
    """
    keyboard = []
    
    # Add link buttons (3 per row)
    row = []
    for idx, link in enumerate(links, start=1):
        row.append(InlineKeyboardButton(
            text=str(idx),  # Visual number = order in list
            callback_data=f"select_link:{link['id']}"  # Internal id
        ))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    # Add create and back buttons
    keyboard.append([InlineKeyboardButton(text="➕ Создать ссылку", callback_data="create_link")])
    keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu_back_profile")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_clients_keyboard(mamonts: list) -> InlineKeyboardMarkup:
    """Generate keyboard with mamont buttons."""
    keyboard = []
    
    # Add mamont buttons (max 2 per row)
    for i in range(0, len(mamonts), 2):
        row = []
        for j in range(2):
            if i + j < len(mamonts):
                mamont = mamonts[i + j]
                display_name = format_mamont_display_for_button(mamont)
                row.append(InlineKeyboardButton(
                    text=display_name, 
                    callback_data=f"mamont:{mamont['mamont_id']}"
                ))
        keyboard.append(row)
    
    # Add back button
    keyboard.append([InlineKeyboardButton(text="Назад", callback_data="menu_back_theatre")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_stub_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="menu_back_theatre")]
    ])

def get_settings_keyboard(settings: dict, link_id: int = None) -> InlineKeyboardMarkup:
    """Generate settings keyboard with current values."""
    min_price = settings.get('min_price_override')
    min_price_text = f"💰 Мин. цена: {min_price}₽" if min_price else "💰 Мин. цена: не установлена"
    
    max_price = settings.get('max_price_override')
    max_price_text = f"💎 Макс. цена: {max_price}₽" if max_price else "💎 Макс. цена: не установлена"
    
    city = settings.get('custom_city')
    city_text = f"🏙️ Город: {city}" if city else "🏙️ Город: Краснодар (по умолчанию)"
    
    # Suffix for callbacks
    suffix = f":{link_id}" if link_id else ""
    back_callback = f"select_link:{link_id}" if link_id else "menu_back_theatre"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=min_price_text, callback_data=f"settings_min_price{suffix}")],
        [InlineKeyboardButton(text=max_price_text, callback_data=f"settings_max_price{suffix}")],
        [InlineKeyboardButton(text=city_text, callback_data=f"settings_city{suffix}")],
        [InlineKeyboardButton(text="Назад", callback_data=back_callback)]
    ])

def get_events_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for events menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Список событий", callback_data="events_list"),
            InlineKeyboardButton(text="Добавить событие", callback_data="events_add")
        ],
        [InlineKeyboardButton(text="Назад", callback_data="menu_back_theatre")]
    ])

def format_mamont_display_for_button(mamont: dict) -> str:
    """Format mamont for display in inline button (shorter version)."""
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
    
    # Build telegram part (shorter for button)
    tg_username = mamont.get('tg_username') or ""
    
    if tg_username:
        tg_part = f"@{tg_username}"
    else:
        tg_part = "TG"
    
    # Limit length for button display
    if len(name_part) > 15:
        name_part = name_part[:12] + "..."
    
    return f"{name_part} ({tg_part})"
