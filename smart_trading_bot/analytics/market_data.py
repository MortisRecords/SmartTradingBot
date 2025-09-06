"""
Провайдер рыночных данных
"""
import asyncio
import aiohttp
import ccxt.async_support as ccxt
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MarketDataProvider:
    """Провайдер рыночных данных из различных источников"""
    
    def __init__(self):
        self.exchanges = {}
        self.forex_api_key = None  # Можно добавить API ключ для форекс данных
        self.session = None
        
    async def __aenter__(self):
        """Асинхронный контекст менеджер"""
        self.session = aiohttp.ClientSession()
        await self._initialize_exchanges()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие соединений"""
        if self.session:
            await self.session.close()
        
        for exchange in self.exchanges.values():
            await exchange.close()
    
    async def _initialize_exchanges(self):
        """Инициализация бирж"""
        try:
            # Binance для криптовалют
            self.exchanges['binance'] = ccxt.binance({
                'apiKey': '',  # Добавить API ключи при необходимости
                'secret': '',
                'sandbox': False,
                'enableRateLimit': True,
            })
            
            # Можно добавить другие биржи
            # self.exchanges['bybit'] = ccxt.bybit({...})
            
        except Exception as e:
            logger.error(f"Ошибка инициализации бирж: {e}")
    
    async def get_ohlcv_data(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[Dict]:
        """Получение OHLCV данных"""
        try:
            # Определяем источник данных по символу
            if self._is_crypto_symbol(symbol):
                return await self._get_crypto_ohlcv(symbol, timeframe, limit)
            elif self._is_forex_symbol(symbol):
                return await self._get_forex_ohlcv(symbol, timeframe, limit)
            else:
                return await self._get_stock_ohlcv(symbol, timeframe, limit)
                
        except Exception as e:
            logger.error(f"Ошибка получения OHLCV для {symbol}: {e}")
            return []
    
    async def _get_crypto_ohlcv(self, symbol: str, timeframe: str, limit: int) -> List[Dict]:
        """Получение криптовалютных данных"""
        try:
            if 'binance' not in self.exchanges:
                return []
            
            # Конвертируем символ в формат Binance
            binance_symbol = self._convert_to_binance_symbol(symbol)
            
            ohlcv = await self.exchanges['binance'].fetch_ohlcv(
                binance_symbol, timeframe, limit=limit
            )
            
            return [
                {
                    'timestamp': candle[0],
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                }
                for candle in ohlcv
            ]
            
        except Exception as e:
            logger.error(f"Ошибка получения криптовалютных данных для {symbol}: {e}")
            return []
    
    async def _get_forex_ohlcv(self, symbol: str, timeframe: str, limit: int) -> List[Dict]:
        """Получение форекс данных"""
        try:
            # Используем бесплатный API для форекс данных
            # Можно заменить на платный API для лучшего качества данных
            url = f"https://api.exchangerate-api.com/v4/latest/{symbol[:3]}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Генерируем фиктивные OHLCV данные на основе текущего курса
                    # В реальном проекте нужно использовать настоящий API
                    return self._generate_mock_forex_data(symbol, limit)
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"Ошибка получения форекс данных для {symbol}: {e}")
            return []
    
    async def _get_stock_ohlcv(self, symbol: str, timeframe: str, limit: int) -> List[Dict]:
        """Получение данных акций и индексов"""
        try:
            # Используем Alpha Vantage или другой бесплатный API
            # Для демонстрации генерируем фиктивные данные
            return self._generate_mock_stock_data(symbol, limit)
            
        except Exception as e:
            logger.error(f"Ошибка получения данных акций для {symbol}: {e}")
            return []
    
    async def get_current_price(self, symbol: str) -> Dict[str, Any]:
        """Получение текущей цены"""
        try:
            if self._is_crypto_symbol(symbol):
                return await self._get_crypto_price(symbol)
            elif self._is_forex_symbol(symbol):
                return await self._get_forex_price(symbol)
            else:
                return await self._get_stock_price(symbol)
                
        except Exception as e:
            logger.error(f"Ошибка получения цены для {symbol}: {e}")
            return {'price': 0, 'timestamp': datetime.now().timestamp()}
    
    async def _get_crypto_price(self, symbol: str) -> Dict[str, Any]:
        """Получение текущей цены криптовалюты"""
        try:
            if 'binance' not in self.exchanges:
                return {'price': 0, 'timestamp': datetime.now().timestamp()}
            
            binance_symbol = self._convert_to_binance_symbol(symbol)
            ticker = await self.exchanges['binance'].fetch_ticker(binance_symbol)
            
            return {
                'price': ticker['last'],
                'timestamp': ticker['timestamp'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'volume': ticker['baseVolume']
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения цены криптовалюты {symbol}: {e}")
            return {'price': 0, 'timestamp': datetime.now().timestamp()}
    
    async def _get_forex_price(self, symbol: str) -> Dict[str, Any]:
        """Получение текущей цены форекс"""
        # Фиктивная реализация - заменить на реальный API
        import random
        base_price = 1.0 if 'USD' in symbol else 100.0
        price = base_price + random.uniform(-0.01, 0.01)
        
        return {
            'price': price,
            'timestamp': datetime.now().timestamp(),
            'bid': price - 0.0001,
            'ask': price + 0.0001
        }
    
    async def _get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """Получение текущей цены акций"""
        # Фиктивная реализация - заменить на реальный API
        import random
        base_prices = {
            'SPX500': 4500,
            'XAUUSD': 2000,
            'CRUDE_OIL': 80
        }
        base_price = base_prices.get(symbol, 100)
        price = base_price + random.uniform(-base_price*0.01, base_price*0.01)
        
        return {
            'price': price,
            'timestamp': datetime.now().timestamp()
        }
    
    def _is_crypto_symbol(self, symbol: str) -> bool:
        """Проверка, является ли символ криптовалютой"""
        crypto_symbols = ['BTC', 'ETH', 'ADA', 'DOT', 'LINK', 'UNI']
        return any(crypto in symbol for crypto in crypto_symbols)
    
    def _is_forex_symbol(self, symbol: str) -> bool:
        """Проверка, является ли символ форекс парой"""
        forex_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD']
        return len(symbol) == 6 and symbol[:3] in forex_currencies and symbol[3:] in forex_currencies
    
    def _convert_to_binance_symbol(self, symbol: str) -> str:
        """Конвертация символа в формат Binance"""
        conversions = {
            'BTCUSD': 'BTC/USDT',
            'ETHUSD': 'ETH/USDT',
            'ADAUSD': 'ADA/USDT',
            'DOTUSD': 'DOT/USDT'
        }
        return conversions.get(symbol, symbol)
    
    def _generate_mock_forex_data(self, symbol: str, limit: int) -> List[Dict]:
        """Генерация фиктивных форекс данных для демонстрации"""
        import random
        
        base_price = 1.0 if 'USD' in symbol else 100.0
        data = []
        current_time = datetime.now()
        
        for i in range(limit):
            timestamp = current_time - timedelta(hours=limit-i)
            
            # Генерируем случайные OHLCV данные
            open_price = base_price + random.uniform(-0.01, 0.01)
            high_price = open_price + random.uniform(0, 0.005)
            low_price = open_price - random.uniform(0, 0.005)
            close_price = open_price + random.uniform(-0.005, 0.005)
            volume = random.uniform(1000, 10000)
            
            data.append({
                'timestamp': int(timestamp.timestamp() * 1000),
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
        
        return data
    
    def _generate_mock_stock_data(self, symbol: str, limit: int) -> List[Dict]:
        """Генерация фиктивных данных акций для демонстрации"""
        import random
        
        base_prices = {
            'SPX500': 4500,
            'XAUUSD': 2000,
            'CRUDE_OIL': 80
        }
        base_price = base_prices.get(symbol, 100)
        
        data = []
        current_time = datetime.now()
        
        for i in range(limit):
            timestamp = current_time - timedelta(hours=limit-i)
            
            # Генерируем случайные OHLCV данные
            open_price = base_price + random.uniform(-base_price*0.02, base_price*0.02)
            high_price = open_price + random.uniform(0, base_price*0.01)
            low_price = open_price - random.uniform(0, base_price*0.01)
            close_price = open_price + random.uniform(-base_price*0.01, base_price*0.01)
            volume = random.uniform(10000, 100000)
            
            data.append({
                'timestamp': int(timestamp.timestamp() * 1000),
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
        
        return data

