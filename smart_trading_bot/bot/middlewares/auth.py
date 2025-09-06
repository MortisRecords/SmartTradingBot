"""
Middleware для аутентификации и авторизации
"""
from telegram import Update
from telegram.ext import ContextTypes, BaseHandler
from database.manager import DatabaseManager
from config import config
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AuthMiddleware:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def check_user_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Проверка регистрации пользователя"""
        if not update.effective_user:
            return False
        
        user_id = update.effective_user.id
        user = await self.db.get_user(user_id)
        
        if not user:
            # Регистрируем нового пользователя
            await self.db.create_user(
                user_id=user_id,
                username=update.effective_user.username,
                first_name=update.effective_user.first_name,
                last_name=update.effective_user.last_name
            )
            logger.info(f"Зарегистрирован новый пользователь: {user_id}")
        
        return True

    async def check_user_banned(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Проверка блокировки пользователя"""
        if not update.effective_user:
            return True
        
        user_id = update.effective_user.id
        user = await self.db.get_user(user_id)
        
        if user and user.get('is_banned', False):
            await update.message.reply_text("❌ Вы заблокированы в боте")
            return True
        
        return False

    async def check_admin_rights(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Проверка прав администратора"""
        if not update.effective_user:
            return False
        
        user_id = update.effective_user.id
        return user_id in config.ADMIN_IDS or user_id == config.SUPER_ADMIN_ID

    async def update_user_activity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обновление активности пользователя"""
        if not update.effective_user:
            return
        
        user_id = update.effective_user.id
        await self.db.update_user_last_activity(user_id)

    async def process_referral(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка реферальной ссылки"""
        if not update.message or not update.message.text:
            return
        
        if update.message.text.startswith('/start ref_'):
            referrer_id = update.message.text.split('ref_')[1]
            user_id = update.effective_user.id
            
            if referrer_id.isdigit() and int(referrer_id) != user_id:
                await self.db.set_user_referrer(user_id, int(referrer_id))
                logger.info(f"Пользователь {user_id} привлечен по реферальной ссылке {referrer_id}")

class AuthHandler(BaseHandler):
    """Обработчик аутентификации"""
    
    def __init__(self, auth_middleware: AuthMiddleware):
        super().__init__(self.callback)
        self.auth = auth_middleware

    async def callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Основной callback для проверки аутентификации"""
        # Проверяем регистрацию
        if not await self.auth.check_user_registration(update, context):
            return
        
        # Проверяем блокировку
        if await self.auth.check_user_banned(update, context):
            return
        
        # Обновляем активность
        await self.auth.update_user_activity(update, context)
        
        # Обрабатываем реферальную ссылку
        await self.auth.process_referral(update, context)

    def check_update(self, update: object) -> Optional[bool]:
        """Проверка типа обновления"""
        return isinstance(update, Update) and (update.message or update.callback_query)

