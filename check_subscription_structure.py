#!/usr/bin/env python3
"""
サブスクリプションの構造を確認するスクリプト
"""

import os
import stripe
from dotenv import load_dotenv
from datetime import datetime
import json

# 環境変数を読み込み
load_dotenv('lp/.env')

def check_subscription_structure():
    """サブスクリプションの構造を確認"""
    
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
        
        print(f"\n=== サブスクリプションの全属性 ===")
        for attr in dir(subscription):
            if not attr.startswith('_'):
                try:
                    value = getattr(subscription, attr)
                    if not callable(value):
                        print(f"{attr}: {value}")
                except:
                    pass
        
        print(f"\n=== items の詳細 ===")
        print(f"items type: {type(subscription.items)}")
        print(f"items: {subscription.items}")
        
        if hasattr(subscription.items, 'data'):
            print(f"items.data: {subscription.items.data}")
            for item in subscription.items.data:
                print(f"  Item: {item}")
        else:
            print("items.data が存在しません")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_subscription_structure() 