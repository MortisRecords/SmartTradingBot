"""
Обработчик административных функций
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from database.manager import DatabaseManager
from bot.utils.texts import TEXTS
from config import config
import logging

logger = logging.getLogger(__name__)

class AdminHandler:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def is_admin(self, user_id: int) -> bool:
        """Проверка прав администратора"""
        return user_id in config.ADMIN_IDS or user_id == config.SUPER_ADMIN_ID

    async def admin_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Главное меню администратора"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return

        keyboard = [
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
            [InlineKeyboardButton("📡 Сигналы", callback_data="admin_signals")],
            [InlineKeyboardButton("💰 Выплаты", callback_data="admin_payouts")],
            [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = TEXTS['admin_menu']
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)

    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статистику бота"""
        stats = await self.db.get_bot_statistics()
        
        text = TEXTS['admin_stats'].format(
            total_users=stats.get('total_users', 0),
            active_users=stats.get('active_users', 0),
            total_signals=stats.get('total_signals', 0),
            successful_signals=stats.get('successful_signals', 0),
            total_commissions=stats.get('total_commissions', 0),
            pending_payouts=stats.get('pending_payouts', 0)
        )
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

    async def manage_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Управление пользователями"""
        users = await self.db.get_recent_users(limit=10)
        
        text = TEXTS['admin_users_header']
        for user in users:
            status = "🟢" if user['is_active'] else "🔴"
            text += f"\n{status} {user['username']} (ID: {user['user_id']})"
        
        keyboard = [
            [InlineKeyboardButton("🔍 Поиск пользователя", callback_data="admin_search_user")],
            [InlineKeyboardButton("📊 Топ рефералов", callback_data="admin_top_referrers")],
            [InlineKeyboardButton("◀️ Назад", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

    async def manage_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Управление сигналами"""
        signals = await self.db.get_recent_signals(limit=5)
        
        text = TEXTS['admin_signals_header']
        for signal in signals:
            status_emoji = "✅" if signal['result'] == 'win' else "❌" if signal['result'] == 'loss' else "⏳"
            text += f"\n{status_emoji} {signal['symbol']} {signal['direction']} - {signal['created_at']}"
        
        keyboard = [
            [InlineKeyboardButton("📡 Отправить сигнал", callback_data="admin_send_signal")],
            [InlineKeyboardButton("📈 Статистика сигналов", callback_data="admin_signal_stats")],
            [InlineKeyboardButton("◀️ Назад", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

    async def broadcast_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Меню рассылки"""
        text = TEXTS['admin_broadcast_menu']
        
        keyboard = [
            [InlineKeyboardButton("📢 Всем пользователям", callback_data="broadcast_all")],
            [InlineKeyboardButton("🎯 Активным пользователям", callback_data="broadcast_active")],
            [InlineKeyboardButton("💎 Premium пользователям", callback_data="broadcast_premium")],
            [InlineKeyboardButton("◀️ Назад", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

    async def start_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать рассылку"""
        broadcast_type = update.callback_query.data.split('_')[1]
        context.user_data['broadcast_type'] = broadcast_type
        
        await update.callback_query.edit_message_text(
            "📝 Отправьте сообщение для рассылки:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Отмена", callback_data="admin_menu")
            ]])
        )

    async def process_broadcast_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка сообщения для рассылки"""
        if 'broadcast_type' not in context.user_data:
            return
        
        broadcast_type = context.user_data['broadcast_type']
        message_text = update.message.text
        
        # Получаем список пользователей для рассылки
        if broadcast_type == 'all':
            users = await self.db.get_all_users()
        elif broadcast_type == 'active':
            users = await self.db.get_active_users()
        elif broadcast_type == 'premium':
            users = await self.db.get_premium_users()
        
        # Отправляем рассылку
        sent_count = 0
        for user in users:
            try:
                await context.bot.send_message(user['user_id'], message_text)
                sent_count += 1
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения пользователю {user['user_id']}: {e}")
        
        await update.message.reply_text(
            f"✅ Рассылка завершена!\nОтправлено: {sent_count} из {len(users)} сообщений"
        )
        
        del context.user_data['broadcast_type']

    def get_handlers(self):
        """Возвращает список обработчиков"""
        return [
            CommandHandler("admin", self.admin_menu),
            CallbackQueryHandler(self.admin_menu, pattern="^admin_menu$"),
            CallbackQueryHandler(self.show_stats, pattern="^admin_stats$"),
            CallbackQueryHandler(self.manage_users, pattern="^admin_users$"),
            CallbackQueryHandler(self.manage_signals, pattern="^admin_signals$"),
            CallbackQueryHandler(self.broadcast_menu, pattern="^admin_broadcast$"),
            CallbackQueryHandler(self.start_broadcast, pattern="^broadcast_"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_broadcast_message),
        ]

