"""
Обработчики сигналов
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from analytics.signal_generator import SignalGenerator
from bot.keyboards.inline import get_signal_keyboard, get_platforms_keyboard
from bot.utils.texts import format_signal_message, NO_SIGNALS_TEXT
from database.models import Signal
from config import config
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SignalHandler:
    """Обработчик торговых сигналов"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.signal_generator = SignalGenerator()
    
    async def get_signal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда получения сигнала"""
        try:
            user_id = update.effective_user.id
            
            # Проверка лимитов для бесплатных пользователей
            user = await self.db.get_user(user_id)
            if not user:
                await update.message.reply_text("❌ Пользователь не найден. Используйте /start")
                return
            
            # Проверка дневного лимита для бесплатных пользователей
            if not user.is_premium:
                daily_signals = await self.db.get_user_daily_signals_count(user_id)
                if daily_signals >= config.FREE_SIGNALS_PER_DAY:
                    keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton("💎 Получить Premium", callback_data="upgrade_premium")
                    ]])
                    await update.message.reply_text(
                        "📊 Вы исчерпали дневной лимит бесплатных сигналов.\n"
                        "💎 Оформите Premium для неограниченных сигналов!",
                        reply_markup=keyboard
                    )
                    return
            
            # Генерация сигнала
            await self._send_signal(update, context, user_id)
            
        except Exception as e:
            logger.error(f"Ошибка в get_signal_command: {e}")
            await update.message.reply_text("❌ Ошибка генерации сигнала")
    
    async def _send_signal(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Отправка сигнала пользователю"""
        try:
            # Получение рыночных данных и генерация сигнала
            signal_data = await self.signal_generator.generate_signal()
            
            if not signal_data:
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Попробовать снова", callback_data="get_signal")
                ]])
                await update.message.reply_text(
                    NO_SIGNALS_TEXT,
                    reply_markup=keyboard
                )
                return
            
            # Сохранение сигнала в БД
            signal = Signal(
                user_id=user_id,
                symbol=signal_data['symbol'],
                signal_type=signal_data['signal_type'],
                entry_price=signal_data['entry_price'],
                take_profit=signal_data.get('take_profit'),
                stop_loss=signal_data.get('stop_loss'),
                confidence=signal_data['confidence'],
                timeframe=signal_data['timeframe'],
                analysis=signal_data.get('analysis', {}),
                expires_at=signal_data.get('expires_at')
            )
            
            signal_id = await self.db.save_signal(signal)
            signal_data['signal_id'] = signal_id
            
            # Форматирование сообщения
            message_text = format_signal_message(signal_data)
            keyboard = get_signal_keyboard(signal_id)
            
            # Отправка сообщения
            await update.message.reply_text(
                text=message_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
            # Обновление статистики пользователя
            await self.db.increment_user_signals_count(user_id)
            
            logger.info(f"Сигнал {signal_id} отправлен пользователю {user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки сигнала: {e}")
            await update.message.reply_text("❌ Ошибка при генерации сигнала")
    
    async def get_detailed_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE, signal_id: int):
        """Получение детального анализа сигнала"""
        try:
            signal = await self.db.get_signal(signal_id)
            if not signal:
                await update.callback_query.answer("Сигнал не найден", show_alert=True)
                return
            
            user = await self.db.get_user(update.effective_user.id)
            if not user or not user.is_premium:
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("💎 Получить Premium", callback_data="upgrade_premium")
                ]])
                await update.callback_query.edit_message_text(
                    "🔐 Детальный анализ доступен только Premium пользователям",
                    reply_markup=keyboard
                )
                return
            
            # Получение детального анализа
            analysis = await self.signal_generator.get_detailed_analysis(signal.symbol)
            
            analysis_text = f"""
🔍 <b>ДЕТАЛЬНЫЙ АНАЛИЗ</b>

📊 <b>Символ:</b> {signal.symbol}
🎯 <b>Сигнал:</b> {signal.signal_type}
💰 <b>Цена входа:</b> ${signal.entry_price:.4f}

<b>📈 Технические индикаторы:</b>
• RSI: {analysis.get('rsi', 'N/A'):.2f}
• MACD: {analysis.get('macd_signal', 'Нейтрально')}
• Moving Average: {analysis.get('ma_signal', 'Нейтрально')}
• Volume: {analysis.get('volume_analysis', 'Средний')}
• Smart Money: {analysis.get('smart_money_flow', 'Нейтральный')}

<b>🎯 Уровни поддержки/сопротивления:</b>
• Поддержка: ${analysis.get('support_level', 0):.4f}
• Сопротивление: ${analysis.get('resistance_level', 0):.4f}

<b>📊 Рыночные условия:</b>
• Тренд: {analysis.get('trend', 'Неопределен')}
• Волатильность: {analysis.get('volatility', 'Средняя')}
• Объем: {analysis.get('volume_condition', 'Нормальный')}

⚠️ <i>Данный анализ носит информационный характер</i>
            """
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Торговые платформы", callback_data="show_platforms")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_signal")]
            ])
            
            await update.callback_query.edit_message_text(
                text=analysis_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения анализа: {e}")
            await update.callback_query.answer("❌ Ошибка получения анализа", show_alert=True)
    
    async def show_platforms(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать торговые платформы"""
        try:
            user_id = update.effective_user.id
            keyboard = get_platforms_keyboard(user_id)
            
            platforms_text = """
🏢 <b>ТОРГОВЫЕ ПЛАТФОРМЫ</b>

Выберите платформу для торговли:

🔸 <b>Binarium</b>
• Бинарные опционы
• Бонус до 100% на депозит  
• Выплаты до 90%
• Минимальный депозит: $10

🔸 <b>PocketOption</b>
• CFD и опционы
• Демо-счет $10,000
• Турниры с призами
• Минимальный депозит: $5

⚠️ <b>Важно:</b> Торговля сопряжена с рисками. 
Используйте только те средства, потерю которых можете себе позволить.

💰 <b>При регистрации по нашим ссылкам вы поддерживаете проект!</b>
            """
            
            await update.callback_query.edit_message_text(
                text=platforms_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Ошибка показа платформ: {e}")
            await update.callback_query.answer("❌ Ошибка", show_alert=True)
    
    async def track_signal_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                signal_id: int, result: str):
        """Отслеживание результата сигнала"""
        try:
            await self.db.update_signal_result(signal_id, result)
            
            result_emoji = "✅" if result == "win" else "❌" if result == "loss" else "⚪️"
            result_text = "Прибыль" if result == "win" else "Убыток" if result == "loss" else "Безубыток"
            
            await update.callback_query.answer(
                f"{result_emoji} Результат записан: {result_text}",
                show_alert=True
            )
            
            # Обновление статистики точности
            await self.db.update_signal_accuracy_stats()
            
        except Exception as e:
            logger.error(f"Ошибка записи результата сигнала: {e}")
            await update.callback_query.answer("❌ Ошибка записи результата", show_alert=True)