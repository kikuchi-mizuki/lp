#!/usr/bin/env python3
"""
サブスクリプションアイテムを修正するスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def fix_subscription_items():
    """サブスクリプションアイテムを修正"""
    subscription_id = 'sub_1Roqi5Ixg6C5hAVd86ASCYle'
    old_usage_price_id = 'price_1RokfbIxg6C5hAVd1v0J5ATb'  # 古いMeter付き従量課金Price
    new_usage_price_id = 'price_1Rog1nIxg6C5hAVdnqB5MJiT'  # 新しい従来の従量課金Price
    
    print(f"サブスクリプション {subscription_id} のアイテムを修正中...")
    
    try:
        # サブスクリプションを取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # 古い従量課金アイテムを削除
        old_item_id = None
        for item in subscription['items']['data']:
            if item['price']['id'] == old_usage_price_id:
                old_item_id = item['id']
                break
        
        if old_item_id:
            print(f"古い従量課金アイテム {old_item_id} を削除中...")
            stripe.SubscriptionItem.delete(old_item_id)
            print(f"✅ 古い従量課金アイテムを削除しました")
        else:
            print(f"古い従量課金アイテムは見つかりませんでした")
        
        # 新しい従量課金アイテムを追加
        print(f"新しい従量課金Price {new_usage_price_id} を追加中...")
        new_item = stripe.SubscriptionItem.create(
            subscription=subscription_id,
            price=new_usage_price_id
            # 従量課金Priceにはquantityを指定しない
        )
        print(f"✅ 新しい従量課金アイテムを追加しました: {new_item.id}")
        
        # 修正後のサブスクリプションを確認
        updated_subscription = stripe.Subscription.retrieve(subscription_id)
        print(f"\n=== 修正後のサブスクリプション ===")
        print(f"Status: {updated_subscription['status']}")
        print(f"Items count: {len(updated_subscription['items']['data'])}")
        
        for i, item in enumerate(updated_subscription['items']['data']):
            print(f"Item {i+1}: {item['price']['id']} (Amount: {item['price']['unit_amount']})")
            
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == '__main__':
    fix_subscription_items() 