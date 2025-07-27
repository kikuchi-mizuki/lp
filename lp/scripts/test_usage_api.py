#!/usr/bin/env python3
"""
Stripeの使用量記録APIをテストするスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import stripe
import time
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def test_usage_api():
    """Stripeの使用量記録APIをテスト"""
    subscription_item_id = 'si_SkMAlItPkKdbt4'  # 現在の従量課金アイテムID
    
    print(f"使用量記録APIをテスト中...")
    print(f"Subscription Item ID: {subscription_item_id}")
    
    # テスト1: stripe.SubscriptionItem.create_usage_record（推奨）
    print("\n=== テスト1: stripe.SubscriptionItem.create_usage_record（推奨） ===")
    try:
        usage_record = stripe.SubscriptionItem.create_usage_record(
            subscription_item_id,
            quantity=1,
            timestamp=int(time.time()),
            action='increment'
        )
        print(f"✅ 成功: {usage_record.id}")
    except Exception as e:
        print(f"❌ エラー: {e}")
    
    # テスト2: stripe.SubscriptionItem.create_usage_record（別の方法）
    print("\n=== テスト2: stripe.SubscriptionItem.create_usage_record（別の方法） ===")
    try:
        usage_record = stripe.SubscriptionItem.create_usage_record(
            subscription_item_id,
            quantity=1,
            timestamp=int(time.time()),
            action='increment'
        )
        print(f"✅ 成功: {usage_record.id}")
    except Exception as e:
        print(f"❌ エラー: {e}")
    
    # テスト3: 直接API呼び出し
    print("\n=== テスト3: 直接API呼び出し ===")
    try:
        import requests
        headers = {
            'Authorization': f'Bearer {os.getenv("STRIPE_SECRET_KEY")}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(
            f'https://api.stripe.com/v1/subscription_items/{subscription_item_id}/usage_records',
            headers=headers,
            data={
                'quantity': 1,
                'timestamp': int(time.time()),
                'action': 'increment'
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ 直接API呼び出し成功")
        else:
            print("❌ 直接API呼び出し失敗")
            
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == '__main__':
    test_usage_api() 