#!/usr/bin/env python3
"""
新しい請求システム（月額基本料金 + コンテンツ追加料金）の状況確認
"""
import os, sys
from dotenv import load_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
from utils.db import get_db_connection, get_db_type

def check_new_billing_system():
    print("🚀 新しい請求システムの状況確認を開始します")
    try:
        conn = get_db_connection()
        c = conn.cursor()
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        print("=== company_monthly_subscriptions確認 ===")
        c.execute(f'SELECT * FROM company_monthly_subscriptions WHERE company_id = {placeholder}', (5,))
        monthly_subs = c.fetchall()
        if monthly_subs:
            for sub in monthly_subs:
                print(f'月額サブスクリプション: {sub}')
        else:
            print("❌ 月額サブスクリプションが見つかりません")
        
        print("\n=== company_content_additions確認 ===")
        c.execute(f'SELECT * FROM company_content_additions WHERE company_id = {placeholder}', (5,))
        content_additions = c.fetchall()
        if content_additions:
            for addition in content_additions:
                print(f'コンテンツ追加: {addition}')
        else:
            print("❌ コンテンツ追加が見つかりません")
        
        print("\n=== 古いcompany_subscriptions確認 ===")
        c.execute(f'SELECT * FROM company_subscriptions WHERE company_id = {placeholder}', (5,))
        old_subs = c.fetchall()
        if old_subs:
            for sub in old_subs:
                print(f'古いサブスクリプション: {sub}')
        else:
            print("✅ 古いサブスクリプションはありません")
        
        conn.close()
        print("\n✅ 新しい請求システム確認完了")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_new_billing_system()
