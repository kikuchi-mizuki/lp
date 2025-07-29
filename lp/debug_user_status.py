#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.append('.')

from services.user_service import is_paid_user, get_user_by_line_id
from services.stripe_service import check_subscription_status
from utils.db import get_db_connection

def debug_user_status(line_user_id):
    """ユーザーの決済状況を詳細にデバッグ"""
    print(f"=== ユーザー決済状況デバッグ ===\n")
    print(f"LINEユーザーID: {line_user_id}\n")
    
    # 1. データベースからユーザー情報を直接取得
    print("📊 1. データベースからユーザー情報を直接取得:")
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # ユーザー情報を取得
        c.execute('''
            SELECT id, email, stripe_customer_id, stripe_subscription_id, line_user_id, created_at, updated_at
            FROM users 
            WHERE line_user_id = %s
        ''', (line_user_id,))
        
        result = c.fetchone()
        
        if result:
            user_id, email, stripe_customer_id, stripe_subscription_id, line_user_id_db, created_at, updated_at = result
            print(f"  ✅ ユーザーが見つかりました:")
            print(f"    ID: {user_id}")
            print(f"    Email: {email}")
            print(f"    Stripe Customer ID: {stripe_customer_id}")
            print(f"    Stripe Subscription ID: {stripe_subscription_id}")
            print(f"    LINE User ID: {line_user_id_db}")
            print(f"    Created: {created_at}")
            print(f"    Updated: {updated_at}")
        else:
            print(f"  ❌ ユーザーが見つかりません")
            
        conn.close()
        
    except Exception as e:
        print(f"  ❌ データベースエラー: {e}")
    
    # 2. is_paid_user関数の結果を確認
    print(f"\n📊 2. is_paid_user関数の結果:")
    try:
        payment_check = is_paid_user(line_user_id)
        print(f"  is_paid: {payment_check['is_paid']}")
        print(f"  subscription_status: {payment_check['subscription_status']}")
        print(f"  message: {payment_check['message']}")
        print(f"  redirect_url: {payment_check['redirect_url']}")
    except Exception as e:
        print(f"  ❌ is_paid_user関数エラー: {e}")
    
    # 3. Stripeサブスクリプションの状態を直接確認
    print(f"\n📊 3. Stripeサブスクリプションの状態を直接確認:")
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT stripe_subscription_id FROM users WHERE line_user_id = %s', (line_user_id,))
        result = c.fetchone()
        conn.close()
        
        if result and result[0]:
            stripe_subscription_id = result[0]
            print(f"  Stripe Subscription ID: {stripe_subscription_id}")
            
            subscription_status = check_subscription_status(stripe_subscription_id)
            print(f"  Stripe API結果:")
            print(f"    is_active: {subscription_status.get('is_active')}")
            print(f"    status: {subscription_status.get('status')}")
            print(f"    cancel_at_period_end: {subscription_status.get('cancel_at_period_end')}")
            print(f"    current_period_end: {subscription_status.get('current_period_end')}")
        else:
            print(f"  ❌ Stripe Subscription IDが見つかりません")
            
    except Exception as e:
        print(f"  ❌ Stripe確認エラー: {e}")
    
    # 4. 全ユーザーの一覧を確認
    print(f"\n📊 4. 全ユーザーの一覧:")
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            SELECT id, email, stripe_subscription_id, line_user_id, created_at
            FROM users 
            ORDER BY created_at DESC
            LIMIT 10
        ''')
        
        results = c.fetchall()
        conn.close()
        
        print(f"  最新10件のユーザー:")
        for user in results:
            user_id, email, stripe_subscription_id, line_user_id_db, created_at = user
            print(f"    ID: {user_id}, Email: {email}, LINE: {line_user_id_db}, Stripe: {stripe_subscription_id}")
            
    except Exception as e:
        print(f"  ❌ 全ユーザー取得エラー: {e}")

def debug_specific_user():
    """特定のユーザーIDでデバッグ"""
    # 実際のLINEユーザーIDを入力してください
    line_user_id = input("LINEユーザーIDを入力してください: ").strip()
    if line_user_id:
        debug_user_status(line_user_id)
    else:
        print("LINEユーザーIDが入力されていません")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        line_user_id = sys.argv[1]
        debug_user_status(line_user_id)
    else:
        debug_specific_user() 