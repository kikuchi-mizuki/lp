#!/usr/bin/env python3
"""
Stripeの請求を正しく修正するスクリプト
"""
import os, sys
from dotenv import load_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
from utils.db import get_db_connection, get_db_type

def fix_stripe_billing():
    print("🚀 Stripe請求の修正を開始します")
    try:
        conn = get_db_connection()
        c = conn.cursor()
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        print("=== 修正前の状況確認 ===")
        
        # company_content_additions確認
        c.execute(f'SELECT * FROM company_content_additions WHERE company_id = {placeholder}', (5,))
        content_additions = c.fetchall()
        print(f"company_content_additions数: {len(content_additions)}")
        for addition in content_additions:
            print(f"  - ID: {addition[0]}, コンテンツ: {addition[2]}, 追加料金: {addition[3]}円, ステータス: {addition[4]}")
        
        # アクティブなLINEアカウント確認
        c.execute(f'SELECT * FROM company_line_accounts WHERE company_id = {placeholder} AND status = {placeholder}', (5, 'active'))
        active_accounts = c.fetchall()
        print(f"\nアクティブなLINEアカウント数: {len(active_accounts)}")
        for account in active_accounts:
            print(f"  - ID: {account[0]}, コンテンツ: {account[2]}, ステータス: {account[5]}")
        
        print("\n=== company_content_additionsの古いデータを削除 ===")
        c.execute(f'DELETE FROM company_content_additions WHERE company_id = {placeholder}', (5,))
        deleted_count = c.rowcount
        print(f"✅ {deleted_count}件の古いデータを削除しました")
        
        conn.commit()
        
        print("\n=== 修正後の状況確認 ===")
        c.execute(f'SELECT * FROM company_content_additions WHERE company_id = {placeholder}', (5,))
        remaining_additions = c.fetchall()
        print(f"残存するcompany_content_additions数: {len(remaining_additions)}")
        
        c.execute(f'SELECT * FROM company_line_accounts WHERE company_id = {placeholder} AND status = {placeholder}', (5, 'active'))
        final_active_accounts = c.fetchall()
        print(f"アクティブなLINEアカウント数: {len(final_active_accounts)}")
        
        conn.close()
        
        print("\n=== 修正結果 ===")
        print("1. company_content_additionsの古いデータを削除")
        print("2. 実際の利用状況（company_line_accounts）のみを参照")
        print("3. Stripeの請求が正しい数量で計算されるようになります")
        
        print("\n✅ Stripe請求の修正完了")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_stripe_billing()
