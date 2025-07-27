import os
import sys
sys.path.append('.')

import stripe
import time
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

print('=== 間違った使用量記録の削除 ===')

try:
    subscription_id = 'sub_1RpVU2Ixg6C5hAVdeyAz8Tjk'
    
    print(f'サブスクリプションID: {subscription_id}')
    
    # サブスクリプションを取得
    subscription = stripe.Subscription.retrieve(subscription_id)
    print(f'ステータス: {subscription.status}')
    
    print(f'\n=== 問題の特定 ===')
    print('問題: 月額サブスクリプション料金（¥3,900）に使用量が記録されている')
    print('解決: この使用量記録を削除し、正しい従量課金（¥1,500）に記録する')
    
    # 月額サブスクリプション料金のSubscription Item
    monthly_item_id = 'si_Sl1X5GPCIseinG'
    monthly_price_id = 'price_1RofzxIxg6C5hAVdDp7fcqds'
    
    # 従量課金のSubscription Item
    usage_item_id = 'si_Sl1XdKM6w8gq79'
    usage_price_id = 'price_1Rog1nIxg6C5hAVdnqB5MJiT'
    
    print(f'\n=== 現在の状況 ===')
    print(f'月額料金Item: {monthly_item_id} (¥3,900)')
    print(f'従量課金Item: {usage_item_id} (¥1,500)')
    
    # 月額料金の使用量を確認
    monthly_usage = stripe.SubscriptionItem.list_usage_record_summaries(
        monthly_item_id,
        limit=10
    )
    
    print(f'\n=== 月額料金の使用量 ===')
    if monthly_usage.data:
        for i, usage in enumerate(monthly_usage.data):
            print(f'記録 {i+1}:')
            print(f'  - 期間開始: {usage.period.start}')
            print(f'  - 期間終了: {usage.period.end}')
            print(f'  - 総使用量: {usage.total_usage}')
    else:
        print('使用量記録なし')
    
    # 従量課金の使用量を確認
    usage_usage = stripe.SubscriptionItem.list_usage_record_summaries(
        usage_item_id,
        limit=10
    )
    
    print(f'\n=== 従量課金の使用量 ===')
    if usage_usage.data:
        for i, usage in enumerate(usage_usage.data):
            print(f'記録 {i+1}:')
            print(f'  - 期間開始: {usage.period.start}')
            print(f'  - 期間終了: {usage.period.end}')
            print(f'  - 総使用量: {usage.total_usage}')
    else:
        print('使用量記録なし')
    
    print(f'\n=== 解決策 ===')
    print('1. 月額料金の使用量記録は削除できない（Stripeの制限）')
    print('2. 従量課金に正しい使用量を記録する')
    print('3. コードで正しい従量課金Itemを使用する')
    
    # 従量課金に正しい使用量を記録
    print(f'\n=== 従量課金に正しい使用量を記録 ===')
    try:
        # 従量課金に使用量1を記録
        usage_record = stripe.SubscriptionItem.create_usage_record(
            usage_item_id,
            quantity=1,
            timestamp=int(time.time()),
            action='increment'
        )
        print(f'✅ 従量課金に使用量を記録: {usage_record.id}')
        
        # 更新後の使用量を確認
        updated_usage = stripe.SubscriptionItem.list_usage_record_summaries(
            usage_item_id,
            limit=10
        )
        
        if updated_usage.data:
            print(f'更新後の使用量: {updated_usage.data[0].total_usage}')
        
    except Exception as e:
        print(f'❌ 使用量記録エラー: {e}')
    
    print(f'\n=== 推奨設定 ===')
    print('コードで以下の設定を使用してください:')
    print(f'usage_subscription_item_id = "{usage_item_id}"')
    print(f'usage_price_id = "{usage_price_id}"')
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 