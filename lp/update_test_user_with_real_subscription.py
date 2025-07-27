#!/usr/bin/env python3
"""
実際のStripeサブスクリプションIDでテストユーザーを更新
"""

import os
from dotenv import load_dotenv
from utils.db import get_db_connection

# 環境変数を読み込み
load_dotenv()

def update_test_user_with_real_subscription():
    """実際のStripeサブスクリプションIDでテストユーザーを更新"""
    print("=== 実際のStripeサブスクリプションIDでテストユーザーを更新 ===")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 実際のStripeサブスクリプションID
        real_stripe_subscription_id = "sub_1RpVU2Ixg6C5hAVdeyAz8Tjk"
        real_stripe_customer_id = "cus_Sl1XN0iy5yAPKV"
        
        # テストユーザーを更新
        c.execute('''
            UPDATE users 
            SET stripe_subscription_id = %s, stripe_customer_id = %s, updated_at = NOW()
            WHERE id = 2
        ''', (real_stripe_subscription_id, real_stripe_customer_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ テストユーザー更新完了:")
        print(f"  - Stripe Subscription ID: {real_stripe_subscription_id}")
        print(f"  - Stripe Customer ID: {real_stripe_customer_id}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    update_test_user_with_real_subscription() 