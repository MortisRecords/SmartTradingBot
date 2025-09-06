"""
Генератор торговых сигналов
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

from .indicators import SignalAnalyzer, IndicatorResult
from .market_data import MarketDataProvider
from .smart_money import SmartMoneyAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    """Торговый сигнал"""
    symbol: str
    direction: str  # 'CALL', 'PUT', 'BUY', 'SELL'
    entry_price: float
    target_price: Optional[float]
    stop_loss: Optional[float]
    expiry_time: datetime
    confidence: float
    reasoning: str
    created_at: datetime
    signal_type: str  # 'TECHNICAL', 'SMART_MONEY', 'COMBINED'

class SignalGenerator:
    """Генератор торговых сигналов"""
    
    def __init__(self, market_data_provider: MarketDataProvider):
        self.market_data = market_data_provider
        self.signal_analyzer = SignalAnalyzer()
        self.smart_money_analyzer = SmartMoneyAnalyzer()
        self.min_confidence = 70.0
        self.active_symbols = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD',
            'BTCUSD', 'ETHUSD', 'XAUUSD', 'CRUDE_OIL', 'SPX500'
        ]
    
    async def generate_signals(self, symbols: Optional[List[str]] = None) -> List[TradingSignal]:
        """Генерация торговых сигналов для указанных символов"""
        if symbols is None:
            symbols = self.active_symbols
        
        signals = []
        
        for symbol in symbols:
            try:
                # Получаем рыночные данные
                market_data = await self.market_data.get_ohlcv_data(symbol, '1h', 100)
                
                if not market_data or len(market_data) < 50:
                    logger.warning(f"Недостаточно данных для {symbol}")
                    continue
                
                # Извлекаем данные
                high_prices = [candle['high'] for candle in market_data]
                low_prices = [candle['low'] for candle in market_data]
                close_prices = [candle['close'] for candle in market_data]
                volumes = [candle['volume'] for candle in market_data]
                
                # Технический анализ
                technical_signal = self.signal_analyzer.get_combined_signal(
                    high_prices, low_prices, close_prices
                )
                
                # Анализ умных денег
                smart_money_signal = await self.smart_money_analyzer.analyze_smart_money_flow(
                    symbol, close_prices, volumes
                )
                
                # Комбинируем сигналы
                combined_signal = self._combine_signals(technical_signal, smart_money_signal)
                
                if combined_signal.confidence >= self.min_confidence:
                    trading_signal = self._create_trading_signal(
                        symbol, combined_signal, close_prices[-1]
                    )
                    signals.append(trading_signal)
                    
            except Exception as e:
                logger.error(f"Ошибка генерации сигнала для {symbol}: {e}")
                continue
        
        return signals
    
    def _combine_signals(self, technical: IndicatorResult, smart_money: IndicatorResult) -> IndicatorResult:
        """Комбинирование технического анализа и анализа умных денег"""
        # Веса для разных типов сигналов
        technical_weight = 0.6
        smart_money_weight = 0.4
        
        # Если сигналы совпадают, увеличиваем уверенность
        if technical.signal == smart_money.signal:
            combined_confidence = (
                technical.confidence * technical_weight + 
                smart_money.confidence * smart_money_weight
            ) * 1.2  # Бонус за совпадение
            combined_signal = technical.signal
        else:
            # Если сигналы противоречат, берем более сильный
            if technical.confidence > smart_money.confidence:
                combined_confidence = technical.confidence * 0.8
                combined_signal = technical.signal
            else:
                combined_confidence = smart_money.confidence * 0.8
                combined_signal = smart_money.signal
        
        # Ограничиваем уверенность
        combined_confidence = min(100, combined_confidence)
        
        reasoning = f"Технический: {technical.description}. Умные деньги: {smart_money.description}"
        
        return IndicatorResult(
            value=(technical.value + smart_money.value) / 2,
            signal=combined_signal,
            confidence=combined_confidence,
            description=reasoning
        )
    
    def _create_trading_signal(self, symbol: str, signal: IndicatorResult, current_price: float) -> TradingSignal:
        """Создание торгового сигнала"""
        # Определяем направление для бинарных опционов
        if signal.signal == 'BUY':
            direction = 'CALL'
        elif signal.signal == 'SELL':
            direction = 'PUT'
        else:
            direction = 'HOLD'
        
        # Рассчитываем время экспирации (обычно 1-5 минут для бинарных опционов)
        expiry_minutes = self._calculate_expiry_time(signal.confidence)
        expiry_time = datetime.now() + timedelta(minutes=expiry_minutes)
        
        # Рассчитываем цели и стоп-лоссы для форекс
        target_price, stop_loss = self._calculate_targets(current_price, direction, symbol)
        
        return TradingSignal(
            symbol=symbol,
            direction=direction,
            entry_price=current_price,
            target_price=target_price,
            stop_loss=stop_loss,
            expiry_time=expiry_time,
            confidence=signal.confidence,
            reasoning=signal.description,
            created_at=datetime.now(),
            signal_type='COMBINED'
        )
    
    def _calculate_expiry_time(self, confidence: float) -> int:
        """Расчет времени экспирации на основе уверенности"""
        if confidence >= 90:
            return 1  # 1 минута для очень сильных сигналов
        elif confidence >= 80:
            return 3  # 3 минуты для сильных сигналов
        else:
            return 5  # 5 минут для умеренных сигналов
    
    def _calculate_targets(self, price: float, direction: str, symbol: str) -> tuple:
        """Расчет целей и стоп-лоссов"""
        # Базовые проценты для разных типов активов
        if 'USD' in symbol or 'EUR' in symbol or 'GBP' in symbol:
            # Форекс - меньшие движения
            target_pct = 0.002  # 0.2%
            stop_pct = 0.001    # 0.1%
        elif 'BTC' in symbol or 'ETH' in symbol:
            # Криптовалюты - большие движения
            target_pct = 0.02   # 2%
            stop_pct = 0.01     # 1%
        elif 'XAU' in symbol:
            # Золото
            target_pct = 0.005  # 0.5%
            stop_pct = 0.0025   # 0.25%
        else:
            # Индексы и сырье
            target_pct = 0.01   # 1%
            stop_pct = 0.005    # 0.5%
        
        if direction == 'CALL' or direction == 'BUY':
            target_price = price * (1 + target_pct)
            stop_loss = price * (1 - stop_pct)
        elif direction == 'PUT' or direction == 'SELL':
            target_price = price * (1 - target_pct)
            stop_loss = price * (1 + stop_pct)
        else:
            target_price = None
            stop_loss = None
        
        return target_price, stop_loss
    
    async def monitor_signals(self, signals: List[TradingSignal]) -> Dict[str, str]:
        """Мониторинг результатов сигналов"""
        results = {}
        
        for signal in signals:
            try:
                # Получаем текущую цену
                current_data = await self.market_data.get_current_price(signal.symbol)
                current_price = current_data.get('price', 0)
                
                # Проверяем результат для бинарных опционов
                if signal.direction in ['CALL', 'PUT']:
                    if datetime.now() >= signal.expiry_time:
                        if signal.direction == 'CALL':
                            result = 'WIN' if current_price > signal.entry_price else 'LOSS'
                        else:  # PUT
                            result = 'WIN' if current_price < signal.entry_price else 'LOSS'
                        results[signal.symbol] = result
                
                # Проверяем результат для форекс
                elif signal.direction in ['BUY', 'SELL']:
                    if signal.target_price and signal.stop_loss:
                        if signal.direction == 'BUY':
                            if current_price >= signal.target_price:
                                results[signal.symbol] = 'WIN'
                            elif current_price <= signal.stop_loss:
                                results[signal.symbol] = 'LOSS'
                        else:  # SELL
                            if current_price <= signal.target_price:
                                results[signal.symbol] = 'WIN'
                            elif current_price >= signal.stop_loss:
                                results[signal.symbol] = 'LOSS'
                
            except Exception as e:
                logger.error(f"Ошибка мониторинга сигнала {signal.symbol}: {e}")
        
        return results
    
    def filter_signals_by_time(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """Фильтрация сигналов по времени (избегаем новости и низкую ликвидность)"""
        filtered_signals = []
        current_time = datetime.now()
        
        for signal in signals:
            # Избегаем торговли в выходные (для форекс)
            if current_time.weekday() >= 5:  # Суббота и воскресенье
                continue
            
            # Избегаем торговли поздно вечером и рано утром (низкая ликвидность)
            hour = current_time.hour
            if hour < 8 or hour > 22:
                continue
            
            # Избегаем торговли во время важных новостей (можно расширить)
            if self._is_news_time(current_time):
                continue
            
            filtered_signals.append(signal)
        
        return filtered_signals
    
    def _is_news_time(self, time: datetime) -> bool:
        """Проверка времени важных новостей"""
        # Простая проверка - можно расширить интеграцией с календарем новостей
        hour = time.hour
        minute = time.minute
        
        # Время выхода NFP (первая пятница месяца в 15:30 МСК)
        if time.weekday() == 4 and hour == 15 and 25 <= minute <= 35:
            return True
        
        # Время выхода решений ФРС (обычно в 21:00 МСК)
        if hour == 21 and 0 <= minute <= 30:
            return True
        
        return False

