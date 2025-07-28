import os
import sys
sys.path.append('.')

from services.stripe_service import check_subscription_status
from utils.db import get_db_connection

print('=== トライアル期間終了後のロジックテスト ===')

try:
    # サブスクリプションIDを取得（実際のIDを使用）
    stripe_subscription_id = 'sub_1RpNPVIxg6C5hAVdQET1f85P'
    
    # サブスクリプションの状態をチェック
    subscription_status = check_subscription_status(stripe_subscription_id)
    is_trial_period = subscription_status.get('subscription', {}).get('status') == 'trialing'
    
    print(f'サブスクリプションID: {stripe_subscription_id}')
    print(f'ステータス: {subscription_status["status"]}')
    print(f'トライアル期間中: {is_trial_period}')
    
    # データベースの状況を確認
    conn = get_db_connection()
    c = conn.cursor()
    
    # 全コンテンツの合計数を取得
    c.execute('SELECT COUNT(*) FROM usage_logs WHERE user_id = 1')
    total_usage_count = c.fetchone()[0]
    
    # トライアル期間中の追加分（pending_charge = FALSE）
    c.execute('SELECT COUNT(*) FROM usage_logs WHERE user_id = 1 AND pending_charge = FALSE')
    trial_additions = c.fetchone()[0]
    
    # トライアル期間終了後の追加分（pending_charge = TRUE）
    c.execute('SELECT COUNT(*) FROM usage_logs WHERE user_id = 1 AND pending_charge = TRUE')
    post_trial_additions = c.fetchone()[0]
    
    conn.close()
    
    print(f'\n=== データベース状況 ===')
    print(f'全コンテンツ数: {total_usage_count}')
    print(f'トライアル期間中の追加分: {trial_additions}')
    print(f'トライアル期間終了後の追加分: {post_trial_additions}')
    
    # トライアル期間終了後のロジック
    print(f'\n=== トライアル期間終了後のロジック ===')
    if not is_trial_period:
        print('トライアル期間が終了しています')
        
        # 次のコンテンツ追加の計算
        current_count = post_trial_additions + 1
        is_free = current_count == 1
        
        print(f'次のコンテンツ追加: {current_count}個目')
        print(f'無料かどうか: {is_free}')
        
        if is_free:
            print('✅ 1個目は無料です')
        else:
            print('💰 2個目以降は1,500円です')
    else:
        print('トライアル期間中です')
        print('✅ すべてのコンテンツ追加は無料です')
    
except Exception as e:
    print(f'エラー: {e}')
    import traceback
    traceback.print_exc() 