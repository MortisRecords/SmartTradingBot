"""
Обработчики команды /start и базовые команды
"""

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.keyboards.inline import get_main_menu_keyboard
from bot.utils.texts import WELCOME_TEXT, HELP_TEXT
from database.models import User
import logging

logger = logging.getLogger(__name__)

class StartHandler:
    """Обработчик команды /start"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        try:
            user_id = update.effective_user.id
            username = update.effective_user.username
            first_name = update.effective_user.first_name or ""
            
            # Проверка реферальной ссылки
            referrer_id = None
            if context.args and context.args[0].startswith('ref_'):
                try:
                    referrer_id = int(context.args[0].replace('ref_', ''))
                    logger.info(f"Новый пользователь {user_id} по реферальной ссылке от {referrer_id}")
                except ValueError:
                    logger.warning(f"Некорректная реферальная ссылка: {context.args[0]}")
            
            # Регистрация или обновление пользователя
            user = await self.db.get_or_create_user(
                user_id=user_id,
                username=username,
                first_name=first_name,
                referrer_id=referrer_id
            )
            
            # Уведомление реферера о новом пользователе
            if referrer_id and user.is_new:
                try:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 По вашей ссылке зарегистрировался новый пользователь: {first_name or username or 'Анонимный'}"
                    )
                except Exception as e:
                    logger.warning(f"Не удалось уведомить реферера {referrer_id}: {e}")
            
            # Отправка приветственного сообщения
            keyboard = get_main_menu_keyboard()
            welcome_message = WELCOME_TEXT.format(
                first_name=first_name or username or "Трейдер",
                user_id=user_id
            )
            
            await update.message.reply_text(
                text=welcome_message,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
            logger.info(f"Пользователь {user_id} успешно {'зарегистрирован' if user.is_new else 'авторизован'}")
            
        except Exception as e:
            logger.error(f"Ошибка в start_command: {e}")
            await update.message.reply_text("❌ Произошла ошибка при запуске бота. Попробуйте позже.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help"""
        try:
            keyboard = get_main_menu_keyboard()
            await update.message.reply_text(
                text=HELP_TEXT,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Ошибка в help_command: {e}")
            await update.message.reply_text("❌ Ошибка загрузки справки")
    
    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка неизвестных команд"""
        await update.message.reply_text(
            "❓ Неизвестная команда. Используйте /help для просмотра доступных команд.",
            reply_markup=get_main_menu_keyboard()
        )
    