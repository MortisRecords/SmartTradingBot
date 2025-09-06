"""
Reply клавиатуры для бота
"""
from telegram import ReplyKeyboardMarkup, KeyboardButton

class ReplyKeyboards:
    @staticmethod
    def main_menu():
        """Главное меню"""
        keyboard = [
            [KeyboardButton("📊 Сигналы"), KeyboardButton("💰 Партнеры")],
            [KeyboardButton("👥 Рефералы"), KeyboardButton("⚙️ Настройки")],
            [KeyboardButton("📞 Поддержка"), KeyboardButton("ℹ️ О боте")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    @staticmethod
    def admin_menu():
        """Меню администратора"""
        keyboard = [
            [KeyboardButton("📊 Статистика"), KeyboardButton("👥 Пользователи")],
            [KeyboardButton("📡 Сигналы"), KeyboardButton("💰 Выплаты")],
            [KeyboardButton("📢 Рассылка"), KeyboardButton("⚙️ Настройки")],
            [KeyboardButton("🔙 Главное меню")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    @staticmethod
    def contact_request():
        """Запрос контакта"""
        keyboard = [
            [KeyboardButton("📱 Поделиться контактом", request_contact=True)],
            [KeyboardButton("❌ Отмена")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    @staticmethod
    def location_request():
        """Запрос геолокации"""
        keyboard = [
            [KeyboardButton("📍 Поделиться геолокацией", request_location=True)],
            [KeyboardButton("❌ Отмена")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    @staticmethod
    def yes_no():
        """Да/Нет"""
        keyboard = [
            [KeyboardButton("✅ Да"), KeyboardButton("❌ Нет")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    @staticmethod
    def cancel():
        """Отмена"""
        keyboard = [
            [KeyboardButton("❌ Отмена")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    @staticmethod
    def remove_keyboard():
        """Удаление клавиатуры"""
        from telegram import ReplyKeyboardRemove
        return ReplyKeyboardRemove()

