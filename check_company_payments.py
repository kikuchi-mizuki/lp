#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
company_paymentsテーブルの詳細を確認するスクリプト
"""

import os
import sys
sys.path.append('lp')

from utils.db import get_db_connection

def check_company_payments():
    """company_paymentsテーブルの詳細を確認"""
    try:
        print("=== company_paymentsテーブル詳細確認 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # company_paymentsテーブルの全データを取得
        c.execute('''
            SELECT 
                id, company_id, stripe_customer_id, stripe_subscription_id,
                subscription_status, current_period_start, current_period_end,
                created_at, updated_at
            FROM company_payments
            ORDER BY created_at DESC
        ''')
        
        payments = c.fetchall()
        print(f"📊 company_paymentsテーブル: {len(payments)}件")
        
        for payment in payments:
            print(f"\n--- 決済レコード {payment[0]} ---")
            print(f"  企業ID: {payment[1]}")
            print(f"  Stripe顧客ID: {payment[2]}")
            print(f"  StripeサブスクリプションID: {payment[3]}")
            print(f"  サブスクリプション状態: {payment[4]}")
            print(f"  期間開始: {payment[5]}")
            print(f"  期間終了: {payment[6]}")
            print(f"  作成日時: {payment[7]}")
            print(f"  更新日時: {payment[8]}")
        
        # 企業情報も確認
        print(f"\n=== 企業情報 ===")
        c.execute('''
            SELECT id, company_name, line_user_id, stripe_subscription_id, status
            FROM companies
        ''')
        
        companies = c.fetchall()
        for company in companies:
            print(f"\n--- 企業 {company[0]} ---")
            print(f"  企業名: {company[1]}")
            print(f"  LINEユーザーID: {company[2]}")
            print(f"  StripeサブスクリプションID: {company[3]}")
            print(f"  状態: {company[4]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_company_payments() 