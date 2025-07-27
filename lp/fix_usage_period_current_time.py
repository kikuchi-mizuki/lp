import stripe
import os
from dotenv import load_dotenv
from datetime import datetime
import time

# 環境変数を読み込み
load_dotenv()

# Stripe APIキーを設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
usage_price_id = 'price_1Rog1nIxg6C5hAVdnqB5MJiT'

print('=== 現在時刻での使用量期間修正 ===')

try:
    # サブスクリプションを取得
    subscriptions = stripe.Subscription.list(limit=1)
    if not subscriptions.data:
        print('❌ サブスクリプションが見つかりません')
        exit()
    
    subscription = subscriptions.data[0]
    subscription_id = subscription.id
    
    print(f'サブスクリプションID: {subscription_id}')
    print(f'ステータス: {subscription.status}')
    print(f'現在期間開始: {datetime.fromtimestamp(subscription.current_period_start)}')
    print(f'現在期間終了: {datetime.fromtimestamp(subscription.current_period_end)}')
    
    # 従量課金アイテムを取得
    usage_item = None
    for item in subscription['items']['data']:
        if item['price']['id'] == usage_price_id:
            usage_item = item
            break
    
    if not usage_item:
        print('❌ 従量課金アイテムが見つかりません')
        exit()
    
    print(f'✅ 従量課金アイテム発見: {usage_item.id}')
    
    # 現在の使用量記録を確認
    print('\n=== 現在の使用量記録 ===')
    try:
        usage_records = stripe.SubscriptionItem.list_usage_record_summaries(
            usage_item.id,
            limit=10
        )
        print(f'使用量記録数: {len(usage_records.data)}')
        
        for i, usage in enumerate(usage_records.data):
            print(f'\n記録 {i+1}:')
            print(f'  期間開始: {datetime.fromtimestamp(usage.period.start)}')
            if usage.period.end:
                print(f'  期間終了: {datetime.fromtimestamp(usage.period.end)}')
            else:
                print(f'  期間終了: 進行中')
            print(f'  総使用量: {usage.total_usage}')
            
    except Exception as e:
        print(f'使用量記録取得エラー: {e}')
    
    # 現在時刻で使用量をリセット
    print('\n=== 現在時刻での使用量リセット ===')
    try:
        current_timestamp = int(time.time())
        print(f'現在時刻: {datetime.fromtimestamp(current_timestamp)}')
        
        reset_record = stripe.SubscriptionItem.create_usage_record(
            usage_item.id,
            quantity=0,
            timestamp=current_timestamp,
            action='set'
        )
        print(f'✅ 使用量リセット成功: {reset_record.id}')
        print(f'  タイムスタンプ: {datetime.fromtimestamp(reset_record.timestamp)}')
        
        # リセット後の使用量記録を確認
        print('\n=== リセット後の使用量記録確認 ===')
        usage_records_after = stripe.SubscriptionItem.list_usage_record_summaries(
            usage_item.id,
            limit=10
        )
        
        for i, usage in enumerate(usage_records_after.data):
            print(f'\n記録 {i+1}:')
            print(f'  期間開始: {datetime.fromtimestamp(usage.period.start)}')
            if usage.period.end:
                print(f'  期間終了: {datetime.fromtimestamp(usage.period.end)}')
            else:
                print(f'  期間終了: 進行中')
            print(f'  総使用量: {usage.total_usage}')
            
            # 使用量が0になっているか確認
            if usage.total_usage == 0:
                print(f'  ✅ 使用量が0にリセットされています')
            else:
                print(f'  ❌ 使用量がまだ残っています: {usage.total_usage}')
                
    except Exception as e:
        print(f'❌ 使用量リセットエラー: {e}')
    
    print('\n=== 修正完了 ===')
    print('現在時刻で使用量がリセットされました。')
    print('次回のコンテンツ追加時に正しい期間で処理されます。')
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 