#!/usr/bin/env python3
"""
古いcompany_subscriptionsテーブルのデータを削除して、新しい請求システムとの競合を解決
"""
import os, sys
from dotenv import load_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
from utils.db import get_db_connection, get_db_type

def fix_billing_system_conflict():
    print("🚀 請求システム競合の修正を開始します")
    try:
        conn = get_db_connection()
        c = conn.cursor()
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        print("=== 修正前の状況確認 ===")
        c.execute(f'SELECT * FROM company_subscriptions WHERE company_id = {placeholder}', (5,))
        old_subs = c.fetchall()
        print(f"古いサブスクリプション数: {len(old_subs)}")
        for sub in old_subs:
            print(f"  - ID: {sub[0]}, コンテンツ: {sub[2]}, ステータス: {sub[3]}")
        
        print("\n=== 新しいシステムの状況確認 ===")
        c.execute(f'SELECT * FROM company_monthly_subscriptions WHERE company_id = {placeholder}', (5,))
        monthly_subs = c.fetchall()
        print(f"月額サブスクリプション数: {len(monthly_subs)}")
        
        c.execute(f'SELECT * FROM company_content_additions WHERE company_id = {placeholder}', (5,))
        content_additions = c.fetchall()
        print(f"コンテンツ追加数: {len(content_additions)}")
        for addition in content_additions:
            print(f"  - コンテンツ: {addition[2]}, 追加料金: {addition[3]}円, ステータス: {addition[4]}")
        
        print("\n=== 古いサブスクリプションデータを削除 ===")
        c.execute(f'DELETE FROM company_subscriptions WHERE company_id = {placeholder}', (5,))
        deleted_count = c.rowcount
        print(f"✅ {deleted_count}件の古いサブスクリプションを削除しました")
        
        conn.commit()
        
        print("\n=== 修正後の状況確認 ===")
        c.execute(f'SELECT * FROM company_subscriptions WHERE company_id = {placeholder}', (5,))
        remaining_old_subs = c.fetchall()
        print(f"残存する古いサブスクリプション数: {len(remaining_old_subs)}")
        
        print("\n=== 新しいシステムの最終確認 ===")
        c.execute(f'SELECT content_type, additional_price, status FROM company_content_additions WHERE company_id = {placeholder}', (5,))
        final_content_additions = c.fetchall()
        print("アクティブなコンテンツ:")
        for addition in final_content_additions:
            content_type, additional_price, status = addition
            if status == 'active':
                price_text = f"+{additional_price}円/月" if additional_price > 0 else "(基本料金に含まれる)"
                print(f"  - {content_type}: {price_text}")
        
        conn.close()
        print("\n✅ 請求システム競合の修正完了")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_billing_system_conflict()
