import stripe
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# Stripe APIキーを設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
usage_price_id = os.getenv('STRIPE_USAGE_PRICE_ID')

print(f'Stripe API Key: {"***" if os.getenv("STRIPE_SECRET_KEY") else "Not set"}')
print(f'Usage Price ID: {usage_price_id}')

# Stripe API接続テスト
try:
    print('\n=== Stripe API接続テスト ===')
    prices = stripe.Price.list(limit=1)
    print('✅ Stripe API接続成功')
    
    # Usage Price IDの詳細を確認
    if usage_price_id:
        print(f'\n=== Usage Price ID詳細確認 ===')
        try:
            price = stripe.Price.retrieve(usage_price_id)
            print(f'Price ID: {price.id}')
            print(f'Product: {price.product}')
            print(f'Billing Scheme: {price.billing_scheme}')
            print(f'Usage Type: {price.usage_type}')
            print(f'Recurring: {price.recurring}')
            print('✅ Usage Price ID確認成功')
        except Exception as e:
            print(f'❌ Usage Price ID確認エラー: {e}')
    
except Exception as e:
    print(f'❌ Stripe API接続エラー: {e}') 