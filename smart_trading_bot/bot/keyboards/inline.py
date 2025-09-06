"""
Inline клавиатуры для Telegram бота
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Получить сигнал", callback_data="get_signal"),
            InlineKeyboardButton("📈 Статистика", callback_data="user_stats")
        ],
        [
            InlineKeyboardButton("👥 Рефералы", callback_data="referral_program"),
            InlineKeyboardButton("🏢 Платформы", callback_data="show_platforms")
        ],
        [
            InlineKeyboardButton("💎 Premium", callback_data="premium_info"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="user_settings")
        ],
        [
            InlineKeyboardButton("ℹ️ Помощь", callback_data="help_info"),
            InlineKeyboardButton("📞 Поддержка", callback_data="support")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_signal_keyboard(signal_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для торгового сигнала"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Детальный анализ", callback_data=f"detailed_analysis_{signal_id}"),
        ],
        [
            InlineKeyboardButton("🎯 Binarium", callback_data=f"trade_binarium_{signal_id}"),
            InlineKeyboardButton("💼 PocketOption", callback_data=f"trade_pocket_{signal_id}")
        ],
        [
            InlineKeyboardButton("✅ Прибыль", callback_data=f"result_win_{signal_id}"),
            InlineKeyboardButton("❌ Убыток", callback_data=f"result_loss_{signal_id}"),
            InlineKeyboardButton("⚪️ Безубыток", callback_data=f"result_break_{signal_id}")
        ],
        [
            InlineKeyboardButton("🔄 Новый сигнал", callback_data="get_signal"),
            InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_platforms_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора торговых платформ"""
    keyboard = [
        [
            InlineKeyboardButton("🎯 Binarium - Бинарные опционы", 
                               url=f"https://clck.biz/lp/sure-start/?partner_id=p43053p136178p011d&user_ref={user_id}")
        ],
        [
            InlineKeyboardButton("💼 PocketOption - CFD торговля", 
                               url=f"https://po-ru4.click/cabinet/demo-quick-high-low?a=OWrYm1TLeFf1Cv&ref={user_id}")
        ],
        [
            InlineKeyboardButton("📊 Сравнить платформы", callback_data="compare_platforms")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_referral_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура реферальной программы"""
    referral_link = f"https://t.me/YourBotUsername?start=ref_{user_id}"
    
    keyboard = [
        [
            InlineKeyboardButton("📋 Скопировать ссылку", callback_data=f"copy_ref_link_{user_id}")
        ],
        [
            InlineKeyboardButton("📊 Моя статистика", callback_data="referral_stats"),
            InlineKeyboardButton("💰 Выплаты", callback_data="payouts_history")
        ],
        [
            InlineKeyboardButton("📈 Топ рефереры", callback_data="top_referrers"),
            InlineKeyboardButton("🎁 Бонусы", callback_data="referral_bonuses")
        ],
        [
            InlineKeyboardButton("📱 Поделиться", switch_inline_query=f"Зарабатывай с торговыми сигналами! {referral_link}")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_premium_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура Premium подписки"""
    keyboard = [
        [
            InlineKeyboardButton("💎 Premium - $29.99/мес", callback_data="buy_premium"),
            InlineKeyboardButton("👑 VIP - $99.99/мес", callback_data="buy_vip")
        ],
        [
            InlineKeyboardButton("📋 Сравнить тарифы", callback_data="compare_plans")
        ],
        [
            InlineKeyboardButton("🎁 Попробовать 7 дней", callback_data="trial_premium")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек пользователя"""
    keyboard = [
        [
            InlineKeyboardButton("🔔 Уведомления", callback_data="notification_settings"),
            InlineKeyboardButton("🌍 Язык", callback_data="language_settings")
        ],
        [
            InlineKeyboardButton("⏰ Время торговли", callback_data="trading_hours"),
            InlineKeyboardButton("📊 Типы сигналов", callback_data="signal_types")
        ],
        [
            InlineKeyboardButton("💳 Способы оплаты", callback_data="payment_methods"),
            InlineKeyboardButton("🔐 Безопасность", callback_data="security_settings")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Админская клавиатура"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton("📡 Рассылка", callback_data="admin_broadcast"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings")
        ],
        [
            InlineKeyboardButton("📈 Сигналы", callback_data="admin_signals"),
            InlineKeyboardButton("💰 Комиссии", callback_data="admin_commissions")
        ],
        [
            InlineKeyboardButton("🔧 Система", callback_data="admin_system"),
            InlineKeyboardButton("📋 Логи", callback_data="admin_logs")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_notification_settings_keyboard(settings: dict) -> InlineKeyboardMarkup:
    """Клавиатура настроек уведомлений"""
    signal_icon = "🔔" if settings.get('signal_notifications', True) else "🔕"
    commission_icon = "🔔" if settings.get('commission_notifications', True) else "🔕"
    news_icon = "🔔" if settings.get('news_notifications', True) else "🔕"
    
    keyboard = [
        [
            InlineKeyboardButton(f"{signal_icon} Сигналы", callback_data="toggle_signal_notifications")
        ],
        [
            InlineKeyboardButton(f"{commission_icon} Комиссии", callback_data="toggle_commission_notifications")
        ],
        [
            InlineKeyboardButton(f"{news_icon} Новости", callback_data="toggle_news_notifications")
        ],
        [
            InlineKeyboardButton("⏰ Время уведомлений", callback_data="notification_time")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="user_settings")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_language_keyboard(current_lang: str = 'ru') -> InlineKeyboardMarkup:
    """Клавиатура выбора языка"""
    languages = {
        'ru': '🇷🇺 Русский',
        'en': '🇺🇸 English',
        'es': '🇪🇸 Español',
        'de': '🇩🇪 Deutsch',
        'fr': '🇫🇷 Français'
    }
    
    keyboard = []
    for code, name in languages.items():
        if code == current_lang:
            name = f"✅ {name}"
        keyboard.append([InlineKeyboardButton(name, callback_data=f"set_language_{code}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="user_settings")])
    return InlineKeyboardMarkup(keyboard)

def get_payment_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура способов оплаты"""
    keyboard = [
        [
            InlineKeyboardButton("💳 Банковская карта", callback_data="payment_card"),
            InlineKeyboardButton("📱 Apple Pay", callback_data="payment_apple")
        ],
        [
            InlineKeyboardButton("🅿️ PayPal", callback_data="payment_paypal"),
            InlineKeyboardButton("₿ Криптовалюта", callback_data="payment_crypto")
        ],
        [
            InlineKeyboardButton("🏦 Банковский перевод", callback_data="payment_bank")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="premium_info")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_signal_types_keyboard(user_preferences: dict) -> InlineKeyboardMarkup:
    """Клавиатура типов сигналов"""
    forex_icon = "✅" if user_preferences.get('forex', True) else "❌"
    crypto_icon = "✅" if user_preferences.get('crypto', True) else "❌"
    stocks_icon = "✅" if user_preferences.get('stocks', False) else "❌"
    commodities_icon = "✅" if user_preferences.get('commodities', False) else "❌"
    
    keyboard = [
        [
            InlineKeyboardButton(f"{forex_icon} Forex", callback_data="toggle_forex"),
            InlineKeyboardButton(f"{crypto_icon} Криптовалюты", callback_data="toggle_crypto")
        ],
        [
            InlineKeyboardButton(f"{stocks_icon} Акции", callback_data="toggle_stocks"),
            InlineKeyboardButton(f"{commodities_icon} Товары", callback_data="toggle_commodities")
        ],
        [
            InlineKeyboardButton("⏱️ Таймфреймы", callback_data="timeframe_settings")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="user_settings")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard(action: str, item_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    callback_confirm = f"confirm_{action}_{item_id}" if item_id else f"confirm_{action}"
    callback_cancel = f"cancel_{action}_{item_id}" if item_id else f"cancel_{action}"
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data=callback_confirm),
            InlineKeyboardButton("❌ Отменить", callback_data=callback_cancel)
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_pagination_keyboard(current_page: int, total_pages: int, 
                          callback_prefix: str, extra_buttons: List = None) -> InlineKeyboardMarkup:
    """Клавиатура с пагинацией"""
    keyboard = []
    
    # Кнопки пагинации
    pagination_row = []
    
    if current_page > 1:
        pagination_row.append(InlineKeyboardButton("⬅️", callback_data=f"{callback_prefix}_page_{current_page-1}"))
    
    pagination_row.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="noop"))
    
    if current_page < total_pages:
        pagination_row.append(InlineKeyboardButton("➡️", callback_data=f"{callback_prefix}_page_{current_page+1}"))
    
    keyboard.append(pagination_row)
    
    # Дополнительные кнопки
    if extra_buttons:
        keyboard.extend(extra_buttons)
    
    return InlineKeyboardMarkup(keyboard)

def get_back_button(callback_data: str) -> InlineKeyboardMarkup:
    """Простая кнопка назад"""
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=callback_data)]])

# Вспомогательные функции
def create_url_button(text: str, url: str) -> InlineKeyboardButton:
    """Создание кнопки с URL"""
    return InlineKeyboardButton(text, url=url)

def create_callback_button(text: str, callback_data: str) -> InlineKeyboardButton:
    """Создание кнопки с callback"""
    return InlineKeyboardButton(text, callback_data=callback_data)

def create_switch_inline_button(text: str, query: str) -> InlineKeyboardButton:
    """Создание кнопки для inline режима"""
    return InlineKeyboardButton(text, switch_inline_query=query)