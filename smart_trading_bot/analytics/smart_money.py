"""
Smart Money Analyzer
Анализатор индикатора Smart Money для генерации торговых сигналов
"""

import pandas as pd
import numpy as np
import talib
from typing import Dict, Optional, List, Tuple
import logging
from datetime import datetime, timedelta
from analytics.market_data import MarketDataProvider

logger = logging.getLogger(__name__)

class SmartMoneyAnalyzer:
    """Анализатор Smart Money индикатора"""
    
    def __init__(self, market_data_provider: MarketDataProvider):
        self.market_data = market_data_provider
        
    def calculate_smart_money_index(self, df: pd.DataFrame) -> pd.Series:
        """
        Расчет индекса Smart Money
        Основан на анализе объемов, цен и поведения институциональных инвесторов
        """
        try:
            if len(df) < 50:
                logger.warning("Недостаточно данных для расчета Smart Money Index")
                return pd.Series(dtype=float)
            
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            volume = df['volume'].values
            open_price = df['open'].values
            
            # 1. True Range для оценки волатильности
            tr1 = high - low
            tr2 = np.abs(high - np.roll(close, 1))
            tr3 = np.abs(low - np.roll(close, 1))
            true_range = np.maximum(tr1, np.maximum(tr2, tr3))
            
            # 2. Typical Price (средняя цена)
            typical_price = (high + low + close) / 3
            
            # 3. Money Flow (денежный поток)
            money_flow = typical_price * volume
            
            # 4. Volume-Weighted Average Price (VWAP)
            vwap = money_flow.cumsum() / volume.cumsum()
            
            # 5. Smart Money Pressure (давление умных денег)
            # Анализ отношения объема к волатильности
            volume_volatility_ratio = volume / (true_range + 0.0001)  # Избегаем деления на ноль
            
            # 6. Accumulation/Distribution Line
            clv = ((close - low) - (high - close)) / (high - low + 0.0001)
            ad_line = (clv * volume).cumsum()
            
            # 7. On Balance Volume (OBV)
            price_change = np.diff(close, prepend=close[0])
            obv = np.where(price_change > 0, volume, 
                          np.where(price_change < 0, -volume, 0)).cumsum()
            
            # 8. Money Flow Index (MFI) компоненты
            price_diff = np.diff(typical_price, prepend=typical_price[0])
            positive_flow = np.where(price_diff > 0, money_flow, 0)
            negative_flow = np.where(price_diff < 0, money_flow, 0)
            
            # Скользящие средние для сглаживания
            positive_flow_ma = pd.Series(positive_flow).rolling(14).sum()
            negative_flow_ma = pd.Series(negative_flow).rolling(14).sum()
            
            # 9. Volume Profile анализ
            high_volume_zones = volume > np.percentile(volume, 80)
            low_volume_zones = volume < np.percentile(volume, 20)
            
            # 10. Smart Money Index calculation
            # Комбинируем все индикаторы в единый Smart Money Index
            
            # Нормализация компонентов (0-1)
            vwap_norm = self._normalize_series(pd.Series(vwap))
            ad_norm = self._normalize_series(pd.Series(ad_line))
            obv_norm = self._normalize_series(pd.Series(obv))
            vol_ratio_norm = self._normalize_series(pd.Series(volume_volatility_ratio))
            
            # Взвешенное среднее с учетом важности каждого индикатора
            weights = {
                'vwap': 0.25,
                'ad': 0.25, 
                'obv': 0.20,
                'vol_ratio': 0.15,
                'mfi': 0.15
            }
            
            # MFI расчет
            mfi_ratio = positive_flow_ma / (negative_flow_ma + positive_flow_ma + 0.0001)
            mfi_norm = self._normalize_series(mfi_ratio)
            
            # Итоговый Smart Money Index
            smi = (weights['vwap'] * vwap_norm + 
                   weights['ad'] * ad_norm + 
                   weights['obv'] * obv_norm + 
                   weights['vol_ratio'] * vol_ratio_norm +
                   weights['mfi'] * mfi_norm)
            
            # Сглаживание результата
            smi_smoothed = smi.rolling(window=5, center=True).mean()
            
            return smi_smoothed.fillna(method='bfill').fillna(method='ffill')
            
        except Exception as e:
            logger.error(f"Ошибка расчета Smart Money Index: {e}")
            return pd.Series(dtype=float)
    
    def _normalize_series(self, series: pd.Series, method='minmax') -> pd.Series:
        """Нормализация временного ряда"""
        try:
            if method == 'minmax':
                min_val = series.min()
                max_val = series.max()
                if max_val == min_val:
                    return pd.Series(0.5, index=series.index)
                return (series - min_val) / (max_val - min_val)
            elif method == 'zscore':
                return (series - series.mean()) / series.std()
        except Exception as e:
            logger.error(f"Ошибка нормализации: {e}")
            return pd.Series(0.5, index=series.index)
    
    def detect_smart_money_signals(self, df: pd.DataFrame) -> Dict:
        """Определение сигналов Smart Money"""
        try:
            smi = self.calculate_smart_money_index(df)
            
            if len(smi) < 20:
                return {'signal': None, 'confidence': 0, 'analysis': {}}
            
            # Текущие значения
            current_smi = smi.iloc[-1]
            prev_smi = smi.iloc[-2]
            smi_change = current_smi - prev_smi
            
            # Расчет дополнительных индикаторов для подтверждения
            close_prices = df['close'].values
            volume = df['volume'].values
            
            # RSI
            rsi = talib.RSI(close_prices, timeperiod=14)
            current_rsi = rsi[-1] if len(rsi) > 0 else 50
            
            # MACD
            macd, macd_signal, macd_hist = talib.MACD(close_prices)
            macd_bullish = macd[-1] > macd_signal[-1] if len(macd) > 0 else False
            macd_bearish = macd[-1] < macd_signal[-1] if len(macd) > 0 else False
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close_prices, timeperiod=20)
            price_position = (close_prices[-1] - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1])
            
            # Volume analysis
            avg_volume = np.mean(volume[-20:])
            current_volume = volume[-1]
            volume_spike = current_volume > avg_volume * 1.5
            
            # Определение сигналов
            signals = []
            confidence_factors = []
            
            # Smart Money покупает (накопление)
            if current_smi > 0.7 and smi_change > 0.05:
                signals.append('BUY')
                confidence_factors.append(30)
                
                # Дополнительные факторы подтверждения
                if current_rsi < 70 and macd_bullish:
                    confidence_factors.append(25)
                if volume_spike:
                    confidence_factors.append(20)
                if price_position < 0.3:  # Цена в нижней части диапазона
                    confidence_factors.append(15)
            
            # Smart Money продает (распределение)
            elif current_smi < 0.3 and smi_change < -0.05:
                signals.append('SELL')
                confidence_factors.append(30)
                
                # Дополнительные факторы подтверждения
                if current_rsi > 30 and macd_bearish:
                    confidence_factors.append(25)
                if volume_spike:
                    confidence_factors.append(20)
                if price_position > 0.7:  # Цена в верхней части диапазона
                    confidence_factors.append(15)
            
            # Боковое движение / неопределенность
            else:
                signals.append(None)
                confidence_factors.append(0)
            
            # Расчет общей уверенности
            total_confidence = min(95, sum(confidence_factors))
            
            # Анализ тренда
            sma_20 = talib.SMA(close_prices, timeperiod=20)
            sma_50 = talib.SMA(close_prices, timeperiod=50)
            trend = 'UPTREND' if sma_20[-1] > sma_50[-1] else 'DOWNTREND'
            
            # Волатильность
            atr = talib.ATR(df['high'].values, df['low'].values, close_prices, timeperiod=14)
            volatility = 'HIGH' if atr[-1] > np.mean(atr[-20:]) * 1.3 else 'NORMAL'
            
            result = {
                'signal': signals[0] if signals else None,
                'confidence': total_confidence,
                'smi_current': current_smi,
                'smi_change': smi_change,
                'analysis': {
                    'rsi': current_rsi,
                    'macd_signal': 'BULLISH' if macd_bullish else 'BEARISH',
                    'trend': trend,
                    'volatility': volatility,
                    'volume_spike': volume_spike,
                    'price_position': price_position,
                    'smart_money_flow': self._interpret_smi_flow(current_smi)
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка определения Smart Money сигналов: {e}")
            return {'signal': None, 'confidence': 0, 'analysis': {}}
    
    def _interpret_smi_flow(self, smi_value: float) -> str:
        """Интерпретация потока Smart Money"""
        if smi_value > 0.8:
            return "STRONG_ACCUMULATION"
        elif smi_value > 0.6:
            return "ACCUMULATION"
        elif smi_value > 0.4:
            return "NEUTRAL_BULLISH"
        elif smi_value > 0.2:
            return "NEUTRAL_BEARISH"
        elif smi_value > 0.1:
            return "DISTRIBUTION"
        else:
            return "STRONG_DISTRIBUTION"
    
    def get_support_resistance_levels(self, df: pd.DataFrame) -> Dict[str, float]:
        """Определение уровней поддержки и сопротивления"""
        try:
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            volume = df['volume'].values
            
            # Поиск локальных экстремумов
            from scipy.signal import argrelextrema
            
            # Локальные максимумы (сопротивление)
            resistance_indices = argrelextrema(high, np.greater, order=5)[0]
            resistance_levels = high[resistance_indices] if len(resistance_indices) > 0 else []
            
            # Локальные минимумы (поддержка)
            support_indices = argrelextrema(low, np.less, order=5)[0]
            support_levels = low[support_indices] if len(support_indices) > 0 else []
            
            # Объемные уровни (Volume Profile)
            price_range = np.linspace(low.min(), high.max(), 50)
            volume_at_price = np.zeros_like(price_range)
            
            for i, (h, l, v) in enumerate(zip(high, low, volume)):
                price_indices = np.where((price_range >= l) & (price_range <= h))[0]
                if len(price_indices) > 0:
                    volume_per_level = v / len(price_indices)
                    volume_at_price[price_indices] += volume_per_level
            
            # Находим уровни с максимальным объемом
            high_volume_indices = np.argsort(volume_at_price)[-5:]
            volume_levels = price_range[high_volume_indices]
            
            # Комбинируем все уровни
            all_resistance = np.concatenate([resistance_levels, volume_levels])
            all_support = np.concatenate([support_levels, volume_levels])
            
            # Находим ближайшие уровни к текущей цене
            current_price = close[-1]
            
            resistance_above = all_resistance[all_resistance > current_price]
            support_below = all_support[all_support < current_price]
            
            nearest_resistance = resistance_above.min() if len(resistance_above) > 0 else current_price * 1.05
            nearest_support = support_below.max() if len(support_below) > 0 else current_price * 0.95
            
            return {
                'resistance': nearest_resistance,
                'support': nearest_support,
                'volume_levels': volume_levels.tolist(),
                'all_resistance': resistance_levels.tolist(),
                'all_support': support_levels.tolist()
            }
            
        except Exception as e:
            logger.error(f"Ошибка определения уровней поддержки/сопротивления: {e}")
            current_price = df['close'].iloc[-1]
            return {
                'resistance': current_price * 1.02,
                'support': current_price * 0.98,
                'volume_levels': [],
                'all_resistance': [],
                'all_support': []
            }
    
    def analyze_institutional_behavior(self, df: pd.DataFrame) -> Dict:
        """Анализ поведения институциональных инвесторов"""
        try:
            volume = df['volume'].values
            close = df['close'].values
            high = df['high'].values
            low = df['low'].values
            
            # Анализ необычной объемной активности
            avg_volume = np.mean(volume[-20:])
            volume_spikes = np.where(volume > avg_volume * 2)[0]
            
            # Анализ крупных свечей (возможные институциональные сделки)
            body_size = np.abs(df['close'] - df['open']).values
            avg_body = np.mean(body_size[-20:])
            large_candles = np.where(body_size > avg_body * 2)[0]
            
            # Анализ разрывов (gaps)
            price_gaps = []
            for i in range(1, len(df)):
                prev_close = df['close'].iloc[i-1]
                current_open = df['open'].iloc[i]
                gap_size = abs(current_open - prev_close) / prev_close
                if gap_size > 0.01:  # Разрыв более 1%
                    price_gaps.append({
                        'index': i,
                        'size': gap_size,
                        'direction': 'UP' if current_open > prev_close else 'DOWN'
                    })
            
            # Анализ времени активности (если доступны временные метки)
            activity_hours = {}
            if 'timestamp' in df.columns:
                df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
                for hour in range(24):
                    hour_data = df[df['hour'] == hour]
                    if len(hour_data) > 0:
                        activity_hours[hour] = {
                            'avg_volume': hour_data['volume'].mean(),
                            'volatility': hour_data['high'].subtract(hour_data['low']).mean()
                        }
            
            return {
                'volume_spikes_count': len(volume_spikes),
                'large_candles_count': len(large_candles),
                'recent_gaps': price_gaps[-5:] if price_gaps else [],
                'institutional_activity_score': min(100, 
                    (len(volume_spikes) * 10 + len(large_candles) * 5 + len(price_gaps) * 15)),
                'activity_by_hour': activity_hours
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа институционального поведения: {e}")
            return {
                'volume_spikes_count': 0,
                'large_candles_count': 0,
                'recent_gaps': [],
                'institutional_activity_score': 0,
                'activity_by_hour': {}
            }
    
    async def generate_smart_money_signal(self, symbol: str, timeframe: str = '1h') -> Optional[Dict]:
        """Генерация сигнала на основе Smart Money анализа"""
        try:
            # Получение рыночных данных
            df = await self.market_data.get_ohlcv_data(symbol, timeframe, limit=200)
            if df is None or len(df) < 50:
                logger.warning(f"Недостаточно данных для {symbol}")
                return None
            
            # Smart Money анализ
            smi_analysis = self.detect_smart_money_signals(df)
            
            if not smi_analysis['signal'] or smi_analysis['confidence'] < 60:
                return None
            
            # Дополнительный анализ
            levels = self.get_support_resistance_levels(df)
            institutional = self.analyze_institutional_behavior(df)
            
            current_price = df['close'].iloc[-1]
            
            # Расчет целевых уровней
            if smi_analysis['signal'] == 'BUY':
                take_profit = min(levels['resistance'], current_price * 1.03)
                stop_loss = max(levels['support'], current_price * 0.98)
            else:  # SELL
                take_profit = max(levels['support'], current_price * 0.97)
                stop_loss = min(levels['resistance'], current_price * 1.02)
            
            # Время экспирации (для бинарных опционов)
            if timeframe == '1m':
                expiry_minutes = 5
            elif timeframe == '5m':
                expiry_minutes = 15
            elif timeframe == '15m':
                expiry_minutes = 30
            elif timeframe == '1h':
                expiry_minutes = 60
            else:
                expiry_minutes = 240
            
            expires_at = datetime.now() + timedelta(minutes=expiry_minutes)
            
            return {
                'symbol': symbol,
                'signal_type': smi_analysis['signal'],
                'entry_price': current_price,
                'take_profit': take_profit,
                'stop_loss': stop_loss,
                'confidence': smi_analysis['confidence'],
                'timeframe': timeframe,
                'expires_at': expires_at,
                'analysis': {
                    **smi_analysis['analysis'],
                    'support_level': levels['support'],
                    'resistance_level': levels['resistance'],
                    'institutional_score': institutional['institutional_activity_score'],
                    'smart_money_index': smi_analysis['smi_current'],
                    'volume_analysis': 'HIGH' if institutional['volume_spikes_count'] > 2 else 'NORMAL'
                }
            }
            
        except Exception as e:
            logger.error(f"Ошибка генерации Smart Money сигнала: {e}")
            return None
            