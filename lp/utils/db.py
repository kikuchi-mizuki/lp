import os
import psycopg2
import sqlite3
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv('DATABASE_URL', 'database.db')


def get_db_connection():
    """データベース接続を取得（改善版）"""
    # 機密情報をログに出さないよう、存在フラグのみ出力
    railway_url_env = os.getenv('RAILWAY_DATABASE_URL')
    database_url_env = os.getenv('DATABASE_URL')
    print(f"[DEBUG] DB URL presence: RAILWAY_DATABASE_URL={'set' if railway_url_env else 'unset'}, DATABASE_URL={'set' if database_url_env else 'unset'}")

    database_url = railway_url_env or database_url_env

    if database_url and database_url.startswith('postgresql://'):
        # PostgreSQL接続
        try:
            return psycopg2.connect(database_url)
        except Exception as e:
            print(f'[ERROR] PostgreSQL接続エラー: {e}')
            # フォールバック: ローカルPostgreSQL
            try:
                return psycopg2.connect(
                    host="localhost",
                    database="ai_collections",
                    user="postgres",
                    password="password"
                )
            except Exception:
                # 最終フォールバック: SQLite
                return sqlite3.connect('database.db')
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
        except Exception:
            # PostgreSQL接続に失敗した場合はSQLiteを使用
            return sqlite3.connect('database.db')


def get_db_type():
    """データベースタイプを取得（postgresql または sqlite）"""
    database_url = os.getenv('RAILWAY_DATABASE_URL') or os.getenv('DATABASE_URL')
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
        
        # データベースタイプを確認
        db_type = get_db_type()
        
        if db_type == 'postgresql':
            # PostgreSQL用のマイグレーション
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
        else:
            # SQLite用のマイグレーション
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