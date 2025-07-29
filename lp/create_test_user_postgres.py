#!/usr/bin/env python3
import os
import sys
from utils.db import get_db_connection
from datetime import datetime

def create_test_user_postgres():
    """PostgreSQL用のテストユーザーを作成"""
    try:
        print("=== PostgreSQL用テストユーザー作成 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 新しいテストユーザーを作成
        test_email = "test_postgres@example.com"
        test_line_user_id = "Upostgres123456789"
        test_stripe_subscription_id = "sub_postgres_test_123"
        
        # 既存のユーザーをチェック
        c.execute('SELECT id FROM users WHERE email = %s', (test_email,))
        existing_user = c.fetchone()
        
        if existing_user:
            print(f"ユーザー {test_email} は既に存在します。ID: {existing_user[0]}")
            user_id = existing_user[0]
        else:
            # 新しいユーザーを作成
            c.execute('''
                INSERT INTO users (email, line_user_id, stripe_subscription_id, stripe_customer_id, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            ''', (test_email, test_line_user_id, test_stripe_subscription_id, "cus_postgres_test_123", datetime.now()))
            
            user_id = c.fetchone()[0]
            print(f"新しいユーザーを作成しました。ID: {user_id}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ テストユーザー準備完了")
        print(f"   ユーザーID: {user_id}")
        print(f"   メール: {test_email}")
        print(f"   LINE ID: {test_line_user_id}")
        print(f"   Stripe ID: {test_stripe_subscription_id}")
        
        return user_id
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    create_test_user_postgres() 