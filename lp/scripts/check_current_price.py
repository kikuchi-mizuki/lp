#!/usr/bin/env python3
"""
現在のPriceの詳細を確認するスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def check_current_price():
    """現在のPriceの詳細を確認"""
    price_id = 'price_1Rog1nIxg6C5hAVdnqB5MJiT'
    
    print(f"Price {price_id} の詳細を確認中...")
    
    try:
        price = stripe.Price.retrieve(price_id)
        print(f"✅ Price取得成功")
        print(f"ID: {price['id']}")
        print(f"Product: {price['product']}")
        print(f"Unit Amount: {price['unit_amount']}")
        print(f"Currency: {price['currency']}")
        print(f"Type: {price['type']}")
        print(f"Billing Scheme: {price['billing_scheme']}")
        
        # 従量課金の詳細を確認
        if 'usage_type' in price:
            print(f"Usage Type: {price['usage_type']}")
        else:
            print("Usage Type: 設定されていません")
            
        if 'recurring' in price:
            recurring = price['recurring']
            print(f"Recurring Interval: {recurring.get('interval', 'N/A')}")
            print(f"Recurring Interval Count: {recurring.get('interval_count', 'N/A')}")
            print(f"Recurring Usage Type: {recurring.get('usage_type', 'N/A')}")
            print(f"Recurring Aggregate Usage: {recurring.get('aggregate_usage', 'N/A')}")
        
        # 従量課金かどうかを判定
        is_metered = False
        if 'recurring' in price and 'usage_type' in price['recurring']:
            if price['recurring']['usage_type'] == 'metered':
                is_metered = True
                print("✅ このPriceは従量課金（metered）として設定されています")
            else:
                print("❌ このPriceは従量課金ではありません")
        else:
            print("❌ このPriceは従量課金として設定されていません")
            
        return is_metered
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == '__main__':
    check_current_price() 