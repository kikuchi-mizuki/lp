#!/usr/bin/env python3
"""
Priceの詳細を確認するスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def check_price_details():
    """Priceの詳細を確認"""
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
        
        if 'usage_type' in price:
            print(f"Usage Type: {price['usage_type']}")
        if 'meter' in price:
            print(f"Meter: {price['meter']}")
            
        print(f"\n=== 全Price一覧 ===")
        prices = stripe.Price.list(limit=10)
        for price in prices['data']:
            print(f"ID: {price['id']}")
            print(f"  Product: {price['product']}")
            print(f"  Amount: {price['unit_amount']}")
            print(f"  Usage Type: {price.get('usage_type', 'N/A')}")
            print(f"  Meter: {price.get('meter', 'N/A')}")
            print()
            
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == '__main__':
    check_price_details() 