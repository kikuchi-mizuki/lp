#!/usr/bin/env python3
"""
サブスクリプションアイテムを確認するスクリプト
"""

import os
import stripe
from dotenv import load_dotenv
from datetime import datetime

# 環境変数を読み込み
load_dotenv('lp/.env')

def check_subscription_items():
    """サブスクリプションアイテムを確認"""
    
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
        
        print(f"=== サブスクリプション基本情報 ===")
        print(f"ID: {subscription.id}")
        print(f"Status: {subscription.status}")
        print(f"Current Period Start: {datetime.fromtimestamp(subscription.current_period_start)}")
        print(f"Current Period End: {datetime.fromtimestamp(subscription.current_period_end)}")
        if subscription.status == 'trialing':
            print(f"Trial End: {datetime.fromtimestamp(subscription.trial_end)}")
        
        # サブスクリプションアイテムを取得
        subscription_items = stripe.SubscriptionItem.list(
            subscription=subscription_id
        )
        
        print(f"\n=== サブスクリプションアイテム ===")
        for item in subscription_items.data:
            print(f"ID: {item.id}")
            print(f"Price ID: {item.price.id}")
            
            # quantityが存在するかチェック
            if hasattr(item, 'quantity'):
                print(f"Quantity: {item.quantity}")
            else:
                print("Quantity: メータード課金")
            
            print(f"Unit Amount: {item.price.unit_amount}")
            print(f"Currency: {item.price.currency}")
            
            # Priceの詳細を取得
            price = stripe.Price.retrieve(item.price.id)
            print(f"Price Nickname: {price.nickname}")
            if hasattr(price, 'usage_type'):
                print(f"Usage Type: {price.usage_type}")
            print("---")
        
        # 関連するProductも確認
        print(f"\n=== Product詳細 ===")
        for item in subscription_items.data:
            price = stripe.Price.retrieve(item.price.id)
            product = stripe.Product.retrieve(price.product)
            print(f"Product ID: {product.id}")
            print(f"Product Name: {product.name}")
            print(f"Product Description: {product.description}")
            print("---")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_subscription_items() 