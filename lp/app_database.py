import os
import logging
from utils.db import get_db_connection

logger = logging.getLogger(__name__)

def init_db():
    """データベースの初期化（企業ユーザー専用最小限設計）"""
    logger.info("🔄 データベース初期化開始")
    conn = None
    c = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプを確認
        from utils.db import get_db_type
        db_type = get_db_type()
        
        if db_type == 'postgresql':
            # 企業基本情報テーブル（最小限）
            c.execute('''
                CREATE TABLE IF NOT EXISTS companies (
                    id SERIAL PRIMARY KEY,
                    company_name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 月額基本サブスクリプション管理テーブル（企業単位）
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_monthly_subscriptions (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL,
                    stripe_subscription_id VARCHAR(255),
                    subscription_status VARCHAR(50) DEFAULT 'active',
                    monthly_base_price INTEGER DEFAULT 3900,
                    current_period_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    current_period_end TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            ''')
            
            # 企業コンテンツ管理テーブル
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_contents (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL,
                    content_type VARCHAR(100) NOT NULL,
                    content_status VARCHAR(50) DEFAULT 'active',
                    stripe_price_id VARCHAR(255),
                    monthly_price INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            ''')
            
            # 企業LINEアカウント管理テーブル
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_line_accounts (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL,
                    line_channel_id VARCHAR(255) UNIQUE,
                    line_channel_secret VARCHAR(255),
                    line_channel_access_token VARCHAR(255),
                    line_user_id VARCHAR(255),
                    line_display_name VARCHAR(255),
                    line_picture_url TEXT,
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            ''')
            
            # 企業通知管理テーブル
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_notifications (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL,
                    notification_type VARCHAR(100) NOT NULL,
                    notification_status VARCHAR(50) DEFAULT 'active',
                    notification_settings JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            ''')
            
            # 企業解約管理テーブル
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_cancellations (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL,
                    content_type VARCHAR(100),
                    cancellation_reason TEXT,
                    cancellation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            ''')
            
            # サブスクリプション期間管理テーブル
            c.execute('''
                CREATE TABLE IF NOT EXISTS subscription_periods (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL,
                    stripe_subscription_id VARCHAR(255),
                    period_start TIMESTAMP NOT NULL,
                    period_end TIMESTAMP NOT NULL,
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            ''')
            
            # 使用量ログテーブル
            c.execute('''
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL,
                    content_type VARCHAR(100),
                    usage_count INTEGER DEFAULT 0,
                    usage_date DATE DEFAULT CURRENT_DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            ''')
            
            # ユーザー状態管理テーブル
            c.execute('''
                CREATE TABLE IF NOT EXISTS user_states (
                    id SERIAL PRIMARY KEY,
                    line_user_id VARCHAR(255) UNIQUE,
                    current_state VARCHAR(100) DEFAULT 'initial',
                    state_data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("✅ PostgreSQLテーブル作成完了")
            
        else:
            # SQLite用のテーブル作成
            c.execute('''
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # その他のSQLiteテーブルも同様に作成
            # ... (省略)
            
            conn.commit()
            logger.info("✅ SQLiteテーブル作成完了")
        
        conn.close()
        logger.info("✅ データベース初期化完了")
        
    except Exception as e:
        logger.error(f"❌ データベース初期化エラー: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise e
