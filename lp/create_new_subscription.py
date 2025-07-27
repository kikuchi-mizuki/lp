import os
import stripe
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# Stripe APIキーを設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

print('=== 新しいサブスクリプション作成 ===')

try:
    # 顧客ID
    customer_id = 'cus_SkMGzumL3BMssw'
    
    # 価格ID
    monthly_price_id = 'price_1Rl5oAIxg6C5hAVdEqGALYX7'  # ¥3,900月額
    usage_price_id = 'price_1Rl5roIxg6C5hAVdBhvV6bS3'   # ¥1,500従量課金
    
    print(f'顧客ID: {customer_id}')
    print(f'月額価格ID: {monthly_price_id}')
    print(f'従量課金価格ID: {usage_price_id}')
    
    # 新しいサブスクリプションを作成
    subscription = stripe.Subscription.create(
        customer=customer_id,
        items=[
            {
                'price': monthly_price_id,
                'quantity': 1
            },
            {
                'price': usage_price_id
            }
        ],
        trial_period_days=7,  # 7日間の無料トライアル
        payment_behavior='default_incomplete',
        payment_settings={'save_default_payment_method': 'on_subscription'},
        expand=['latest_invoice.payment_intent']
    )
    
    print(f'\n✅ 新しいサブスクリプションを作成しました')
    print(f'サブスクリプションID: {subscription.id}')
    print(f'ステータス: {subscription.status}')
    print(f'試用期間終了: {subscription.trial_end}')
    
    # データベースを更新
    from utils.db import get_db_connection
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET stripe_subscription_id = ? WHERE id = 1", (subscription.id,))
    conn.commit()
    conn.close()
    
    print(f'✅ データベースを更新しました')
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 