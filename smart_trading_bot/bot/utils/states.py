"""
Состояния для ConversationHandler
"""
from enum import Enum, auto

class UserStates(Enum):
    """Состояния пользователя"""
    # Основные состояния
    MAIN_MENU = auto()
    WAITING_INPUT = auto()
    
    # Регистрация
    REGISTRATION_NAME = auto()
    REGISTRATION_PHONE = auto()
    REGISTRATION_EMAIL = auto()
    
    # Настройки
    SETTINGS_MENU = auto()
    SETTINGS_NOTIFICATIONS = auto()
    SETTINGS_LANGUAGE = auto()
    
    # Поддержка
    SUPPORT_MENU = auto()
    SUPPORT_MESSAGE = auto()
    SUPPORT_WAITING_RESPONSE = auto()
    
    # Админ панель
    ADMIN_MENU = auto()
    ADMIN_BROADCAST = auto()
    ADMIN_USER_SEARCH = auto()
    ADMIN_SIGNAL_CREATE = auto()
    
    # Рефералы
    REFERRAL_MENU = auto()
    REFERRAL_WITHDRAW = auto()
    REFERRAL_WITHDRAW_AMOUNT = auto()
    REFERRAL_WITHDRAW_METHOD = auto()
    
    # Сигналы
    SIGNALS_MENU = auto()
    SIGNALS_HISTORY = auto()
    SIGNALS_SETTINGS = auto()
    
    # Партнеры
    PARTNERS_MENU = auto()
    PARTNERS_REGISTRATION = auto()
    PARTNERS_STATS = auto()

class AdminStates(Enum):
    """Состояния администратора"""
    # Рассылка
    BROADCAST_TYPE = auto()
    BROADCAST_MESSAGE = auto()
    BROADCAST_CONFIRM = auto()
    
    # Управление пользователями
    USER_SEARCH = auto()
    USER_EDIT = auto()
    USER_BAN = auto()
    
    # Управление сигналами
    SIGNAL_CREATE = auto()
    SIGNAL_SYMBOL = auto()
    SIGNAL_DIRECTION = auto()
    SIGNAL_EXPIRY = auto()
    SIGNAL_CONFIDENCE = auto()
    
    # Настройки
    SETTINGS_EDIT = auto()
    SETTINGS_VALUE = auto()

class ConversationStates:
    """Константы состояний для удобства использования"""
    
    # Основные
    MAIN = "main"
    CANCEL = "cancel"
    END = "end"
    
    # Регистрация
    REG_NAME = "reg_name"
    REG_PHONE = "reg_phone"
    REG_EMAIL = "reg_email"
    
    # Поддержка
    SUPPORT_MSG = "support_msg"
    SUPPORT_WAIT = "support_wait"
    
    # Админ
    ADMIN_BROADCAST = "admin_broadcast"
    ADMIN_USER_SEARCH = "admin_user_search"
    ADMIN_SIGNAL = "admin_signal"
    
    # Рефералы
    REF_WITHDRAW = "ref_withdraw"
    REF_AMOUNT = "ref_amount"
    REF_METHOD = "ref_method"

# Функции для работы с состояниями
def get_state_name(state) -> str:
    """Получить название состояния"""
    if isinstance(state, Enum):
        return state.name
    return str(state)

def is_admin_state(state) -> bool:
    """Проверить, является ли состояние административным"""
    if isinstance(state, AdminStates):
        return True
    if isinstance(state, str):
        return state.startswith('admin_') or state.startswith('ADMIN_')
    return False

def get_next_state(current_state, action: str):
    """Получить следующее состояние на основе текущего и действия"""
    state_transitions = {
        UserStates.MAIN_MENU: {
            'settings': UserStates.SETTINGS_MENU,
            'support': UserStates.SUPPORT_MENU,
            'referrals': UserStates.REFERRAL_MENU,
            'signals': UserStates.SIGNALS_MENU,
            'partners': UserStates.PARTNERS_MENU,
        },
        UserStates.SETTINGS_MENU: {
            'notifications': UserStates.SETTINGS_NOTIFICATIONS,
            'language': UserStates.SETTINGS_LANGUAGE,
            'back': UserStates.MAIN_MENU,
        },
        UserStates.SUPPORT_MENU: {
            'message': UserStates.SUPPORT_MESSAGE,
            'back': UserStates.MAIN_MENU,
        },
        # Добавить другие переходы по мере необходимости
    }
    
    if current_state in state_transitions:
        return state_transitions[current_state].get(action, current_state)
    
    return current_state

