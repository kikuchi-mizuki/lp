#!/usr/bin/env python3
"""
サブスクリプションの状態を確認するスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def check_subscription_status():
    """サブスクリプションの状態を確認"""
    subscription_id = 'sub_1RorXVIxg6C5hAVdvE7sSTeA'
    
    print(f"サブスクリプション {subscription_id} の状態を確認中...")
    
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        print(f"✅ サブスクリプション取得成功")
        print(f"Status: {subscription['status']}")
        print(f"Customer: {subscription['customer']}")
        print(f"Current Period Start: {subscription['current_period_start']}")
        print(f"Current Period End: {subscription['current_period_end']}")
        print(f"Trial End: {subscription.get('trial_end', 'N/A')}")
        print(f"Canceled At: {subscription.get('canceled_at', 'N/A')}")
        print(f"Ended At: {subscription.get('ended_at', 'N/A')}")
        
        print(f"\n=== 含まれているPrice一覧 ===")
        for i, item in enumerate(subscription['items']['data']):
            print(f"Item {i+1}:")
            print(f"  ID: {item['id']}")
            print(f"  Price ID: {item['price']['id']}")
            print(f"  Amount: {item['price']['unit_amount']}")
            print(f"  Usage Type: {item['price'].get('recurring', {}).get('usage_type', 'N/A')}")
            print()
        
        # サブスクリプションの状態に基づいて推奨アクションを表示
        if subscription['status'] == 'canceled':
            print("❌ サブスクリプションがキャンセルされています")
            print("推奨アクション: 新しいサブスクリプションを作成してください")
        elif subscription['status'] == 'active':
            print("✅ サブスクリプションがアクティブです")
        elif subscription['status'] == 'trialing':
            print("✅ サブスクリプションがトライアル中です")
        else:
            print(f"⚠️ サブスクリプションの状態: {subscription['status']}")
            
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == '__main__':
    check_subscription_status() 