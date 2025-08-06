import os
import stripe
from datetime import datetime
from lp.utils.db import get_db_connection, get_db_type

class SubscriptionPeriodService:
    """契約期間管理サービス"""
    
    def __init__(self):
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.db_type = get_db_type()
    
    def sync_subscription_period(self, user_id, stripe_subscription_id):
        """
        Stripeから契約期間情報を同期してデータベースに保存
        """
        try:
            # Stripe APIでサブスクリプション情報を取得
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            
            conn = get_db_connection()
            c = conn.cursor()
            
            # 契約期間情報をデータベースに保存/更新
            if self.db_type == 'postgresql':
                c.execute('''
                    INSERT INTO subscription_periods 
                    (user_id, stripe_subscription_id, subscription_status, 
                     current_period_start, current_period_end, trial_start, trial_end, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (stripe_subscription_id) 
                    DO UPDATE SET
                        subscription_status = EXCLUDED.subscription_status,
                        current_period_start = EXCLUDED.current_period_start,
                        current_period_end = EXCLUDED.current_period_end,
                        trial_start = EXCLUDED.trial_start,
                        trial_end = EXCLUDED.trial_end,
                        updated_at = CURRENT_TIMESTAMP
                ''', (
                    user_id,
                    stripe_subscription_id,
                    subscription.status,
                    datetime.fromtimestamp(subscription.current_period_start) if subscription.current_period_start else None,
                    datetime.fromtimestamp(subscription.current_period_end) if subscription.current_period_end else None,
                    datetime.fromtimestamp(subscription.trial_start) if subscription.trial_start else None,
                    datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None
                ))
            else:
                # SQLite用
                c.execute('''
                    INSERT OR REPLACE INTO subscription_periods 
                    (user_id, stripe_subscription_id, subscription_status, 
                     current_period_start, current_period_end, trial_start, trial_end, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    user_id,
                    stripe_subscription_id,
                    subscription.status,
                    datetime.fromtimestamp(subscription.current_period_start) if subscription.current_period_start else None,
                    datetime.fromtimestamp(subscription.current_period_end) if subscription.current_period_end else None,
                    datetime.fromtimestamp(subscription.trial_start) if subscription.trial_start else None,
                    datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None
                ))
            
            conn.commit()
            conn.close()
            
            print(f'[DEBUG] 契約期間同期完了: user_id={user_id}, status={subscription.status}')
            return True
            
        except Exception as e:
            print(f'[ERROR] 契約期間同期エラー: {e}')
            return False
    
    def check_user_access_local(self, user_id, content_type):
        """
        ローカルデータベースで契約期間をチェック
        """
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # usage_logsとsubscription_periodsを結合して判定
            if self.db_type == 'postgresql':
                c.execute('''
                    SELECT 
                        ul.id,
                        sp.subscription_status,
                        sp.current_period_end,
                        sp.trial_end
                    FROM usage_logs ul
                    JOIN users u ON ul.user_id = u.id
                    LEFT JOIN subscription_periods sp ON u.stripe_subscription_id = sp.stripe_subscription_id
                    WHERE ul.user_id = %s AND ul.content_type = %s
                ''', (user_id, content_type))
            else:
                c.execute('''
                    SELECT 
                        ul.id,
                        sp.subscription_status,
                        sp.current_period_end,
                        sp.trial_end
                    FROM usage_logs ul
                    JOIN users u ON ul.user_id = u.id
                    LEFT JOIN subscription_periods sp ON u.stripe_subscription_id = sp.stripe_subscription_id
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
            else:
                return False, f"サブスクリプションが無効（ステータス: {subscription_status}）"
                
        except Exception as e:
            print(f'[ERROR] ローカルチェックエラー: {e}')
            return False, "データベースエラーが発生しました"
    
    def get_subscription_info(self, user_id):
        """
        ユーザーのサブスクリプション情報を取得
        """
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            if self.db_type == 'postgresql':
                c.execute('''
                    SELECT 
                        sp.subscription_status,
                        sp.current_period_start,
                        sp.current_period_end,
                        sp.trial_start,
                        sp.trial_end,
                        sp.updated_at
                    FROM subscription_periods sp
                    JOIN users u ON sp.user_id = u.id
                    WHERE u.id = %s
                ''', (user_id,))
            else:
                c.execute('''
                    SELECT 
                        sp.subscription_status,
                        sp.current_period_start,
                        sp.current_period_end,
                        sp.trial_start,
                        sp.trial_end,
                        sp.updated_at
                    FROM subscription_periods sp
                    JOIN users u ON sp.user_id = u.id
                    WHERE u.id = ?
                ''', (user_id,))
            
            result = c.fetchone()
            conn.close()
            
            if result:
                return {
                    'status': result[0],
                    'current_period_start': result[1],
                    'current_period_end': result[2],
                    'trial_start': result[3],
                    'trial_end': result[4],
                    'updated_at': result[5]
                }
            else:
                return None
                
        except Exception as e:
            print(f'[ERROR] サブスクリプション情報取得エラー: {e}')
            return None