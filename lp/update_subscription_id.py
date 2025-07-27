import os
import sys
sys.path.append('.')

from utils.db import get_db_connection

print('=== サブスクリプションID更新 ===')

try:
    # 新しいサブスクリプションID
    new_subscription_id = 'sub_1BpVU2lxg6C5hAVdevAz8Tik'
    
    # データベース接続
    conn = get_db_connection()
    c = conn.cursor()
    
    # 現在のサブスクリプションIDを確認
    c.execute("SELECT id, email, stripe_subscription_id FROM users WHERE id = 1")
    user = c.fetchone()
    
    if user:
        print(f'現在のサブスクリプションID: {user[2]}')
        print(f'新しいサブスクリプションID: {new_subscription_id}')
        
        # サブスクリプションIDを更新
        c.execute("UPDATE users SET stripe_subscription_id = ? WHERE id = 1", (new_subscription_id,))
        conn.commit()
        
        print(f'✅ サブスクリプションIDを更新しました')
        
        # 更新後の確認
        c.execute("SELECT id, email, stripe_subscription_id FROM users WHERE id = 1")
        updated_user = c.fetchone()
        print(f'更新後のサブスクリプションID: {updated_user[2]}')
        
    else:
        print('❌ ユーザーが見つかりません')
    
    conn.close()
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 