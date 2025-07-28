#!/usr/bin/env python3
"""
サブスクリプションの詳細を確認するスクリプト
"""

import os
import stripe
from dotenv import load_dotenv
from datetime import datetime

# 環境変数を読み込み
load_dotenv('lp/.env')

def check_subscription_details():
    """サブスクリプションの詳細を確認"""
    
    # Stripe APIキーを設定
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    if not stripe.api_key:
        print("❌ STRIPE_SECRET_KEYが設定されていません")
        return
    
    # サブスクリプションID
    subscription_id = "sub_1RpdcsIxg6C5hAVdneqtbnUG"
    
    try:
        # サブスクリプションを取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        print(f"=== サブスクリプション詳細 ===")
        print(f"ID: {subscription.id}")
        print(f"ステータス: {subscription.status}")
        print(f"期間: {datetime.fromtimestamp(subscription.current_period_start)} - {datetime.fromtimestamp(subscription.current_period_end)}")
        if subscription.status == 'trialing':
            print(f"トライアル終了: {datetime.fromtimestamp(subscription.trial_end)}")
        
        print(f"\n=== サブスクリプションアイテム ===")
        for item in subscription.items.data:
            print(f"ID: {item.id}")
            print(f"Price ID: {item.price.id}")
            print(f"Price Description: {item.price.nickname}")
            print(f"Quantity: {item.quantity}")
            print(f"Unit Amount: {item.price.unit_amount}")
            print("---")
        
        # 関連するPriceオブジェクトも確認
        print(f"\n=== Priceオブジェクト詳細 ===")
        for item in subscription.items.data:
            price = stripe.Price.retrieve(item.price.id)
            print(f"Price ID: {price.id}")
            print(f"Nickname: {price.nickname}")
            print(f"Product: {price.product}")
            print(f"Unit Amount: {price.unit_amount}")
            print(f"Currency: {price.currency}")
            print(f"Recurring: {price.recurring}")
            print("---")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    check_subscription_details() 