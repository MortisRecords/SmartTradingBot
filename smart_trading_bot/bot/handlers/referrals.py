"""
Обработчик реферальной системы
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from database.manager import DatabaseManager
from bot.utils.texts import TEXTS
import logging

logger = logging.getLogger(__name__)

class ReferralHandler:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def referral_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Главное меню реферальной системы"""
        user_id = update.effective_user.id
        
        # Получаем статистику пользователя
        user_stats = await self.db.get_user_referral_stats(user_id)
        
        keyboard = [
            [InlineKeyboardButton("📊 Моя статистика", callback_data="ref_stats")],
            [InlineKeyboardButton("👥 Мои рефералы", callback_data="ref_list")],
            [InlineKeyboardButton("💰 Вывод средств", callback_data="ref_withdraw")],
            [InlineKeyboardButton("🔗 Получить ссылку", callback_data="ref_link")],
            [InlineKeyboardButton("◀️ Назад", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = TEXTS['referral_menu'].format(
            referrals_count=user_stats.get('referrals_count', 0),
            total_earned=user_stats.get('total_earned', 0),
            available_balance=user_stats.get('available_balance', 0)
        )
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)

    async def show_referral_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать детальную статистику"""
        user_id = update.effective_user.id
        stats = await self.db.get_detailed_referral_stats(user_id)
        
        text = TEXTS['referral_stats'].format(**stats)
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="referrals")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

    async def show_referral_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать список рефералов"""
        user_id = update.effective_user.id
        referrals = await self.db.get_user_referrals(user_id)
        
        if not referrals:
            text = TEXTS['no_referrals']
        else:
            text = TEXTS['referral_list_header']
            for ref in referrals[:10]:  # Показываем только первые 10
                text += f"\n👤 {ref['username']} - {ref['earned']}$"
            
            if len(referrals) > 10:
                text += f"\n\n... и еще {len(referrals) - 10} рефералов"
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="referrals")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

    async def show_referral_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать реферальную ссылку"""
        user_id = update.effective_user.id
        bot_username = context.bot.username
        
        referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
        
        text = TEXTS['referral_link'].format(link=referral_link)
        
        keyboard = [
            [InlineKeyboardButton("📋 Копировать", url=referral_link)],
            [InlineKeyboardButton("◀️ Назад", callback_data="referrals")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

    async def withdraw_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Меню вывода средств"""
        user_id = update.effective_user.id
        balance = await self.db.get_user_balance(user_id)
        
        if balance < 50:  # Минимальная сумма для вывода
            text = TEXTS['withdraw_min_amount'].format(balance=balance, min_amount=50)
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="referrals")]]
        else:
            text = TEXTS['withdraw_menu'].format(balance=balance)
            keyboard = [
                [InlineKeyboardButton("💳 Банковская карта", callback_data="withdraw_card")],
                [InlineKeyboardButton("🪙 Криптовалюта", callback_data="withdraw_crypto")],
                [InlineKeyboardButton("◀️ Назад", callback_data="referrals")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

    def get_handlers(self):
        """Возвращает список обработчиков"""
        return [
            CommandHandler("referrals", self.referral_menu),
            CallbackQueryHandler(self.referral_menu, pattern="^referrals$"),
            CallbackQueryHandler(self.show_referral_stats, pattern="^ref_stats$"),
            CallbackQueryHandler(self.show_referral_list, pattern="^ref_list$"),
            CallbackQueryHandler(self.show_referral_link, pattern="^ref_link$"),
            CallbackQueryHandler(self.withdraw_menu, pattern="^ref_withdraw$"),
        ]

