#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import psycopg2
from datetime import datetime

def check_railway_data():
    """Railwayデータベースの実際のデータを確認"""
    print("=== Railwayデータベースデータ確認 ===\n")
    
    # RailwayデータベースURLを取得
    railway_db_url = os.getenv('RAILWAY_DATABASE_URL')
    if not railway_db_url:
        print("❌ RAILWAY_DATABASE_URLが設定されていません")
        return
    
    try:
        conn = psycopg2.connect(railway_db_url)
        c = conn.cursor()
        
        # subscription_periodsテーブルのデータを確認
        print("📋 subscription_periodsテーブルのデータ:")
        c.execute('''
            SELECT id, user_id, stripe_subscription_id, subscription_status, 
                   current_period_start, current_period_end, created_at
            FROM subscription_periods 
            ORDER BY user_id, created_at DESC
        ''')
        
        results = c.fetchall()
        
        if results:
            for row in results:
                id_val, user_id, stripe_sub_id, status, period_start, period_end, created_at = row
                print(f"  ID: {id_val}, ユーザーID: {user_id}")
                print(f"    Stripe ID: {stripe_sub_id}")
                print(f"    ステータス: {status}")
                print(f"    期間開始: {period_start}")
                print(f"    期間終了: {period_end}")
                print(f"    作成日時: {created_at}")
                print()
        else:
            print("  データが見つかりません")
        
        # usersテーブルのデータを確認
        print("\n📋 usersテーブルのデータ:")
        c.execute('''
            SELECT id, email, stripe_customer_id, stripe_subscription_id, line_user_id, created_at
            FROM users 
            ORDER BY id
        ''')
        
        user_results = c.fetchall()
        
        if user_results:
            for row in user_results:
                id_val, email, customer_id, sub_id, line_id, created_at = row
                print(f"  ID: {id_val}, メール: {email}")
                print(f"    Stripe Customer: {customer_id}")
                print(f"    Stripe Subscription: {sub_id}")
                print(f"    LINE ID: {line_id}")
                print(f"    作成日時: {created_at}")
                print()
        else:
            print("  データが見つかりません")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_railway_data() 