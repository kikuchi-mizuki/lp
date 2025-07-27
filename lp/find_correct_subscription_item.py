import os
import sys
sys.path.append('.')

import stripe
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

print('=== 正しいSubscription Item ID特定 ===')

try:
    subscription_id = 'sub_1RpVU2Ixg6C5hAVdeyAz8Tjk'
    
    # サブスクリプションを取得
    subscription = stripe.Subscription.retrieve(subscription_id)
    print(f'サブスクリプションID: {subscription_id}')
    print(f'ステータス: {subscription.status}')
    
    # 各Subscription Itemの詳細を確認
    for i, item in enumerate(subscription["items"]["data"]):
        print(f'\n=== Subscription Item {i+1} ===')
        print(f'ID: {item["id"]}')
        print(f'Price ID: {item["price"]["id"]}')
        
        # Priceの詳細を取得
        price = stripe.Price.retrieve(item["price"]["id"])
        print(f'Price 詳細:')
        print(f'  - 通貨: {price["currency"]}')
        print(f'  - 単価: {price["unit_amount"]}')
        print(f'  - 請求方式: {price["billing_scheme"]}')
        try:
            print(f'  - 使用量タイプ: {price["usage_type"]}')
        except KeyError:
            print(f'  - 使用量タイプ: 不明')
        try:
            print(f'  - 請求間隔: {price["recurring"]["interval"]}')
        except KeyError:
            print(f'  - 請求間隔: N/A')
        
        # 使用量記録を確認
        usage_records = stripe.SubscriptionItem.list_usage_record_summaries(
            item["id"],
            limit=10
        )
        
        print(f'使用量記録:')
        total_usage = 0
        for j, usage in enumerate(usage_records.data):
            print(f'  記録 {j+1}:')
            print(f'    - 期間開始: {usage.period.start}')
            print(f'    - 期間終了: {usage.period.end}')
            print(f'    - 総使用量: {usage.total_usage}')
            total_usage = usage.total_usage
        
        # 使用量に基づいて判断
        if total_usage > 0:
            print(f'✅ このSubscription Itemに使用量が記録されています！')
            print(f'   正しいSubscription Item ID: {item["id"]}')
            print(f'   正しいPrice ID: {item["price"]["id"]}')
            print(f'   現在の使用量: {total_usage}')
        else:
            print(f'❌ このSubscription Itemには使用量が記録されていません')
    
    # 推奨設定
    print(f'\n=== 推奨設定 ===')
    for i, item in enumerate(subscription["items"]["data"]):
        price = stripe.Price.retrieve(item["price"]["id"])
        usage_records = stripe.SubscriptionItem.list_usage_record_summaries(
            item["id"],
            limit=10
        )
        total_usage = usage_records.data[0].total_usage if usage_records.data else 0
        
        if total_usage > 0:
            print(f'✅ 使用量が記録されているSubscription Item:')
            print(f'   - Subscription Item ID: {item["id"]}')
            print(f'   - Price ID: {item["price"]["id"]}')
            print(f'   - 使用量: {total_usage}')
            print(f'   - 単価: ¥{price["unit_amount"]}')
            
            # コードで使用すべき設定
            print(f'\n📝 コードで使用すべき設定:')
            print(f'   usage_price_id = \'{item["price"]["id"]}\'')
            print(f'   subscription_item_id = \'{item["id"]}\'')
            
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 