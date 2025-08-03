import os
import sqlite3
from sqlite3 import connect

DATABASE_URL = os.getenv('DATABASE_URL', 'database.db')

def get_db_connection():
    """データベース接続を取得（SQLiteのみ）"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url and database_url.startswith('sqlite://'):
        # SQLite接続（URL形式）
        db_path = database_url.replace('sqlite://', '')
        return sqlite3.connect(db_path)
    elif database_url and not database_url.startswith(('postgresql://', 'sqlite://')):
        # SQLite接続（ファイルパス形式）
        return sqlite3.connect(database_url)
    else:
        # デフォルトSQLite
        return sqlite3.connect('database.db')

def get_db_type():
    """データベースタイプを取得（sqlite）"""
    return 'sqlite'

def migrate_add_pending_charge():
    """pending_chargeカラムを追加するマイグレーション（SQLite用）"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # pending_chargeカラムが存在するかチェック
        c.execute("PRAGMA table_info(usage_logs)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'pending_charge' not in columns:
            # pending_chargeカラムを追加
            c.execute("ALTER TABLE usage_logs ADD COLUMN pending_charge BOOLEAN DEFAULT 0")
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