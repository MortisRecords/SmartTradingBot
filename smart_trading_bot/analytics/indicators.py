"""
Модуль технических индикаторов для анализа рынка
"""
import numpy as np
import pandas as pd
from typing import Tuple, List, Optional
import talib
from dataclasses import dataclass

@dataclass
class IndicatorResult:
    """Результат расчета индикатора"""
    value: float
    signal: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0-100
    description: str

class TechnicalIndicators:
    """Класс для расчета технических индикаторов"""
    
    @staticmethod
    def sma(prices: List[float], period: int = 20) -> List[float]:
        """Простая скользящая средняя"""
        return talib.SMA(np.array(prices), timeperiod=period).tolist()
    
    @staticmethod
    def ema(prices: List[float], period: int = 20) -> List[float]:
        """Экспоненциальная скользящая средняя"""
        return talib.EMA(np.array(prices), timeperiod=period).tolist()
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> List[float]:
        """Индекс относительной силы"""
        return talib.RSI(np.array(prices), timeperiod=period).tolist()
    
    @staticmethod
    def macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[List[float], List[float], List[float]]:
        """MACD индикатор"""
        macd_line, macd_signal, macd_hist = talib.MACD(
            np.array(prices), 
            fastperiod=fast, 
            slowperiod=slow, 
            signalperiod=signal
        )
        return macd_line.tolist(), macd_signal.tolist(), macd_hist.tolist()
    
    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, std_dev: int = 2) -> Tuple[List[float], List[float], List[float]]:
        """Полосы Боллинджера"""
        upper, middle, lower = talib.BBANDS(
            np.array(prices), 
            timeperiod=period, 
            nbdevup=std_dev, 
            nbdevdn=std_dev
        )
        return upper.tolist(), middle.tolist(), lower.tolist()
    
    @staticmethod
    def stochastic(high: List[float], low: List[float], close: List[float], 
                   k_period: int = 14, d_period: int = 3) -> Tuple[List[float], List[float]]:
        """Стохастический осциллятор"""
        k_percent, d_percent = talib.STOCH(
            np.array(high), 
            np.array(low), 
            np.array(close),
            fastk_period=k_period,
            slowk_period=d_period,
            slowd_period=d_period
        )
        return k_percent.tolist(), d_percent.tolist()
    
    @staticmethod
    def atr(high: List[float], low: List[float], close: List[float], period: int = 14) -> List[float]:
        """Average True Range - средний истинный диапазон"""
        return talib.ATR(np.array(high), np.array(low), np.array(close), timeperiod=period).tolist()
    
    @staticmethod
    def adx(high: List[float], low: List[float], close: List[float], period: int = 14) -> List[float]:
        """Average Directional Index - индекс направленного движения"""
        return talib.ADX(np.array(high), np.array(low), np.array(close), timeperiod=period).tolist()

class SignalAnalyzer:
    """Анализатор торговых сигналов на основе индикаторов"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
    
    def analyze_rsi_signal(self, prices: List[float], period: int = 14) -> IndicatorResult:
        """Анализ сигнала RSI"""
        rsi_values = self.indicators.rsi(prices, period)
        current_rsi = rsi_values[-1] if rsi_values else 50
        
        if current_rsi > 70:
            return IndicatorResult(
                value=current_rsi,
                signal='SELL',
                confidence=min(100, (current_rsi - 70) * 3),
                description=f'RSI перекуплен: {current_rsi:.2f}'
            )
        elif current_rsi < 30:
            return IndicatorResult(
                value=current_rsi,
                signal='BUY',
                confidence=min(100, (30 - current_rsi) * 3),
                description=f'RSI перепродан: {current_rsi:.2f}'
            )
        else:
            return IndicatorResult(
                value=current_rsi,
                signal='HOLD',
                confidence=50,
                description=f'RSI нейтрален: {current_rsi:.2f}'
            )
    
    def analyze_macd_signal(self, prices: List[float]) -> IndicatorResult:
        """Анализ сигнала MACD"""
        macd_line, macd_signal, macd_hist = self.indicators.macd(prices)
        
        if len(macd_hist) < 2:
            return IndicatorResult(0, 'HOLD', 0, 'Недостаточно данных для MACD')
        
        current_hist = macd_hist[-1]
        prev_hist = macd_hist[-2]
        
        if current_hist > 0 and prev_hist <= 0:
            return IndicatorResult(
                value=current_hist,
                signal='BUY',
                confidence=75,
                description='MACD пересечение вверх'
            )
        elif current_hist < 0 and prev_hist >= 0:
            return IndicatorResult(
                value=current_hist,
                signal='SELL',
                confidence=75,
                description='MACD пересечение вниз'
            )
        else:
            return IndicatorResult(
                value=current_hist,
                signal='HOLD',
                confidence=50,
                description='MACD без сигнала'
            )
    
    def analyze_bollinger_signal(self, prices: List[float]) -> IndicatorResult:
        """Анализ сигнала полос Боллинджера"""
        upper, middle, lower = self.indicators.bollinger_bands(prices)
        
        if not prices or len(upper) == 0:
            return IndicatorResult(0, 'HOLD', 0, 'Недостаточно данных для Bollinger Bands')
        
        current_price = prices[-1]
        current_upper = upper[-1]
        current_lower = lower[-1]
        current_middle = middle[-1]
        
        if current_price >= current_upper:
            return IndicatorResult(
                value=current_price,
                signal='SELL',
                confidence=70,
                description='Цена у верхней полосы Боллинджера'
            )
        elif current_price <= current_lower:
            return IndicatorResult(
                value=current_price,
                signal='BUY',
                confidence=70,
                description='Цена у нижней полосы Боллинджера'
            )
        else:
            return IndicatorResult(
                value=current_price,
                signal='HOLD',
                confidence=50,
                description='Цена в пределах полос Боллинджера'
            )
    
    def analyze_stochastic_signal(self, high: List[float], low: List[float], close: List[float]) -> IndicatorResult:
        """Анализ сигнала стохастического осциллятора"""
        k_percent, d_percent = self.indicators.stochastic(high, low, close)
        
        if len(k_percent) == 0 or len(d_percent) == 0:
            return IndicatorResult(0, 'HOLD', 0, 'Недостаточно данных для Stochastic')
        
        current_k = k_percent[-1]
        current_d = d_percent[-1]
        
        if current_k > 80 and current_d > 80:
            return IndicatorResult(
                value=current_k,
                signal='SELL',
                confidence=65,
                description=f'Stochastic перекуплен: K={current_k:.2f}, D={current_d:.2f}'
            )
        elif current_k < 20 and current_d < 20:
            return IndicatorResult(
                value=current_k,
                signal='BUY',
                confidence=65,
                description=f'Stochastic перепродан: K={current_k:.2f}, D={current_d:.2f}'
            )
        else:
            return IndicatorResult(
                value=current_k,
                signal='HOLD',
                confidence=50,
                description=f'Stochastic нейтрален: K={current_k:.2f}, D={current_d:.2f}'
            )
    
    def get_combined_signal(self, high: List[float], low: List[float], close: List[float]) -> IndicatorResult:
        """Комбинированный сигнал на основе нескольких индикаторов"""
        signals = []
        
        # Анализируем каждый индикатор
        rsi_signal = self.analyze_rsi_signal(close)
        macd_signal = self.analyze_macd_signal(close)
        bb_signal = self.analyze_bollinger_signal(close)
        stoch_signal = self.analyze_stochastic_signal(high, low, close)
        
        signals = [rsi_signal, macd_signal, bb_signal, stoch_signal]
        
        # Подсчитываем голоса
        buy_votes = sum(1 for s in signals if s.signal == 'BUY')
        sell_votes = sum(1 for s in signals if s.signal == 'SELL')
        
        # Средняя уверенность
        avg_confidence = sum(s.confidence for s in signals) / len(signals)
        
        if buy_votes > sell_votes:
            final_signal = 'BUY'
            confidence = avg_confidence * (buy_votes / len(signals))
        elif sell_votes > buy_votes:
            final_signal = 'SELL'
            confidence = avg_confidence * (sell_votes / len(signals))
        else:
            final_signal = 'HOLD'
            confidence = 50
        
        description = f"Комбинированный сигнал: BUY({buy_votes}) SELL({sell_votes})"
        
        return IndicatorResult(
            value=close[-1] if close else 0,
            signal=final_signal,
            confidence=confidence,
            description=description
        )

