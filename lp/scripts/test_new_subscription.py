#!/usr/bin/env python3
"""
新しいサブスクリプションで使用量記録APIをテストするスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import stripe
import time
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def test_new_subscription():
    """新しいサブスクリプションで使用量記録APIをテスト"""
    subscription_id = 'sub_1RorbZIxg6C5hAVdJsW2k1Ow'
    subscription_item_id = 'si_SkMK5GLKJ6RHFa'  # 従量課金アイテムID
    
    print(f"新しいサブスクリプションで使用量記録APIをテスト中...")
    print(f"Subscription ID: {subscription_id}")
    print(f"Subscription Item ID: {subscription_item_id}")
    
    try:
        # サブスクリプションの状態を確認
        subscription = stripe.Subscription.retrieve(subscription_id)
        print(f"✅ サブスクリプション取得成功")
        print(f"Status: {subscription['status']}")
        
        # 使用量記録を作成
        print(f"\n=== 使用量記録を作成中 ===")
        usage_record = stripe.UsageRecord.create(
            subscription_item=subscription_item_id,
            quantity=1,
            timestamp=int(time.time()),
            action='increment'
        )
        print(f"✅ 使用量記録作成成功")
        print(f"Usage Record ID: {usage_record.id}")
        print(f"Quantity: {usage_record.quantity}")
        print(f"Timestamp: {usage_record.timestamp}")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == '__main__':
    test_new_subscription() 