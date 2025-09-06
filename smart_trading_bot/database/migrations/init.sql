-- Инициализация базы данных для торгового бота
-- Версия: 1.0.0
-- Дата создания: 2024-09-06

-- Создание таблицы пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(255),
    language_code VARCHAR(10) DEFAULT 'ru',
    is_active BOOLEAN DEFAULT TRUE,
    is_banned BOOLEAN DEFAULT FALSE,
    is_premium BOOLEAN DEFAULT FALSE,
    is_vip BOOLEAN DEFAULT FALSE,
    referrer_id BIGINT,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_earned DECIMAL(10, 2) DEFAULT 0.00,
    available_balance DECIMAL(10, 2) DEFAULT 0.00,
    total_withdrawn DECIMAL(10, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов для таблицы пользователей
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_referrer_id ON users(referrer_id);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Создание таблицы сигналов
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('CALL', 'PUT', 'BUY', 'SELL')),
    entry_price DECIMAL(12, 6),
    target_price DECIMAL(12, 6),
    stop_loss DECIMAL(12, 6),
    expiry_time TIMESTAMP,
    confidence INTEGER CHECK (confidence >= 0 AND confidence <= 100),
    result VARCHAR(10) CHECK (result IN ('WIN', 'LOSS', 'PENDING', 'CANCELLED')),
    profit_loss DECIMAL(10, 2),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP
);

-- Создание индексов для таблицы сигналов
CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol);
CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at);
CREATE INDEX IF NOT EXISTS idx_signals_result ON signals(result);
CREATE INDEX IF NOT EXISTS idx_signals_created_by ON signals(created_by);

-- Создание таблицы подписок пользователей на сигналы
CREATE TABLE IF NOT EXISTS user_signal_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    signal_id INTEGER REFERENCES signals(id),
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id, signal_id)
);

-- Создание таблицы партнерских программ
CREATE TABLE IF NOT EXISTS partner_programs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    commission_rate DECIMAL(5, 4) NOT NULL,
    min_payout DECIMAL(10, 2) DEFAULT 50.00,
    api_endpoint VARCHAR(255),
    api_key VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Вставка данных партнерских программ
INSERT INTO partner_programs (name, description, commission_rate, min_payout) VALUES
('Binarium', 'Binarium binary options broker', 0.0200, 50.00),
('PocketOption', 'PocketOption binary options broker', 0.0250, 30.00),
('Quotex', 'Quotex binary options broker', 0.0300, 25.00)
ON CONFLICT DO NOTHING;

-- Создание таблицы регистраций пользователей у партнеров
CREATE TABLE IF NOT EXISTS partner_registrations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    partner_program_id INTEGER REFERENCES partner_programs(id),
    partner_user_id VARCHAR(255),
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_verified BOOLEAN DEFAULT FALSE,
    first_deposit_amount DECIMAL(10, 2),
    first_deposit_date TIMESTAMP,
    total_deposits DECIMAL(10, 2) DEFAULT 0.00,
    total_volume DECIMAL(15, 2) DEFAULT 0.00,
    commission_earned DECIMAL(10, 2) DEFAULT 0.00,
    UNIQUE(user_id, partner_program_id)
);

-- Создание таблицы комиссий
CREATE TABLE IF NOT EXISTS commissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    referral_id INTEGER REFERENCES users(id),
    partner_program_id INTEGER REFERENCES partner_programs(id),
    amount DECIMAL(10, 2) NOT NULL,
    commission_type VARCHAR(20) NOT NULL CHECK (commission_type IN ('REFERRAL', 'DEPOSIT', 'TRADING', 'BONUS')),
    description TEXT,
    is_paid BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP
);

-- Создание индексов для таблицы комиссий
CREATE INDEX IF NOT EXISTS idx_commissions_user_id ON commissions(user_id);
CREATE INDEX IF NOT EXISTS idx_commissions_referral_id ON commissions(referral_id);
CREATE INDEX IF NOT EXISTS idx_commissions_is_paid ON commissions(is_paid);

-- Создание таблицы выплат
CREATE TABLE IF NOT EXISTS payouts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_details TEXT,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'CANCELLED', 'FAILED')),
    transaction_id VARCHAR(255),
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    completed_at TIMESTAMP,
    notes TEXT
);

-- Создание индексов для таблицы выплат
CREATE INDEX IF NOT EXISTS idx_payouts_user_id ON payouts(user_id);
CREATE INDEX IF NOT EXISTS idx_payouts_status ON payouts(status);
CREATE INDEX IF NOT EXISTS idx_payouts_requested_at ON payouts(requested_at);

-- Создание таблицы настроек пользователей
CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,
    notifications_enabled BOOLEAN DEFAULT TRUE,
    signal_notifications BOOLEAN DEFAULT TRUE,
    commission_notifications BOOLEAN DEFAULT TRUE,
    marketing_notifications BOOLEAN DEFAULT FALSE,
    language VARCHAR(10) DEFAULT 'ru',
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы логов активности
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов для таблицы логов
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_action ON activity_logs(action);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON activity_logs(created_at);

-- Создание таблицы сессий
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов для таблицы сессий
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);

-- Создание таблицы уведомлений
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

-- Создание индексов для таблицы уведомлений
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);

-- Создание таблицы статистики
CREATE TABLE IF NOT EXISTS statistics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15, 2),
    metric_date DATE DEFAULT CURRENT_DATE,
    additional_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(metric_name, metric_date)
);

-- Создание функции для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Создание триггеров для автоматического обновления updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_signals_updated_at BEFORE UPDATE ON signals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_settings_updated_at BEFORE UPDATE ON user_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Создание представлений для удобства работы
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.id,
    u.user_id,
    u.username,
    u.first_name,
    u.last_name,
    u.is_active,
    u.is_premium,
    u.total_earned,
    u.available_balance,
    COUNT(DISTINCT r.id) as referrals_count,
    COUNT(DISTINCT pr.id) as partner_registrations_count,
    COUNT(DISTINCT s.id) as signals_subscribed,
    u.registration_date,
    u.last_activity
FROM users u
LEFT JOIN users r ON r.referrer_id = u.user_id
LEFT JOIN partner_registrations pr ON pr.user_id = u.id
LEFT JOIN user_signal_subscriptions s ON s.user_id = u.id AND s.is_active = TRUE
GROUP BY u.id;

-- Создание представления для статистики сигналов
CREATE OR REPLACE VIEW signal_stats AS
SELECT 
    s.id,
    s.symbol,
    s.direction,
    s.confidence,
    s.result,
    s.created_at,
    COUNT(uss.user_id) as subscribers_count,
    u.username as created_by_username
FROM signals s
LEFT JOIN user_signal_subscriptions uss ON uss.signal_id = s.id AND uss.is_active = TRUE
LEFT JOIN users u ON u.id = s.created_by
GROUP BY s.id, u.username;

-- Вставка начальных данных для администратора (если нужно)
-- INSERT INTO users (user_id, username, first_name, is_active) VALUES 
-- (123456789, 'admin', 'Admin', TRUE) ON CONFLICT DO NOTHING;

COMMIT;

