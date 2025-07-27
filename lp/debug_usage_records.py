import os
import sys
sys.path.append('.')

import stripe
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

print('=== Stripe使用量記録デバッグ ===')

try:
    subscription_id = 'sub_1RpVU2Ixg6C5hAVdeyAz8Tjk'
    
    # サブスクリプションを取得
    subscription = stripe.Subscription.retrieve(subscription_id)
    print(f'サブスクリプションID: {subscription_id}')
    print(f'ステータス: {subscription.status}')
    
    # サブスクリプションアイテムを取得
    for item in subscription["items"]["data"]:
        print(f'\n=== Subscription Item ===')
        print(f'ID: {item["id"]}')
        print(f'Price ID: {item["price"]["id"]}')
        try:
            print(f'Usage Type: {item["price"]["usage_type"]}')
        except KeyError:
            print(f'Usage Type: 不明（属性が存在しません）')
        
        # 使用量記録を取得
        try:
            usage_records = stripe.SubscriptionItem.list_usage_record_summaries(
                item.id,
                limit=10
            )
            
            print(f'\n使用量記録数: {len(usage_records.data)}')
            
            for i, usage in enumerate(usage_records.data):
                print(f'\n記録 {i+1}:')
                print(f'  期間開始: {usage.period.start}')
                print(f'  期間終了: {usage.period.end}')
                print(f'  総使用量: {usage.total_usage}')
                
                # 詳細な使用量記録を取得
                try:
                    detailed_records = stripe.SubscriptionItem.list_usage_records(
                        item.id,
                        limit=10
                    )
                    
                    print(f'  詳細記録数: {len(detailed_records.data)}')
                    
                    for j, record in enumerate(detailed_records.data):
                        print(f'    詳細記録 {j+1}:')
                        print(f'      数量: {record.quantity}')
                        print(f'      タイムスタンプ: {record.timestamp}')
                        print(f'      アクション: {record.action}')
                        
                except Exception as e:
                    print(f'  詳細記録取得エラー: {e}')
                    
        except Exception as e:
            print(f'使用量記録取得エラー: {e}')
            
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 