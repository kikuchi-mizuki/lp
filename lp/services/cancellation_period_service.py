import os
import stripe
from datetime import datetime
from utils.db import get_db_connection, get_db_type

class CancellationPeriodService:
    """cancellation_historyテーブルを使用した契約期間管理サービス"""
    
    def __init__(self):
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.db_type = get_db_type()
    
    def create_content_period_record(self, user_id, content_type, stripe_subscription_id):
        """
        コンテンツ追加時に契約期間情報をcancellation_historyテーブルに作成
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
                # 既存レコードを更新（コンテンツを再追加した場合）
                if self.db_type == 'postgresql':
                    c.execute('''
                        UPDATE cancellation_history SET
                            subscription_status = %s,
                            current_period_start = %s,
                            current_period_end = %s,
                            trial_start = %s,
                            trial_end = %s,
                            stripe_subscription_id = %s,
                            cancelled_at = NULL
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
                            stripe_subscription_id = ?,
                            cancelled_at = NULL
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
                        VALUES (%s, %s, NULL, %s, %s, %s, %s, %s, %s)
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
                        VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?)
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
            
            print(f'[DEBUG] コンテンツ期間記録作成完了: user_id={user_id}, content_type={content_type}, status={subscription.status}')
            return True
            
        except Exception as e:
            print(f'[ERROR] コンテンツ期間記録作成エラー: {e}')
            return False
    
    def update_subscription_status(self, user_id, content_type, new_status):
        """
        サブスクリプションステータスを更新（解約時など）
        """
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            if self.db_type == 'postgresql':
                c.execute('''
                    UPDATE cancellation_history SET
                        subscription_status = %s,
                        cancelled_at = CASE WHEN %s = 'canceled' THEN CURRENT_TIMESTAMP ELSE cancelled_at END
                    WHERE user_id = %s AND content_type = %s
                ''', (new_status, new_status, user_id, content_type))
            else:
                c.execute('''
                    UPDATE cancellation_history SET
                        subscription_status = ?,
                        cancelled_at = CASE WHEN ? = 'canceled' THEN CURRENT_TIMESTAMP ELSE cancelled_at END
                    WHERE user_id = ? AND content_type = ?
                ''', (new_status, new_status, user_id, content_type))
            
            conn.commit()
            conn.close()
            
            print(f'[DEBUG] ステータス更新完了: user_id={user_id}, content_type={content_type}, status={new_status}')
            return True
            
        except Exception as e:
            print(f'[ERROR] ステータス更新エラー: {e}')
            return False
    
    def check_user_access_local(self, user_id, content_type):
        """
        cancellation_historyテーブルで契約期間をチェック
        """
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # cancellation_historyテーブルでコンテンツの契約期間情報を確認
            if self.db_type == 'postgresql':
                c.execute('''
                    SELECT 
                        subscription_status,
                        current_period_end,
                        trial_end,
                        cancelled_at
                    FROM cancellation_history 
                    WHERE user_id = %s AND content_type = %s
                ''', (user_id, content_type))
            else:
                c.execute('''
                    SELECT 
                        subscription_status,
                        current_period_end,
                        trial_end,
                        cancelled_at
                    FROM cancellation_history 
                    WHERE user_id = ? AND content_type = ?
                ''', (user_id, content_type))
            
            result = c.fetchone()
            conn.close()
            
            if not result:
                return False, "コンテンツが追加されていません"
            
            subscription_status, current_period_end, trial_end, cancelled_at = result
            
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