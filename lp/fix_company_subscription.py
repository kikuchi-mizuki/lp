#!/usr/bin/env python3
"""
企業サブスクリプションのステータスをactiveに修正するスクリプト
"""

import os
import sys
from dotenv import load_dotenv

# 現在のディレクトリをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils.db import get_db_connection, get_db_type

def fix_company_subscription_status():
    """企業サブスクリプションのステータスをactiveに修正"""
    print("🚀 企業サブスクリプションステータス修正を開始します")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプを取得
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        print("=== 修正前の状況 ===")
        c.execute(f'SELECT id, company_id, content_type, subscription_status, stripe_subscription_id FROM company_subscriptions ORDER BY id')
        subscriptions = c.fetchall()
        
        for sub in subscriptions:
            print(f"ID: {sub[0]}, 企業ID: {sub[1]}, コンテンツ: {sub[2]}, ステータス: {sub[3]}, Stripe ID: {sub[4]}")
        
        print("\n=== ステータスをactiveに修正 ===")
        c.execute(f'UPDATE company_subscriptions SET subscription_status = {placeholder} WHERE subscription_status = {placeholder}', ('active', 'canceled'))
        updated_count = c.rowcount
        print(f"✅ {updated_count}件のサブスクリプションをactiveに修正しました")
        
        conn.commit()
        
        print("\n=== 修正後の状況 ===")
        c.execute(f'SELECT id, company_id, content_type, subscription_status, stripe_subscription_id FROM company_subscriptions ORDER BY id')
        subscriptions = c.fetchall()
        
        for sub in subscriptions:
            print(f"ID: {sub[0]}, 企業ID: {sub[1]}, コンテンツ: {sub[2]}, ステータス: {sub[3]}, Stripe ID: {sub[4]}")
        
        conn.close()
        print("\n✅ 企業サブスクリプションステータス修正完了")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_company_subscription_status()
