#!/usr/bin/env python3
"""
利用可能なPrice一覧を確認するスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def check_prices():
    """利用可能なPrice一覧を確認"""
    print(f"利用可能なPrice一覧を確認中...")
    
    try:
        prices = stripe.Price.list(limit=20)
        
        print(f"✅ Price一覧取得成功")
        print(f"Total Prices: {len(prices['data'])}")
        
        print(f"\n=== Price一覧 ===")
        for i, price in enumerate(prices['data']):
            print(f"Price {i+1}:")
            print(f"  ID: {price['id']}")
            print(f"  Product: {price['product']}")
            print(f"  Unit Amount: {price['unit_amount']}")
            print(f"  Currency: {price['currency']}")
            print(f"  Type: {price['type']}")
            print(f"  Billing Scheme: {price['billing_scheme']}")
            
            if 'recurring' in price:
                recurring = price['recurring']
                print(f"  Recurring Interval: {recurring.get('interval', 'N/A')}")
                print(f"  Recurring Usage Type: {recurring.get('usage_type', 'N/A')}")
                print(f"  Recurring Aggregate Usage: {recurring.get('aggregate_usage', 'N/A')}")
            
            print()
        
        # 環境変数の確認
        print(f"環境変数:")
        print(f"  STRIPE_MONTHLY_PRICE_ID: {os.getenv('STRIPE_MONTHLY_PRICE_ID')}")
        print(f"  STRIPE_USAGE_PRICE_ID: {os.getenv('STRIPE_USAGE_PRICE_ID')}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == '__main__':
    check_prices() 