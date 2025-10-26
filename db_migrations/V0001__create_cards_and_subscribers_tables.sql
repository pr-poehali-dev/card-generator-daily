-- Создание таблицы открыток
CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    date VARCHAR(5) NOT NULL UNIQUE, -- формат MM-DD
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    image_url TEXT NOT NULL,
    is_holiday BOOLEAN DEFAULT false,
    holiday_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы подписчиков Telegram
CREATE TABLE IF NOT EXISTS telegram_subscribers (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL UNIQUE,
    username VARCHAR(255),
    first_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sent_at TIMESTAMP
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_cards_date ON cards(date);
CREATE INDEX IF NOT EXISTS idx_cards_holiday ON cards(is_holiday);
CREATE INDEX IF NOT EXISTS idx_subscribers_active ON telegram_subscribers(is_active);