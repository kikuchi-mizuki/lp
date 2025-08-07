#!/usr/bin/env python3
"""
古いcompany_subscriptionsテーブルのcanceledレコードを削除するスクリプト
"""

import os
import sys
from dotenv import load_dotenv

# 現在のディレクトリをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils.db import get_db_connection, get_db_type

def fix_old_subscriptions_table():
    """古いcompany_subscriptionsテーブルのcanceledレコードを削除"""
    print("🚀 古いサブスクリプションテーブルの修正を開始します")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプを取得
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        print("=== 修正前の状況確認 ===")
        c.execute(f'SELECT id, company_id, content_type, subscription_status, stripe_subscription_id FROM company_subscriptions WHERE company_id = 5')
        old_subscriptions = c.fetchall()
        
        for sub in old_subscriptions:
            print(f"ID: {sub[0]}, 企業ID: {sub[1]}, コンテンツ: {sub[2]}, ステータス: {sub[3]}, Stripe ID: {sub[4]}")
        
        # canceledステータスのレコードを削除
        print("\n=== canceledレコードを削除 ===")
        c.execute(f'DELETE FROM company_subscriptions WHERE company_id = %s AND subscription_status = %s', (5, 'canceled'))
        deleted_count = c.rowcount
        print(f"✅ {deleted_count}件のcanceledレコードを削除しました")
        
        conn.commit()
        
        print("\n=== 修正後の状況確認 ===")
        c.execute(f'SELECT id, company_id, content_type, subscription_status, stripe_subscription_id FROM company_subscriptions WHERE company_id = 5')
        remaining_subscriptions = c.fetchall()
        
        for sub in remaining_subscriptions:
            print(f"ID: {sub[0]}, 企業ID: {sub[1]}, コンテンツ: {sub[2]}, ステータス: {sub[3]}, Stripe ID: {sub[4]}")
        
        # 新しいシステムとの整合性確認
        print("\n=== 新しいシステムとの整合性確認 ===")
        
        # 月額サブスクリプション確認
        c.execute(f'SELECT subscription_status FROM company_monthly_subscriptions WHERE company_id = 5')
        monthly_status = c.fetchone()
        if monthly_status:
            print(f"月額サブスクリプション: {monthly_status[0]}")
        
        # コンテンツ追加確認
        c.execute(f'SELECT content_type, status FROM company_content_additions WHERE company_id = 5')
        content_additions = c.fetchall()
        for addition in content_additions:
            print(f"コンテンツ追加: {addition[0]} - {addition[1]}")
        
        conn.close()
        print("\n✅ 古いサブスクリプションテーブルの修正完了")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_old_subscriptions_table()
