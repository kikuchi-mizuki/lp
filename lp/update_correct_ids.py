import os
import sys
sys.path.append('.')

from utils.db import get_db_connection

print('=== 正しいIDでデータベース更新 ===')

try:
    # 正しいID
    correct_customer_id = 'cus_Sl1XN0iy5yAPKV'
    correct_subscription_id = 'sub_1RpVU2Ixg6C5hAVdeyAz8Tjk'
    
    # データベース接続
    conn = get_db_connection()
    c = conn.cursor()
    
    # 現在の状況を確認
    c.execute("SELECT id, email, stripe_customer_id, stripe_subscription_id FROM users WHERE id = 1")
    user = c.fetchone()
    
    if user:
        print(f'現在の状況:')
        print(f'  顧客ID: {user[2]}')
        print(f'  サブスクリプションID: {user[3]}')
        
        print(f'\n正しいID:')
        print(f'  顧客ID: {correct_customer_id}')
        print(f'  サブスクリプションID: {correct_subscription_id}')
        
        # データベースを更新
        c.execute("UPDATE users SET stripe_customer_id = ?, stripe_subscription_id = ? WHERE id = 1", 
                 (correct_customer_id, correct_subscription_id))
        conn.commit()
        
        print(f'\n✅ データベースを更新しました')
        
        # 更新後の確認
        c.execute("SELECT id, email, stripe_customer_id, stripe_subscription_id FROM users WHERE id = 1")
        updated_user = c.fetchone()
        print(f'\n更新後の状況:')
        print(f'  顧客ID: {updated_user[2]}')
        print(f'  サブスクリプションID: {updated_user[3]}')
        
    else:
        print('❌ ユーザーが見つかりません')
    
    conn.close()
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 