"""
Базовый класс для партнерских интеграций
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import aiohttp
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PartnerBase(ABC):
    """Базовый класс для всех партнерских интеграций"""
    
    def __init__(self, api_key: str = None, partner_id: str = None):
        self.api_key = api_key
        self.partner_id = partner_id
        self.base_url = ""
        self.session = None
        
    async def __aenter__(self):
        """Асинхронный контекст менеджер - вход"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекст менеджер - выход"""
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def get_referral_link(self, user_id: int) -> str:
        """Получить реферальную ссылку для пользователя"""
        pass
    
    @abstractmethod
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Получить статистику пользователя"""
        pass
    
    @abstractmethod
    async def track_click(self, user_id: int, ref_id: str) -> bool:
        """Отследить клик по реферальной ссылке"""
        pass
    
    @abstractmethod
    async def track_registration(self, user_id: int, platform_user_id: str) -> bool:
        """Отследить регистрацию пользователя"""
        pass
    
    @abstractmethod
    async def track_deposit(self, user_id: int, amount: float) -> bool:
        """Отследить депозит пользователя"""
        pass
    
    @abstractmethod
    async def get_commission_data(self, user_id: int, 
                                date_from: datetime = None, 
                                date_to: datetime = None) -> List[Dict]:
        """Получить данные о комиссиях"""
        pass
    
    async def make_request(self, method: str, endpoint: str, 
                          data: Dict = None, params: Dict = None) -> Optional[Dict]:
        """Выполнить HTTP запрос к API партнера"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"API request failed: {response.status} - {await response.text()}")
                    return None
                    
        except Exception as e:
            logger.error(f"Request error: {e}")
            return None
    
    def _get_headers(self) -> Dict[str, str]:
        """Получить заголовки для запросов"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'SmartTradingBot/1.0'
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        return headers
    
    def _generate_ref_code(self, user_id: int) -> str:
        """Генерировать реферальный код"""
        return f"{self.partner_id}_{user_id}"
    
    def _parse_date(self, date_str: str) -> datetime:
        """Парсинг даты из строки"""
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return datetime.now()
    
    async def validate_api_connection(self) -> bool:
        """Проверить соединение с API"""
        try:
            result = await self.make_request('GET', '/ping')
            return result is not None
        except:
            return False

class CommissionCalculator:
    """Калькулятор комиссий"""
    
    @staticmethod
    def calculate_commission(volume: float, rate: float, 
                           min_commission: float = 0.0,
                           max_commission: float = None) -> float:
        """Рассчитать комиссию"""
        commission = volume * (rate / 100)
        
        if commission < min_commission:
            commission = min_commission
        
        if max_commission and commission > max_commission:
            commission = max_commission
        
        return round(commission, 2)
    
    @staticmethod
    def get_commission_rate(volume: float, tier_rates: Dict[float, float]) -> float:
        """Получить ставку комиссии в зависимости от объема"""
        sorted_tiers = sorted(tier_rates.keys(), reverse=True)
        
        for tier_volume in sorted_tiers:
            if volume >= tier_volume:
                return tier_rates[tier_volume]
        
        return min(tier_rates.values())

class PartnerMetrics:
    """Метрики партнерской программы"""
    
    def __init__(self):
        self.clicks = 0
        self.registrations = 0
        self.deposits = 0
        self.total_volume = 0.0
        self.commission_earned = 0.0
        self.conversion_rate = 0.0
    
    def calculate_conversion_rate(self) -> float:
        """Рассчитать конверсию"""
        if self.clicks == 0:
            return 0.0
        return (self.registrations / self.clicks) * 100
    
    def calculate_deposit_rate(self) -> float:
        """Рассчитать процент депозитов"""
        if self.registrations == 0:
            return 0.0
        return (self.deposits / self.registrations) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертировать в словарь"""
        return {
            'clicks': self.clicks,
            'registrations': self.registrations,
            'deposits': self.deposits,
            'total_volume': self.total_volume,
            'commission_earned': self.commission_earned,
            'conversion_rate': self.calculate_conversion_rate(),
            'deposit_rate': self.calculate_deposit_rate()
        }

class PartnerError(Exception):
    """Исключение для ошибок партнерских интеграций"""
    pass

class APIError(PartnerError):
    """Ошибка API"""
    pass

class AuthenticationError(PartnerError):
    """Ошибка аутентификации"""
    pass

class RateLimitError(PartnerError):
    """Ошибка превышения лимита запросов"""
    pass

