#!/usr/bin/env python3
# クリップボードにSQLをコピーするスクリプト
import pyperclip

sql_content = '''-- Railway PostgreSQL用企業管理テーブル作成SQL
-- PostgreSQL管理画面のSQLエディタで実行してください

-- 1. 企業基本情報テーブル
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    company_code VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    address TEXT,
    industry VARCHAR(100),
    employee_count INTEGER,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 企業LINEアカウントテーブル
CREATE TABLE IF NOT EXISTS company_line_accounts (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    line_channel_id VARCHAR(255) UNIQUE NOT NULL,
    line_channel_access_token VARCHAR(255) NOT NULL,
    line_channel_secret VARCHAR(255) NOT NULL,
    line_basic_id VARCHAR(255),
    line_qr_code_url VARCHAR(500),
    webhook_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 3. 企業決済情報テーブル
CREATE TABLE IF NOT EXISTS company_payments (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    stripe_customer_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_subscription_id VARCHAR(255),
    subscription_status VARCHAR(50),
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    trial_start TIMESTAMP,
    trial_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 4. 企業コンテンツ管理テーブル
CREATE TABLE IF NOT EXISTS company_contents (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    content_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    line_bot_url VARCHAR(500),
    api_endpoint VARCHAR(500),
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 5. 企業通知設定テーブル
CREATE TABLE IF NOT EXISTS company_notifications (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    notification_type VARCHAR(100) NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    recipients JSONB,
    schedule VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 6. 企業解約履歴テーブル
CREATE TABLE IF NOT EXISTS company_cancellations (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    cancellation_reason VARCHAR(255),
    cancelled_by VARCHAR(100),
    data_deletion_status VARCHAR(50) DEFAULT 'pending',
    line_account_status VARCHAR(50) DEFAULT 'active',
    cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 7. 企業ユーザー管理テーブル
CREATE TABLE IF NOT EXISTS company_users (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    permissions JSONB,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(company_id, user_id)
);

-- テーブル作成確認クエリ
SELECT 
    table_name,
    '企業管理テーブル' as category
FROM information_schema.tables 
WHERE table_schema = 'public' 
    AND table_name LIKE 'company%'
ORDER BY table_name;

-- 全テーブル一覧確認
SELECT 
    table_name,
    CASE 
        WHEN table_name LIKE 'company%' THEN '企業管理テーブル'
        ELSE 'その他のテーブル'
    END as category
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY category, table_name;
'''

try:
    pyperclip.copy(sql_content)
    print("✅ SQLコマンドがクリップボードにコピーされました！")
    print("💡 PostgreSQL管理画面のSQLエディタにペーストしてください")
except Exception as e:
    print(f"❌ クリップボードコピー失敗: {e}")
    print("💡 手動でSQLコマンドをコピーしてください")
