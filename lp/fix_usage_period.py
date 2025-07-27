import os
import sys
sys.path.append('.')

import stripe
import time
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

print('=== 従量課金の期間修正 ===')

try:
    subscription_id = 'sub_1RpVU2Ixg6C5hAVdeyAz8Tjk'
    usage_subscription_item_id = 'si_Sl1XdKM6w8gq79'  # ¥1,500の従量課金
    
    print(f'サブスクリプションID: {subscription_id}')
    print(f'従量課金Subscription Item ID: {usage_subscription_item_id}')
    
    # 現在の使用量記録を確認
    usage_records = stripe.SubscriptionItem.list_usage_record_summaries(
        usage_subscription_item_id,
        limit=10
    )
    
    print(f'\n=== 現在の使用量記録 ===')
    for i, usage in enumerate(usage_records.data):
        print(f'記録 {i+1}:')
        print(f'  - 期間開始: {usage.period.start}')
        print(f'  - 期間終了: {usage.period.end}')
        print(f'  - 総使用量: {usage.total_usage}')
    
    # サブスクリプションの詳細を取得
    subscription = stripe.Subscription.retrieve(subscription_id)
    print(f'\n=== サブスクリプション詳細 ===')
    print(f'ステータス: {subscription.status}')
    print(f'現在期間開始: {subscription.current_period_start}')
    print(f'現在期間終了: {subscription.current_period_end}')
    
    # トライアル期間の終了日を確認
    if subscription.trial_end:
        trial_end_timestamp = subscription.trial_end
        print(f'トライアル終了: {trial_end_timestamp}')
        
        # トライアル終了後の期間を計算
        trial_end_date = time.gmtime(trial_end_timestamp)
        print(f'トライアル終了日: {time.strftime("%Y-%m-%d %H:%M:%S", trial_end_date)}')
        
        # 従量課金の期間を正しく設定
        print(f'\n=== 従量課金期間の修正 ===')
        print('従量課金は以下の期間で正しく記録されるべきです:')
        print(f'開始: トライアル終了後 ({time.strftime("%Y-%m-%d", trial_end_date)})')
        print(f'終了: 次回請求日 ({time.strftime("%Y-%m-%d", time.gmtime(subscription.current_period_end))})')
        
        # 現在の使用量を0にリセット
        print(f'\n=== 使用量リセット ===')
        try:
            # 使用量を0に設定
            reset_record = stripe.SubscriptionItem.create_usage_record(
                usage_subscription_item_id,
                quantity=0,
                timestamp=int(time.time()),
                action='set'
            )
            print(f'✅ 使用量を0にリセットしました: {reset_record.id}')
        except Exception as e:
            print(f'❌ 使用量リセットエラー: {e}')
        
        # 修正後の使用量を確認
        updated_records = stripe.SubscriptionItem.list_usage_record_summaries(
            usage_subscription_item_id,
            limit=10
        )
        
        print(f'\n=== 修正後の使用量記録 ===')
        for i, usage in enumerate(updated_records.data):
            print(f'記録 {i+1}:')
            print(f'  - 期間開始: {usage.period.start}')
            print(f'  - 期間終了: {usage.period.end}')
            print(f'  - 総使用量: {usage.total_usage}')
    
    print(f'\n=== 推奨設定 ===')
    print('1. 従量課金の期間は自動的にサブスクリプションの請求期間と同期されます')
    print('2. トライアル期間中は使用量を記録しない')
    print('3. トライアル終了後から従量課金を開始する')
    print('4. 期間は月単位（2025/08/03 - 2025/09/03）で設定される')
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 