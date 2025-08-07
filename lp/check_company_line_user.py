#!/usr/bin/env python3
"""
企業のLINEユーザーIDを確認するスクリプト
"""
import os, sys
from dotenv import load_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
from utils.db import get_db_connection, get_db_type

def check_company_line_user():
    print("🚀 企業のLINEユーザーID確認を開始します")
    try:
        conn = get_db_connection()
        c = conn.cursor()
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        print("=== companiesテーブル確認 ===")
        c.execute(f'SELECT id, company_name, line_user_id FROM companies WHERE id = {placeholder}', (5,))
        company = c.fetchone()
        if company:
            company_id, company_name, line_user_id = company
            print(f"企業ID: {company_id}")
            print(f"企業名: {company_name}")
            print(f"LINEユーザーID: {line_user_id}")
        else:
            print("❌ 企業が見つかりません")
            return
        
        print("\n=== 月額サブスクリプション確認 ===")
        c.execute(f'SELECT subscription_status, stripe_subscription_id FROM company_monthly_subscriptions WHERE company_id = {placeholder}', (5,))
        monthly_sub = c.fetchone()
        if monthly_sub:
            status, stripe_id = monthly_sub
            print(f"ステータス: {status}")
            print(f"Stripe ID: {stripe_id}")
        else:
            print("❌ 月額サブスクリプションが見つかりません")
        
        print("\n=== コンテンツ追加確認 ===")
        c.execute(f'SELECT content_type, additional_price, status FROM company_content_additions WHERE company_id = {placeholder}', (5,))
        content_additions = c.fetchall()
        for addition in content_additions:
            content_type, additional_price, status = addition
            price_text = f"+{additional_price}円/月" if additional_price > 0 else "(基本料金に含まれる)"
            print(f"  - {content_type}: {price_text} ({status})")
        
        conn.close()
        print("\n✅ 企業のLINEユーザーID確認完了")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_company_line_user()
