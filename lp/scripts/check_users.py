#!/usr/bin/env python3
"""
データベースのユーザー一覧を確認するスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from utils.db import get_db_connection

def check_users():
    """データベースのユーザー一覧を確認"""
    print(f"データベースのユーザー一覧を確認中...")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 全ユーザーを取得
        c.execute('SELECT id, email, stripe_customer_id, stripe_subscription_id FROM users')
        users = c.fetchall()
        
        print(f"✅ ユーザー一覧取得成功")
        print(f"Total Users: {len(users)}")
        
        print(f"\n=== ユーザー一覧 ===")
        for user in users:
            user_id, email, customer_id, subscription_id = user
            print(f"User ID: {user_id}")
            print(f"  Email: {email}")
            print(f"  Customer ID: {customer_id}")
            print(f"  Subscription ID: {subscription_id}")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == '__main__':
    check_users() 