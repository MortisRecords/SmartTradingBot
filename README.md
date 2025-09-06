# 🤖 Smart Trading Bot

> **Профессиональный торговый бот с Telegram интерфейсом, Smart Money анализом и партнерской программой**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](docker-compose.yml)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://telegram.org)

## 🎯 Описание проекта

Smart Trading Bot — это комплексная система для анализа финансовых рынков с использованием алгоритмов Smart Money, Telegram-ботом для пользователей, веб-панелью администратора и интегрированной партнерской программой.

### 🔥 Ключевые особенности

- **🧠 Smart Money анализ** — продвинутые алгоритмы определения движений крупного капитала
- **🤖 Telegram бот** — интуитивный интерфейс для получения торговых сигналов
- **💰 Партнерская программа** — интеграция с Binarium и PocketOption
- **📊 Веб-панель** — админ интерфейс с детальной аналитикой
- **🔄 Реферальная система** — автоматическое начисление комиссий
- **📈 Premium подписки** — монетизация через VIP функции

## 📦 Структура проекта

```
smart_trading_bot/
├── 📄 main.py                         # Точка входа в приложение
├── 📄 config.py                       # Конфигурация и настройки
├── 📄 requirements.txt                # Python зависимости
├── 📄 .env.example                    # Пример переменных окружения
├── 📄 docker-compose.yml              # Docker конфигурация
├── 📄 Dockerfile                      # Docker образ
│
├── bot/                               # 🤖 Telegram Bot
│   ├── handlers/                      # Обработчики команд
│   │   ├── start.py                   # Команды /start, /help
│   │   ├── signals.py                 # Торговые сигналы
│   │   ├── referrals.py               # Реферальная система
│   │   └── admin.py                   # Админ команды
│   ├── keyboards/                     # Клавиатуры
│   │   └── inline.py                  # Inline клавиатуры
│   └── utils/
│       └── texts.py                   # Текстовые сообщения
│
├── database/                          # 💾 База данных
│   ├── models.py                      # SQLAlchemy модели
│   └── manager.py                     # CRUD операции
│
├── analytics/                         # 📈 Анализ рынка
│   └── smart_money.py                 # Smart Money алгоритмы
│
├── partners/                          # 🤝 Партнерские программы
│   ├── binarium.py                    # Интеграция с Binarium
│   └── pocket_option.py               # Интеграция с PocketOption
│
├── web_panel/                         # 🌐 Веб-панель
│   ├── app.py                         # Flask приложение
│   └── templates/                     # HTML шаблоны
│
└── scripts/                           # 🛠️ Утилиты
    ├── deploy.sh                      # Автоматический деплой
    └── backup.sh                      # Система бэкапов
```

## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/MortisRecords/SmartTradingBot.git
cd SmartTradingBot
```

### 2. Настройка окружения

```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt
```

### 3. Конфигурация

```bash
# Копирование конфигурации
cp .env.example .env

# Редактирование настроек
nano .env
```

### 4. Настройка переменных окружения

```env
# Telegram Bot
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_IDS=123456789,987654321

# База данных
DATABASE_URL=sqlite:///bot.db
# Или PostgreSQL: postgresql://user:password@localhost/dbname

# Smart Money API (опционально)
SMART_MONEY_API_KEY=your_api_key

# Партнерские программы
BINARIUM_PARTNER_ID=your_partner_id
POCKET_OPTION_PARTNER_ID=your_partner_id

# Веб-панель
SECRET_KEY=your_secret_key_for_flask
WEB_PANEL_PORT=5000

# Уведомления
WEBHOOK_URL=https://your-domain.com/webhook
```

### 5. Запуск приложения

#### Обычный запуск:
```bash
python main.py
```

#### Запуск с Docker:
```bash
docker-compose up -d
```

#### Автоматический деплой:
```bash
chmod +x scripts/deploy.sh
sudo ./scripts/deploy.sh install
```

## 🧠 Smart Money анализ

Система включает продвинутые алгоритмы анализа поведения крупного капитала:

### Основные индикаторы:

- **📊 Smart Money Index (SMI)** — сводный индекс активности институционалов
- **💹 Volume Profile** — анализ объемов по ценовым уровням  
- **🔄 Money Flow Index** — индекс денежного потока
- **📈 Accumulation/Distribution** — фазы накопления и распределения
- **🎯 Support/Resistance** — автоматическое определение уровней

### Алгоритмы:

```python
# Пример использования Smart Money анализа
from analytics.smart_money import SmartMoneyAnalyzer

analyzer = SmartMoneyAnalyzer()
analysis = analyzer.analyze_symbol("BTCUSDT")

print(f"Smart Money Index: {analysis.smi_score}")
print(f"Trend Direction: {analysis.trend}")
print(f"Key Levels: {analysis.support_resistance}")
```

## 🤖 Telegram Bot

### Доступные команды:

- `/start` — Запуск бота и регистрация
- `/signal` — Получение торгового сигнала
- `/stats` — Статистика пользователя
- `/referral` — Реферальная программа
- `/premium` — Premium подписка
- `/help` — Справка по командам

### Функциональность:

- **🎯 Торговые сигналы** — на основе Smart Money анализа
- **📊 Персональная статистика** — история и результаты
- **💰 Реферальная система** — заработок с рефералов
- **🔔 Уведомления** — важные рыночные события
- **🎛️ Настройки** — персонализация опыта

## 💰 Монетизация

### Партнерские программы:

#### Binarium:
- Комиссия: до 60% от депозитов
- Автоматические партнерские ссылки
- Отслеживание конверсий

#### PocketOption:
- Комиссия: до 50% от оборота
- Реальная статистика доходности
- Мгновенные выплаты

### Premium подписки:

| План | Цена | Особенности |
|------|------|-------------|
| **Free** | $0/мес | 3 сигнала в день, базовый анализ |
| **Premium** | $29.99/мес | Неограниченные сигналы, детальный анализ |
| **VIP** | $99.99/мес | Персональный аналитик, эксклюзивные стратегии |

### Реферальная система:
- **2% комиссия** от всех доходов рефералов
- **Многоуровневая структура** (до 3 уровней)
- **Еженедельные выплаты** автоматически

## 🌐 Веб-панель администратора

Доступна по адресу: `http://localhost:5000`

### Возможности:
- **👥 Управление пользователями** — статистика, блокировка, настройки
- **📊 Аналитика в реальном времени** — графики и метрики
- **📤 Система рассылок** — массовые уведомления
- **💳 Управление подписками** — Premium и VIP планы
- **🔧 Настройки бота** — конфигурация без перезапуска
- **📈 Финансовые отчеты** — доходы, комиссии, выплаты

## 📊 API Documentation

### Основные эндпоинты:

```bash
# Получение сигнала
GET /api/v1/signal/{symbol}

# Статистика пользователя
GET /api/v1/user/{user_id}/stats

# Создание реферальной ссылки
POST /api/v1/referral/create

# Информация о подписке
GET /api/v1/subscription/{user_id}
```

### Webhook для уведомлений:

```bash
POST /webhook/signal
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "direction": "BUY",
  "confidence": 85,
  "entry_price": 45000,
  "take_profit": 46500,
  "stop_loss": 44000
}
```

## 🛠️ Разработка

### Установка для разработки:

```bash
# Клонирование
git clone https://github.com/MortisRecords/SmartTradingBot.git
cd SmartTradingBot

# Установка в режиме разработки
pip install -e .
pip install -r requirements-dev.txt

# Запуск тестов
pytest tests/

# Форматирование кода
black .
flake8 .
```

### Структура базы данных:

```sql
-- Основные таблицы
users          -- Пользователи бота
signals        -- История сигналов  
subscriptions  -- Подписки пользователей
referrals      -- Реферальные связи
transactions   -- Финансовые операции
```

## 🚀 Деплой на продакшн

### Автоматический деплой:

```bash
# Полная установка с настройкой сервера
sudo ./scripts/deploy.sh install

# Обновление приложения
sudo ./scripts/deploy.sh update

# Создание бэкапа
sudo ./scripts/backup.sh create
```

### Что включает автодеплой:
- ✅ Установка Docker и Docker Compose
- ✅ Настройка Nginx с SSL сертификатами
- ✅ Конфигурация PostgreSQL
- ✅ Настройка мониторинга (Grafana + Prometheus)
- ✅ Автоматические бэкапы
- ✅ Логирование и ротация логов
- ✅ Файрвол и базовая безопасность

### Системные требования:
- **ОС**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM**: минимум 2GB, рекомендуется 4GB+
- **Диск**: минимум 20GB SSD
- **CPU**: 2+ ядра
- **Интернет**: стабильное соединение

## 📈 Мониторинг и аналитика

### Grafana Dashboard:
- 📊 Метрики пользователей в реальном времени
- 🎯 Эффективность торговых сигналов  
- 💰 Доходность партнерских программ
- 🔄 Статистика конверсии и удержания

### Логирование:
```
logs/
├── bot.log           # Основные логи бота
├── trades.log        # История сигналов
├── errors.log        # Ошибки и исключения
└── analytics.log     # Аналитические данные
```

## 🔒 Безопасность

- **🔐 Шифрование данных** — все sensitive данные зашифрованы
- **🛡️ Rate limiting** — защита от спама и DDoS
- **🔑 JWT токены** — безопасная авторизация в API
- **📝 Аудит логи** — полное логирование действий
- **🚫 Blacklist система** — защита от мошенников

## 🤝 Contributing

1. Fork проекта
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add some AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

### Стиль кодирования:
- Используйте Black для форматирования
- Следуйте PEP 8
- Добавляйте docstrings к функциям
- Покрывайте код тестами

## 📋 TODO / Roadmap

### Версия 2.0:
- [ ] 🌍 Поддержка форекс рынков
- [ ] 🤖 Machine Learning модели
- [ ] 📱 Мобильное приложение
- [ ] 🔄 Copy-trading функциональность
- [ ] 🌐 Мультиязычность (EN, RU, ES, ZH)

### Версия 2.1:
- [ ] 🎮 Gamification системы
- [ ] 👥 Социальные функции
- [ ] 📚 Обучающие материалы
- [ ] 💎 NFT интеграция

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## ⚠️ Отказ от ответственности

**ВАЖНО**: Торговля на финансовых рынках связана с высоким риском потери средств. Данный бот предоставляется только в образовательных целях и не является финансовой консультацией.

- 📊 Прошлые результаты не гарантируют будущую прибыль
- 💰 Не инвестируйте больше, чем можете позволить себе потерять
- 🧠 Всегда проводите собственный анализ перед принятием торговых решений
- ⚖️ Разработчики не несут ответственности за торговые убытки

## 📞 Поддержка

- **💬 Telegram**: [@your_support_bot](https://t.me/your_support_bot)
- **📧 Email**: support@smarttradingbot.com
- **🐛 Issues**: [GitHub Issues](https://github.com/MortisRecords/SmartTradingBot/issues)
- **📖 Docs**: [Wiki](https://github.com/MortisRecords/SmartTradingBot/wiki)

## 📊 Статистика проекта

![GitHub stars](https://img.shields.io/github/stars/MortisRecords/SmartTradingBot?style=social)
![GitHub forks](https://img.shields.io/github/forks/MortisRecords/SmartTradingBot?style=social)
![GitHub issues](https://img.shields.io/github/issues/MortisRecords/SmartTradingBot)
![GitHub last commit](https://img.shields.io/github/last-commit/MortisRecords/SmartTradingBot)

---

## 🎉 Готов к запуску!

Проект содержит все необходимые компоненты для коммерческого использования. Просто следуйте инструкциям по установке и начинайте зарабатывать!

**💎 Smart Trading Bot — ваш путь к автоматизированному трейдингу! 🚀**
