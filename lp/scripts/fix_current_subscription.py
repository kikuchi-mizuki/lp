#!/usr/bin/env python3
"""
現在のサブスクリプションに新しい従量課金Priceを追加するスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

from services.stripe_service import add_metered_price_to_subscription

def fix_current_subscription():
    """現在のサブスクリプションを修正"""
    subscription_id = 'sub_1Roqi5Ixg6C5hAVd86ASCYle'  # 現在のサブスクリプションID
    usage_price_id = 'price_1Rog1nIxg6C5hAVdnqB5MJiT'  # 新しい従量課金Price ID
    
    print(f"サブスクリプション {subscription_id} に従量課金Price {usage_price_id} を追加します...")
    
    try:
        result = add_metered_price_to_subscription(subscription_id, usage_price_id)
        print(f"✅ 成功: {result}")
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == '__main__':
    fix_current_subscription() 