#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
現在のデータ状況を確認するスクリプト
"""

from utils.db import get_db_connection

def check_data_status():
    """現在のデータ状況を確認"""
    try:
        print("=== 現在のデータ状況 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        tables = [
            'companies', 'company_line_accounts', 'company_payments', 
            'company_deployments', 'users', 'usage_logs', 
            'subscription_periods', 'cancellation_history', 'user_states'
        ]
        
        total_records = 0
        
        for table in tables:
            try:
                c.execute(f'SELECT COUNT(*) FROM {table}')
                count = c.fetchone()[0]
                print(f"📊 {table}: {count}件")
                total_records += count
            except Exception as e:
                print(f"❌ {table}: エラー ({e})")
        
        print(f"\n📈 総レコード数: {total_records}件")
        
        # 企業データの詳細
        print(f"\n=== 企業データ詳細 ===")
        c.execute('''
            SELECT c.id, c.company_name, c.company_code, cla.line_channel_id, cla.created_at
            FROM companies c
            LEFT JOIN company_line_accounts cla ON c.id = cla.company_id
            ORDER BY c.id
        ''')
        
        companies = c.fetchall()
        if companies:
            print(f"📋 企業数: {len(companies)}件")
            for company_id, company_name, company_code, line_channel_id, created_at in companies:
                print(f"  - 企業ID {company_id}: {company_name}")
                print(f"    企業コード: {company_code}")
                print(f"    LINEチャネルID: {line_channel_id or '未設定'}")
                print(f"    作成日時: {created_at}")
        else:
            print("📋 企業データ: なし")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ データ状況確認エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_data_status() 