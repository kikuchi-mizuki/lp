#!/usr/bin/env python3
"""
請求データの不整合を確認するスクリプト
"""
import os, sys
from dotenv import load_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
from utils.db import get_db_connection, get_db_type

def check_billing_discrepancy():
    print("🚀 請求データの不整合確認を開始します")
    try:
        conn = get_db_connection()
        c = conn.cursor()
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        print("=== データベースの実際の状況 ===")
        
        # 月額サブスクリプション確認
        c.execute(f'SELECT stripe_subscription_id, subscription_status FROM company_monthly_subscriptions WHERE company_id = {placeholder}', (5,))
        monthly_sub = c.fetchone()
        if monthly_sub:
            stripe_subscription_id, status = monthly_sub
            print(f"月額サブスクリプション: {stripe_subscription_id}, ステータス: {status}")
        else:
            print("❌ 月額サブスクリプションが見つかりません")
            return
        
        # アクティブなLINEアカウント確認（実際に利用可能なコンテンツ）
        c.execute(f'SELECT content_type, status FROM company_line_accounts WHERE company_id = {placeholder} AND status = {placeholder}', (5, 'active'))
        active_accounts = c.fetchall()
        print(f"\nアクティブなLINEアカウント数: {len(active_accounts)}")
        for account in active_accounts:
            print(f"  - {account[0]}: {account[1]}")
        
        # 非アクティブなLINEアカウント確認
        c.execute(f'SELECT content_type, status FROM company_line_accounts WHERE company_id = {placeholder} AND status = {placeholder}', (5, 'inactive'))
        inactive_accounts = c.fetchall()
        print(f"\n非アクティブなLINEアカウント数: {len(inactive_accounts)}")
        for account in inactive_accounts:
            print(f"  - {account[0]}: {account[1]}")
        
        # company_content_additions確認（古いデータ）
        c.execute(f'SELECT content_type, status FROM company_content_additions WHERE company_id = {placeholder}', (5,))
        content_additions = c.fetchall()
        print(f"\ncompany_content_additions数: {len(content_additions)}")
        for addition in content_additions:
            print(f"  - {addition[0]}: {addition[1]}")
        
        conn.close()
        
        print("\n=== 問題の分析 ===")
        print("Stripeの請求書で「AIコレクションズ (追加)」の数量が4になっている理由:")
        print("1. company_content_additionsテーブルに古いデータが残っている")
        print("2. 実際の利用状況（company_line_accounts）と請求データが一致していない")
        print("3. Stripeの請求項目が古いデータに基づいて計算されている")
        
        print("\n=== 修正が必要な項目 ===")
        print("1. company_content_additionsテーブルの古いデータを削除")
        print("2. Stripeの請求項目を実際の利用状況に合わせて更新")
        print("3. アクティブなコンテンツのみを請求対象とする")
        
        print("\n✅ 請求データの不整合確認完了")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_billing_discrepancy()
