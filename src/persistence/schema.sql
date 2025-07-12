-- Database Schema for AssetFetch Pro Telegram Bot

-- Table: admins
-- Stores authorized admin Telegram user IDs.
CREATE TABLE IF NOT EXISTS admins (
    user_id INTEGER PRIMARY KEY
);

-- Table: groups
-- Stores approved group IDs and their status.
CREATE TABLE IF NOT EXISTS groups (
    group_id INTEGER PRIMARY KEY,
    is_approved BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 0, -- Bot status in the group (/bot-start, /stop-bot)
    is_paused BOOLEAN DEFAULT 0, -- Paused state (/unactivate, /activate)
    subscription_plan TEXT DEFAULT 'default',
    blocked_websites TEXT, -- JSON list of blocked domains for this group
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: users
-- Tracks user request history for rate-limiting.
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    last_request_time DATETIME,
    last_request_plan TEXT
);

-- Table: tasks
-- The core task queue.
CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    group_id INTEGER,
    message_id INTEGER, -- Original message ID for replying
    original_link TEXT,
    edited_link TEXT,
    status TEXT DEFAULT 'pending', -- pending, downloading, uploading, complete, error, retrying
    priority INTEGER DEFAULT 0, -- 1 for priority queue, 0 for normal
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    error_count INTEGER DEFAULT 0,
    local_filepath TEXT,
    gdrive_link TEXT,
    FOREIGN KEY (group_id) REFERENCES groups(group_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Table: blocked_domains
-- Stores group-specific blocked domains.
CREATE TABLE IF NOT EXISTS blocked_domains (
    group_id INTEGER,
    domain TEXT,
    PRIMARY KEY (group_id, domain),
    FOREIGN KEY (group_id) REFERENCES groups(group_id) ON DELETE CASCADE
);

-- Table: user_requests
-- Tracks user request counts for subscription limits (e.g., 1/24h).
CREATE TABLE IF NOT EXISTS user_requests (
    user_id INTEGER,
    group_id INTEGER,
    last_request TIMESTAMP,
    request_count INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, group_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (group_id) REFERENCES groups(group_id) ON DELETE CASCADE
);

-- Table: subscriptions
-- Stores active subscription plan per group.
CREATE TABLE IF NOT EXISTS subscriptions (
    group_id INTEGER PRIMARY KEY,
    plan TEXT,
    activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES groups(group_id) ON DELETE CASCADE
);
