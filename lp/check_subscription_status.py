import os
import stripe
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# Stripe APIキーを設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

print('=== サブスクリプション状況確認 ===')

try:
    # サブスクリプションID
    subscription_id = 'sub_1RorbZIxg6C5hAVdJsW2k1Ow'
    
    # サブスクリプションを取得
    subscription = stripe.Subscription.retrieve(subscription_id)
    
    print(f'サブスクリプションID: {subscription.id}')
    print(f'ステータス: {subscription.status}')
    print(f'期間終了時解約: {subscription.cancel_at_period_end}')
    print(f'現在期間開始: {subscription.current_period_start}')
    print(f'現在期間終了: {subscription.current_period_end}')
    print(f'試用期間終了: {subscription.trial_end}')
    
    # サブスクリプションアイテムを確認
    print(f'\n=== サブスクリプションアイテム ===')
    for item in subscription["items"]["data"]:
        print(f'アイテムID: {item.id}')
        print(f'価格ID: {item["price"]["id"]}')
        print(f'価格: ¥{item["price"]["unit_amount"]}')
        print(f'数量: {item.quantity}')
        print(f'使用量タイプ: {item["price"].get("usage_type", "N/A")}')
        print('---')
    
    # 使用量記録を確認
    print(f'\n=== 使用量記録 ===')
    for item in subscription["items"]["data"]:
        if item["price"].get("usage_type") == "metered":
            print(f'従量課金アイテム: {item.id}')
            usage_records = stripe.SubscriptionItem.list_usage_record_summaries(
                item.id,
                limit=10
            )
            
            if usage_records.data:
                for record in usage_records.data:
                    print(f'  期間: {record.period.start} - {record.period.end}')
                    print(f'  総使用量: {record.total_usage}')
                    print(f'  請求可能使用量: {record.invoiceable_usage}')
            else:
                print('  使用量記録なし')
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 