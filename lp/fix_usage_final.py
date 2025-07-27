import stripe
import os
from dotenv import load_dotenv
from datetime import datetime

# 環境変数を読み込み
load_dotenv()

# Stripe APIキーを設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
usage_price_id = 'price_1Rog1nIxg6C5hAVdnqB5MJiT'

print('=== 最終的な使用量修正 ===')

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
    
    # 現在の使用量を確認
    print('\n=== 現在の使用量確認 ===')
    try:
        usage_records = stripe.SubscriptionItem.list_usage_record_summaries(
            usage_item.id,
            limit=10
        )
        
        current_usage = 0
        if usage_records.data:
            current_usage = usage_records.data[0].total_usage
            print(f'現在の使用量: {current_usage}')
        
        if current_usage > 0:
            print(f'❌ 使用量がまだ残っています: {current_usage}')
            print('使用量を0にリセットします...')
            
            # 使用量を0にリセット
            try:
                reset_record = stripe.SubscriptionItem.create_usage_record(
                    usage_item.id,
                    quantity=0,
                    timestamp=int(datetime.now().timestamp()),
                    action='set'
                )
                print(f'✅ 使用量リセット成功: {reset_record.id}')
                
                # リセット後の確認
                usage_records_after = stripe.SubscriptionItem.list_usage_record_summaries(
                    usage_item.id,
                    limit=10
                )
                
                if usage_records_after.data:
                    new_usage = usage_records_after.data[0].total_usage
                    print(f'リセット後の使用量: {new_usage}')
                    
                    if new_usage == 0:
                        print('✅ 使用量が正常に0にリセットされました')
                    else:
                        print(f'❌ 使用量のリセットが不完全です: {new_usage}')
                else:
                    print('✅ 使用量記録がクリアされました')
                    
            except Exception as e:
                print(f'❌ 使用量リセットエラー: {e}')
        else:
            print('✅ 使用量は既に0です')
            
    except Exception as e:
        print(f'使用量確認エラー: {e}')
    
    print('\n=== 修正完了 ===')
    print('トライアル期間中の使用量をリセットしました。')
    print('トライアル期間終了後、新しいコンテンツ追加時に正しくUsageRecordが作成されます。')
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 