import os
import sys
sys.path.append('.')

from services.stripe_service import check_subscription_status
from utils.db import get_db_connection

print('=== 新しいサブスクリプションロジックテスト ===')

try:
    # サブスクリプションIDを取得（実際のIDを使用）
    stripe_subscription_id = 'sub_1RpNPVIxg6C5hAVdQET1f85P'
    
    # サブスクリプションの状態をチェック
    subscription_status = check_subscription_status(stripe_subscription_id)
    
    print(f'サブスクリプションID: {stripe_subscription_id}')
    print(f'ステータス: {subscription_status["status"]}')
    print(f'有効かどうか: {subscription_status["is_active"]}')
    
    # データベースの状況を確認
    conn = get_db_connection()
    c = conn.cursor()
    
    # ユーザー情報を取得
    c.execute('SELECT id, email FROM users WHERE stripe_subscription_id = %s', (stripe_subscription_id,))
    user = c.fetchone()
    
    if user:
        user_id, email = user
        print(f'\n=== ユーザー情報 ===')
        print(f'ユーザーID: {user_id}')
        print(f'メール: {email}')
        
        # 使用ログを取得
        c.execute('SELECT * FROM usage_logs WHERE user_id = %s ORDER BY created_at', (user_id,))
        usage_logs = c.fetchall()
        
        print(f'\n=== 使用ログ ===')
        print(f'総ログ数: {len(usage_logs)}')
        
        # トライアル期間中の追加分（pending_charge = FALSE）
        trial_additions = [log for log in usage_logs if not log[6]]  # pending_charge = FALSE
        # トライアル期間終了後の追加分（pending_charge = TRUE）
        post_trial_additions = [log for log in usage_logs if log[6]]  # pending_charge = TRUE
        
        print(f'トライアル期間中の追加分: {len(trial_additions)}')
        print(f'トライアル期間終了後の追加分: {len(post_trial_additions)}')
        
        # 新しいロジックのテスト
        print(f'\n=== 新しいロジックテスト ===')
        
        if subscription_status['status'] == 'trialing':
            print('トライアル期間中です')
            print('✅ すべてのコンテンツ追加は無料です')
            
            # 次のコンテンツ追加のシミュレーション
            next_count = len(usage_logs) + 1
            print(f'次のコンテンツ追加: {next_count}個目')
            print(f'料金: 無料（トライアル期間中）')
            
        else:
            print('トライアル期間が終了しています')
            
            # 次のコンテンツ追加のシミュレーション
            next_count = len(post_trial_additions) + 1
            is_free = next_count == 1
            
            print(f'次のコンテンツ追加: {next_count}個目')
            if is_free:
                print(f'料金: 無料（1個目）')
            else:
                print(f'料金: 1,500円（{next_count}個目）')
        
        # 詳細なログ表示
        print(f'\n=== 詳細ログ ===')
        for i, log in enumerate(usage_logs):
            print(f'ログ {i+1}: {log[5]} (無料: {log[4]}, 課金予定: {log[6]}, 作成日: {log[7]})')
    
    else:
        print(f'\n❌ データベースにユーザーが見つかりません')
    
    conn.close()
    
except Exception as e:
    print(f'エラー: {e}')
    import traceback
    traceback.print_exc() 