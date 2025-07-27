import os
import psycopg2
import sqlite3
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv('DATABASE_URL', 'database.db')

def get_db_connection():
    """データベース接続を取得"""
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith('postgresql://'):
        # PostgreSQL接続
        return psycopg2.connect(database_url)
    elif database_url and database_url.startswith('sqlite://'):
        # SQLite接続（URL形式）
        db_path = database_url.replace('sqlite://', '')
        return sqlite3.connect(db_path)
    elif database_url and not database_url.startswith(('postgresql://', 'sqlite://')):
        # SQLite接続（ファイルパス形式）
        return sqlite3.connect(database_url)
    else:
        # ローカル開発用（PostgreSQL）
        try:
            return psycopg2.connect(
                host="localhost",
                database="ai_collections",
                user="postgres",
                password="password"
            )
        except:
            # PostgreSQL接続に失敗した場合はSQLiteを使用
            return sqlite3.connect('database.db')

def get_db_type():
    """データベースタイプを取得（postgresql または sqlite）"""
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith('postgresql://'):
        return 'postgresql'
    elif database_url and database_url.startswith('sqlite://'):
        return 'sqlite'
    elif database_url and not database_url.startswith(('postgresql://', 'sqlite://')):
        return 'sqlite'
    else:
        # ローカル開発用（PostgreSQL）
        try:
            psycopg2.connect(
                host="localhost",
                database="ai_collections",
                user="postgres",
                password="password"
            )
            return 'postgresql'
        except:
            return 'sqlite'

def migrate_add_pending_charge():
    """pending_chargeカラムを追加するマイグレーション"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # pending_chargeカラムが存在するかチェック
        c.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'usage_logs' AND column_name = 'pending_charge'
        """)
        
        if not c.fetchone():
            # pending_chargeカラムを追加
            c.execute("""
                ALTER TABLE usage_logs 
                ADD COLUMN pending_charge BOOLEAN DEFAULT FALSE
            """)
            conn.commit()
            print("✅ pending_chargeカラムを追加しました")
        else:
            print("ℹ️ pending_chargeカラムは既に存在します")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ マイグレーションエラー: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_add_pending_charge() 