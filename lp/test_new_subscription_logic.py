import os
import sys
sys.path.append('.')

from services.line_service import check_subscription_status
from utils.db import get_db_connection

print('=== 新しいサブスクリプションでのロジックテスト ===')

try:
    # 新しいサブスクリプションIDを取得
    stripe_subscription_id = 'sub_1RpVU2Ixg6C5hAVdeyAz8Tjk'
    
    # サブスクリプションの状態をチェック
    subscription_status = check_subscription_status(stripe_subscription_id)
    is_trial_period = subscription_status.get('subscription', {}).get('status') == 'trialing'
    is_trial = subscription_status['status'] == 'trialing'
    
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
    
    # 詳細な記録を確認
    c.execute('''
        SELECT content_type, is_free, pending_charge, created_at 
        FROM usage_logs 
        WHERE user_id = 1 
        ORDER BY created_at
    ''')
    records = c.fetchall()
    
    conn.close()
    
    print(f'\n=== データベース状況 ===')
    print(f'全コンテンツ数: {total_usage_count}')
    print(f'トライアル期間中の追加分: {trial_additions}')
    print(f'トライアル期間終了後の追加分: {post_trial_additions}')
    
    print(f'\n=== 詳細記録 ===')
    for i, record in enumerate(records):
        print(f'記録 {i+1}: {record[0]} (無料: {record[1]}, 課金予定: {record[2]}, 作成日: {record[3]})')
    
    # 新しいロジックで計算
    print(f'\n=== 新しいロジックでの計算 ===')
    if is_trial_period:
        current_count = total_usage_count + 1
        is_free = True
        print(f'トライアル期間中: current_count = {current_count}, is_free = {is_free}')
    else:
        current_count = post_trial_additions + 1
        is_free = current_count == 1
        print(f'トライアル期間終了後: current_count = {current_count}, is_free = {is_free}')
    
    print(f'\n=== シミュレーション結果 ===')
    if is_free:
        print(f'✅ 次のコンテンツ追加は無料です（{current_count}個目）')
    else:
        print(f'💰 次のコンテンツ追加は有料です（{current_count}個目、1,500円）')
    
    # 実際のLINE Botでの動作をシミュレート
    print(f'\n=== LINE Bot動作シミュレート ===')
    print('1. ユーザーが「追加」と入力')
    print('2. コンテンツ選択画面が表示される')
    print('3. ユーザーがコンテンツを選択')
    print('4. 確認画面で料金が表示される')
    
    if is_trial_period:
        print(f'   料金表示: 無料（トライアル期間中）')
    else:
        if is_free:
            print(f'   料金表示: 無料（{current_count}個目）')
        else:
            print(f'   料金表示: 1,500円（{current_count}個目、1週間後に課金）')
    
    print('5. ユーザーが「はい」と入力')
    print('6. コンテンツが追加される')
    
    if is_trial_period:
        print('   処理: データベースのみに記録（Stripe UsageRecordは作成されない）')
    else:
        if is_free:
            print('   処理: Stripe UsageRecordを作成（無料）')
        else:
            print('   処理: Stripe UsageRecordを作成（有料、1週間後に課金）')
    
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc() 