"""
Обработчики команд и сообщений Telegram бота
"""

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from .start import StartHandler
from .signals import SignalHandler
from .referrals import ReferralHandler
from .admin import AdminHandler
from .callbacks import CallbackHandler

def register_all_handlers(application: Application, db_manager):
    """Регистрация всех обработчиков"""
    
    # Инициализация обработчиков
    start_handler = StartHandler(db_manager)
    signal_handler = SignalHandler(db_manager)
    referral_handler = ReferralHandler(db_manager)
    admin_handler = AdminHandler(db_manager)
    callback_handler = CallbackHandler(db_manager)
    
    # Команды
    application.add_handler(CommandHandler("start", start_handler.start_command))
    application.add_handler(CommandHandler("help", start_handler.help_command))
    application.add_handler(CommandHandler("signal", signal_handler.get_signal_command))
    application.add_handler(CommandHandler("stats", signal_handler.user_stats_command))
    application.add_handler(CommandHandler("referral", referral_handler.referral_info_command))
    application.add_handler(CommandHandler("admin", admin_handler.admin_panel_command))
    
    # Callback queries
    application.add_handler(CallbackQueryHandler(callback_handler.handle_callback))
    
    # Неизвестные команды
    application.add_handler(MessageHandler(filters.COMMAND, start_handler.unknown_command))
    
    # Текстовые сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, callback_handler.handle_text_message))

