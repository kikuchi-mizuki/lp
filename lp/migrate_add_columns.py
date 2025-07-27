import os
import sys
sys.path.append('.')

from utils.db import get_db_connection

print('=== カラム追加マイグレーション ===')

try:
    conn = get_db_connection()
    c = conn.cursor()
    
    # 既存のカラムを確認
    c.execute("PRAGMA table_info(usage_logs)")
    columns = [column[1] for column in c.fetchall()]
    
    print('現在のカラム:', columns)
    
    # content_typeカラムを追加
    if 'content_type' not in columns:
        c.execute("ALTER TABLE usage_logs ADD COLUMN content_type VARCHAR(255)")
        print('✅ content_typeカラムを追加しました')
    else:
        print('ℹ️ content_typeカラムは既に存在します')
    
    # is_freeカラムを追加
    if 'is_free' not in columns:
        c.execute("ALTER TABLE usage_logs ADD COLUMN is_free BOOLEAN DEFAULT FALSE")
        print('✅ is_freeカラムを追加しました')
    else:
        print('ℹ️ is_freeカラムは既に存在します')
    
    conn.commit()
    
    # 更新後のカラムを確認
    c.execute("PRAGMA table_info(usage_logs)")
    updated_columns = [column[1] for column in c.fetchall()]
    print('更新後のカラム:', updated_columns)
    
    conn.close()
    print('✅ マイグレーション完了')
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 