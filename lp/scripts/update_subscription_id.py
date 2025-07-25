#!/usr/bin/env python3
"""
データベースのサブスクリプションIDを更新するスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from utils.db import get_db_connection

def update_subscription_id():
    """データベースのサブスクリプションIDを更新"""
    old_subscription_id = 'sub_1RorXVIxg6C5hAVdvE7sSTeA'
    new_subscription_id = 'sub_1RorbZIxg6C5hAVdJsW2k1Ow'
    
    print(f"データベースのサブスクリプションIDを更新中...")
    print(f"Old: {old_subscription_id}")
    print(f"New: {new_subscription_id}")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 古いサブスクリプションIDを持つユーザーを検索
        c.execute('SELECT id, email FROM users WHERE stripe_subscription_id = ?', (old_subscription_id,))
        users = c.fetchall()
        
        if users:
            print(f"更新対象ユーザー数: {len(users)}")
            for user in users:
                user_id, email = user
                print(f"ユーザー {user_id} ({email}) を更新中...")
                
                # サブスクリプションIDを更新
                c.execute('UPDATE users SET stripe_subscription_id = ? WHERE id = ?', (new_subscription_id, user_id))
                print(f"✅ ユーザー {user_id} の更新完了")
        else:
            print("更新対象のユーザーが見つかりませんでした")
        
        conn.commit()
        conn.close()
        print("✅ データベース更新完了")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == '__main__':
    update_subscription_id() 