#!/usr/bin/env python3
"""
get_company_info関数の動作を詳しくデバッグするスクリプト
"""
import os, sys
from dotenv import load_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
from utils.db import get_db_connection, get_db_type

def debug_company_info():
    print("🚀 get_company_info関数のデバッグを開始します")
    try:
        user_id = "U1b9d0d75b0c770dc1107dde349d572f7"
        print(f"テスト用LINEユーザーID: {user_id}")
        
        conn = get_db_connection()
        c = conn.cursor()
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        print("\n=== companiesテーブル検索 ===")
        c.execute(f'SELECT id, company_name, line_user_id FROM companies WHERE line_user_id = {placeholder}', (user_id,))
        company = c.fetchone()
        print(f'[DEBUG] 企業データ検索結果: {company}')
        
        if not company:
            print("❌ 企業が見つかりません")
            conn.close()
            return
        
        company_id = company[0]
        print(f"企業ID: {company_id}")
        
        print("\n=== 月額基本サブスクリプション検索 ===")
        c.execute(f'SELECT stripe_subscription_id, subscription_status FROM company_monthly_subscriptions WHERE company_id = {placeholder}', (company_id,))
        monthly_subscription = c.fetchone()
        print(f'[DEBUG] 月額基本サブスクリプション: {monthly_subscription}')
        
        if not monthly_subscription:
            print("❌ 月額基本サブスクリプションが見つかりません")
            conn.close()
            return
        
        stripe_subscription_id, subscription_status = monthly_subscription
        print(f'[DEBUG] 月額基本サブスクリプション: stripe_subscription_id={stripe_subscription_id}, status={subscription_status}')
        
        if subscription_status != 'active':
            print(f"❌ 月額サブスクリプションが非アクティブ: status={subscription_status}")
            conn.close()
            return
        
        print("✅ get_company_info関数は正常に動作しています")
        print(f"返却値: company_id={company_id}, stripe_subscription_id={stripe_subscription_id}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_company_info()
