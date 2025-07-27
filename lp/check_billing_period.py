import stripe
import os
from dotenv import load_dotenv
from datetime import datetime

# 環境変数を読み込み
load_dotenv()

# Stripe APIキーを設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

print('=== サブスクリプションと従量課金の請求期間確認 ===')

try:
    # サブスクリプションを取得
    subscriptions = stripe.Subscription.list(limit=1)
    if not subscriptions.data:
        print('❌ サブスクリプションが見つかりません')
        exit()
    
    subscription = subscriptions.data[0]
    print(f'サブスクリプションID: {subscription.id}')
    print(f'ステータス: {subscription.status}')
    print(f'現在期間開始: {datetime.fromtimestamp(subscription.current_period_start)}')
    print(f'現在期間終了: {datetime.fromtimestamp(subscription.current_period_end)}')
    print(f'請求間隔: {subscription["items"]["data"][0]["price"]["recurring"]["interval"]}')
    print(f'請求間隔数: {subscription["items"]["data"][0]["price"]["recurring"]["interval_count"]}')
    
    # 従量課金アイテムを確認
    usage_price_id = 'price_1Rog1nIxg6C5hAVdnqB5MJiT'
    usage_item = None
    
    for item in subscription['items']['data']:
        if item['price']['id'] == usage_price_id:
            usage_item = item
            break
    
    if usage_item:
        print(f'\n=== 従量課金アイテム詳細 ===')
        print(f'Subscription Item ID: {usage_item.id}')
        print(f'Price ID: {usage_item.price.id}')
        print(f'Billing Scheme: {usage_item.price.billing_scheme}')
        print(f'Usage Type: {usage_item.price.recurring.usage_type}')
        print(f'請求間隔: {usage_item.price.recurring.interval}')
        print(f'請求間隔数: {usage_item.price.recurring.interval_count}')
        
        # 使用量記録の詳細を確認
        print(f'\n=== 使用量記録詳細 ===')
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
                print(f'  請求状態: {usage.invoice}')
                
        except Exception as e:
            print(f'使用量記録取得エラー: {e}')
    
    # 請求書の詳細を確認
    print(f'\n=== 請求書詳細 ===')
    try:
        invoices = stripe.Invoice.list(
            subscription=subscription.id,
            limit=5
        )
        print(f'請求書数: {len(invoices.data)}')
        
        for invoice in invoices.data:
            print(f'\n請求書ID: {invoice.id}')
            print(f'請求日: {datetime.fromtimestamp(invoice.created)}')
            print(f'期間開始: {datetime.fromtimestamp(invoice.period_start) if invoice.period_start else "N/A"}')
            print(f'期間終了: {datetime.fromtimestamp(invoice.period_end) if invoice.period_end else "N/A"}')
            print(f'ステータス: {invoice.status}')
            print(f'金額: {invoice.amount_due}')
            
    except Exception as e:
        print(f'請求書取得エラー: {e}')
        
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 