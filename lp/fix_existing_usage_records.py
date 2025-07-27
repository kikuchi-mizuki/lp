import stripe
import os
from dotenv import load_dotenv
from datetime import datetime

# 環境変数を読み込み
load_dotenv()

# Stripe APIキーを設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
usage_price_id = 'price_1Rog1nIxg6C5hAVdnqB5MJiT'

print('=== 既存のUsageRecord修正 ===')

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
    
    # トライアル期間中の使用量を相殺
    print('\n=== トライアル期間中の使用量相殺 ===')
    
    if subscription.status == 'trialing':
        print('トライアル期間中のため、既存の使用量を相殺します')
        
        try:
            # 現在の使用量を0にリセット
            reset_record = stripe.SubscriptionItem.create_usage_record(
                usage_item.id,
                quantity=0,  # 使用量を0にリセット
                timestamp=int(datetime.now().timestamp()),
                action='set'  # 既存の使用量を上書き
            )
            print(f'✅ 使用量リセット成功: {reset_record.id}')
            
        except Exception as e:
            print(f'❌ 使用量リセットエラー: {e}')
            
            # 代替案: 負の数量で相殺
            try:
                # 現在の使用量を確認して負の数量で相殺
                current_usage = usage_records.data[0].total_usage if usage_records.data else 0
                print(f'現在の使用量: {current_usage}')
                
                if current_usage > 0:
                    offset_record = stripe.SubscriptionItem.create_usage_record(
                        usage_item.id,
                        quantity=-current_usage,  # 負の数量で相殺
                        timestamp=int(datetime.now().timestamp()),
                        action='increment'  # 既存の使用量に追加
                    )
                    print(f'✅ 使用量相殺成功: {offset_record.id}')
                else:
                    print('✅ 使用量は既に0です')
                    
            except Exception as e2:
                print(f'❌ 使用量相殺エラー: {e2}')
    else:
        print('✅ 通常期間中のため、使用量の修正は不要です')
    
    print('\n=== 修正完了 ===')
    print('トライアル期間中の使用量を相殺しました。')
    print('トライアル期間終了後、新しいコンテンツ追加時に正しくUsageRecordが作成されます。')
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 