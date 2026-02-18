from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.copy_text_button import CopyTextButton

def get_profile_keyboard(balance: int = 0, is_admin: bool = False) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="Театр", callback_data="menu_theatre"),
            InlineKeyboardButton(text="Кино", callback_data="menu_cinema"),
        ],
        [
            InlineKeyboardButton(text="О проекте", callback_data="menu_about")
        ]
    ]
    
    if balance > 0:
        keyboard.insert(0, [InlineKeyboardButton(text="💸 Вывод", callback_data="menu_withdraw")])
    
    if is_admin:
        # Add Admin Panel button in a new row or same row? Let's add new row for visibility
        keyboard.append([InlineKeyboardButton(text="Админ панель", callback_data="menu_admin")])
        
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_cinema_keyboard(ref_link: str, link_id: int = None) -> InlineKeyboardMarkup:
    # If link_id is present, settings should be for that link
    settings_callback = f"menu_settings_cinema:{link_id}" if link_id else "menu_settings_cinema"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Скопировать реф. ссылку", copy_text=CopyTextButton(text=ref_link))],
        [
            InlineKeyboardButton(text="Клиенты", callback_data="menu_clients_cinema"),
            InlineKeyboardButton(text="События", callback_data="menu_events_cinema")
        ],
        [InlineKeyboardButton(text="Настройки", callback_data=settings_callback)],
        [InlineKeyboardButton(text="Назад", callback_data="menu_back_links_cinema")]
    ])

def get_links_management_keyboard(links: list, type: str = "theatre") -> InlineKeyboardMarkup:
    """Generate keyboard for links management menu."""
    keyboard = []
    
    # Prefix for callbacks
    prefix = "select_link" if type == "theatre" else "select_link_cinema"
    create_callback = "create_link" if type == "theatre" else "create_link_cinema"
    
    # Add link buttons (3 per row)
    row = []
    for idx, link in enumerate(links, start=1):
        row.append(InlineKeyboardButton(
            text=str(idx),
            callback_data=f"{prefix}:{link['id']}"
        ))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    # Add create and back buttons
    keyboard.append([InlineKeyboardButton(text="➕ Создать ссылку", callback_data=create_callback)])
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
    
    # Back button logic based on type
    type_suffix = "_cinema" if "cinema" in (settings.get('type') or "") else ""
    back_callback = f"select_link{type_suffix}:{link_id}" if link_id else f"menu_back{type_suffix}_links"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=min_price_text, callback_data=f"settings_min_price{type_suffix}{suffix}")],
        [InlineKeyboardButton(text=max_price_text, callback_data=f"settings_max_price{type_suffix}{suffix}")],
        [InlineKeyboardButton(text=city_text, callback_data=f"settings_city{type_suffix}{suffix}")],
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

def get_about_keyboard(chat_link: str = None) -> InlineKeyboardMarkup:
    """Generate keyboard for About Project menu."""
    chat_btn = InlineKeyboardButton(text="Чат воркеров", callback_data="about_chat")
    
    if chat_link:
        chat_btn = InlineKeyboardButton(text="Чат воркеров", url=chat_link)
        
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Кураторы", callback_data="about_curators"),
            chat_btn
        ],
        [InlineKeyboardButton(text="Мануалы", callback_data="about_manuals")],
        [InlineKeyboardButton(text="Назад", callback_data="menu_back_profile")]
    ])

def get_about_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="menu_about")]
    ])
