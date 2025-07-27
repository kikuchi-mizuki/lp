import stripe
import os
from dotenv import load_dotenv
import datetime

# 環境変数を読み込み
load_dotenv()

# Stripe APIキーを設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
usage_price_id = 'price_1Rog1nIxg6C5hAVdnqB5MJiT'  # 実際のサブスクリプションに含まれているPrice ID

print('=== UsageRecord作成テスト ===')

try:
    # サブスクリプションを取得
    subscriptions = stripe.Subscription.list(limit=1)
    if not subscriptions.data:
        print('❌ サブスクリプションが見つかりません')
        exit()
    
    subscription = subscriptions.data[0]
    print(f'サブスクリプションID: {subscription.id}')
    print(f'ステータス: {subscription.status}')
    
    # 従量課金アイテムを取得
    usage_item = None
    for item in subscription['items']['data']:
        if item['price']['id'] == usage_price_id:
            usage_item = item
            break
    
    if not usage_item:
        print(f'❌ 従量課金アイテムが見つかりません: {usage_price_id}')
        print('利用可能なPrice ID:')
        for item in subscription['items']['data']:
            print(f'  - {item.price.id} (Usage Type: {item.price.recurring.usage_type if hasattr(item.price, "recurring") else "N/A"})')
        exit()
    
    print(f'✅ 従量課金アイテム発見: {usage_item.id}')
    
    # UsageRecord作成テスト
    print('\n=== UsageRecord作成テスト ===')
    try:
        usage_record = stripe.SubscriptionItem.create_usage_record(
            usage_item['id'],
            quantity=1,
            timestamp=int(datetime.datetime.now().timestamp()),
            action='increment'
        )
        print(f'✅ UsageRecord作成成功: {usage_record.id}')
        print(f'  数量: {usage_record.quantity}')
        print(f'  タイムスタンプ: {usage_record.timestamp}')
        
    except Exception as e:
        print(f'❌ UsageRecord作成エラー: {e}')
        
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 