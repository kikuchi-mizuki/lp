import os
import sys
sys.path.append('.')

from services.line_service import handle_content_confirmation
from services.user_service import get_user_by_line_id
from utils.db import get_db_connection

print('=== LINE Bot処理ログ確認 ===')

try:
    # データベース接続
    conn = get_db_connection()
    c = conn.cursor()
    
    # 最新の使用量ログを確認
    c.execute("""
        SELECT * FROM usage_logs 
        ORDER BY created_at DESC 
        LIMIT 5
    """)
    logs = c.fetchall()
    
    print(f'最新の使用量ログ ({len(logs)}件):')
    for log in logs:
        print(f'  ID: {log[0]}, ユーザー: {log[1]}, コンテンツ: {log[2]}, 無料: {log[3]}, 保留中: {log[4]}, 作成日時: {log[5]}')
    
    # ユーザー情報を確認
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    
    print(f'\n登録ユーザー ({len(users)}件):')
    for user in users:
        print(f'  ID: {user[0]}, Email: {user[1]}, Stripe Customer: {user[2]}, Stripe Subscription: {user[3]}, LINE ID: {user[4]}')
    
    conn.close()
    
    # 実際のLINEユーザーIDをテスト（実際のユーザーIDに変更してください）
    test_line_id = 'U1234567890abcdef'  # 実際のLINEユーザーIDに変更
    
    print(f'\n=== テストユーザー確認 ===')
    user = get_user_by_line_id(test_line_id)
    if user:
        print(f'ユーザーが見つかりました: {user}')
        
        # コンテンツ追加処理をシミュレート
        print(f'\n=== コンテンツ追加処理シミュレート ===')
        try:
            result = handle_content_confirmation(test_line_id, 'accounting')
            print(f'処理結果: {result}')
        except Exception as e:
            print(f'処理エラー: {e}')
            import traceback
            traceback.print_exc()
    else:
        print(f'ユーザーが見つかりません: {test_line_id}')
        
        # 実際のユーザーIDを推測
        print(f'\n=== 実際のユーザーID推測 ===')
        if users:
            # 最初のユーザーを使用
            user = users[0]
            print(f'利用可能なユーザー: {user}')
            
            # LINEユーザーIDを設定してテスト
            print(f'\n=== LINEユーザーID設定テスト ===')
            try:
                # 一時的にLINEユーザーIDを設定
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("UPDATE users SET line_user_id = ? WHERE id = ?", (test_line_id, user[0]))
                conn.commit()
                conn.close()
                
                print(f'LINEユーザーIDを設定しました: {test_line_id}')
                
                # 再度ユーザー取得をテスト
                user = get_user_by_line_id(test_line_id)
                if user:
                    print(f'ユーザー取得成功: {user}')
                    
                    # コンテンツ追加処理をテスト
                    result = handle_content_confirmation(test_line_id, 'accounting')
                    print(f'コンテンツ追加処理結果: {result}')
                else:
                    print('ユーザー取得失敗')
                    
            except Exception as e:
                print(f'テストエラー: {e}')
                import traceback
                traceback.print_exc()
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 