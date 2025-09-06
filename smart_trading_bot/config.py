import os
from typing import List
from dataclasses import dataclass

@dataclass
class Config:
    """Конфигурация приложения"""
    
    # Telegram Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/trading_bot.db")
    
    # Admin settings
    ADMIN_IDS: List[int] = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
    SUPER_ADMIN_ID: int = int(os.getenv("SUPER_ADMIN_ID", "0"))
    
    # Commission settings
    REFERRAL_COMMISSION: float = float(os.getenv("REFERRAL_COMMISSION", "0.02"))  # 2%
    MIN_PAYOUT_AMOUNT: float = float(os.getenv("MIN_PAYOUT_AMOUNT", "50.0"))  # $50
    
    # Partner Programs
    # Binarium
    BINARIUM_PARTNER_ID: str = os.getenv("BINARIUM_PARTNER_ID", "p43053p136178p011d")
    BINARIUM_API_KEY: str = os.getenv("BINARIUM_API_KEY", "")
    BINARIUM_SECRET: str = os.getenv("BINARIUM_SECRET", "")
    
    # PocketOption
    POCKET_OPTION_AFFILIATE_ID: str = os.getenv("POCKET_OPTION_AFFILIATE_ID", "OWrYm1TLeFf1Cv")
    POCKET_OPTION_API_KEY: str = os.getenv("POCKET_OPTION_API_KEY", "")
    
    # Exchange APIs
    BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")
    BINANCE_SECRET_KEY: str = os.getenv("BINANCE_SECRET_KEY", "")
    BINANCE_TESTNET: bool = os.getenv("BINANCE_TESTNET", "true").lower() == "true"
    
    # TradingView
    TRADINGVIEW_USERNAME: str = os.getenv("TRADINGVIEW_USERNAME", "")
    TRADINGVIEW_PASSWORD: str = os.getenv("TRADINGVIEW_PASSWORD", "")
    
    # Signal settings
    ENABLE_SIGNAL_MONITORING: bool = os.getenv("ENABLE_SIGNAL_MONITORING", "true").lower() == "true"
    SIGNAL_MONITOR_INTERVAL: int = int(os.getenv("SIGNAL_MONITOR_INTERVAL", "300"))  # 5 минут
    MIN_SIGNAL_CONFIDENCE: float = float(os.getenv("MIN_SIGNAL_CONFIDENCE", "70.0"))
    MAX_SIGNALS_PER_HOUR: int = int(os.getenv("MAX_SIGNALS_PER_HOUR", "12"))
    
    # Monitoring symbols
    MONITORING_SYMBOLS: List[str] = os.getenv("MONITORING_SYMBOLS", "BTC/USDT,ETH/USDT,EUR/USD,GBP/USD").split(",")
    
    # Web Panel
    WEB_PANEL_HOST: str = os.getenv("WEB_PANEL_HOST", "0.0.0.0")
    WEB_PANEL_PORT: int = int(os.getenv("WEB_PANEL_PORT", "5000"))
    WEB_PANEL_SECRET_KEY: str = os.getenv("WEB_PANEL_SECRET_KEY", "your-secret-key-here")
    WEB_PANEL_USERNAME: str = os.getenv("WEB_PANEL_USERNAME", "admin")
    WEB_PANEL_PASSWORD: str = os.getenv("WEB_PANEL_PASSWORD", "admin123")
    
    # API settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "your-api-secret-key")
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # секунд
    
    # Notifications
    ENABLE_EMAIL_NOTIFICATIONS: bool = os.getenv("ENABLE_EMAIL_NOTIFICATIONS", "false").lower() == "true"
    EMAIL_HOST: str = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT: int = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USERNAME: str = os.getenv("EMAIL_USERNAME", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")
    
    # Webhook settings (for production)
    WEBHOOK_HOST: str = os.getenv("WEBHOOK_HOST", "")
    WEBHOOK_PORT: int = int(os.getenv("WEBHOOK_PORT", "8443"))
    WEBHOOK_URL_PATH: str = os.getenv("WEBHOOK_URL_PATH", f"/{BOT_TOKEN}")
    
    # Redis (for caching and session storage)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/bot.log")
    
    # Security
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    
    # Premium features
    PREMIUM_SUBSCRIPTION_PRICE: float = float(os.getenv("PREMIUM_SUBSCRIPTION_PRICE", "29.99"))
    VIP_SUBSCRIPTION_PRICE: float = float(os.getenv("VIP_SUBSCRIPTION_PRICE", "99.99"))
    
    def __post_init__(self):
        """Валидация конфигурации"""
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не может быть пустым")
        
        if not self.ADMIN_IDS:
            raise ValueError("Необходимо указать хотя бы одного администратора")
        
        if self.REFERRAL_COMMISSION < 0 or self.REFERRAL_COMMISSION > 1:
            raise ValueError("REFERRAL_COMMISSION должна быть между 0 и 1")

# Создание экземпляра конфигурации
config = Config()