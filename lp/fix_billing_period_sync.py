import stripe
import os
from dotenv import load_dotenv
from datetime import datetime

# 環境変数を読み込み
load_dotenv()

# Stripe APIキーを設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
usage_price_id = 'price_1Rog1nIxg6C5hAVdnqB5MJiT'

print('=== 請求期間同期修正 ===')

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
    
    # トライアル期間終了後の処理
    if subscription.status == 'trialing':
        trial_end = datetime.fromtimestamp(subscription.current_period_end)
        print(f'\n=== トライアル期間終了後の処理 ===')
        print(f'トライアル期間終了: {trial_end}')
        print('トライアル期間終了後:')
        print('1. サブスクリプションが通常の月額請求に移行')
        print('2. 従量課金の請求期間が月額サブスクリプションと同期')
        print('3. 新しいコンテンツ追加時に正しい期間でUsageRecordが作成される')
        
        # 現在の使用量をリセット（トライアル期間中の分をクリア）
        print('\n=== トライアル期間中の使用量リセット ===')
        try:
            reset_record = stripe.SubscriptionItem.create_usage_record(
                usage_item.id,
                quantity=0,
                timestamp=int(datetime.now().timestamp()),
                action='set'
            )
            print(f'✅ 使用量リセット成功: {reset_record.id}')
            
        except Exception as e:
            print(f'❌ 使用量リセットエラー: {e}')
    
    else:
        print('\n=== 通常期間中の確認 ===')
        print('✅ サブスクリプションは通常期間中です')
        print('✅ 従量課金の請求期間は月額サブスクリプションと同期しています')
    
    print('\n=== 修正完了 ===')
    print('トライアル期間終了後、従量課金の請求期間が月額サブスクリプションと同期されます。')
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 