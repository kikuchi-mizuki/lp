import os
import stripe
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# Stripe APIキーを設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

print('=== Stripe反映状況確認 ===')

# ユーザーのサブスクリプションを確認
user_id = 'U1234567890abcdef'  # 実際のユーザーIDに変更してください

try:
    # ユーザー情報を取得
    from services.user_service import get_user_by_line_id
    user = get_user_by_line_id(user_id)
    
    if not user:
        print('❌ ユーザーが見つかりません')
        exit()
    
    print(f'ユーザーID: {user_id}')
    print(f'Stripe Customer ID: {user.get("stripe_customer_id")}')
    print(f'Stripe Subscription ID: {user.get("stripe_subscription_id")}')
    
    # サブスクリプションを取得
    subscription = stripe.Subscription.retrieve(user.get("stripe_subscription_id"))
    print(f'\n=== サブスクリプション情報 ===')
    print(f'ステータス: {subscription.status}')
    print(f'現在期間: {subscription.current_period_start} - {subscription.current_period_end}')
    
    # サブスクリプションアイテムを確認
    print(f'\n=== サブスクリプションアイテム ===')
    for item in subscription["items"]["data"]:
        print(f'アイテムID: {item.id}')
        print(f'価格ID: {item["price"]["id"]}')
        print(f'価格: ¥{item["price"]["unit_amount"]}')
        print(f'数量: {item.quantity}')
        print(f'使用量タイプ: {item["price"].get("usage_type", "N/A")}')
        
        # 使用量記録を確認
        if item["price"].get("usage_type") == "metered":
            print(f'\n--- 使用量記録 ({item.id}) ---')
            usage_records = stripe.SubscriptionItem.list_usage_record_summaries(
                item.id,
                limit=10
            )
            
            if usage_records.data:
                for record in usage_records.data:
                    print(f'期間: {record.period.start} - {record.period.end}')
                    print(f'総使用量: {record.total_usage}')
                    print(f'請求可能使用量: {record.invoiceable_usage}')
            else:
                print('使用量記録なし')
        print('---')
    
    # データベースの使用量ログを確認
    print(f'\n=== データベース使用量ログ ===')
    from utils.db import get_db_connection
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""
        SELECT id, user_id, content_type, is_free, pending_charge, created_at 
        FROM usage_logs 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 10
    """, (user_id,))
    
    logs = c.fetchall()
    if logs:
        for log in logs:
            print(f'ID: {log[0]}, コンテンツ: {log[2]}, 無料: {log[3]}, 保留中: {log[4]}, 作成日時: {log[5]}')
    else:
        print('使用量ログなし')
    
    conn.close()
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 