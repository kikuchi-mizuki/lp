import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv('DATABASE_URL', 'database.db')

def get_db_connection():
    """データベース接続を取得"""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)
    else:
        # ローカル開発用
        return psycopg2.connect(
            host="localhost",
            database="ai_collections",
            user="postgres",
            password="password"
        )

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