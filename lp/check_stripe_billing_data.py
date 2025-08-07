#!/usr/bin/env python3
"""
Stripeの請求データとデータベースの状況を確認するスクリプト
"""
import os, sys
from dotenv import load_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
from utils.db import get_db_connection, get_db_type
import stripe

def check_stripe_billing_data():
    print("🚀 Stripe請求データの確認を開始します")
    try:
        # Stripe API設定
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        if not stripe.api_key:
            print("❌ STRIPE_SECRET_KEYが設定されていません")
            return
        
        print(f"Stripe API Key: {stripe.api_key[:20]}...")
        
        # データベース接続
        conn = get_db_connection()
        c = conn.cursor()
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        print("\n=== データベースの状況確認 ===")
        
        # 月額サブスクリプション確認
        c.execute(f'SELECT stripe_subscription_id, subscription_status FROM company_monthly_subscriptions WHERE company_id = {placeholder}', (5,))
        monthly_sub = c.fetchone()
        if monthly_sub:
            stripe_subscription_id, status = monthly_sub
            print(f"月額サブスクリプション: {stripe_subscription_id}, ステータス: {status}")
        else:
            print("❌ 月額サブスクリプションが見つかりません")
            return
        
        # アクティブなLINEアカウント確認
        c.execute(f'SELECT content_type, status FROM company_line_accounts WHERE company_id = {placeholder} AND status = {placeholder}', (5, 'active'))
        active_accounts = c.fetchall()
        print(f"アクティブなLINEアカウント数: {len(active_accounts)}")
        for account in active_accounts:
            print(f"  - {account[0]}: {account[1]}")
        
        # 古いcompany_content_additions確認
        c.execute(f'SELECT content_type, status FROM company_content_additions WHERE company_id = {placeholder}', (5,))
        content_additions = c.fetchall()
        print(f"company_content_additions数: {len(content_additions)}")
        for addition in content_additions:
            print(f"  - {addition[0]}: {addition[1]}")
        
        conn.close()
        
        print("\n=== Stripeサブスクリプション確認 ===")
        try:
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            print(f"StripeサブスクリプションID: {subscription.id}")
            print(f"ステータス: {subscription.status}")
            print(f"現在の期間終了: {subscription.current_period_end}")
            
            print("\n=== Stripe請求項目確認 ===")
            for item in subscription.items.data:
                print(f"請求項目ID: {item.id}")
                print(f"価格ID: {item.price.id}")
                print(f"数量: {item.quantity}")
                print(f"単価: {item.price.unit_amount}円")
                print(f"説明: {item.price.nickname if item.price.nickname else '説明なし'}")
                print("---")
                
        except Exception as e:
            print(f"❌ Stripe API エラー: {e}")
        
        print("\n✅ Stripe請求データ確認完了")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_stripe_billing_data()
