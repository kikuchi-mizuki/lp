import os
import sys
sys.path.append('.')

# 環境変数を読み込み
from dotenv import load_dotenv
load_dotenv()

from services.line_service import handle_content_confirmation
from services.user_service import get_user_by_line_id
from utils.db import get_db_connection

print('=== 新しいサブスクリプションでテスト ===')

try:
    # データベース接続
    conn = get_db_connection()
    c = conn.cursor()
    
    # 現在のユーザー状況を確認
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    
    print(f'現在のユーザー状況:')
    for user in users:
        print(f'  ID: {user[0]}, Email: {user[1]}, LINE ID: {user[4]}, Stripe Subscription: {user[3]}')
    
    # 使用量ログを確認
    c.execute("SELECT * FROM usage_logs")
    logs = c.fetchall()
    print(f'使用量ログ数: {len(logs)}')
    
    conn.close()
    
    # 実際のLINEユーザーID
    actual_line_id = 'U1234567890abcdef'  # 実際のLINEユーザーIDに変更
    
    # ユーザー確認
    user = get_user_by_line_id(actual_line_id)
    if user:
        print(f'\nユーザー取得成功: {user}')
        
        # コンテンツ追加処理をテスト
        print(f'\n=== コンテンツ追加処理テスト ===')
        try:
            stripe_subscription_id = user['stripe_subscription_id']
            user_id_db = user['id']
            result = handle_content_confirmation(
                None,  # reply_token (テスト用なのでNone)
                user_id_db,  # user_id_db
                stripe_subscription_id,  # stripe_subscription_id
                1,  # content_number
                True  # confirmed
            )
            print(f'処理結果: {result}')
            
            # 処理後の使用量ログを確認
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM usage_logs ORDER BY created_at DESC LIMIT 5")
            new_logs = c.fetchall()
            conn.close()
            
            print(f'\n処理後の使用量ログ ({len(new_logs)}件):')
            for log in new_logs:
                print(f'  ID: {log[0]}, ユーザー: {log[1]}, コンテンツ: {log[2]}, 無料: {log[3]}, 保留中: {log[4]}, 作成日時: {log[5]}')
                
        except Exception as e:
            print(f'コンテンツ追加処理エラー: {e}')
            import traceback
            traceback.print_exc()
    else:
        print(f'ユーザー取得失敗: {actual_line_id}')
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 