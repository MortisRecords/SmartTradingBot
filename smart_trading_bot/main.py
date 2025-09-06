#!/usr/bin/env python3
"""
Smart Trading Bot - Main Application
Telegram бот для торговых сигналов с партнерской программой
"""

import asyncio
import logging
from telegram.ext import Application
from bot.handlers import register_all_handlers
from bot.middlewares import setup_middlewares
from database.manager import DatabaseManager
from monitoring.signal_monitor import SignalMonitor
from config import Config

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SmartTradingBot:
    """Основной класс приложения"""
    
    def __init__(self):
        self.config = Config()
        self.db_manager = None
        self.application = None
        self.signal_monitor = None
    
    async def initialize(self):
        """Инициализация всех компонентов"""
        try:
            # Инициализация базы данных
            logger.info("Инициализация базы данных...")
            self.db_manager = DatabaseManager(self.config.DATABASE_URL)
            await self.db_manager.initialize()
            
            # Создание Telegram приложения
            logger.info("Создание Telegram приложения...")
            self.application = Application.builder().token(self.config.BOT_TOKEN).build()
            
            # Настройка middleware
            logger.info("Настройка middleware...")
            setup_middlewares(self.application)
            
            # Регистрация обработчиков
            logger.info("Регистрация обработчиков...")
            register_all_handlers(self.application, self.db_manager)
            
            # Инициализация мониторинга сигналов
            logger.info("Инициализация мониторинга сигналов...")
            self.signal_monitor = SignalMonitor(self.application, self.db_manager)
            
            logger.info("Инициализация завершена успешно!")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
            raise
    
    async def start(self):
        """Запуск бота"""
        try:
            await self.initialize()
            
            # Запуск мониторинга сигналов в фоне
            if self.config.ENABLE_SIGNAL_MONITORING:
                asyncio.create_task(self.signal_monitor.start())
                logger.info("Мониторинг сигналов запущен")
            
            # Запуск Telegram бота
            logger.info("🤖 Smart Trading Bot запускается...")
            logger.info(f"Bot username: @{(await self.application.bot.get_me()).username}")
            
            await self.application.run_polling(
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query', 'inline_query']
            )
            
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            raise
    
    async def stop(self):
        """Остановка бота"""
        logger.info("Остановка бота...")
        
        if self.signal_monitor:
            await self.signal_monitor.stop()
        
        if self.application:
            await self.application.stop()
        
        if self.db_manager:
            await self.db_manager.close()
        
        logger.info("Бот остановлен")

async def main():
    """Главная функция"""
    bot = SmartTradingBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    # Создание директорий если их нет
    import os
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('backups', exist_ok=True)
    
    # Запуск приложения
    asyncio.run(main())