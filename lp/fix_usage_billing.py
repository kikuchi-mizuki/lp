import os
import sys
sys.path.append('.')

import stripe
from dotenv import load_dotenv
import time

load_dotenv()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

print('=== 使用量記録の根本的解決 ===')

try:
    subscription_id = 'sub_1RpVU2Ixg6C5hAVdeyAz8Tjk'
    
    print(f'サブスクリプションID: {subscription_id}')
    
    # サブスクリプションを取得
    subscription = stripe.Subscription.retrieve(subscription_id)
    print(f'ステータス: {subscription.status}')
    
    print(f'\n=== 現在のSubscription Items ===')
    for i, item in enumerate(subscription["items"]["data"]):
        print(f'Item {i+1}:')
        print(f'  ID: {item["id"]}')
        print(f'  Price ID: {item["price"]["id"]}')
        
        # Priceの詳細を取得
        price = stripe.Price.retrieve(item["price"]["id"])
        print(f'  Price 詳細:')
        print(f'    - 通貨: {price["currency"]}')
        print(f'    - 単価: {price["unit_amount"]}')
        print(f'    - 請求方式: {price["billing_scheme"]}')
        try:
            print(f'    - 使用量タイプ: {price["usage_type"]}')
        except KeyError:
            print(f'    - 使用量タイプ: 不明')
        try:
            print(f'    - 請求間隔: {price["recurring"]["interval"]}')
        except KeyError:
            print(f'    - 請求間隔: N/A')
        
        # 使用量記録を確認
        usage_records = stripe.SubscriptionItem.list_usage_record_summaries(
            item["id"],
            limit=10
        )
        
        total_usage = 0
        if usage_records.data:
            total_usage = usage_records.data[0].total_usage
        
        print(f'  - 現在の使用量: {total_usage}')
        
        # 判断
        if price["unit_amount"] == 3900:
            print(f'  ❌ これは月額サブスクリプション料金（¥3,900）です')
        elif price["unit_amount"] == 1500:
            print(f'  ✅ これは従量課金（¥1,500）です')
        else:
            print(f'  ❓ 不明な料金設定（¥{price["unit_amount"]}）')
    
    print(f'\n=== 問題の分析 ===')
    print('問題: 月額サブスクリプション料金（¥3,900）に使用量が記録されている')
    print('原因: 従量課金のPriceが正しく設定されていない可能性')
    
    print(f'\n=== 解決策 ===')
    print('1. 現在の使用量をリセット')
    print('2. 正しい従量課金のPriceを確認')
    print('3. 必要に応じて新しい従量課金のPriceを作成')
    
    # 現在の使用量をリセット
    print(f'\n=== 使用量リセット ===')
    for item in subscription["items"]["data"]:
        price = stripe.Price.retrieve(item["price"]["id"])
        if price["unit_amount"] == 3900:  # 月額サブスクリプション料金
            try:
                # 使用量を0にリセット
                reset_record = stripe.SubscriptionItem.create_usage_record(
                    item["id"],
                    quantity=0,
                    timestamp=int(time.time()),
                    action='set'
                )
                print(f'✅ 月額料金の使用量をリセット: {item["id"]}')
            except Exception as e:
                print(f'❌ リセットエラー: {e}')
    
    print(f'\n=== 推奨設定 ===')
    print('従量課金のPriceが正しく設定されているか確認してください:')
    print('- Price ID: price_1Rog1nIxg6C5hAVdnqB5MJiT')
    print('- 単価: ¥1,500')
    print('- 使用量タイプ: metered')
    print('- 請求方式: per_unit')
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 