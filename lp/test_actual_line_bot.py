import os
import sys
sys.path.append('.')

# 環境変数を読み込み
from dotenv import load_dotenv
load_dotenv()

from services.line_service import handle_content_confirmation
from services.user_service import get_user_by_line_id
from utils.db import get_db_connection

print('=== 実際のLINE Botテスト ===')

# 環境変数確認
print(f'環境変数確認:')
print(f'  STRIPE_SECRET_KEY: {"設定済み" if os.getenv("STRIPE_SECRET_KEY") else "未設定"}')
print(f'  LINE_CHANNEL_ACCESS_TOKEN: {"設定済み" if os.getenv("LINE_CHANNEL_ACCESS_TOKEN") else "未設定"}')

try:
    # データベース接続
    conn = get_db_connection()
    c = conn.cursor()
    
    # 現在のユーザー状況を確認
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    
    print(f'現在のユーザー状況:')
    for user in users:
        print(f'  ID: {user[0]}, Email: {user[1]}, LINE ID: {user[4]}')
    
    # 使用量ログを確認
    c.execute("SELECT * FROM usage_logs")
    logs = c.fetchall()
    print(f'使用量ログ数: {len(logs)}')
    
    conn.close()
    
    # 実際のLINEユーザーIDを設定（実際のユーザーIDに変更してください）
    actual_line_id = 'U1234567890abcdef'  # 実際のLINEユーザーIDに変更
    
    print(f'\n=== 実際のLINEユーザーID設定 ===')
    print(f'設定するLINEユーザーID: {actual_line_id}')
    
    # ユーザーにLINEユーザーIDを設定
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET line_user_id = ? WHERE id = 1", (actual_line_id,))
    conn.commit()
    conn.close()
    
    print(f'LINEユーザーIDを設定しました')
    
    # 設定後のユーザー確認
    user = get_user_by_line_id(actual_line_id)
    if user:
        print(f'ユーザー取得成功: {user}')
        
        # コンテンツ追加処理をテスト（正しい引数で）
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