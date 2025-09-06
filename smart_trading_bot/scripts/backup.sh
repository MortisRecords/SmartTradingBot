#!/bin/bash

# Smart Trading Bot - Backup Script
# Скрипт создания резервных копий

set -e  # Останавливаться при ошибках

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Логирование
log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] [INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] [SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] [WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] [ERROR]${NC} $1"
}

# Конфигурация
PROJECT_DIR="/opt/smart_trading_bot"
BACKUP_DIR="/opt/backups/smart_trading_bot"
MAX_BACKUPS=30  # Максимальное количество бэкапов
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="backup_${TIMESTAMP}"
CURRENT_BACKUP_DIR="${BACKUP_DIR}/${BACKUP_NAME}"

# AWS S3 настройки (если используется)
S3_BUCKET="${S3_BACKUP_BUCKET:-}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Telegram уведомления
TELEGRAM_BOT_TOKEN="${BACKUP_NOTIFICATION_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${BACKUP_NOTIFICATION_CHAT_ID:-}"

# Функция отправки уведомления в Telegram
send_telegram_notification() {
    local message="$1"
    
    if [[ -n "$TELEGRAM_BOT_TOKEN" && -n "$TELEGRAM_CHAT_ID" ]]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d "chat_id=${TELEGRAM_CHAT_ID}" \
            -d "text=${message}" \
            -d "parse_mode=HTML" > /dev/null 2>&1 || true
    fi
}

# Проверка зависимостей
check_dependencies() {
    log_info "Проверка зависимостей..."
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен"
        exit 1
    fi
    
    # Проверка docker-compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose не установлен"
        exit 1
    fi
    
    # Проверка доступности проекта
    if [[ ! -d "$PROJECT_DIR" ]]; then
        log_error "Директория проекта не найдена: $PROJECT_DIR"
        exit 1
    fi
    
    log_success "Все зависимости в порядке"
}

# Создание директорий для бэкапа
create_backup_directories() {
    log_info "Создание директорий для бэкапа..."
    
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$CURRENT_BACKUP_DIR"
    mkdir -p "$CURRENT_BACKUP_DIR/database"
    mkdir -p "$CURRENT_BACKUP_DIR/files"
    mkdir -p "$CURRENT_BACKUP_DIR/logs"
    mkdir -p "$CURRENT_BACKUP_DIR/config"
    
    log_success "Директории созданы"
}

# Бэкап базы данных
backup_database() {
    log_info "Создание бэкапа базы данных..."
    
    cd "$PROJECT_DIR"
    
    # PostgreSQL бэкап
    if docker-compose ps postgres | grep -q "Up"; then
        log_info "Создание PostgreSQL дампа..."
        
        # Полный дамп
        docker-compose exec -T postgres pg_dump -U postgres -d trading_bot \
            > "$CURRENT_BACKUP_DIR/database/postgresql_full.sql"
        
        # Дамп только данных
        docker-compose exec -T postgres pg_dump -U postgres -d trading_bot --data-only \
            > "$CURRENT_BACKUP_DIR/database/postgresql_data.sql"
        
        # Дамп только схемы
        docker-compose exec -T postgres pg_dump -U postgres -d trading_bot --schema-only \
            > "$CURRENT_BACKUP_DIR/database/postgresql_schema.sql"
        
        # Сжатие дампов
        gzip "$CURRENT_BACKUP_DIR/database/postgresql_full.sql"
        gzip "$CURRENT_BACKUP_DIR/database/postgresql_data.sql"
        gzip "$CURRENT_BACKUP_DIR/database/postgresql_schema.sql"
        
        log_success "PostgreSQL дамп создан"
    else
        log_warning "PostgreSQL контейнер не запущен"
    fi
    
    # Redis бэкап
    if docker-compose ps redis | grep -q "Up"; then
        log_info "Создание Redis дампа..."
        
        docker-compose exec -T redis redis-cli --rdb - > "$CURRENT_BACKUP_DIR/database/redis_dump.rdb"
        gzip "$CURRENT_BACKUP_DIR/database/redis_dump.rdb"
        
        log_success "Redis дамп создан"
    else
        log_warning "Redis контейнер не запущен"
    fi
}

# Бэкап файлов
backup_files() {
    log_info "Создание бэкапа файлов..."
    
    # Конфигурационные файлы
    cp "$PROJECT_DIR/.env" "$CURRENT_BACKUP_DIR/config/" 2>/dev/null || log_warning ".env файл не найден"
    cp "$PROJECT_DIR/docker-compose.yml" "$CURRENT_BACKUP_DIR/config/"
    cp "$PROJECT_DIR/requirements.txt" "$CURRENT_BACKUP_DIR/config/"
    
    # Пользовательские данные
    if [[ -d "$PROJECT_DIR/data" ]]; then
        cp -r "$PROJECT_DIR/data" "$CURRENT_BACKUP_DIR/files/"
        log_info "Данные скопированы"
    fi
    
    # Загруженные файлы
    if [[ -d "$PROJECT_DIR/uploads" ]]; then
        cp -r "$PROJECT_DIR/uploads" "$CURRENT_BACKUP_DIR/files/"
        log_info "Загруженные файлы скопированы"
    fi
    
    # SSL сертификаты
    if [[ -d "/etc/letsencrypt" ]]; then
        mkdir -p "$CURRENT_BACKUP_DIR/files/ssl"
        cp -r /etc/letsencrypt "$CURRENT_BACKUP_DIR/files/ssl/" 2>/dev/null || true
        log_info "SSL сертификаты скопированы"
    fi
    
    log_success "Файлы скопированы"
}

# Бэкап логов
backup_logs() {
    log_info "Создание бэкапа логов..."
    
    # Логи приложения
    if [[ -d "$PROJECT_DIR/logs" ]]; then
        cp -r "$PROJECT_DIR/logs" "$CURRENT_BACKUP_DIR/"
        
        # Сжимаем большие лог-файлы
        find "$CURRENT_BACKUP_DIR/logs" -name "*.log" -size +10M -exec gzip {} \;
        
        log_info "Логи приложения скопированы"
    fi
    
    # Логи системы
    mkdir -p "$CURRENT_BACKUP_DIR/logs/system"
    
    # Логи Docker
    if [[ -d "/var/lib/docker/containers" ]]; then
        cd "$PROJECT_DIR"
        for container in $(docker-compose ps -q); do
            container_name=$(docker inspect --format='{{.Name}}' "$container" | sed 's/\///')
            docker logs "$container" > "$CURRENT_BACKUP_DIR/logs/system/${container_name}.log" 2>&1 || true
        done
        log_info "Логи Docker скопированы"
    fi
    
    # Логи Nginx
    if [[ -d "/var/log/nginx" ]]; then
        cp /var/log/nginx/*smart* "$CURRENT_BACKUP_DIR/logs/system/" 2>/dev/null || true
        log_info "Логи Nginx скопированы"
    fi
    
    log_success "Логи скопированы"
}

# Создание метаданных бэкапа
create_backup_metadata() {
    log_info "Создание метаданных бэкапа..."
    
    cat > "$CURRENT_BACKUP_DIR/backup_info.json" << EOF
{
    "backup_name": "$BACKUP_NAME",
    "timestamp": "$TIMESTAMP",
    "date": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "project_dir": "$PROJECT_DIR",
    "backup_type": "full",
    "components": {
        "database": true,
        "files": true,
        "logs": true,
        "config": true
    },
    "database_info": {
        "postgresql": {
            "version": "$(docker-compose -f $PROJECT_DIR/docker-compose.yml exec -T postgres psql -U postgres -t -c 'SELECT version();' 2>/dev/null | head -1 | xargs || echo 'N/A')"
        },
        "redis": {
            "version": "$(docker-compose -f $PROJECT_DIR/docker-compose.yml exec -T redis redis-server --version 2>/dev/null | cut -d' ' -f3 || echo 'N/A')"
        }
    },
    "system_info": {
        "os": "$(uname -a)",
        "docker_version": "$(docker --version)",
        "docker_compose_version": "$(docker-compose --version)",
        "disk_usage": "$(df -h $BACKUP_DIR | tail -1)"
    }
}
EOF
    
    # Создание README
    cat > "$CURRENT_BACKUP_DIR/README.md" << EOF
# Smart Trading Bot Backup

**Дата создания:** $(date)
**Имя бэкапа:** $BACKUP_NAME

## Содержимое

- \`database/\` - Дампы PostgreSQL и Redis
- \`files/\` - Пользовательские данные и загруженные файлы
- \`config/\` - Конфигурационные файлы (.env, docker-compose.yml)
- \`logs/\` - Логи приложения и системы
- \`backup_info.json\` - Метаданные бэкапа

## Восстановление

### База данных PostgreSQL:
\`\`\`bash
# Остановить контейнеры
docker-compose down

# Запустить только PostgreSQL
docker-compose up -d postgres

# Восстановить дамп
gunzip -c database/postgresql_full.sql.gz | docker-compose exec -T postgres psql -U postgres -d trading_bot
\`\`\`

### База данных Redis:
\`\`\`bash
# Остановить Redis
docker-compose stop redis

# Скопировать дамп
gunzip -c database/redis_dump.rdb.gz > /var/lib/docker/volumes/redis_data/_data/dump.rdb

# Запустить Redis
docker-compose start redis
\`\`\`

### Файлы:
\`\`\`bash
# Восстановить данные
cp -r files/data/* /opt/smart_trading_bot/data/

# Восстановить конфигурацию
cp config/.env /opt/smart_trading_bot/
\`\`\`

## Проверка целостности

Проверьте размеры файлов и соответствие хэшей в backup_info.json
EOF

    # Расчет размера бэкапа
    BACKUP_SIZE=$(du -sh "$CURRENT_BACKUP_DIR" | cut -f1)
    
    # Добавление размера в метаданные
    echo "    \"backup_size\": \"$BACKUP_SIZE\"," >> "$CURRENT_BACKUP_DIR/backup_info.json"
    sed -i '$s/,$//' "$CURRENT_BACKUP_DIR/backup_info.json"
    echo "}" >> "$CURRENT_BACKUP_DIR/backup_info.json"
    
    log_success "Метаданные созданы (размер: $BACKUP_SIZE)"
}

# Сжатие бэкапа
compress_backup() {
    log_info "Сжатие бэкапа..."
    
    cd "$BACKUP_DIR"
    
    # Создание tar.gz архива
    tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
    
    if [[ $? -eq 0 ]]; then
        # Удаление исходной директории после успешного сжатия
        rm -rf "$BACKUP_NAME"
        
        COMPRESSED_SIZE=$(du -sh "${BACKUP_NAME}.tar.gz" | cut -f1)
        log_success "Бэкап сжат: ${BACKUP_NAME}.tar.gz ($COMPRESSED_SIZE)"
    else
        log_error "Ошибка сжатия бэкапа"
        return 1
    fi
}

# Загрузка в AWS S3
upload_to_s3() {
    if [[ -z "$S3_BUCKET" ]]; then
        log_info "S3 бэкап не настроен, пропускаем..."
        return 0
    fi
    
    log_info "Загрузка в AWS S3..."
    
    # Проверка AWS CLI
    if ! command -v aws &> /dev/null; then
        log_warning "AWS CLI не установлен, устанавливаем..."
        
        # Установка AWS CLI
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
        unzip awscliv2.zip
        ./aws/install
        rm -rf awscliv2.zip aws
    fi
    
    # Загрузка файла
    aws s3 cp "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" \
        "s3://$S3_BUCKET/smart-trading-bot/backups/${BACKUP_NAME}.tar.gz" \
        --region "$AWS_REGION"
    
    if [[ $? -eq 0 ]]; then
        log_success "Бэкап загружен в S3"
        
        # Опционально удаляем локальный файл после загрузки в S3
        if [[ "${DELETE_LOCAL_AFTER_S3:-false}" == "true" ]]; then
            rm "$BACKUP_DIR/${BACKUP_NAME}.tar.gz"
            log_info "Локальный бэкап удален после загрузки в S3"
        fi
    else
        log_error "Ошибка загрузки в S3"
        return 1
    fi
}

# Очистка старых бэкапов
cleanup_old_backups() {
    log_info "Очистка старых бэкапов..."
    
    cd "$BACKUP_DIR"
    
    # Подсчет количества бэкапов
    BACKUP_COUNT=$(ls -1 backup_*.tar.gz 2>/dev/null | wc -l)
    
    if [[ $BACKUP_COUNT -gt $MAX_BACKUPS ]]; then
        EXCESS_COUNT=$((BACKUP_COUNT - MAX_BACKUPS))
        
        # Удаление самых старых бэкапов
        ls -1t backup_*.tar.gz | tail -n $EXCESS_COUNT | while read backup; do
            log_info "Удаляем старый бэкап: $backup"
            rm "$backup"
        done
        
        log_success "Удалено $EXCESS_COUNT старых бэкапов"
    else
        log_info "Старых бэкапов для удаления нет ($BACKUP_COUNT/$MAX_BACKUPS)"
    fi
    
    # Очистка S3 (если используется)
    if [[ -n "$S3_BUCKET" ]] && command -v aws &> /dev/null; then
        log_info "Очистка старых бэкапов в S3..."
        
        # Получение списка бэкапов в S3
        aws s3 ls "s3://$S3_BUCKET/smart-trading-bot/backups/" \
            --region "$AWS_REGION" \
            | sort -k1,1 -k2,2 \
            | head -n -$MAX_BACKUPS \
            | awk '{print $4}' \
            | while read file; do
                if [[ -n "$file" ]]; then
                    aws s3 rm "s3://$S3_BUCKET/smart-trading-bot/backups/$file" --region "$AWS_REGION"
                    log_info "Удален из S3: $file"
                fi
            done
    fi
}

# Проверка целостности бэкапа
verify_backup() {
    log_info "Проверка целостности бэкапа..."
    
    BACKUP_FILE="$BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    
    if [[ ! -f "$BACKUP_FILE" ]]; then
        log_error "Файл бэкапа не найден: $BACKUP_FILE"
        return 1
    fi
    
    # Проверка архива
    if tar -tzf "$BACKUP_FILE" > /dev/null 2>&1; then
        log_success "Архив бэкапа корректен"
    else
        log_error "Архив бэкапа поврежден"
        return 1
    fi
    
    # Проверка размера
    FILE_SIZE=$(stat -c%s "$BACKUP_FILE")
    if [[ $FILE_SIZE -lt 1000 ]]; then
        log_error "Подозрительно маленький размер бэкапа: $FILE_SIZE байт"
        return 1
    fi
    
    log_success "Бэкап прошел проверку целостности"
}

# Отправка отчета
send_backup_report() {
    local status="$1"
    local details="$2"
    
    BACKUP_FILE="$BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    BACKUP_SIZE=""
    
    if [[ -f "$BACKUP_FILE" ]]; then
        BACKUP_SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
    fi
    
    if [[ "$status" == "success" ]]; then
        MESSAGE="✅ <b>Бэкап выполнен успешно</b>

📅 <b>Дата:</b> $(date)
📦 <b>Имя:</b> $BACKUP_NAME
💾 <b>Размер:</b> $BACKUP_SIZE
🏠 <b>Сервер:</b> $(hostname)

<b>Компоненты:</b>
• База данных PostgreSQL ✅
• База данных Redis ✅  
• Пользовательские файлы ✅
• Конфигурация ✅
• Логи ✅

$details"
    else
        MESSAGE="❌ <b>Ошибка создания бэкапа</b>

📅 <b>Дата:</b> $(date)
🏠 <b>Сервер:</b> $(hostname)
❌ <b>Ошибка:</b> $details

Требуется проверка системы!"
    fi
    
    send_telegram_notification "$MESSAGE"
}

# Восстановление из бэкапа
restore_backup() {
    local backup_file="$1"
    
    if [[ -z "$backup_file" ]]; then
        echo "Использование: $0 restore <backup_file.tar.gz>"
        exit 1
    fi
    
    if [[ ! -f "$backup_file" ]]; then
        log_error "Файл бэкапа не найден: $backup_file"
        exit 1
    fi
    
    log_info "Начинаем восстановление из бэкапа: $backup_file"
    
    # Подтверждение
    read -p "⚠️  Восстановление перезапишет существующие данные. Продолжить? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Восстановление отменено"
        exit 0
    fi
    
    # Остановка сервисов
    log_info "Остановка сервисов..."
    cd "$PROJECT_DIR"
    docker-compose down
    
    # Создание резервной копии текущих данных
    log_info "Создание резервной копии текущих данных..."
    RESTORE_BACKUP_NAME="pre_restore_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR/$RESTORE_BACKUP_NAME"
    
    if [[ -d "$PROJECT_DIR/data" ]]; then
        cp -r "$PROJECT_DIR/data" "$BACKUP_DIR/$RESTORE_BACKUP_NAME/"
    fi
    
    # Извлечение бэкапа
    log_info "Извлечение бэкапа..."
    TEMP_RESTORE_DIR="/tmp/restore_$(date +%s)"
    mkdir -p "$TEMP_RESTORE_DIR"
    
    tar -xzf "$backup_file" -C "$TEMP_RESTORE_DIR"
    EXTRACTED_DIR=$(ls -1 "$TEMP_RESTORE_DIR" | head -1)
    RESTORE_SOURCE="$TEMP_RESTORE_DIR/$EXTRACTED_DIR"
    
    # Восстановление файлов
    log_info "Восстановление файлов..."
    if [[ -d "$RESTORE_SOURCE/files/data" ]]; then
        rm -rf "$PROJECT_DIR/data"
        cp -r "$RESTORE_SOURCE/files/data" "$PROJECT_DIR/"
        log_success "Файлы данных восстановлены"
    fi
    
    # Восстановление конфигурации
    if [[ -f "$RESTORE_SOURCE/config/.env" ]]; then
        cp "$RESTORE_SOURCE/config/.env" "$PROJECT_DIR/"
        log_success "Конфигурация восстановлена"
    fi
    
    # Запуск PostgreSQL для восстановления БД
    log_info "Запуск PostgreSQL..."
    docker-compose up -d postgres
    sleep 10
    
    # Восстановление базы данных
    if [[ -f "$RESTORE_SOURCE/database/postgresql_full.sql.gz" ]]; then
        log_info "Восстановление PostgreSQL..."
        
        # Пересоздание базы данных
        docker-compose exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS trading_bot;"
        docker-compose exec -T postgres psql -U postgres -c "CREATE DATABASE trading_bot;"
        
        # Восстановление данных
        gunzip -c "$RESTORE_SOURCE/database/postgresql_full.sql.gz" | \
            docker-compose exec -T postgres psql -U postgres -d trading_bot
        
        log_success "PostgreSQL восстановлен"
    fi
    
    # Восстановление Redis
    if [[ -f "$RESTORE_SOURCE/database/redis_dump.rdb.gz" ]]; then
        log_info "Восстановление Redis..."
        
        docker-compose stop redis
        
        # Найти том Redis
        REDIS_VOLUME=$(docker volume ls | grep redis_data | awk '{print $2}' | head -1)
        if [[ -n "$REDIS_VOLUME" ]]; then
            REDIS_PATH="/var/lib/docker/volumes/${REDIS_VOLUME}/_data"
            gunzip -c "$RESTORE_SOURCE/database/redis_dump.rdb.gz" > "$REDIS_PATH/dump.rdb"
            log_success "Redis восстановлен"
        fi
    fi
    
    # Запуск всех сервисов
    log_info "Запуск всех сервисов..."
    docker-compose up -d
    
    # Очистка временных файлов
    rm -rf "$TEMP_RESTORE_DIR"
    
    log_success "Восстановление завершено!"
    log_info "Резервная копия старых данных: $BACKUP_DIR/$RESTORE_BACKUP_NAME"
}

# Главная функция
main() {
    case "${1:-backup}" in
        "backup")
            log_info "🚀 Начинаем создание бэкапа..."
            
            start_time=$(date +%s)
            
            # Отправка уведомления о начале
            send_telegram_notification "🔄 <b>Начато создание бэкапа</b>

📅 $(date)
🏠 $(hostname)
📦 $BACKUP_NAME"
            
            # Выполнение бэкапа
            if check_dependencies && \
               create_backup_directories && \
               backup_database && \
               backup_files && \
               backup_logs && \
               create_backup_metadata && \
               compress_backup && \
               verify_backup; then
                
                # Загрузка в S3 (опционально)
                upload_to_s3 || log_warning "Ошибка загрузки в S3, но бэкап создан локально"
                
                # Очистка старых бэкапов
                cleanup_old_backups
                
                end_time=$(date +%s)
                duration=$((end_time - start_time))
                
                send_backup_report "success" "⏱️ <b>Время выполнения:</b> ${duration}с"
                log_success "✅ Бэкап создан успешно за ${duration} секунд"
                
            else
                send_backup_report "error" "Ошибка на одном из этапов создания бэкапа"
                log_error "❌ Ошибка создания бэкапа"
                exit 1
            fi
            ;;
            
        "restore")
            restore_backup "$2"
            ;;
            
        "list")
            log_info "📋 Список доступных бэкапов:"
            if [[ -d "$BACKUP_DIR" ]]; then
                ls -lah "$BACKUP_DIR"/*.tar.gz 2>/dev/null || echo "Бэкапы не найдены"
            else
                echo "Директория бэкапов не найдена"
            fi
            ;;
            
        "cleanup")
            log_info "🧹 Очистка старых бэкапов..."
            cleanup_old_backups
            ;;
            
        "verify")
            if [[ -n "$2" ]]; then
                log_info "🔍 Проверка бэкапа: $2"
                BACKUP_NAME=$(basename "$2" .tar.gz)
                verify_backup
            else
                echo "Использование: $0 verify <backup_file.tar.gz>"
                exit 1
            fi
            ;;
            
        *)
            echo "Smart Trading Bot - Backup Script"
            echo ""
            echo "Использование: $0 {backup|restore|list|cleanup|verify}"
            echo ""
            echo "Команды:"
            echo "  backup            - Создать полный бэкап"
            echo "  restore <file>    - Восстановить из бэкапа"
            echo "  list             - Показать список бэкапов"
            echo "  cleanup          - Удалить старые бэкапы"
            echo "  verify <file>    - Проверить целостность бэкапа"
            echo ""
            echo "Переменные окружения:"
            echo "  S3_BACKUP_BUCKET          - Bucket для загрузки в S3"
            echo "  DELETE_LOCAL_AFTER_S3     - Удалять локальный файл после S3"
            echo "  BACKUP_NOTIFICATION_BOT_TOKEN - Токен бота для уведомлений"
            echo "  BACKUP_NOTIFICATION_CHAT_ID   - Chat ID для уведомлений"
            exit 1
            ;;
    esac
}

# Обработка сигналов
trap 'log_error "Скрипт прерван пользователем"; exit 1' INT TERM

# Запуск
main "$@"