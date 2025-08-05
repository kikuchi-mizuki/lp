import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """データベース接続を取得（PostgreSQLまたはSQLite）"""
    database_url = os.getenv('DATABASE_URL', 'database.db')
    
    if database_url.startswith('postgresql://'):
        # PostgreSQL接続
        return psycopg2.connect(database_url)
    else:
        # SQLite接続
        return sqlite3.connect(database_url)

print('=== 実際のデータベース確認 ===')

try:
    # データベースに接続
    conn = get_db_connection()
    c = conn.cursor()
    
    # データベースタイプを確認
    database_url = os.getenv('DATABASE_URL', 'database.db')
    is_postgresql = database_url.startswith('postgresql://')
    
    if is_postgresql:
        # PostgreSQL用のテーブル一覧取得
        c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = c.fetchall()
        print('テーブル一覧:', [table[0] for table in tables])
        
        # usage_logsテーブルの構造を確認
        c.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'usage_logs'")
        columns = c.fetchall()
        print('\nusage_logsテーブルのカラム:')
        for column in columns:
            print(f'  {column[0]} ({column[1]})')
    else:
        # SQLite用のテーブル一覧取得
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = c.fetchall()
        print('テーブル一覧:', [table[0] for table in tables])
        
        # usage_logsテーブルの構造を確認
        c.execute("PRAGMA table_info(usage_logs)")
        columns = c.fetchall()
        print('\nusage_logsテーブルのカラム:')
        for column in columns:
            print(f'  {column[1]} ({column[2]})')
    
    # 実際のデータを確認
    c.execute('SELECT COUNT(*) FROM usage_logs')
    total_count = c.fetchone()[0]
    print(f'\n総レコード数: {total_count}')
    
    if total_count > 0:
        c.execute('''
            SELECT id, user_id, usage_quantity, stripe_usage_record_id, 
                   pending_charge, content_type, is_free, created_at
            FROM usage_logs 
            ORDER BY created_at
        ''')
        records = c.fetchall()
        
        print('\n=== 詳細記録 ===')
        for i, record in enumerate(records):
            print(f'記録 {i+1}: ID={record[0]}, ユーザー={record[1]}, 数量={record[2]}, StripeID={record[3]}, 課金予定={record[4]}, コンテンツ={record[5]}, 無料={record[6]}, 作成日={record[7]}')
    
    conn.close()
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 