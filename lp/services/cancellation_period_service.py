import os
import stripe
from datetime import datetime
from utils.db import get_db_connection, get_db_type

class CancellationPeriodService:
    """cancellation_historyテーブルを使用した契約期間管理サービス"""
    
    def __init__(self):
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.db_type = get_db_type()
    
    def update_subscription_period(self, user_id, content_type, stripe_subscription_id):
        """
        契約期間情報をcancellation_historyテーブルに更新
        """
        try:
            # Stripe APIでサブスクリプション情報を取得
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            
            conn = get_db_connection()
            c = conn.cursor()
            
            # 既存のレコードを確認
            if self.db_type == 'postgresql':
                c.execute('''
                    SELECT id FROM cancellation_history 
                    WHERE user_id = %s AND content_type = %s
                ''', (user_id, content_type))
            else:
                c.execute('''
                    SELECT id FROM cancellation_history 
                    WHERE user_id = ? AND content_type = ?
                ''', (user_id, content_type))
            
            existing_record = c.fetchone()
            
            if existing_record:
                # 既存レコードを更新
                if self.db_type == 'postgresql':
                    c.execute('''
                        UPDATE cancellation_history SET
                            subscription_status = %s,
                            current_period_start = %s,
                            current_period_end = %s,
                            trial_start = %s,
                            trial_end = %s,
                            stripe_subscription_id = %s
                        WHERE user_id = %s AND content_type = %s
                    ''', (
                        subscription.status,
                        datetime.fromtimestamp(subscription.current_period_start) if subscription.current_period_start else None,
                        datetime.fromtimestamp(subscription.current_period_end) if subscription.current_period_end else None,
                        datetime.fromtimestamp(subscription.trial_start) if subscription.trial_start else None,
                        datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None,
                        stripe_subscription_id,
                        user_id,
                        content_type
                    ))
                else:
                    c.execute('''
                        UPDATE cancellation_history SET
                            subscription_status = ?,
                            current_period_start = ?,
                            current_period_end = ?,
                            trial_start = ?,
                            trial_end = ?,
                            stripe_subscription_id = ?
                        WHERE user_id = ? AND content_type = ?
                    ''', (
                        subscription.status,
                        datetime.fromtimestamp(subscription.current_period_start) if subscription.current_period_start else None,
                        datetime.fromtimestamp(subscription.current_period_end) if subscription.current_period_end else None,
                        datetime.fromtimestamp(subscription.trial_start) if subscription.trial_start else None,
                        datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None,
                        stripe_subscription_id,
                        user_id,
                        content_type
                    ))
            else:
                # 新規レコードを作成
                if self.db_type == 'postgresql':
                    c.execute('''
                        INSERT INTO cancellation_history 
                        (user_id, content_type, cancelled_at, subscription_status, 
                         current_period_start, current_period_end, trial_start, trial_end, stripe_subscription_id)
                        VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s, %s)
                    ''', (
                        user_id,
                        content_type,
                        subscription.status,
                        datetime.fromtimestamp(subscription.current_period_start) if subscription.current_period_start else None,
                        datetime.fromtimestamp(subscription.current_period_end) if subscription.current_period_end else None,
                        datetime.fromtimestamp(subscription.trial_start) if subscription.trial_start else None,
                        datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None,
                        stripe_subscription_id
                    ))
                else:
                    c.execute('''
                        INSERT INTO cancellation_history 
                        (user_id, content_type, cancelled_at, subscription_status, 
                         current_period_start, current_period_end, trial_start, trial_end, stripe_subscription_id)
                        VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id,
                        content_type,
                        subscription.status,
                        datetime.fromtimestamp(subscription.current_period_start) if subscription.current_period_start else None,
                        datetime.fromtimestamp(subscription.current_period_end) if subscription.current_period_end else None,
                        datetime.fromtimestamp(subscription.trial_start) if subscription.trial_start else None,
                        datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None,
                        stripe_subscription_id
                    ))
            
            conn.commit()
            conn.close()
            
            print(f'[DEBUG] 契約期間更新完了: user_id={user_id}, content_type={content_type}, status={subscription.status}')
            return True
            
        except Exception as e:
            print(f'[ERROR] 契約期間更新エラー: {e}')
            return False
    
    def check_user_access_local(self, user_id, content_type):
        """
        cancellation_historyテーブルで契約期間をチェック
        """
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # usage_logsとcancellation_historyを結合して判定
            if self.db_type == 'postgresql':
                c.execute('''
                    SELECT 
                        ul.id,
                        ch.subscription_status,
                        ch.current_period_end,
                        ch.trial_end
                    FROM usage_logs ul
                    LEFT JOIN cancellation_history ch ON ul.user_id = ch.user_id AND ul.content_type = ch.content_type
                    WHERE ul.user_id = %s AND ul.content_type = %s
                ''', (user_id, content_type))
            else:
                c.execute('''
                    SELECT 
                        ul.id,
                        ch.subscription_status,
                        ch.current_period_end,
                        ch.trial_end
                    FROM usage_logs ul
                    LEFT JOIN cancellation_history ch ON ul.user_id = ch.user_id AND ul.content_type = ch.content_type
                    WHERE ul.user_id = ? AND ul.content_type = ?
                ''', (user_id, content_type))
            
            result = c.fetchone()
            conn.close()
            
            if not result:
                return False, "コンテンツが追加されていません"
            
            _, subscription_status, current_period_end, trial_end = result
            
            # 契約期間の判定
            current_time = datetime.now()
            
            if subscription_status == 'active':
                return True, "アクティブなサブスクリプション"
            elif subscription_status == 'past_due':
                return True, "支払い遅延中だが利用可能"
            elif subscription_status == 'canceled':
                if current_period_end and current_period_end > current_time:
                    return True, "キャンセル済みだが期間内"
                else:
                    return False, "契約期間が終了"
            elif subscription_status == 'trialing':
                return False, "トライアル期間中（請求が始まっていません）"
            elif subscription_status in ['incomplete', 'incomplete_expired', 'unpaid']:
                return False, "支払いが完了していません"
            elif subscription_status is None:
                # cancellation_historyにレコードがない場合は、usage_logsの存在だけで判定
                return True, "コンテンツが追加済み"
            else:
                return False, f"サブスクリプションが無効（ステータス: {subscription_status}）"
                
        except Exception as e:
            print(f'[ERROR] ローカルチェックエラー: {e}')
            return False, "データベースエラーが発生しました"
    
    def get_subscription_info(self, user_id, content_type):
        """
        ユーザーのサブスクリプション情報を取得
        """
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            if self.db_type == 'postgresql':
                c.execute('''
                    SELECT 
                        subscription_status,
                        current_period_start,
                        current_period_end,
                        trial_start,
                        trial_end,
                        cancelled_at
                    FROM cancellation_history
                    WHERE user_id = %s AND content_type = %s
                ''', (user_id, content_type))
            else:
                c.execute('''
                    SELECT 
                        subscription_status,
                        current_period_start,
                        current_period_end,
                        trial_start,
                        trial_end,
                        cancelled_at
                    FROM cancellation_history
                    WHERE user_id = ? AND content_type = ?
                ''', (user_id, content_type))
            
            result = c.fetchone()
            conn.close()
            
            if result:
                return {
                    'status': result[0],
                    'current_period_start': result[1],
                    'current_period_end': result[2],
                    'trial_start': result[3],
                    'trial_end': result[4],
                    'cancelled_at': result[5]
                }
            else:
                return None
                
        except Exception as e:
            print(f'[ERROR] サブスクリプション情報取得エラー: {e}')
            return None 