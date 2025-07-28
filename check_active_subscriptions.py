#!/usr/bin/env python3
"""
アクティブなサブスクリプションを確認するスクリプト
"""

import os
import stripe
from dotenv import load_dotenv
from datetime import datetime

# 環境変数を読み込み
load_dotenv('lp/.env')

def check_active_subscriptions():
    """アクティブなサブスクリプションを確認"""
    
    # Stripe APIキーを設定
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    if not stripe.api_key:
        print("❌ STRIPE_SECRET_KEYが設定されていません")
        return
    
    try:
        # 顧客を取得
        customers = stripe.Customer.list(limit=10)
        
        for customer in customers.data:
            print(f"\n=== 顧客: {customer.id} ===")
            print(f"Email: {customer.email}")
            
            # サブスクリプションを取得
            subscriptions = stripe.Subscription.list(
                customer=customer.id,
                limit=10
            )
            
            for sub in subscriptions.data:
                print(f"  サブスクリプション: {sub.id}")
                print(f"    ステータス: {sub.status}")
                print(f"    期間: {datetime.fromtimestamp(sub.current_period_start)} - {datetime.fromtimestamp(sub.current_period_end)}")
                if sub.status == 'trialing':
                    print(f"    トライアル終了: {datetime.fromtimestamp(sub.trial_end)}")
                print()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    check_active_subscriptions() 