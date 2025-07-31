#!/usr/bin/env python3
"""
企業関連データを自動削除するスクリプト
確認なしで実行されます
"""

import os
import sys
import psycopg2
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db import get_db_connection

def clear_company_data_auto():
    """企業関連データを自動削除（確認なし）"""
    try:
        print("=== 企業関連データ自動クリア ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 削除前のデータ数を確認
        c.execute("SELECT COUNT(*) FROM company_deployments")
        deployments_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM company_payments")
        payments_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM company_line_accounts")
        line_accounts_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM companies")
        companies_count = c.fetchone()[0]
        
        print(f"削除されるデータ:")
        print(f"- 企業情報 (companies): {companies_count}件")
        print(f"- LINEアカウント情報 (company_line_accounts): {line_accounts_count}件")
        print(f"- 企業決済情報 (company_payments): {payments_count}件")
        print(f"- 企業デプロイ情報 (company_deployments): {deployments_count}件")
        print(f"\n合計: {companies_count + line_accounts_count + payments_count + deployments_count}件のレコードが削除されます")
        
        # 削除実行
        print("\n🚀 データ削除を開始します...")
        
        # 外部キー制約の順序で削除
        c.execute("DELETE FROM company_deployments")
        print(f"✅ company_deployments: {deployments_count}件削除")
        
        c.execute("DELETE FROM company_payments")
        print(f"✅ company_payments: {payments_count}件削除")
        
        c.execute("DELETE FROM company_line_accounts")
        print(f"✅ company_line_accounts: {line_accounts_count}件削除")
        
        c.execute("DELETE FROM companies")
        print(f"✅ companies: {companies_count}件削除")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 企業関連データの削除が完了しました！")
        print(f"削除時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ データ削除エラー: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    clear_company_data_auto() 