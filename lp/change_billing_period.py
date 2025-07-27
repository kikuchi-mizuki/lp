import os
import sys
sys.path.append('.')

import stripe
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

print('=== サブスクリプション請求期間変更 ===')

try:
    subscription_id = 'sub_1RpVU2Ixg6C5hAVdeyAz8Tjk'
    
    print(f'サブスクリプションID: {subscription_id}')
    
    # 現在のサブスクリプションを取得
    subscription = stripe.Subscription.retrieve(subscription_id)
    print(f'現在のステータス: {subscription.status}')
    print(f'現在の請求間隔: {subscription["items"]["data"][0]["price"]["recurring"]["interval"]}')
    print(f'現在の請求間隔数: {subscription["items"]["data"][0]["price"]["recurring"]["interval_count"]}')
    
    print(f'\n=== 請求期間変更オプション ===')
    print('1. 月額（現在）: interval="month", interval_count=1')
    print('2. 週額: interval="week", interval_count=1')
    print('3. 年額: interval="year", interval_count=1')
    print('4. 2ヶ月ごと: interval="month", interval_count=2')
    
    print(f'\n=== 注意事項 ===')
    print('⚠️ 請求期間を変更すると、新しい請求サイクルが開始されます')
    print('⚠️ 現在のトライアル期間は影響を受けません')
    print('⚠️ 従量課金の期間も自動的に同期されます')
    
    # 実際の変更は行わない（デモ用）
    print(f'\n=== 変更方法 ===')
    print('実際に変更する場合は、以下のコードを使用します:')
    print('''
    # 月額から週額に変更する場合
    stripe.Subscription.modify(
        subscription_id,
        items=[{
            'id': subscription["items"]["data"][0]["id"],
            'price': 'price_weekly_id'  # 週額のPrice ID
        }]
    )
    ''')
    
    print(f'\n=== 推奨設定 ===')
    print('現在の月額設定が適切です。変更は推奨しません。')
    print('理由:')
    print('- 月額は一般的で理解しやすい')
    print('- 従量課金との同期が簡単')
    print('- 請求書の管理が容易')
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 