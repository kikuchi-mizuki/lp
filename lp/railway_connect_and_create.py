#!/usr/bin/env python3
"""
Railway CLI接続・企業管理テーブル作成スクリプト
"""

import os
import psycopg2
import sys
import subprocess
import json
import time

def install_railway_cli():
    """Railway CLIをインストール"""
    print("=== Railway CLIインストール ===")
    
    try:
        # npmが利用可能かチェック
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm利用可能: {result.stdout.strip()}")
        else:
            print("❌ npmが利用できません")
            return False
        
        # Railway CLIをインストール
        print("📦 Railway CLIをインストール中...")
        result = subprocess.run(['npm', 'install', '-g', '@railway/cli'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Railway CLIインストール完了")
            return True
        else:
            print(f"❌ Railway CLIインストール失敗: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ インストールエラー: {e}")
        return False

def railway_login():
    """Railwayにログイン"""
    print("\n=== Railwayログイン ===")
    
    try:
        # ログイン状態をチェック
        result = subprocess.run(['railway', 'whoami'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ 既にログイン済み: {result.stdout.strip()}")
            return True
        
        # ログイン実行
        print("🔐 Railwayにログイン中...")
        result = subprocess.run(['railway', 'login'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Railwayログイン完了")
            return True
        else:
            print(f"❌ Railwayログイン失敗: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ ログインエラー: {e}")
        return False

def railway_link_project():
    """Railwayプロジェクトにリンク"""
    print("\n=== Railwayプロジェクトリンク ===")
    
    try:
        # プロジェクト一覧を取得
        result = subprocess.run(['railway', 'projects'], capture_output=True, text=True)
        if result.returncode == 0:
            print("📋 利用可能なプロジェクト:")
            print(result.stdout)
        
        # プロジェクトにリンク
        print("🔗 プロジェクトにリンク中...")
        result = subprocess.run(['railway', 'link'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ プロジェクトリンク完了")
            return True
        else:
            print(f"❌ プロジェクトリンク失敗: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ リンクエラー: {e}")
        return False

def get_railway_database_url():
    """Railway CLIからデータベースURLを取得"""
    print("\n=== RailwayデータベースURL取得 ===")
    
    try:
        # 環境変数を取得
        result = subprocess.run(['railway', 'variables'], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'DATABASE_URL' in line:
                    url = line.split('=')[1].strip()
                    if url.startswith('postgresql://'):
                        print(f"✅ DATABASE_URL取得: {url[:50]}...")
                        return url
        
        # 接続情報を取得
        result = subprocess.run(['railway', 'connect'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Railway接続情報取得完了")
            # 接続情報からURLを抽出
            for line in result.stdout.split('\n'):
                if 'postgresql://' in line:
                    url = line.strip()
                    print(f"✅ 接続URL取得: {url[:50]}...")
                    return url
        
        print("❌ データベースURLを取得できませんでした")
        return None
        
    except Exception as e:
        print(f"❌ URL取得エラー: {e}")
        return None

def create_company_tables_via_railway(database_url):
    """Railway CLI経由で企業管理テーブルを作成"""
    print(f"\n=== Railway経由企業管理テーブル作成 ===")
    
    try:
        # SQLファイルを作成
        sql_content = """
-- 企業管理テーブル作成SQL
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
"""
        
        # 一時SQLファイルを作成
        with open('temp_company_tables.sql', 'w') as f:
            f.write(sql_content)
        
        print("📋 SQLファイル作成完了")
        
        # Railway CLIでSQLを実行
        print("🚀 Railway CLIでSQLを実行中...")
        result = subprocess.run(['railway', 'run', 'psql', '-f', 'temp_company_tables.sql'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 企業管理テーブル作成完了")
            print("出力:")
            print(result.stdout)
        else:
            print(f"❌ SQL実行失敗: {result.stderr}")
            return False
        
        # 一時ファイルを削除
        os.remove('temp_company_tables.sql')
        
        return True
        
    except Exception as e:
        print(f"❌ テーブル作成エラー: {e}")
        return False

def create_company_tables_direct(database_url):
    """直接接続で企業管理テーブルを作成"""
    print(f"\n=== 直接接続企業管理テーブル作成 ===")
    
    try:
        # PostgreSQLに直接接続
        print(f"🔗 PostgreSQLに接続中...")
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        
        # 接続情報を表示
        c.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port()")
        db_info = c.fetchone()
        print(f"✅ 接続成功")
        print(f"  データベース: {db_info[0]}")
        print(f"  ユーザー: {db_info[1]}")
        print(f"  サーバー: {db_info[2]}:{db_info[3]}")
        
        # 企業管理テーブルを作成
        print("🚀 企業管理テーブル作成中...")
        
        # 1. 企業基本情報テーブル
        c.execute('''
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
            )
        ''')
        
        # 2. 企業LINEアカウントテーブル
        c.execute('''
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
            )
        ''')
        
        # 3. 企業決済情報テーブル
        c.execute('''
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
            )
        ''')
        
        # 4. 企業コンテンツ管理テーブル
        c.execute('''
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
            )
        ''')
        
        # 5. 企業通知設定テーブル
        c.execute('''
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
            )
        ''')
        
        # 6. 企業解約履歴テーブル
        c.execute('''
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
            )
        ''')
        
        # 7. 企業ユーザー管理テーブル
        c.execute('''
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
            )
        ''')
        
        conn.commit()
        print("✅ 企業管理テーブル作成完了")
        
        # 作成後のテーブル一覧を確認
        c.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name LIKE 'company%'
            ORDER BY table_name
        """)
        created_tables = c.fetchall()
        
        print(f"\n📋 作成された企業管理テーブル:")
        for table in created_tables:
            print(f"  - {table[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン処理"""
    print("=== Railway CLI接続・企業管理テーブル作成 ===")
    
    # 1. Railway CLIをインストール
    if not install_railway_cli():
        print("❌ Railway CLIインストールに失敗しました")
        return False
    
    # 2. Railwayにログイン
    if not railway_login():
        print("❌ Railwayログインに失敗しました")
        return False
    
    # 3. プロジェクトにリンク
    if not railway_link_project():
        print("❌ プロジェクトリンクに失敗しました")
        return False
    
    # 4. データベースURLを取得
    database_url = get_railway_database_url()
    if not database_url:
        print("❌ データベースURLを取得できませんでした")
        return False
    
    # 5. 企業管理テーブルを作成（複数の方法を試行）
    success = False
    
    # 方法1: Railway CLI経由
    print("\n🔄 方法1: Railway CLI経由でテーブル作成を試行...")
    success = create_company_tables_via_railway(database_url)
    
    if not success:
        # 方法2: 直接接続
        print("\n🔄 方法2: 直接接続でテーブル作成を試行...")
        success = create_company_tables_direct(database_url)
    
    if success:
        print(f"\n🎉 企業管理テーブルの作成が完了しました！")
        print(f"💡 PostgreSQL管理画面を更新して企業管理テーブルを確認してください")
        return True
    else:
        print(f"\n❌ すべての方法でテーブル作成に失敗しました")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 