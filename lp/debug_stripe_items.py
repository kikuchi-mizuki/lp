#!/usr/bin/env python3
"""
Stripeサブスクリプションアイテムのデバッグ
"""

import os
import stripe

# Stripe APIキーを設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def debug_subscription_items(subscription_id):
    """サブスクリプションアイテムの詳細を表示"""
    try:
        print(f"[DEBUG] サブスクリプション ID: {subscription_id}")
        
        # サブスクリプション取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        print(f"[DEBUG] サブスクリプション ステータス: {subscription.status}")
        print(f"[DEBUG] 現在期間: {subscription.current_period_start} - {subscription.current_period_end}")
        print(f"[DEBUG] アイテム数: {len(subscription.items.data)}")
        
        # 各アイテムの詳細を表示
        for i, item in enumerate(subscription.items.data):
            print(f"\n[DEBUG] === アイテム {i+1} ===")
            print(f"  ID: {item.id}")
            print(f"  Price ID: {item.price.id}")
            print(f"  Price Nickname: {item.price.nickname}")
            print(f"  Unit Amount: {item.price.unit_amount}")
            print(f"  Currency: {item.price.currency}")
            print(f"  Billing Scheme: {item.price.billing_scheme}")
            print(f"  Usage Type: {item.price.usage_type}")
            print(f"  Quantity: {item.quantity}")
            
            # Priceの詳細情報
            print(f"  Price Type: {item.price.type}")
            if hasattr(item.price, 'product'):
                print(f"  Product: {item.price.product}")
            
        return subscription
        
    except Exception as e:
        print(f"[ERROR] エラー: {e}")
        return None

if __name__ == "__main__":
    # テスト用サブスクリプションID（実際のものに置き換える）
    subscription_id = "sub_1RtgnjIxg6C5hAVdsu8rq8S8"
    debug_subscription_items(subscription_id)