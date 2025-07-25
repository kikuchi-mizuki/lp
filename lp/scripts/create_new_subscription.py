#!/usr/bin/env python3
"""
新しいサブスクリプションを作成するスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def create_new_subscription():
    """新しいサブスクリプションを作成"""
    customer_id = 'cus_SkMGzumL3BMssw'  # 現在の顧客ID
    monthly_price_id = os.getenv('STRIPE_MONTHLY_PRICE_ID')
    usage_price_id = os.getenv('STRIPE_USAGE_PRICE_ID')
    
    print(f"新しいサブスクリプションを作成中...")
    print(f"Customer ID: {customer_id}")
    print(f"Monthly Price ID: {monthly_price_id}")
    print(f"Usage Price ID: {usage_price_id}")
    
    try:
        # 新しいサブスクリプションを作成
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[
                {
                    'price': monthly_price_id,
                    'quantity': 1,
                },
                {
                    'price': usage_price_id,
                    # 従量課金Priceにはquantityを指定しない
                }
            ],
            trial_period_days=7,
        )
        
        print(f"✅ 新しいサブスクリプション作成成功")
        print(f"Subscription ID: {subscription['id']}")
        print(f"Status: {subscription['status']}")
        print(f"Trial End: {subscription.get('trial_end', 'N/A')}")
        
        print(f"\n=== 含まれているPrice一覧 ===")
        for i, item in enumerate(subscription['items']['data']):
            print(f"Item {i+1}:")
            print(f"  ID: {item['id']}")
            print(f"  Price ID: {item['price']['id']}")
            print(f"  Amount: {item['price']['unit_amount']}")
            print(f"  Usage Type: {item['price'].get('recurring', {}).get('usage_type', 'N/A')}")
            print()
        
        return subscription['id']
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None

if __name__ == '__main__':
    create_new_subscription() 