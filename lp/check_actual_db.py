import sqlite3
import os

print('=== 実際のデータベース確認 ===')

try:
    # 実際のデータベースファイルに接続
    db_path = '../database.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # テーブル一覧を確認
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