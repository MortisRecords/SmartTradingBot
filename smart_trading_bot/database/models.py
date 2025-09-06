"""
Database models for Smart Trading Bot
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

Base = declarative_base()

class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True, nullable=False)  # Telegram user ID
    username = Column(String(50), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    
    # Реферальная система
    referrer_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    referral_code = Column(String(20), unique=True, nullable=True)
    referrals_count = Column(Integer, default=0)
    
    # Подписки и статус
    is_premium = Column(Boolean, default=False)
    is_vip = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    premium_until = Column(DateTime, nullable=True)
    vip_until = Column(DateTime, nullable=True)
    
    # Статистика
    total_signals_received = Column(Integer, default=0)
    successful_signals = Column(Integer, default=0)
    total_volume_traded = Column(Float, default=0.0)
    commission_earned = Column(Float, default=0.0)
    commission_withdrawn = Column(Float, default=0.0)
    
    # Настройки уведомлений
    notifications_enabled = Column(Boolean, default=True)
    signal_notifications = Column(Boolean, default=True)
    commission_notifications = Column(Boolean, default=True)
    
    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_active = Column(DateTime, default=func.now())
    
    # Связи
    referrer = relationship("User", remote_side=[user_id], backref="referrals")
    signals = relationship("Signal", back_populates="user")
    trades = relationship("Trade", back_populates="user")
    
    @property
    def is_new(self):
        """Проверка, новый ли пользователь (зарегистрирован менее часа назад)"""
        return (datetime.now() - self.created_at) < timedelta(hours=1)
    
    @property
    def success_rate(self):
        """Процент успешных сигналов"""
        if self.total_signals_received == 0:
            return 0
        return (self.successful_signals / self.total_signals_received) * 100
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'first_name': self.first_name,
            'is_premium': self.is_premium,
            'is_vip': self.is_vip,
            'referrals_count': self.referrals_count,
            'commission_earned': self.commission_earned,
            'success_rate': self.success_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Signal(Base):
    """Модель торгового сигнала"""
    __tablename__ = 'signals'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # Параметры сигнала
    symbol = Column(String(20), nullable=False)  # BTC/USDT, EUR/USD, etc.
    signal_type = Column(String(10), nullable=False)  # BUY, SELL, CALL, PUT
    timeframe = Column(String(10), default='1h')  # 1m, 5m, 15m, 1h, 4h, 1d
    
    # Цены
    entry_price = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    current_price = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    
    # Анализ
    confidence = Column(Float, nullable=False)  # 0-100
    analysis = Column(JSON, nullable=True)  # Детальный анализ индикаторов
    
    # Статус и результат
    status = Column(String(20), default='active')  # active, closed, expired, cancelled
    result = Column(String(10), nullable=True)  # win, loss, breakeven
    profit_loss = Column(Float, default=0.0)  # Прибыль/убыток в долларах
    
    # Временные метки
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    # Связи
    user = relationship("User", back_populates="signals")
    
    @property
    def is_expired(self):
        """Проверка на истечение сигнала"""
        return self.expires_at and datetime.now() > self.expires_at
    
    @property
    def duration_minutes(self):
        """Длительность сигнала в минутах"""
        if self.closed_at:
            return int((self.closed_at - self.created_at).total_seconds() / 60)
        return int((datetime.now() - self.created_at).total_seconds() / 60)
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'signal_type': self.signal_type,
            'entry_price': self.entry_price,
            'take_profit': self.take_profit,
            'stop_loss': self.stop_loss,
            'confidence': self.confidence,
            'status': self.status,
            'result': self.result,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

class Trade(Base):
    """Модель торговой операции (для отслеживания оборота)"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    signal_id = Column(Integer, ForeignKey('signals.id'), nullable=True)
    
    # Параметры сделки
    symbol = Column(String(20), nullable=False)
    platform = Column(String(50), nullable=True)  # binarium, pocket_option, etc.
    trade_type = Column(String(20), nullable=True)  # binary_option, cfd, forex
    
    # Объемы и результат
    amount = Column(Float, nullable=False)  # Размер сделки
    profit_loss = Column(Float, default=0.0)
    commission_paid = Column(Float, default=0.0)  # Комиссия, уплаченная платформе
    
    # Статус
    status = Column(String(20), default='pending')  # pending, completed, failed
    
    # Временные метки
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Связи
    user = relationship("User", back_populates="trades")
    signal = relationship("Signal")

class Commission(Base):
    """Модель комиссионных выплат"""
    __tablename__ = 'commissions'
    
    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    referred_user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    trade_id = Column(Integer, ForeignKey('trades.id'), nullable=True)
    
    # Суммы
    trade_volume = Column(Float, nullable=False)  # Объем сделки
    commission_rate = Column(Float, nullable=False)  # Процент комиссии
    commission_amount = Column(Float, nullable=False)  # Размер комиссии
    
    # Статус выплаты
    status = Column(String(20), default='pending')  # pending, paid, cancelled
    paid_at = Column(DateTime, nullable=True)
    
    # Временные метки
    created_at = Column(DateTime, default=func.now())
    
    # Связи
    referrer = relationship("User", foreign_keys=[referrer_id])
    referred_user = relationship("User", foreign_keys=[referred_user_id])
    trade = relationship("Trade")

class Analytics(Base):
    """Модель аналитических данных"""
    __tablename__ = 'analytics'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Тип метрики
    metric_type = Column(String(50), nullable=False)  # signals_accuracy, user_activity, etc.
    metric_name = Column(String(100), nullable=False)
    
    # Данные
    value = Column(Float, nullable=True)
    data = Column(JSON, nullable=True)  # Дополнительные данные
    
    # Период
    date = Column(DateTime, default=func.now())
    period = Column(String(20), default='daily')  # daily, weekly, monthly
    
    created_at = Column(DateTime, default=func.now())

class SystemSettings(Base):
    """Системные настройки"""
    __tablename__ = 'system_settings'
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Notification(Base):
    """Модель уведомлений"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # Содержание уведомления
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # signal, commission, system, etc.
    
    # Статус
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    
    # Данные для отправки
    telegram_message_id = Column(Integer, nullable=True)
    
    # Временные метки
    created_at = Column(DateTime, default=func.now())
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    
    # Связи
    user = relationship("User")

class PartnerStats(Base):
    """Статистика партнерских программ"""
    __tablename__ = 'partner_stats'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # Платформа
    platform = Column(String(50), nullable=False)  # binarium, pocket_option
    platform_user_id = Column(String(100), nullable=True)  # ID на платформе
    
    # Статистика
    clicks = Column(Integer, default=0)  # Переходы по ссылке
    registrations = Column(Integer, default=0)  # Регистрации
    deposits = Column(Integer, default=0)  # Депозиты
    total_volume = Column(Float, default=0.0)  # Общий оборот
    commission_earned = Column(Float, default=0.0)  # Заработанные комиссии
    
    # Последние данные
    last_sync = Column(DateTime, nullable=True)  # Последняя синхронизация с API
    last_activity = Column(DateTime, nullable=True)  # Последняя активность
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связи
    user = relationship("User")