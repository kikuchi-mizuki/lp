#!/usr/bin/env python3
"""
現在のサブスクリプションの詳細を確認するスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def check_subscription_details():
    """現在のサブスクリプションの詳細を確認"""
    subscription_id = 'sub_1Roqi5Ixg6C5hAVd86ASCYle'
    
    print(f"サブスクリプション {subscription_id} の詳細を確認中...")
    
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        print(f"✅ サブスクリプション取得成功")
        print(f"Status: {subscription['status']}")
        print(f"Customer: {subscription['customer']}")
        print(f"Items count: {len(subscription['items']['data'])}")
        
        print("\n=== 含まれているPrice一覧 ===")
        for i, item in enumerate(subscription['items']['data']):
            print(f"Item {i+1}:")
            print(f"  ID: {item['id']}")
            print(f"  Price ID: {item['price']['id']}")
            print(f"  Product: {item['price']['product']}")
            print(f"  Amount: {item['price']['unit_amount']}")
            
            # 安全にプロパティを確認
            if 'usage_type' in item['price']:
                print(f"  Usage Type: {item['price']['usage_type']}")
            if 'billing_scheme' in item['price']:
                print(f"  Billing Scheme: {item['price']['billing_scheme']}")
            if 'meter' in item['price']:
                print(f"  Meter: {item['price']['meter']}")
            print()
        
        # 環境変数の確認
        print(f"環境変数 STRIPE_USAGE_PRICE_ID: {os.getenv('STRIPE_USAGE_PRICE_ID')}")
        
        # 新しい従量課金Priceが含まれているかチェック
        target_price_id = os.getenv('STRIPE_USAGE_PRICE_ID')
        found = False
        for item in subscription['items']['data']:
            if item['price']['id'] == target_price_id:
                found = True
                print(f"✅ 新しい従量課金Price {target_price_id} が見つかりました")
                break
        
        if not found:
            print(f"❌ 新しい従量課金Price {target_price_id} が見つかりません")
            
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == '__main__':
    check_subscription_details() 