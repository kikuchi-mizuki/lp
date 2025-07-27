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

print('=== トライアル期間中の処理テスト ===')

def check_subscription_status(stripe_subscription_id):
    """サブスクリプションの状態をチェック"""
    try:
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        status = subscription['status']
        cancel_at_period_end = subscription.get('cancel_at_period_end', False)
        
        return {
            'is_active': status in ['active', 'trialing'],
            'status': status,
            'cancel_at_period_end': cancel_at_period_end,
            'current_period_end': subscription.get('current_period_end'),
            'subscription': subscription
        }
    except Exception as e:
        return {
            'is_active': False,
            'status': 'error',
            'error': str(e)
        }

try:
    # サブスクリプションを取得
    subscriptions = stripe.Subscription.list(limit=1)
    if not subscriptions.data:
        print('❌ サブスクリプションが見つかりません')
        exit()
    
    subscription = subscriptions.data[0]
    subscription_id = subscription.id
    
    print(f'サブスクリプションID: {subscription_id}')
    
    # サブスクリプション状態をチェック
    status = check_subscription_status(subscription_id)
    print(f'ステータス: {status["status"]}')
    print(f'現在期間終了: {datetime.fromtimestamp(status["current_period_end"])}')
    
    is_trial = status['status'] == 'trialing'
    print(f'トライアル期間中: {is_trial}')
    
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
            print(f'  期間終了: {datetime.fromtimestamp(usage.period.end)}')
            print(f'  総使用量: {usage.total_usage}')
            
    except Exception as e:
        print(f'使用量記録取得エラー: {e}')
    
    # トライアル期間中の処理をシミュレート
    print(f'\n=== トライアル期間中の処理シミュレート ===')
    
    if is_trial:
        print('✅ トライアル期間中のため、UsageRecordは作成せず記録のみ')
        print('   データベースに記録: user_id=1, content_type="テスト", is_free=False, pending_charge=True')
        print('   実際のUsageRecord作成はトライアル期間終了後に行われる')
    else:
        print('✅ 通常期間中のため、UsageRecordを作成')
        print('   実際のUsageRecord作成テスト:')
        try:
            usage_record = stripe.SubscriptionItem.create_usage_record(
                usage_item['id'],
                quantity=1,
                timestamp=int(time.time()),
                action='increment'
            )
            print(f'   ✅ UsageRecord作成成功: {usage_record.id}')
        except Exception as e:
            print(f'   ❌ UsageRecord作成エラー: {e}')
    
    # トライアル期間終了後の処理について説明
    print(f'\n=== トライアル期間終了後の処理 ===')
    if is_trial:
        trial_end = datetime.fromtimestamp(status["current_period_end"])
        print(f'トライアル期間終了: {trial_end}')
        print('トライアル期間終了後:')
        print('1. サブスクリプションが通常の月額請求に移行')
        print('2. 従量課金の請求期間が月額サブスクリプションと同期')
        print('3. トライアル期間中の記録が正しく請求される')
        print('4. 新しいコンテンツ追加時にUsageRecordが作成される')
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 