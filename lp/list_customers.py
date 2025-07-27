import os
import stripe
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# Stripe APIキーを設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

print('=== 顧客一覧確認 ===')

try:
    # 顧客一覧を取得
    customers = stripe.Customer.list(
        limit=10
    )
    
    print(f'\n=== 顧客一覧 ({len(customers.data)}件) ===')
    
    for customer in customers.data:
        print(f'\n顧客ID: {customer.id}')
        print(f'メール: {customer.email}')
        print(f'名前: {customer.name}')
        print(f'作成日: {customer.created}')
        
        # サブスクリプション数を確認
        subscriptions = stripe.Subscription.list(
            customer=customer.id,
            limit=5
        )
        print(f'サブスクリプション数: {len(subscriptions.data)}')
        
        for sub in subscriptions.data:
            print(f'  - サブスクリプションID: {sub.id}')
            print(f'    ステータス: {sub.status}')
            print(f'    作成日: {sub.created}')
        
        print('---')
    
    # メールアドレスで検索
    target_email = 'mmms.dy.23@gmail.com'
    print(f'\n=== メールアドレス検索: {target_email} ===')
    
    for customer in customers.data:
        if customer.email == target_email:
            print(f'✅ 顧客が見つかりました: {customer.id}')
            
            # データベースを更新
            from utils.db import get_db_connection
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("UPDATE users SET stripe_customer_id = ? WHERE id = 1", (customer.id,))
            conn.commit()
            conn.close()
            
            print(f'✅ データベースの顧客IDを更新しました')
            break
    else:
        print(f'❌ メールアドレス {target_email} の顧客が見つかりません')
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 