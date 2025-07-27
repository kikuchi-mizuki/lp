import stripe
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# Stripe APIキーを設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
usage_price_id = 'price_1RokfbIxg6C5hAVd1v0J5ATb'  # 正しいPrice ID

print('=== 現在のサブスクリプション状況確認 ===')

try:
    # サブスクリプション一覧を取得
    subscriptions = stripe.Subscription.list(limit=10)
    print(f'サブスクリプション数: {len(subscriptions.data)}')
    
    for sub in subscriptions.data:
        print(f'\n--- サブスクリプション: {sub.id} ---')
        print(f'ステータス: {sub.status}')
        print(f'顧客ID: {sub.customer}')
        print(f'作成日: {sub.created}')
        
        # サブスクリプションアイテムを確認
        print('\nサブスクリプションアイテム:')
        for item in sub['items']['data']:
            print(f'  - Price ID: {item.price.id}')
            print(f'    Product: {item.price.product}')
            print(f'    Billing Scheme: {item.price.billing_scheme}')
            if hasattr(item.price, 'recurring') and item.price.recurring:
                print(f'    Usage Type: {item.price.recurring.usage_type}')
            print(f'    Quantity: {item.quantity}')
            
            # 従量課金アイテムの場合、使用量を確認
            if (hasattr(item.price, 'recurring') and 
                item.price.recurring and 
                item.price.recurring.usage_type == 'metered'):
                print(f'    Subscription Item ID: {item.id}')
                
                # 使用量記録を取得
                try:
                    usage_records = stripe.SubscriptionItem.list_usage_record_summaries(
                        item.id,
                        limit=10
                    )
                    print(f'    使用量記録数: {len(usage_records.data)}')
                    for usage in usage_records.data:
                        print(f'      - 期間: {usage.period.start} 〜 {usage.period.end}')
                        print(f'        総使用量: {usage.total_usage}')
                except Exception as e:
                    print(f'    使用量記録取得エラー: {e}')
        
        print('---')

except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 