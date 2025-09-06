"""
Middleware для ограничения частоты запросов (throttling)
"""
from telegram import Update
from telegram.ext import ContextTypes
import time
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class ThrottlingMiddleware:
    def __init__(self, rate_limit: int = 30, time_window: int = 60):
        """
        Инициализация middleware для ограничения запросов
        
        Args:
            rate_limit: Максимальное количество запросов
            time_window: Временное окно в секундах
        """
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.user_requests = defaultdict(list)

    async def check_rate_limit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Проверка ограничения частоты запросов
        
        Returns:
            True если запрос разрешен, False если превышен лимит
        """
        if not update.effective_user:
            return True
        
        user_id = update.effective_user.id
        current_time = time.time()
        
        # Очищаем старые запросы
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if current_time - req_time < self.time_window
        ]
        
        # Проверяем лимит
        if len(self.user_requests[user_id]) >= self.rate_limit:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            
            # Отправляем предупреждение
            if update.message:
                await update.message.reply_text(
                    "⚠️ Слишком много запросов. Пожалуйста, подождите немного."
                )
            elif update.callback_query:
                await update.callback_query.answer(
                    "⚠️ Слишком много запросов. Подождите немного.",
                    show_alert=True
                )
            
            return False
        
        # Добавляем текущий запрос
        self.user_requests[user_id].append(current_time)
        return True

    async def check_spam(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Проверка на спам (быстрые повторяющиеся сообщения)
        
        Returns:
            True если сообщение не является спамом, False если спам
        """
        if not update.effective_user or not update.message:
            return True
        
        user_id = update.effective_user.id
        current_time = time.time()
        
        # Проверяем последние сообщения пользователя
        user_messages = context.user_data.get('recent_messages', [])
        
        # Очищаем старые сообщения (старше 10 секунд)
        user_messages = [
            (msg_time, msg_text) for msg_time, msg_text in user_messages
            if current_time - msg_time < 10
        ]
        
        # Добавляем текущее сообщение
        message_text = update.message.text or ""
        user_messages.append((current_time, message_text))
        
        # Сохраняем обновленный список
        context.user_data['recent_messages'] = user_messages
        
        # Проверяем на спам
        if len(user_messages) >= 5:  # 5 сообщений за 10 секунд
            # Проверяем, одинаковые ли сообщения
            recent_texts = [msg_text for _, msg_text in user_messages[-5:]]
            if len(set(recent_texts)) <= 2:  # Максимум 2 уникальных сообщения
                logger.warning(f"Spam detected from user {user_id}")
                await update.message.reply_text(
                    "🚫 Обнаружен спам. Пожалуйста, не отправляйте одинаковые сообщения."
                )
                return False
        
        return True

    async def check_flood(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Проверка на флуд (слишком много сообщений подряд)
        
        Returns:
            True если флуда нет, False если обнаружен флуд
        """
        if not update.effective_user:
            return True
        
        user_id = update.effective_user.id
        current_time = time.time()
        
        # Получаем время последнего сообщения
        last_message_time = context.user_data.get('last_message_time', 0)
        
        # Если сообщения отправляются слишком быстро
        if current_time - last_message_time < 1:  # Меньше 1 секунды между сообщениями
            flood_count = context.user_data.get('flood_count', 0) + 1
            context.user_data['flood_count'] = flood_count
            
            if flood_count >= 5:  # 5 быстрых сообщений подряд
                logger.warning(f"Flood detected from user {user_id}")
                
                if update.message:
                    await update.message.reply_text(
                        "🌊 Обнаружен флуд. Пожалуйста, отправляйте сообщения медленнее."
                    )
                
                # Сбрасываем счетчик
                context.user_data['flood_count'] = 0
                return False
        else:
            # Сбрасываем счетчик если сообщения отправляются нормально
            context.user_data['flood_count'] = 0
        
        # Обновляем время последнего сообщения
        context.user_data['last_message_time'] = current_time
        return True

    async def process_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Основная функция обработки обновления
        
        Returns:
            True если обновление можно обрабатывать, False если нужно заблокировать
        """
        # Проверяем все ограничения
        if not await self.check_rate_limit(update, context):
            return False
        
        if not await self.check_spam(update, context):
            return False
        
        if not await self.check_flood(update, context):
            return False
        
        return True

