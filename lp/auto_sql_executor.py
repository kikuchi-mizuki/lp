#!/usr/bin/env python3
"""
PostgreSQL管理画面自動SQL実行スクリプト
"""

import os
import sys
import time

def create_sql_file():
    """SQLファイルを作成"""
    print("=== SQLファイル作成 ===")
    
    sql_content = """-- Railway PostgreSQL用企業管理テーブル作成SQL
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
"""
    
    # SQLファイルを作成
    with open('railway_company_tables.sql', 'w', encoding='utf-8') as f:
        f.write(sql_content)
    
    print("✅ SQLファイル作成完了: railway_company_tables.sql")
    return True

def show_execution_instructions():
    """実行手順を表示"""
    print("\n" + "="*60)
    print("🚀 PostgreSQL管理画面での実行手順")
    print("="*60)
    
    print("\n📋 手順1: Railwayダッシュボードにアクセス")
    print("   - Railwayダッシュボードを開く")
    print("   - プロジェクトを選択")
    print("   - PostgreSQLサービスをクリック")
    
    print("\n📋 手順2: Dataタブを開く")
    print("   - 上部の「Data」タブをクリック")
    print("   - データベースのテーブル一覧が表示される")
    
    print("\n📋 手順3: SQLエディタを開く")
    print("   - 「Query」または「SQL Editor」ボタンをクリック")
    print("   - SQLエディタが開く")
    
    print("\n📋 手順4: SQLを実行")
    print("   - 以下のSQLコマンドをコピー")
    print("   - SQLエディタにペースト")
    print("   - 「Run」または「Execute」ボタンをクリック")
    
    print("\n📋 手順5: 結果確認")
    print("   - テーブル作成が成功したことを確認")
    print("   - 管理画面を更新して企業管理テーブルを確認")
    
    print("\n" + "="*60)
    print("📄 実行するSQLコマンド:")
    print("="*60)
    
    # SQLファイルの内容を表示
    try:
        with open('railway_company_tables.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
            print(sql_content)
    except FileNotFoundError:
        print("❌ SQLファイルが見つかりません")
        return False
    
    print("\n" + "="*60)
    print("✅ 完了後、PostgreSQL管理画面で企業管理テーブルが表示されます！")
    print("="*60)
    
    return True

def create_quick_copy_script():
    """クイックコピー用スクリプトを作成"""
    print("\n=== クイックコピー用スクリプト作成 ===")
    
    # SQLファイルの内容を読み込み
    try:
        with open('railway_company_tables.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
    except FileNotFoundError:
        print("❌ SQLファイルが見つかりません")
        return False
    
    # クリップボード用のスクリプトを作成
    clipboard_script = f"""#!/usr/bin/env python3
# クリップボードにSQLをコピーするスクリプト
import pyperclip

sql_content = '''{sql_content}'''

try:
    pyperclip.copy(sql_content)
    print("✅ SQLコマンドがクリップボードにコピーされました！")
    print("💡 PostgreSQL管理画面のSQLエディタにペーストしてください")
except Exception as e:
    print(f"❌ クリップボードコピー失敗: {{e}}")
    print("💡 手動でSQLコマンドをコピーしてください")
"""
    
    with open('copy_sql_to_clipboard.py', 'w', encoding='utf-8') as f:
        f.write(clipboard_script)
    
    print("✅ クイックコピー用スクリプト作成完了: copy_sql_to_clipboard.py")
    return True

def main():
    """メイン処理"""
    print("=== PostgreSQL管理画面自動SQL実行準備 ===")
    
    # 1. SQLファイルを作成
    if not create_sql_file():
        print("❌ SQLファイル作成に失敗しました")
        return False
    
    # 2. クイックコピー用スクリプトを作成
    if not create_quick_copy_script():
        print("❌ クイックコピー用スクリプト作成に失敗しました")
        return False
    
    # 3. 実行手順を表示
    if not show_execution_instructions():
        print("❌ 実行手順の表示に失敗しました")
        return False
    
    print(f"\n🎯 準備完了！")
    print(f"📁 作成されたファイル:")
    print(f"   - railway_company_tables.sql (SQLコマンド)")
    print(f"   - copy_sql_to_clipboard.py (クイックコピー用)")
    
    print(f"\n💡 次のステップ:")
    print(f"   1. PostgreSQL管理画面にアクセス")
    print(f"   2. SQLエディタを開く")
    print(f"   3. SQLコマンドを実行")
    print(f"   4. 企業管理テーブルを確認")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 