import os
import sys
sys.path.append('.')

from services.user_service import get_user_by_line_id
from utils.db import get_db_connection

print('=== LINE Botユーザー登録確認 ===')

# 実際のLINEユーザーID（LINE Botで確認）
test_line_ids = [
    'U1234567890abcdef',  # テスト用
    'Uabcdef1234567890',  # テスト用
]

try:
    # データベース接続
    conn = get_db_connection()
    c = conn.cursor()
    
    # 全ユーザーを確認
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    
    print(f'登録ユーザー数: {len(users)}')
    for user in users:
        print(f'ユーザー: {user}')
        if user[4]:  # line_user_id
            print(f'  LINE ID: {user[4]}')
            print(f'  Stripe Customer: {user[2]}')
            print(f'  Stripe Subscription: {user[3]}')
    
    # 使用量ログを確認
    c.execute("SELECT * FROM usage_logs")
    logs = c.fetchall()
    
    print(f'\n使用量ログ数: {len(logs)}')
    for log in logs:
        print(f'ログ: {log}')
    
    conn.close()
    
    # LINE Botサービスでユーザー取得をテスト
    print(f'\n=== LINE Botサービステスト ===')
    for line_id in test_line_ids:
        user = get_user_by_line_id(line_id)
        if user:
            print(f'LINE ID {line_id}: 見つかりました')
            print(f'  ユーザー: {user}')
        else:
            print(f'LINE ID {line_id}: 見つかりません')
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 