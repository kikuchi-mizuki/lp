#!/usr/bin/env python3
"""
テストユーザーを作成するスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from utils.db import get_db_connection

def create_test_user():
    """テストユーザーを作成"""
    email = 'mmms.dy.23@gmail.com'
    customer_id = 'cus_SkMGzumL3BMssw'
    subscription_id = 'sub_1RorbZIxg6C5hAVdJsW2k1Ow'
    
    print(f"テストユーザーを作成中...")
    print(f"Email: {email}")
    print(f"Customer ID: {customer_id}")
    print(f"Subscription ID: {subscription_id}")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # ユーザーを作成
        c.execute('INSERT INTO users (email, stripe_customer_id, stripe_subscription_id) VALUES (?, ?, ?)', 
                  (email, customer_id, subscription_id))
        
        conn.commit()
        conn.close()
        print("✅ テストユーザー作成完了")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == '__main__':
    create_test_user() 