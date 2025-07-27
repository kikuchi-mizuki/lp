import os
import sys
sys.path.append('.')

import stripe
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

print('=== 正しいPrice ID確認 ===')

try:
    subscription_id = 'sub_1RpVU2Ixg6C5hAVdeyAz8Tjk'
    
    # サブスクリプションを取得
    subscription = stripe.Subscription.retrieve(subscription_id)
    print(f'サブスクリプションID: {subscription_id}')
    print(f'ステータス: {subscription.status}')
    
    # 各Subscription Itemを確認
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
        for j, usage in enumerate(usage_records.data):
            print(f'  記録 {j+1}:')
            print(f'    - 期間開始: {usage.period.start}')
            print(f'    - 期間終了: {usage.period.end}')
            print(f'    - 総使用量: {usage.total_usage}')
    
    # どのPrice IDが従量課金用かを判断
    print(f'\n=== 推奨設定 ===')
    for i, item in enumerate(subscription["items"]["data"]):
        price = stripe.Price.retrieve(item["price"]["id"])
        try:
            usage_type = price["usage_type"]
            if usage_type == 'metered':
                print(f'✅ 従量課金用Price ID: {item["price"]["id"]}')
                print(f'   - Subscription Item ID: {item["id"]}')
                # 使用量を取得
                usage_records = stripe.SubscriptionItem.list_usage_record_summaries(
                    item["id"],
                    limit=10
                )
                current_usage = usage_records.data[0].total_usage if usage_records.data else 0
                print(f'   - 現在の使用量: {current_usage}')
            else:
                print(f'❌ 従量課金ではないPrice ID: {item["price"]["id"]} (type: {usage_type})')
        except KeyError:
            print(f'❓ 使用量タイプ不明のPrice ID: {item["price"]["id"]}')
            
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 