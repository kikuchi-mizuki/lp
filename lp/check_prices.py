import stripe
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# Stripe APIキーを設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

print('=== 利用可能なStripe Price ID一覧 ===')

try:
    # すべてのPriceを取得
    prices = stripe.Price.list(limit=50)
    
    print(f'総数: {len(prices.data)}個のPriceが見つかりました\n')
    
    for price in prices.data:
        print(f'Price ID: {price.id}')
        print(f'  Product: {price.product}')
        print(f'  Billing Scheme: {price.billing_scheme}')
        
        # usage_typeが存在するかチェック
        if hasattr(price, 'usage_type'):
            print(f'  Usage Type: {price.usage_type}')
        else:
            print(f'  Usage Type: 不明')
            
        if hasattr(price, 'recurring') and price.recurring:
            print(f'  Recurring: {price.recurring}')
        print(f'  Active: {price.active}')
        print(f'  Created: {price.created}')
        print('---')
    
    # 従量課金のPriceを特定（より安全に）
    print('\n=== 従量課金Price（metered）===')
    metered_prices = []
    
    for price in prices.data:
        if (price.billing_scheme == 'per_unit' and 
            hasattr(price, 'usage_type') and 
            price.usage_type == 'metered'):
            metered_prices.append(price)
    
    if metered_prices:
        for price in metered_prices:
            print(f'✅ 従量課金Price: {price.id}')
            print(f'  Product: {price.product}')
            print(f'  Active: {price.active}')
            print('---')
    else:
        print('❌ 従量課金Priceが見つかりません')
        
        # 代替案：per_unitのPriceを表示
        print('\n=== per_unit Price（従量課金の可能性）===')
        per_unit_prices = [p for p in prices.data if p.billing_scheme == 'per_unit']
        for price in per_unit_prices:
            print(f'Price ID: {price.id}')
            print(f'  Product: {price.product}')
            print(f'  Active: {price.active}')
            print('---')
        
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 