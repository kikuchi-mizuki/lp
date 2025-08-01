#!/usr/bin/env python3
"""
company_deploymentsテーブルの詳細確認
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import get_db_connection

def check_deployment_status():
    """company_deploymentsテーブルの詳細を確認"""
    
    print("=== company_deployments テーブル詳細確認 ===")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 全レコードを取得
        c.execute('SELECT * FROM company_deployments ORDER BY created_at DESC')
        results = c.fetchall()
        
        if results:
            print(f"📊 レコード数: {len(results)}件")
            print("\n最新のレコード:")
            for i, row in enumerate(results[:3]):  # 最新3件を表示
                print(f"\n--- レコード {i+1} ---")
                print(f"ID: {row[0]}")
                print(f"Company ID: {row[1]}")
                print(f"Railway Project ID: {row[2]}")
                print(f"Railway URL: {row[3]}")
                print(f"Deployment Status: {row[4]}")
                print(f"Deployment Log: {row[5][:200] if row[5] else 'None'}...")
                print(f"Environment Variables: {row[6][:200] if row[6] else 'None'}...")
                print(f"Created At: {row[7]}")
        else:
            print("❌ company_deployments テーブルにデータがありません")
        
        # 企業ID 30のレコードを確認
        c.execute('SELECT * FROM company_deployments WHERE company_id = 30')
        result = c.fetchone()
        
        if result:
            print(f"\n✅ 企業ID 30のデプロイ情報:")
            print(f"Railway Project ID: {result[2]}")
            print(f"Railway URL: {result[3]}")
            print(f"Deployment Status: {result[4]}")
        else:
            print(f"\n❌ 企業ID 30のデプロイ情報がありません")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    check_deployment_status() 