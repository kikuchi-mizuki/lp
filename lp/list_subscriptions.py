import os
import stripe
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# Stripe APIキーを設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

print('=== サブスクリプション一覧確認 ===')

try:
    # 顧客ID
    customer_id = 'cus_SkMGzumL3BMssw'
    
    print(f'顧客ID: {customer_id}')
    
    # 顧客のサブスクリプション一覧を取得
    subscriptions = stripe.Subscription.list(
        customer=customer_id,
        limit=10
    )
    
    print(f'\n=== サブスクリプション一覧 ({len(subscriptions.data)}件) ===')
    
    for sub in subscriptions.data:
        print(f'\nサブスクリプションID: {sub.id}')
        print(f'ステータス: {sub.status}')
        print(f'作成日: {sub.created}')
        print(f'現在期間開始: {sub.current_period_start}')
        print(f'現在期間終了: {sub.current_period_end}')
        print(f'試用期間終了: {sub.trial_end}')
        print(f'期間終了時解約: {sub.cancel_at_period_end}')
        
        # サブスクリプションアイテムを確認
        print(f'  アイテム:')
        for item in sub["items"]["data"]:
            print(f'    - アイテムID: {item.id}')
            print(f'      価格ID: {item["price"]["id"]}')
            print(f'      価格: ¥{item["price"]["unit_amount"]}')
            print(f'      使用量タイプ: {item["price"].get("usage_type", "N/A")}')
        
        print('---')
    
    # 最新のサブスクリプションを特定
    if subscriptions.data:
        latest_sub = max(subscriptions.data, key=lambda x: x.created)
        print(f'\n=== 最新のサブスクリプション ===')
        print(f'サブスクリプションID: {latest_sub.id}')
        print(f'ステータス: {latest_sub.status}')
        print(f'作成日: {latest_sub.created}')
        
        # データベースを更新
        from utils.db import get_db_connection
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE users SET stripe_subscription_id = ? WHERE id = 1", (latest_sub.id,))
        conn.commit()
        conn.close()
        
        print(f'✅ データベースを最新のサブスクリプションIDで更新しました')
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 