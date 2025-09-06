"""
Web Admin Panel for Smart Trading Bot
Flask приложение для администрирования бота
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import asyncio
import json
import os
from functools import wraps
import logging

from database.manager import DatabaseManager
from config import config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = config.WEB_PANEL_SECRET_KEY

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class AdminUser(UserMixin):
    def __init__(self, username):
        self.id = username
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    if user_id == config.WEB_PANEL_USERNAME:
        return AdminUser(user_id)
    return None

# Database connection
db_manager = None

async def init_db():
    """Инициализация базы данных"""
    global db_manager
    db_manager = DatabaseManager(config.DATABASE_URL)
    await db_manager.initialize()

def async_route(f):
    """Декоратор для асинхронных маршрутов"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница авторизации"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if (username == config.WEB_PANEL_USERNAME and 
            password == config.WEB_PANEL_PASSWORD):
            user = AdminUser(username)
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Неверные учетные данные', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Выход"""
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
@async_route
async def dashboard():
    """Главная панель"""
    try:
        # Статистика пользователей
        total_users = await db_manager.get_total_users_count()
        active_users = await db_manager.get_active_users_count(days=7)
        premium_users = await db_manager.get_premium_users_count()
        
        # Статистика сигналов
        total_signals = await db_manager.get_total_signals_count()
        signals_today = await db_manager.get_signals_count_today()
        avg_accuracy = await db_manager.get_average_signal_accuracy()
        
        # Финансовая статистика
        total_commission = await db_manager.get_total_commission_earned()
        commission_this_month = await db_manager.get_commission_this_month()
        total_volume = await db_manager.get_total_trading_volume()
        
        # Графики активности за последние 30 дней
        user_activity = await db_manager.get_daily_user_activity(30)
        signals_activity = await db_manager.get_daily_signals_activity(30)
        
        stats = {
            'users': {
                'total': total_users,
                'active': active_users,
                'premium': premium_users,
                'conversion_rate': (premium_users / total_users * 100) if total_users > 0 else 0
            },
            'signals': {
                'total': total_signals,
                'today': signals_today,
                'accuracy': avg_accuracy
            },
            'finance': {
                'total_commission': total_commission,
                'monthly_commission': commission_this_month,
                'total_volume': total_volume
            },
            'charts': {
                'user_activity': user_activity,
                'signals_activity': signals_activity
            }
        }
        
        return render_template('dashboard.html', stats=stats)
        
    except Exception as e:
        logger.error(f"Ошибка загрузки панели: {e}")
        flash('Ошибка загрузки данных', 'error')
        return render_template('dashboard.html', stats={})

@app.route('/users')
@login_required
@async_route
async def users():
    """Управление пользователями"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        
        # Фильтры
        user_type = request.args.get('type', 'all')  # all, premium, regular, banned
        search = request.args.get('search', '')
        
        users_data = await db_manager.get_users_paginated(
            page=page,
            per_page=per_page,
            user_type=user_type,
            search=search
        )
        
        return render_template('users.html', 
                             users=users_data['users'],
                             pagination=users_data['pagination'],
                             filters={'type': user_type, 'search': search})
        
    except Exception as e:
        logger.error(f"Ошибка загрузки пользователей: {e}")
        flash('Ошибка загрузки пользователей', 'error')
        return render_template('users.html', users=[], pagination={})

@app.route('/users/<int:user_id>')
@login_required
@async_route
async def user_detail(user_id):
    """Детали пользователя"""
    try:
        user = await db_manager.get_user_by_id(user_id)
        if not user:
            flash('Пользователь не найден', 'error')
            return redirect(url_for('users'))
        
        # Статистика пользователя
        user_stats = await db_manager.get_user_detailed_stats(user_id)
        
        # Последние сигналы
        recent_signals = await db_manager.get_user_recent_signals(user_id, limit=20)
        
        # Рефералы
        referrals = await db_manager.get_user_referrals(user_id)
        
        return render_template('user_detail.html',
                             user=user,
                             stats=user_stats,
                             signals=recent_signals,
                             referrals=referrals)
        
    except Exception as e:
        logger.error(f"Ошибка загрузки пользователя {user_id}: {e}")
        flash('Ошибка загрузки данных пользователя', 'error')
        return redirect(url_for('users'))

@app.route('/signals')
@login_required
@async_route
async def signals():
    """Управление сигналами"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        
        # Фильтры
        symbol = request.args.get('symbol', '')
        signal_type = request.args.get('type', '')
        status = request.args.get('status', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        filters = {
            'symbol': symbol,
            'signal_type': signal_type,
            'status': status,
            'date_from': date_from,
            'date_to': date_to
        }
        
        signals_data = await db_manager.get_signals_paginated(
            page=page,
            per_page=per_page,
            filters=filters
        )
        
        # Статистика сигналов
        signals_stats = await db_manager.get_signals_statistics(filters)
        
        return render_template('signals.html',
                             signals=signals_data['signals'],
                             pagination=signals_data['pagination'],
                             filters=filters,
                             stats=signals_stats)
        
    except Exception as e:
        logger.error(f"Ошибка загрузки сигналов: {e}")
        flash('Ошибка загрузки сигналов', 'error')
        return render_template('signals.html', signals=[], pagination={})

@app.route('/analytics')
@login_required
@async_route
async def analytics():
    """Аналитика и отчеты"""
    try:
        # Выбор периода
        period = request.args.get('period', '30')  # дни
        
        # Общая статистика
        general_stats = await db_manager.get_analytics_general_stats(int(period))
        
        # График конверсии
        conversion_data = await db_manager.get_conversion_analytics(int(period))
        
        # Топ символы
        top_symbols = await db_manager.get_top_trading_symbols(int(period))
        
        # Распределение по странам (если доступно)
        geo_data = await db_manager.get_users_geo_distribution()
        
        # Анализ рефералов
        referral_stats = await db_manager.get_referral_program_stats()
        
        analytics_data = {
            'general': general_stats,
            'conversion': conversion_data,
            'top_symbols': top_symbols,
            'geo_data': geo_data,
            'referrals': referral_stats,
            'period': period
        }
        
        return render_template('analytics.html', data=analytics_data)
        
    except Exception as e:
        logger.error(f"Ошибка загрузки аналитики: {e}")
        flash('Ошибка загрузки аналитики', 'error')
        return render_template('analytics.html', data={})

@app.route('/broadcast', methods=['GET', 'POST'])
@login_required
async def broadcast():
    """Рассылка сообщений"""
    if request.method == 'POST':
        try:
            message = request.form['message']
            target = request.form['target']  # all, premium, active
            
            # Здесь должна быть логика отправки сообщений через бота
            # Пока что просто сохраняем задачу в БД
            await db_manager.create_broadcast_task(
                message=message,
                target=target,
                created_by=current_user.username
            )
            
            flash('Рассылка запущена', 'success')
            return redirect(url_for('broadcast'))
            
        except Exception as e:
            logger.error(f"Ошибка создания рассылки: {e}")
            flash('Ошибка создания рассылки', 'error')
    
    # Получение истории рассылок
    try:
        broadcast_history = await db_manager.get_broadcast_history(limit=20)
        return render_template('broadcast.html', history=broadcast_history)
    except Exception as e:
        logger.error(f"Ошибка загрузки истории рассылок: {e}")
        return render_template('broadcast.html', history=[])

@app.route('/settings', methods=['GET', 'POST'])
@login_required
@async_route
async def settings():
    """Настройки системы"""
    if request.method == 'POST':
        try:
            settings_data = request.get_json()
            await db_manager.update_system_settings(settings_data)
            return jsonify({'status': 'success', 'message': 'Настройки сохранены'})
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек: {e}")
            return jsonify({'status': 'error', 'message': 'Ошибка сохранения настроек'})
    
    try:
        current_settings = await db_manager.get_system_settings()
        return render_template('settings.html', settings=current_settings)
    except Exception as e:
        logger.error(f"Ошибка загрузки настроек: {e}")
        return render_template('settings.html', settings={})

# API endpoints
@app.route('/api/stats/summary')
@login_required
@async_route
async def api_stats_summary():
    """API получения краткой статистики"""
    try:
        stats = {
            'users_today': await db_manager.get_new_users_count_today(),
            'signals_today': await db_manager.get_signals_count_today(),
            'commission_today': await db_manager.get_commission_today(),
            'active_users': await db_manager.get_active_users_count(1),
        }
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Ошибка API статистики: {e}")
        return jsonify({'error': 'Ошибка получения данных'}), 500

@app.route('/api/users/<int:user_id>/ban', methods=['POST'])
@login_required
@async_route
async def api_ban_user(user_id):
    """API блокировки пользователя"""
    try:
        reason = request.json.get('reason', 'Административная блокировка')
        await db_manager.ban_user(user_id, reason)
        return jsonify({'status': 'success', 'message': 'Пользователь заблокирован'})
    except Exception as e:
        logger.error(f"Ошибка блокировки пользователя {user_id}: {e}")
        return jsonify({'status': 'error', 'message': 'Ошибка блокировки'}), 500

@app.route('/api/users/<int:user_id>/unban', methods=['POST'])
@login_required
@async_route
async def api_unban_user(user_id):
    """API разблокировки пользователя"""
    try:
        await db_manager.unban_user(user_id)
        return jsonify({'status': 'success', 'message': 'Пользователь разблокирован'})
    except Exception as e:
        logger.error(f"Ошибка разблокировки пользователя {user_id}: {e}")
        return jsonify({'status': 'error', 'message': 'Ошибка разблокировки'}), 500

@app.route('/api/users/<int:user_id>/premium', methods=['POST'])
@login_required
@async_route
async def api_toggle_premium(user_id):
    """API управления премиум статусом"""
    try:
        days = request.json.get('days', 30)
        await db_manager.set_user_premium(user_id, days)
        return jsonify({'status': 'success', 'message': f'Premium статус установлен на {days} дней'})
    except Exception as e:
        logger.error(f"Ошибка установки премиум {user_id}: {e}")
        return jsonify({'status': 'error', 'message': 'Ошибка установки премиум'}), 500

@app.route('/api/signals/<int:signal_id>/close', methods=['POST'])
@login_required
@async_route
async def api_close_signal(signal_id):
    """API закрытия сигнала"""
    try:
        result = request.json.get('result', 'manual_close')
        await db_manager.close_signal(signal_id, result)
        return jsonify({'status': 'success', 'message': 'Сигнал закрыт'})
    except Exception as e:
        logger.error(f"Ошибка закрытия сигнала {signal_id}: {e}")
        return jsonify({'status': 'error', 'message': 'Ошибка закрытия сигнала'}), 500

@app.route('/api/chart/users')
@login_required
@async_route
async def api_chart_users():
    """API данных графика пользователей"""
    try:
        days = request.args.get('days', 30, type=int)
        data = await db_manager.get_users_chart_data(days)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Ошибка получения данных графика: {e}")
        return jsonify({'error': 'Ошибка получения данных'}), 500

@app.route('/api/chart/signals')
@login_required
@async_route
async def api_chart_signals():
    """API данных графика сигналов"""
    try:
        days = request.args.get('days', 30, type=int)
        data = await db_manager.get_signals_chart_data(days)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Ошибка получения данных графика сигналов: {e}")
        return jsonify({'error': 'Ошибка получения данных'}), 500

@app.route('/api/export/users')
@login_required
@async_route
async def api_export_users():
    """API экспорта пользователей в CSV"""
    try:
        import csv
        from io import StringIO
        
        users = await db_manager.get_all_users_for_export()
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow([
            'ID', 'Username', 'First Name', 'Premium', 'Referrals Count',
            'Commission Earned', 'Created At', 'Last Active'
        ])
        
        # Данные
        for user in users:
            writer.writerow([
                user['user_id'], user['username'], user['first_name'],
                'Yes' if user['is_premium'] else 'No', user['referrals_count'],
                user['commission_earned'], user['created_at'], user['last_active']
            ])
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=users_export.csv'}
        )
        
    except Exception as e:
        logger.error(f"Ошибка экспорта пользователей: {e}")
        return jsonify({'error': 'Ошибка экспорта'}), 500

# Обработчики ошибок
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         error_code=404, 
                         error_message='Страница не найдена'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html',
                         error_code=500,
                         error_message='Внутренняя ошибка сервера'), 500

@app.errorhandler(403)
def forbidden(error):
    return render_template('error.html',
                         error_code=403,
                         error_message='Доступ запрещен'), 403

# Контекстные процессоры
@app.context_processor
def inject_now():
    """Добавление текущего времени в контекст шаблонов"""
    return {'now': datetime.now()}

@app.context_processor
def inject_config():
    """Добавление конфигурации в контекст шаблонов"""
    return {'config': config}

if __name__ == '__main__':
    # Инициализация базы данных при запуске
    asyncio.run(init_db())
    
    # Запуск приложения
    app.run(
        host=config.WEB_PANEL_HOST,
        port=config.WEB_PANEL_PORT,
        debug=True
    )