import stripe
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# 正しいPrice IDを設定
correct_usage_price_id = 'price_1RokfbIxg6C5hAVd1v0J5ATb'

# Stripe APIキーを設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

print(f'Stripe API Key: {"***" if os.getenv("STRIPE_SECRET_KEY") else "Not set"}')
print(f'Current Usage Price ID: {os.getenv("STRIPE_USAGE_PRICE_ID")}')
print(f'Correct Usage Price ID: {correct_usage_price_id}')

# 正しいPrice IDでテスト
try:
    print('\n=== 正しいPrice IDでテスト ===')
    price = stripe.Price.retrieve(correct_usage_price_id)
    print(f'✅ Price確認成功: {price.id}')
    print(f'  Product: {price.product}')
    print(f'  Billing Scheme: {price.billing_scheme}')
    print(f'  Usage Type: {price.recurring.usage_type}')
    print(f'  Active: {price.active}')
    
    # UsageRecord作成テスト（サブスクリプションが必要）
    print('\n=== UsageRecord作成テスト ===')
    print('注意: 実際のUsageRecord作成には有効なサブスクリプションが必要です')
    
except Exception as e:
    print(f'❌ エラー: {e}') 