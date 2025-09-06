"""
Database Manager for Smart Trading Bot
Управление базой данных и CRUD операции
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import create_engine, func, and_, or_, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import asyncpg
from contextlib import asynccontextmanager
import json

from .models import Base, User, Signal, Trade, Commission, Analytics, SystemSettings, Notification, PartnerStats
from config import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Менеджер базы данных"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        self._pool = None
        
    async def initialize(self):
        """Инициализация подключения к БД"""
        try:
            # Для PostgreSQL
            if self.database_url.startswith('postgresql'):
                self.engine = create_engine(self.database_url, echo=False)
                self.SessionLocal = sessionmaker(bind=self.engine)
                
                # Создание таблиц
                Base.metadata.create_all(bind=self.engine)
                
                # Пул соединений для async операций
                self._pool = await asyncpg.create_pool(self.database_url)
                
            # Для SQLite
            elif self.database_url.startswith('sqlite'):
                self.engine = create_engine(self.database_url, echo=False)
                self.SessionLocal = sessionmaker(bind=self.engine)
                Base.metadata.create_all(bind=self.engine)
            
            logger.info("База данных инициализирована успешно")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            raise
    
    async def close(self):
        """Закрытие подключений"""
        if self._pool:
            await self._pool.close()
        if self.engine:
            self.engine.dispose()
    
    @asynccontextmanager
    async def get_session(self):
        """Контекстный менеджер для сессий"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка в сессии БД: {e}")
            raise
        finally:
            session.close()
    
    # === USER OPERATIONS ===
    
    async def get_or_create_user(self, user_id: int, username: str = None, 
                               first_name: str = None, referrer_id: int = None) -> User:
        """Получение или создание пользователя"""
        async with self.get_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            
            if user:
                # Обновление данных существующего пользователя
                user.username = username
                user.first_name = first_name
                user.last_active = datetime.now()
                user.is_new = False
                return user
            
            # Создание нового пользователя
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                referrer_id=referrer_id,
                referral_code=f"ref_{user_id}",
                is_new=True
            )
            
            session.add(user)
            
            # Обновление счетчика рефералов
            if referrer_id:
                referrer = session.query(User).filter(User.user_id == referrer_id).first()
                if referrer:
                    referrer.referrals_count += 1
            
            return user
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        async with self.get_session() as session:
            return session.query(User).filter(User.user_id == user_id).first()
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Получение пользователя с дополнительной информацией"""
        async with self.get_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            return user.to_dict() if user else None
    
    async def update_user_activity(self, user_id: int):
        """Обновление времени последней активности"""
        async with self.get_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                user.last_active = datetime.now()
    
    async def ban_user(self, user_id: int, reason: str = None):
        """Блокировка пользователя"""
        async with self.get_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                user.is_banned = True
    
    async def unban_user(self, user_id: int):
        """Разблокировка пользователя"""
        async with self.get_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                user.is_banned = False
    
    async def set_user_premium(self, user_id: int, days: int):
        """Установка Premium статуса"""
        async with self.get_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                user.is_premium = True
                user.premium_until = datetime.now() + timedelta(days=days)
    
    # === SIGNAL OPERATIONS ===
    
    async def save_signal(self, signal: Signal) -> int:
        """Сохранение сигнала"""
        async with self.get_session() as session:
            session.add(signal)
            session.flush()  # Для получения ID
            return signal.id
    
    async def get_signal(self, signal_id: int) -> Optional[Signal]:
        """Получение сигнала по ID"""
        async with self.get_session() as session:
            return session.query(Signal).filter(Signal.id == signal_id).first()
    
    async def update_signal_result(self, signal_id: int, result: str):
        """Обновление результата сигнала"""
        async with self.get_session() as session:
            signal = session.query(Signal).filter(Signal.id == signal_id).first()
            if signal:
                signal.result = result
                signal.status = 'closed'
                signal.closed_at = datetime.now()
                
                # Обновление статистики пользователя
                if result == 'win':
                    user = session.query(User).filter(User.user_id == signal.user_id).first()
                    if user:
                        user.successful_signals += 1
    
    async def close_signal(self, signal_id: int, result: str):
        """Закрытие сигнала"""
        await self.update_signal_result(signal_id, result)
    
    async def get_active_signals(self, limit: int = 50) -> List[Signal]:
        """Получение активных сигналов"""
        async with self.get_session() as session:
            return session.query(Signal).filter(
                Signal.status == 'active',
                or_(Signal.expires_at.is_(None), Signal.expires_at > datetime.now())
            ).order_by(Signal.created_at.desc()).limit(limit).all()
    
    async def get_user_recent_signals(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Получение последних сигналов пользователя"""
        async with self.get_session() as session:
            signals = session.query(Signal).filter(
                Signal.user_id == user_id
            ).order_by(Signal.created_at.desc()).limit(limit).all()
            
            return [signal.to_dict() for signal in signals]
    
    async def increment_user_signals_count(self, user_id: int):
        """Увеличение счетчика сигналов пользователя"""
        async with self.get_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                user.total_signals_received += 1
    
    async def get_user_daily_signals_count(self, user_id: int) -> int:
        """Получение количества сигналов пользователя за сегодня"""
        async with self.get_session() as session:
            today = datetime.now().date()
            count = session.query(Signal).filter(
                Signal.user_id == user_id,
                func.date(Signal.created_at) == today
            ).count()
            return count
    
    # === STATISTICS ===
    
    async def get_total_users_count(self) -> int:
        """Общее количество пользователей"""
        async with self.get_session() as session:
            return session.query(User).count()
    
    async def get_active_users_count(self, days: int = 7) -> int:
        """Количество активных пользователей"""
        async with self.get_session() as session:
            cutoff_date = datetime.now() - timedelta(days=days)
            return session.query(User).filter(User.last_active >= cutoff_date).count()
    
    async def get_premium_users_count(self) -> int:
        """Количество Premium пользователей"""
        async with self.get_session() as session:
            return session.query(User).filter(
                User.is_premium == True,
                or_(User.premium_until.is_(None), User.premium_until > datetime.now())
            ).count()
    
    async def get_new_users_count_today(self) -> int:
        """Количество новых пользователей сегодня"""
        async with self.get_session() as session:
            today = datetime.now().date()
            return session.query(User).filter(func.date(User.created_at) == today).count()
    
    async def get_total_signals_count(self) -> int:
        """Общее количество сигналов"""
        async with self.get_session() as session:
            return session.query(Signal).count()
    
    async def get_signals_count_today(self) -> int:
        """Количество сигналов сегодня"""
        async with self.get_session() as session:
            today = datetime.now().date()
            return session.query(Signal).filter(func.date(Signal.created_at) == today).count()
    
    async def get_average_signal_accuracy(self) -> float:
        """Средняя точность сигналов"""
        async with self.get_session() as session:
            total = session.query(Signal).filter(Signal.result.isnot(None)).count()
            if total == 0:
                return 0.0
            
            wins = session.query(Signal).filter(Signal.result == 'win').count()
            return (wins / total) * 100
    
    async def get_total_commission_earned(self) -> float:
        """Общая заработанная комиссия"""
        async with self.get_session() as session:
            result = session.query(func.sum(User.commission_earned)).scalar()
            return result or 0.0
    
    async def get_commission_this_month(self) -> float:
        """Комиссия за текущий месяц"""
        async with self.get_session() as session:
            start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            result = session.query(func.sum(Commission.commission_amount)).filter(
                Commission.created_at >= start_of_month,
                Commission.status == 'paid'
            ).scalar()
            return result or 0.0
    
    async def get_commission_today(self) -> float:
        """Комиссия за сегодня"""
        async with self.get_session() as session:
            today = datetime.now().date()
            result = session.query(func.sum(Commission.commission_amount)).filter(
                func.date(Commission.created_at) == today,
                Commission.status == 'paid'
            ).scalar()
            return result or 0.0
    
    async def get_total_trading_volume(self) -> float:
        """Общий торговый оборот"""
        async with self.get_session() as session:
            result = session.query(func.sum(Trade.amount)).scalar()
            return result or 0.0
    
    # === REFERRAL SYSTEM ===
    
    async def get_user_referrals(self, user_id: int) -> List[Dict]:
        """Получение рефералов пользователя"""
        async with self.get_session() as session:
            referrals = session.query(User).filter(User.referrer_id == user_id).all()
            return [{'user_id': r.user_id, 'username': r.username, 
                    'created_at': r.created_at, 'is_active': r.last_active > datetime.now() - timedelta(days=7)} 
                   for r in referrals]
    
    async def track_commission(self, referrer_id: int, referred_user_id: int, 
                             trade_volume: float, commission_rate: float) -> int:
        """Отслеживание комиссии"""
        async with self.get_session() as session:
            commission_amount = trade_volume * commission_rate
            
            # Создание записи комиссии
            commission = Commission(
                referrer_id=referrer_id,
                referred_user_id=referred_user_id,
                trade_volume=trade_volume,
                commission_rate=commission_rate,
                commission_amount=commission_amount,
                status='pending'
            )
            session.add(commission)
            
            # Обновление заработанной комиссии у реферера
            referrer = session.query(User).filter(User.user_id == referrer_id).first()
            if referrer:
                referrer.commission_earned += commission_amount
            
            session.flush()
            return commission.id
    
    # === ANALYTICS ===
    
    async def save_analytics(self, metric_type: str, metric_name: str, 
                           value: float = None, data: Dict = None):
        """Сохранение аналитических данных"""
        async with self.get_session() as session:
            analytics = Analytics(
                metric_type=metric_type,
                metric_name=metric_name,
                value=value,
                data=data
            )
            session.add(analytics)
    
    async def get_daily_user_activity(self, days: int) -> List[Dict]:
        """Получение ежедневной активности пользователей"""
        async with self.get_session() as session:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Генерируем данные по дням
            activity_data = []
            current_date = start_date
            
            while current_date <= end_date:
                active_count = session.query(User).filter(
                    func.date(User.last_active) == current_date
                ).count()
                
                new_count = session.query(User).filter(
                    func.date(User.created_at) == current_date
                ).count()
                
                activity_data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'active_users': active_count,
                    'new_users': new_count
                })
                current_date += timedelta(days=1)
            
            return activity_data
    
    async def get_daily_signals_activity(self, days: int) -> List[Dict]:
        """Получение ежедневной активности сигналов"""
        async with self.get_session() as session:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            signals_data = []
            current_date = start_date
            
            while current_date <= end_date:
                total_signals = session.query(Signal).filter(
                    func.date(Signal.created_at) == current_date
                ).count()
                
                successful_signals = session.query(Signal).filter(
                    func.date(Signal.created_at) == current_date,
                    Signal.result == 'win'
                ).count()
                
                signals_data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'total_signals': total_signals,
                    'successful_signals': successful_signals,
                    'accuracy': (successful_signals / total_signals * 100) if total_signals > 0 else 0
                })
                current_date += timedelta(days=1)
            
            return signals_data
    
    # === SYSTEM SETTINGS ===
    
    async def get_system_settings(self) -> Dict[str, Any]:
        """Получение системных настроек"""
        async with self.get_session() as session:
            settings = session.query(SystemSettings).all()
            return {s.key: s.value for s in settings}
    
    async def update_system_settings(self, settings: Dict[str, Any]):
        """Обновление системных настроек"""
        async with self.get_session() as session:
            for key, value in settings.items():
                setting = session.query(SystemSettings).filter(SystemSettings.key == key).first()
                if setting:
                    setting.value = str(value)
                    setting.updated_at = datetime.now()
                else:
                    new_setting = SystemSettings(key=key, value=str(value))
                    session.add(new_setting)
    
    # === NOTIFICATIONS ===
    
    async def create_notification(self, user_id: int, title: str, message: str, 
                                notification_type: str = 'system') -> int:
        """Создание уведомления"""
        async with self.get_session() as session:
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type
            )
            session.add(notification)
            session.flush()
            return notification.id
    
    async def mark_notification_as_sent(self, notification_id: int, telegram_message_id: int = None):
        """Отметка уведомления как отправленного"""
        async with self.get_session() as session:
            notification = session.query(Notification).filter(Notification.id == notification_id).first()
            if notification:
                notification.is_sent = True
                notification.sent_at = datetime.now()
                notification.telegram_message_id = telegram_message_id
    
    async def get_unsent_notifications(self, limit: int = 100) -> List[Notification]:
        """Получение неотправленных уведомлений"""
        async with self.get_session() as session:
            return session.query(Notification).filter(
                Notification.is_sent == False
            ).order_by(Notification.created_at.asc()).limit(limit).all()
    
    # === BROADCAST ===
    
    async def create_broadcast_task(self, message: str, target: str, created_by: str) -> int:
        """Создание задачи на рассылку"""
        async with self.get_session() as session:
            # Сохраняем как системную настройку для простоты
            task_data = {
                'message': message,
                'target': target,
                'created_by': created_by,
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            
            setting = SystemSettings(
                key=f"broadcast_task_{datetime.now().timestamp()}",
                value=json.dumps(task_data),
                description="Broadcast task"
            )
            session.add(setting)
            session.flush()
            return setting.id
    
    async def get_broadcast_history(self, limit: int = 20) -> List[Dict]:
        """Получение истории рассылок"""
        async with self.get_session() as session:
            broadcasts = session.query(SystemSettings).filter(
                SystemSettings.key.like('broadcast_task_%')
            ).order_by(SystemSettings.created_at.desc()).limit(limit).all()
            
            history = []
            for broadcast in broadcasts:
                try:
                    data = json.loads(broadcast.value)
                    history.append({
                        'id': broadcast.id,
                        'message': data.get('message', '')[:100] + '...',
                        'target': data.get('target', 'all'),
                        'created_by': data.get('created_by', 'unknown'),
                        'status': data.get('status', 'unknown'),
                        'created_at': broadcast.created_at
                    })
                except json.JSONDecodeError:
                    continue
            
            return history
    
    # === PAGINATION ===
    
    async def get_users_paginated(self, page: int = 1, per_page: int = 50, 
                                user_type: str = 'all', search: str = '') -> Dict:
        """Получение пользователей с пагинацией"""
        async with self.get_session() as session:
            query = session.query(User)
            
            # Фильтры
            if user_type == 'premium':
                query = query.filter(User.is_premium == True)
            elif user_type == 'regular':
                query = query.filter(User.is_premium == False)
            elif user_type == 'banned':
                query = query.filter(User.is_banned == True)
            
            if search:
                query = query.filter(
                    or_(
                        User.username.ilike(f'%{search}%'),
                        User.first_name.ilike(f'%{search}%'),
                        User.user_id.like(f'%{search}%')
                    )
                )
            
            total = query.count()
            users = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'users': [user.to_dict() for user in users],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
    
    async def get_signals_paginated(self, page: int = 1, per_page: int = 50, 
                                  filters: Dict = None) -> Dict:
        """Получение сигналов с пагинацией"""
        async with self.get_session() as session:
            query = session.query(Signal)
            
            if filters:
                if filters.get('symbol'):
                    query = query.filter(Signal.symbol.ilike(f"%{filters['symbol']}%"))
                if filters.get('signal_type'):
                    query = query.filter(Signal.signal_type == filters['signal_type'])
                if filters.get('status'):
                    query = query.filter(Signal.status == filters['status'])
                if filters.get('date_from'):
                    query = query.filter(Signal.created_at >= datetime.fromisoformat(filters['date_from']))
                if filters.get('date_to'):
                    query = query.filter(Signal.created_at <= datetime.fromisoformat(filters['date_to']))
            
            total = query.count()
            signals = query.order_by(Signal.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'signals': [signal.to_dict() for signal in signals],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
    
    # === ADVANCED ANALYTICS ===
    
    async def get_user_detailed_stats(self, user_id: int) -> Dict:
        """Получение детальной статистики пользователя"""
        async with self.get_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                return {}
            
            # Статистика сигналов
            total_signals = session.query(Signal).filter(Signal.user_id == user_id).count()
            successful_signals = session.query(Signal).filter(
                Signal.user_id == user_id, Signal.result == 'win'
            ).count()
            
            # Статистика рефералов
            active_referrals = session.query(User).filter(
                User.referrer_id == user_id,
                User.last_active >= datetime.now() - timedelta(days=30)
            ).count()
            
            # Комиссии за последний месяц
            monthly_commission = session.query(func.sum(Commission.commission_amount)).filter(
                Commission.referrer_id == user_id,
                Commission.created_at >= datetime.now() - timedelta(days=30)
            ).scalar() or 0
            
            return {
                'user_info': user.to_dict(),
                'signals_stats': {
                    'total': total_signals,
                    'successful': successful_signals,
                    'success_rate': (successful_signals / total_signals * 100) if total_signals > 0 else 0
                },
                'referral_stats': {
                    'total_referrals': user.referrals_count,
                    'active_referrals': active_referrals,
                    'total_commission': user.commission_earned,
                    'monthly_commission': monthly_commission
                }
            }
    
    async def get_signals_statistics(self, filters: Dict = None) -> Dict:
        """Получение статистики сигналов"""
        async with self.get_session() as session:
            query = session.query(Signal)
            
            if filters:
                # Применяем фильтры как в get_signals_paginated
                pass
            
            total_signals = query.count()
            successful = query.filter(Signal.result == 'win').count()
            failed = query.filter(Signal.result == 'loss').count()
            pending = query.filter(Signal.result.is_(None)).count()
            
            # Статистика по символам
            symbol_stats = session.query(
                Signal.symbol,
                func.count(Signal.id).label('count'),
                func.avg(Signal.confidence).label('avg_confidence')
            ).group_by(Signal.symbol).order_by(func.count(Signal.id).desc()).limit(10).all()
            
            return {
                'total': total_signals,
                'successful': successful,
                'failed': failed,
                'pending': pending,
                'success_rate': (successful / (successful + failed) * 100) if (successful + failed) > 0 else 0,
                'top_symbols': [
                    {'symbol': s.symbol, 'count': s.count, 'avg_confidence': float(s.avg_confidence or 0)}
                    for s in symbol_stats
                ]
            }
    
    async def get_analytics_general_stats(self, period_days: int) -> Dict:
        """Получение общей аналитики"""
        async with self.get_session() as session:
            start_date = datetime.now() - timedelta(days=period_days)
            
            # Пользователи
            total_users = session.query(User).count()
            new_users = session.query(User).filter(User.created_at >= start_date).count()
            active_users = session.query(User).filter(User.last_active >= start_date).count()
            
            # Сигналы
            total_signals = session.query(Signal).filter(Signal.created_at >= start_date).count()
            successful_signals = session.query(Signal).filter(
                Signal.created_at >= start_date, Signal.result == 'win'
            ).count()
            
            # Финансы
            total_volume = session.query(func.sum(Trade.amount)).filter(
                Trade.created_at >= start_date
            ).scalar() or 0
            
            commission_earned = session.query(func.sum(Commission.commission_amount)).filter(
                Commission.created_at >= start_date
            ).scalar() or 0
            
            return {
                'period_days': period_days,
                'users': {
                    'total': total_users,
                    'new': new_users,
                    'active': active_users
                },
                'signals': {
                    'total': total_signals,
                    'successful': successful_signals,
                    'accuracy': (successful_signals / total_signals * 100) if total_signals > 0 else 0
                },
                'finance': {
                    'total_volume': total_volume,
                    'commission_earned': commission_earned
                }
            }
    
    async def get_conversion_analytics(self, period_days: int) -> List[Dict]:
        """Аналитика конверсии"""
        async with self.get_session() as session:
            # Упрощенная конверсионная воронка
            start_date = datetime.now() - timedelta(days=period_days)
            
            registered = session.query(User).filter(User.created_at >= start_date).count()
            got_first_signal = session.query(func.count(func.distinct(Signal.user_id))).filter(
                Signal.created_at >= start_date
            ).scalar() or 0
            
            premium_users = session.query(User).filter(
                User.created_at >= start_date,
                User.is_premium == True
            ).count()
            
            return [
                {'step': 'Регистрация', 'count': registered, 'conversion': 100},
                {'step': 'Первый сигнал', 'count': got_first_signal, 
                 'conversion': (got_first_signal / registered * 100) if registered > 0 else 0},
                {'step': 'Premium', 'count': premium_users,
                 'conversion': (premium_users / registered * 100) if registered > 0 else 0}
            ]
    
    async def get_top_trading_symbols(self, period_days: int) -> List[Dict]:
        """Топ торговых символов"""
        async with self.get_session() as session:
            start_date = datetime.now() - timedelta(days=period_days)
            
            symbols = session.query(
                Signal.symbol,
                func.count(Signal.id).label('total_signals'),
                func.count(case([(Signal.result == 'win', 1)])).label('successful'),
                func.avg(Signal.confidence).label('avg_confidence')
            ).filter(
                Signal.created_at >= start_date
            ).group_by(Signal.symbol).order_by(
                func.count(Signal.id).desc()
            ).limit(10).all()
            
            return [
                {
                    'symbol': s.symbol,
                    'total_signals': s.total_signals,
                    'successful': s.successful,
                    'success_rate': (s.successful / s.total_signals * 100) if s.total_signals > 0 else 0,
                    'avg_confidence': float(s.avg_confidence or 0)
                } for s in symbols
            ]
    
    async def get_users_geo_distribution(self) -> List[Dict]:
        """Географическое распределение пользователей (заглушка)"""
        # В реальном проекте здесь бы была интеграция с GeoIP
        return [
            {'country': 'Russia', 'count': 150, 'percentage': 45.5},
            {'country': 'Ukraine', 'count': 80, 'percentage': 24.2},
            {'country': 'Kazakhstan', 'count': 50, 'percentage': 15.2},
            {'country': 'Belarus', 'count': 30, 'percentage': 9.1},
            {'country': 'Other', 'count': 20, 'percentage': 6.0}
        ]
    
    async def get_referral_program_stats(self) -> Dict:
        """Статистика реферальной программы"""
        async with self.get_session() as session:
            # Общая статистика
            total_referrers = session.query(User).filter(User.referrals_count > 0).count()
            total_referrals = session.query(User).filter(User.referrer_id.isnot(None)).count()
            total_commission = session.query(func.sum(User.commission_earned)).scalar() or 0
            
            # Топ рефереры
            top_referrers = session.query(
                User.user_id, User.username, User.first_name,
                User.referrals_count, User.commission_earned
            ).filter(
                User.referrals_count > 0
            ).order_by(User.commission_earned.desc()).limit(10).all()
            
            return {
                'total_referrers': total_referrers,
                'total_referrals': total_referrals,
                'total_commission': total_commission,
                'avg_referrals_per_user': total_referrals / total_referrers if total_referrers > 0 else 0,
                'top_referrers': [
                    {
                        'user_id': r.user_id,
                        'username': r.username or 'Anonymous',
                        'first_name': r.first_name or '',
                        'referrals_count': r.referrals_count,
                        'commission_earned': r.commission_earned
                    } for r in top_referrers
                ]
            }
    
    # === DATA EXPORT ===
    
    async def get_all_users_for_export(self) -> List[Dict]:
        """Получение всех пользователей для экспорта"""
        async with self.get_session() as session:
            users = session.query(User).all()
            return [
                {
                    'user_id': user.user_id,
                    'username': user.username or '',
                    'first_name': user.first_name or '',
                    'is_premium': user.is_premium,
                    'referrals_count': user.referrals_count,
                    'commission_earned': user.commission_earned,
                    'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
                    'last_active': user.last_active.strftime('%Y-%m-%d %H:%M:%S') if user.last_active else ''
                } for user in users
            ]
    
    # === MAINTENANCE ===
    
    async def cleanup_old_data(self, days: int = 90):
        """Очистка старых данных"""
        async with self.get_session() as session:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Удаление старых сигналов
            old_signals = session.query(Signal).filter(
                Signal.created_at < cutoff_date,
                Signal.status == 'closed'
            ).count()
            
            session.query(Signal).filter(
                Signal.created_at < cutoff_date,
                Signal.status == 'closed'
            ).delete()
            
            # Удаление старых уведомлений
            old_notifications = session.query(Notification).filter(
                Notification.created_at < cutoff_date,
                Notification.is_sent == True
            ).count()
            
            session.query(Notification).filter(
                Notification.created_at < cutoff_date,
                Notification.is_sent == True
            ).delete()
            
            logger.info(f"Удалено {old_signals} старых сигналов и {old_notifications} уведомлений")
    
    async def update_signal_accuracy_stats(self):
        """Обновление статистики точности сигналов"""
        async with self.get_session() as session:
            # Обновляем общую статистику
            total_closed = session.query(Signal).filter(Signal.result.isnot(None)).count()
            successful = session.query(Signal).filter(Signal.result == 'win').count()
            
            accuracy = (successful / total_closed * 100) if total_closed > 0 else 0
            
            # Сохраняем в аналитику
            await self.save_analytics('signals', 'overall_accuracy', accuracy, {
                'total_signals': total_closed,
                'successful_signals': successful,
                'updated_at': datetime.now().isoformat()
            })