import os
import sys
sys.path.append('.')

from utils.db import get_db_connection

print('=== データベーススキーマ確認 ===')

try:
    conn = get_db_connection()
    c = conn.cursor()
    
    # usage_logsテーブルの構造を確認
    c.execute("PRAGMA table_info(usage_logs)")
    columns = c.fetchall()
    
    print('usage_logsテーブルのカラム:')
    for column in columns:
        print(f'  {column[1]} ({column[2]})')
    
    # 実際のデータを確認
    c.execute('SELECT * FROM usage_logs LIMIT 1')
    sample_data = c.fetchone()
    
    if sample_data:
        print(f'\nサンプルデータ: {sample_data}')
    
    conn.close()
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 