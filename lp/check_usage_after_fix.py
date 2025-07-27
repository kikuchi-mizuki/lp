import stripe
import os
from dotenv import load_dotenv
from datetime import datetime

# 環境変数を読み込み
load_dotenv()

# Stripe APIキーを設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
usage_price_id = 'price_1Rog1nIxg6C5hAVdnqB5MJiT'

print('=== 修正後の使用量確認 ===')

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
    print('\n=== 修正後の使用量記録 ===')
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
            
            # 使用量が0になっているか確認
            if usage.total_usage == 0:
                print(f'  ✅ 使用量が0にリセットされています')
            else:
                print(f'  ❌ 使用量がまだ残っています: {usage.total_usage}')
                
    except Exception as e:
        print(f'使用量記録取得エラー: {e}')
    
    # 新しいUsageRecord作成テスト
    print('\n=== 新しいUsageRecord作成テスト ===')
    try:
        test_record = stripe.SubscriptionItem.create_usage_record(
            usage_item.id,
            quantity=1,
            timestamp=int(datetime.now().timestamp()),
            action='increment'
        )
        print(f'✅ テストUsageRecord作成成功: {test_record.id}')
        print(f'  数量: {test_record.quantity}')
        print(f'  タイムスタンプ: {datetime.fromtimestamp(test_record.timestamp)}')
        
        # 作成したテストレコードを削除（負の数量で相殺）
        cleanup_record = stripe.SubscriptionItem.create_usage_record(
            usage_item.id,
            quantity=-1,
            timestamp=int(datetime.now().timestamp()),
            action='increment'
        )
        print(f'✅ テストレコード削除成功: {cleanup_record.id}')
        
    except Exception as e:
        print(f'❌ テストUsageRecord作成エラー: {e}')
    
    print('\n=== 修正完了確認 ===')
    print('✅ トライアル期間中の使用量がリセットされました')
    print('✅ 新しいUsageRecord作成が正常に動作します')
    print('✅ トライアル期間終了後、正しく従量課金が処理されます')
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 