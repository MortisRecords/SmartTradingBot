#!/bin/bash

# Smart Trading Bot Deployment Script
# Скрипт для деплоя бота на VPS

set -e  # Останавливаться при ошибках

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Логирование
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Конфигурация
PROJECT_NAME="smart_trading_bot"
DEPLOY_DIR="/opt/$PROJECT_NAME"
BACKUP_DIR="/opt/backups/$PROJECT_NAME"
SERVICE_NAME="smart-trading-bot"
WEB_SERVICE_NAME="smart-trading-web"

# Проверка прав root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Этот скрипт должен быть запущен с правами root"
        exit 1
    fi
}

# Установка зависимостей
install_dependencies() {
    log_info "Установка системных зависимостей..."
    
    # Обновление пакетов
    apt update && apt upgrade -y
    
    # Установка необходимых пакетов
    apt install -y \
        docker.io \
        docker-compose \
        nginx \
        certbot \
        python3-certbot-nginx \
        git \
        curl \
        wget \
        htop \
        unzip \
        cron \
        logrotate
    
    # Запуск Docker
    systemctl start docker
    systemctl enable docker
    
    # Добавление пользователя в группу docker
    usermod -aG docker $SUDO_USER
    
    log_success "Системные зависимости установлены"
}

# Создание директорий проекта
create_directories() {
    log_info "Создание директорий проекта..."
    
    mkdir -p $DEPLOY_DIR
    mkdir -p $BACKUP_DIR
    mkdir -p $DEPLOY_DIR/logs
    mkdir -p $DEPLOY_DIR/data
    mkdir -p $DEPLOY_DIR/backups
    mkdir -p /etc/nginx/sites-available
    mkdir -p /etc/nginx/sites-enabled
    
    log_success "Директории созданы"
}

# Клонирование или обновление репозитория
setup_repository() {
    log_info "Настройка репозитория..."
    
    if [ -d "$DEPLOY_DIR/.git" ]; then
        log_info "Обновление существующего репозитория..."
        cd $DEPLOY_DIR
        git stash
        git pull origin main
        git stash pop || true
    else
        log_info "Клонирование репозитория..."
        git clone https://github.com/your-username/smart-trading-bot.git $DEPLOY_DIR
        cd $DEPLOY_DIR
    fi
    
    log_success "Репозиторий настроен"
}

# Настройка переменных окружения
setup_environment() {
    log_info "Настройка переменных окружения..."
    
    if [ ! -f "$DEPLOY_DIR/.env" ]; then
        log_info "Создание файла .env..."
        cp $DEPLOY_DIR/.env.example $DEPLOY_DIR/.env
        
        # Генерация случайных паролей
        POSTGRES_PASSWORD=$(openssl rand -base64 32)
        REDIS_PASSWORD=$(openssl rand -base64 32)
        WEB_PANEL_SECRET=$(openssl rand -base64 32)
        API_SECRET=$(openssl rand -base64 32)
        
        # Замена в .env файле
        sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" $DEPLOY_DIR/.env
        sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASSWORD/" $DEPLOY_DIR/.env
        sed -i "s/WEB_PANEL_SECRET_KEY=.*/WEB_PANEL_SECRET_KEY=$WEB_PANEL_SECRET/" $DEPLOY_DIR/.env
        sed -i "s/API_SECRET_KEY=.*/API_SECRET_KEY=$API_SECRET/" $DEPLOY_DIR/.env
        
        log_warning "⚠️  ВАЖНО: Отредактируйте файл $DEPLOY_DIR/.env и укажите:"
        log_warning "   - BOT_TOKEN (токен Telegram бота)"
        log_warning "   - ADMIN_IDS (ID администраторов)"
        log_warning "   - API ключи для бирж и партнерских программ"
        log_warning "   - Данные для уведомлений"
        
        read -p "Нажмите Enter после редактирования .env файла..."
    else
        log_info "Файл .env уже существует"
    fi
    
    log_success "Переменные окружения настроены"
}

# Настройка SSL сертификата
setup_ssl() {
    log_info "Настройка SSL сертификата..."
    
    read -p "Введите доменное имя для веб-панели: " DOMAIN_NAME
    
    if [ ! -z "$DOMAIN_NAME" ]; then
        # Получение SSL сертификата
        certbot certonly --nginx -d $DOMAIN_NAME --non-interactive --agree-tos --email admin@$DOMAIN_NAME
        
        if [ $? -eq 0 ]; then
            log_success "SSL сертификат получен для $DOMAIN_NAME"
        else
            log_warning "Не удалось получить SSL сертификат. Продолжаем без SSL."
        fi
    else
        log_warning "Доменное имя не указано. SSL не настроен."
    fi
}

# Настройка Nginx
setup_nginx() {
    log_info "Настройка Nginx..."
    
    cat > /etc/nginx/sites-available/$PROJECT_NAME << EOF
server {
    listen 80;
    server_name _;
    
    # Редирект на HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;
    
    # SSL конфигурация
    ssl_certificate /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem;
    
    # Безопасность
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Web Panel
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Статические файлы
    location /static/ {
        alias $DEPLOY_DIR/web_panel/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Логи
    access_log /var/log/nginx/${PROJECT_NAME}_access.log;
    error_log /var/log/nginx/${PROJECT_NAME}_error.log;
}
EOF

    # Активация сайта
    ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
    
    # Тест конфигурации
    nginx -t
    
    if [ $? -eq 0 ]; then
        systemctl reload nginx
        log_success "Nginx настроен и перезапущен"
    else
        log_error "Ошибка в конфигурации Nginx"
        exit 1
    fi
}

# Создание systemd сервисов
create_systemd_services() {
    log_info "Создание systemd сервисов..."
    
    # Сервис для бота
    cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Smart Trading Bot
After=docker.service postgresql.service redis.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=$DEPLOY_DIR
ExecStart=/usr/bin/docker-compose up bot
ExecStop=/usr/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Сервис для веб-панели
    cat > /etc/systemd/system/$WEB_SERVICE_NAME.service << EOF
[Unit]
Description=Smart Trading Web Panel
After=docker.service postgresql.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=$DEPLOY_DIR
ExecStart=/usr/bin/docker-compose up web_panel
ExecStop=/usr/bin/docker-compose down web_panel
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Перезагрузка systemd
    systemctl daemon-reload
    
    log_success "Systemd сервисы созданы"
}

# Настройка логирования
setup_logging() {
    log_info "Настройка логирования..."
    
    # Logrotate конфигурация
    cat > /etc/logrotate.d/$PROJECT_NAME << EOF
$DEPLOY_DIR/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    create 644 root root
    postrotate
        docker-compose -f $DEPLOY_DIR/docker-compose.yml restart bot web_panel api
    endscript
}
EOF

    log_success "Логирование настроено"
}

# Настройка cron задач
setup_cron() {
    log_info "Настройка cron задач..."
    
    # Бэкапы базы данных каждый день в 2:00
    echo "0 2 * * * root cd $DEPLOY_DIR && ./scripts/backup.sh" >> /etc/crontab
    
    # Очистка старых логов каждую неделю
    echo "0 3 * * 0 root find $DEPLOY_DIR/logs -name '*.log' -mtime +30 -delete" >> /etc/crontab
    
    # Обновление SSL сертификатов
    echo "0 12 * * * root /usr/bin/certbot renew --quiet" >> /etc/crontab
    
    systemctl restart cron
    
    log_success "Cron задачи настроены"
}

# Настройка мониторинга
setup_monitoring() {
    log_info "Настройка мониторинга..."
    
    # Установка Node Exporter для Prometheus
    cd /tmp
    wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz
    tar xvf node_exporter-1.6.1.linux-amd64.tar.gz
    mv node_exporter-1.6.1.linux-amd64/node_exporter /usr/local/bin/
    
    # Systemd сервис для Node Exporter
    cat > /etc/systemd/system/node_exporter.service << EOF
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=nobody
Group=nobody
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl start node_exporter
    systemctl enable node_exporter
    
    log_success "Мониторинг настроен"
}

# Настройка файрвола
setup_firewall() {
    log_info "Настройка файрвола..."
    
    # Установка UFW если не установлен
    apt install -y ufw
    
    # Базовые правила
    ufw default deny incoming
    ufw default allow outgoing
    
    # Разрешенные порты
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 5432/tcp  # PostgreSQL (только для бэкапов)
    
    # Активация (с подтверждением)
    echo "y" | ufw enable
    
    log_success "Файрвол настроен"
}

# Запуск приложения
deploy_application() {
    log_info "Запуск приложения..."
    
    cd $DEPLOY_DIR
    
    # Сборка и запуск контейнеров
    docker-compose build
    docker-compose up -d
    
    # Ожидание запуска сервисов
    log_info "Ожидание запуска сервисов..."
    sleep 30
    
    # Проверка состояния
    if docker-compose ps | grep -q "Up"; then
        log_success "Приложение успешно запущено!"
    else
        log_error "Ошибка запуска приложения"
        docker-compose logs
        exit 1
    fi
    
    # Запуск systemd сервисов
    systemctl enable $SERVICE_NAME
    systemctl enable $WEB_SERVICE_NAME
    systemctl start $SERVICE_NAME
    systemctl start $WEB_SERVICE_NAME
    
    log_success "Сервисы запущены и добавлены в автозагрузку"
}

# Проверка здоровья системы
health_check() {
    log_info "Проверка состояния системы..."
    
    # Проверка Docker контейнеров
    if docker-compose -f $DEPLOY_DIR/docker-compose.yml ps | grep -q "Up"; then
        log_success "✅ Docker контейнеры запущены"
    else
        log_error "❌ Проблемы с Docker контейнерами"
    fi
    
    # Проверка базы данных
    if docker-compose -f $DEPLOY_DIR/docker-compose.yml exec -T postgres pg_isready -U postgres; then
        log_success "✅ База данных доступна"
    else
        log_error "❌ База данных недоступна"
    fi
    
    # Проверка Redis
    if docker-compose -f $DEPLOY_DIR/docker-compose.yml exec -T redis redis-cli ping | grep -q "PONG"; then
        log_success "✅ Redis доступен"
    else
        log_error "❌ Redis недоступен"
    fi
    
    # Проверка веб-панели
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 | grep -q "200\|302"; then
        log_success "✅ Веб-панель доступна"
    else
        log_error "❌ Веб-панель недоступна"
    fi
    
    # Проверка API
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health | grep -q "200"; then
        log_success "✅ API доступно"
    else
        log_error "❌ API недоступно"
    fi
    
    # Проверка Nginx
    if systemctl is-active --quiet nginx; then
        log_success "✅ Nginx активен"
    else
        log_error "❌ Nginx неактивен"
    fi
}

# Создание бэкапа перед деплоем
create_backup() {
    if [ -d "$DEPLOY_DIR" ] && [ -f "$DEPLOY_DIR/.env" ]; then
        log_info "Создание бэкапа перед обновлением..."
        
        BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
        mkdir -p $BACKUP_DIR/$BACKUP_NAME
        
        # Бэкап конфигурации
        cp -r $DEPLOY_DIR/.env $BACKUP_DIR/$BACKUP_NAME/
        cp -r $DEPLOY_DIR/data $BACKUP_DIR/$BACKUP_NAME/ 2>/dev/null || true
        
        # Бэкап базы данных
        cd $DEPLOY_DIR
        docker-compose exec -T postgres pg_dump -U postgres trading_bot > $BACKUP_DIR/$BACKUP_NAME/database.sql
        
        log_success "Бэкап создан: $BACKUP_DIR/$BACKUP_NAME"
    fi
}

# Показать информацию после установки
show_final_info() {
    log_success "🎉 Развертывание завершено успешно!"
    echo ""
    echo "📋 Информация о системе:"
    echo "   🗂️  Директория проекта: $DEPLOY_DIR"
    echo "   💾 Директория бэкапов: $BACKUP_DIR"
    echo "   🌐 Веб-панель: http://$(hostname -I | awk '{print $1}'):5000"
    echo "   🔌 API: http://$(hostname -I | awk '{print $1}'):8000"
    echo ""
    echo "🔧 Управление сервисами:"
    echo "   systemctl status $SERVICE_NAME"
    echo "   systemctl status $WEB_SERVICE_NAME"
    echo "   docker-compose -f $DEPLOY_DIR/docker-compose.yml logs -f"
    echo ""
    echo "📊 Мониторинг:"
    echo "   🎯 Prometheus: http://$(hostname -I | awk '{print $1}'):9090"
    echo "   📈 Grafana: http://$(hostname -I | awk '{print $1}'):3000"
    echo ""
    echo "⚠️  Важные напоминания:"
    echo "   1. Проверьте и отредактируйте $DEPLOY_DIR/.env"
    echo "   2. Настройте домен и SSL сертификат"
    echo "   3. Установите мониторинг и алерты"
    echo "   4. Настройте регулярные бэкапы"
    echo ""
    echo "📚 Документация: $DEPLOY_DIR/docs/"
    echo "🆘 Поддержка: https://github.com/your-username/smart-trading-bot/issues"
}

# Функция отката
rollback() {
    log_warning "Выполнение отката к предыдущей версии..."
    
    LATEST_BACKUP=$(ls -t $BACKUP_DIR | head -1)
    
    if [ ! -z "$LATEST_BACKUP" ]; then
        log_info "Восстановление из бэкапа: $LATEST_BACKUP"
        
        # Остановка сервисов
        systemctl stop $SERVICE_NAME
        systemctl stop $WEB_SERVICE_NAME
        cd $DEPLOY_DIR && docker-compose down
        
        # Восстановление конфигурации
        cp $BACKUP_DIR/$LATEST_BACKUP/.env $DEPLOY_DIR/
        cp -r $BACKUP_DIR/$LATEST_BACKUP/data/* $DEPLOY_DIR/data/ 2>/dev/null || true
        
        # Восстановление базы данных
        cd $DEPLOY_DIR && docker-compose up -d postgres
        sleep 10
        docker-compose exec -T postgres psql -U postgres -d trading_bot < $BACKUP_DIR/$LATEST_BACKUP/database.sql
        
        # Запуск сервисов
        docker-compose up -d
        systemctl start $SERVICE_NAME
        systemctl start $WEB_SERVICE_NAME
        
        log_success "Откат выполнен успешно"
    else
        log_error "Бэкапы не найдены"
        exit 1
    fi
}

# Главная функция
main() {
    echo "🚀 Smart Trading Bot - Скрипт развертывания"
    echo "=========================================="
    echo ""
    
    # Проверка аргументов
    case "${1:-install}" in
        "install")
            log_info "Начинается полная установка..."
            check_root
            create_directories
            install_dependencies
            setup_repository
            setup_environment
            create_backup
            setup_ssl
            setup_nginx
            create_systemd_services
            setup_logging
            setup_cron
            setup_monitoring
            setup_firewall
            deploy_application
            health_check
            show_final_info
            ;;
        "update")
            log_info "Начинается обновление..."
            check_root
            create_backup
            setup_repository
            cd $DEPLOY_DIR
            docker-compose pull
            docker-compose up -d --build
            health_check
            log_success "Обновление завершено"
            ;;
        "rollback")
            log_info "Начинается откат..."
            check_root
            rollback
            ;;
        "health")
            log_info "Проверка состояния системы..."
            health_check
            ;;
        "backup")
            log_info "Создание бэкапа..."
            create_backup
            ;;
        "logs")
            log_info "Просмотр логов..."
            cd $DEPLOY_DIR
            docker-compose logs -f
            ;;
        "restart")
            log_info "Перезапуск сервисов..."
            systemctl restart $SERVICE_NAME
            systemctl restart $WEB_SERVICE_NAME
            cd $DEPLOY_DIR && docker-compose restart
            log_success "Сервисы перезапущены"
            ;;
        *)
            echo "Использование: $0 {install|update|rollback|health|backup|logs|restart}"
            echo ""
            echo "Команды:"
            echo "  install  - Полная установка системы"
            echo "  update   - Обновление до последней версии"
            echo "  rollback - Откат к предыдущей версии"
            echo "  health   - Проверка состояния системы"
            echo "  backup   - Создание бэкапа"
            echo "  logs     - Просмотр логов в реальном времени"
            echo "  restart  - Перезапуск всех сервисов"
            exit 1
            ;;
    esac
}

# Обработка сигналов
trap 'log_error "Скрипт прерван пользователем"; exit 1' INT TERM

# Запуск
main "$@"