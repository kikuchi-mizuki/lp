#!/usr/bin/env python3
"""
新しいテストユーザー作成
"""

import os
from dotenv import load_dotenv
from utils.db import get_db_connection

# 環境変数を読み込み
load_dotenv()

def create_new_test_user():
    """新しいテストユーザーを作成"""
    print("=== 新しいテストユーザー作成 ===")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 新しいテストユーザーを作成
        test_line_user_id = "U1234567890abcdef"
        test_stripe_customer_id = "cus_test123456789"
        test_stripe_subscription_id = "sub_test123456789"
        test_email = "test@example.com"
        
        c.execute('''
            INSERT INTO users (line_user_id, stripe_customer_id, stripe_subscription_id, email, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        ''', (test_line_user_id, test_stripe_customer_id, test_stripe_subscription_id, test_email))
        
        conn.commit()
        conn.close()
        
        print(f"✅ 新しいテストユーザー作成成功:")
        print(f"  - LINE User ID: {test_line_user_id}")
        print(f"  - Stripe Customer ID: {test_stripe_customer_id}")
        print(f"  - Stripe Subscription ID: {test_stripe_subscription_id}")
        print(f"  - Email: {test_email}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    create_new_test_user() 