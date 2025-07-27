#!/usr/bin/env python3
"""
テストユーザー作成
"""

import os
from dotenv import load_dotenv
from utils.db import get_db_connection

# 環境変数を読み込み
load_dotenv()

def create_test_user():
    """テストユーザーを作成"""
    print("=== テストユーザー作成 ===")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # テストユーザーを作成
        test_line_user_id = "U1234567890abcdef"
        test_stripe_customer_id = "cus_Sl1XN0iy5yAPKV"
        test_stripe_subscription_id = "sub_1RpVU2Ixg6C5hAVdeyAz8Tjk"
        
        c.execute('''
            INSERT INTO users (line_user_id, stripe_customer_id, stripe_subscription_id, email, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        ''', (test_line_user_id, test_stripe_customer_id, test_stripe_subscription_id, "test@example.com"))
        
        conn.commit()
        conn.close()
        
        print(f"✅ テストユーザー作成成功: {test_line_user_id}")
        print(f"Stripe Customer ID: {test_stripe_customer_id}")
        print(f"Stripe Subscription ID: {test_stripe_subscription_id}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    create_test_user() 