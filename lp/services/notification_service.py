import os
import json
from datetime import datetime, timedelta
from lp.utils.db import get_db_connection
from lp.services.line_api_service import line_api_service
from lp.services.stripe_payment_service import stripe_payment_service
from lp.services.company_service import CompanyService

class NotificationService:
    """通知・アラート機能サービス"""
    
    def __init__(self):
        self.notification_types = {
            'payment_success': {
                'name': '支払い完了',
                'template': '🎉 支払いが完了しました！\n\n📅 次回請求日: {next_billing_date}\n💰 請求金額: ¥{amount:,}\n\n📱 何かご質問がございましたら、お気軽にお声かけください。'
            },
            'payment_failed': {
                'name': '支払い失敗',
                'template': '⚠️ 支払いに失敗しました\n\n💰 請求金額: ¥{amount:,}\n📅 再試行日: {retry_date}\n\n💳 お支払い方法の確認をお願いします。\n📞 サポートが必要でしたら、お気軽にお声かけください。'
            },
            'subscription_renewal': {
                'name': '契約更新',
                'template': '📅 契約更新のお知らせ\n\n🔄 自動更新日: {renewal_date}\n💰 更新金額: ¥{amount:,}\n\n📱 解約をご希望の場合は、お気軽にお声かけください。'
            },
            'trial_ending': {
                'name': 'トライアル終了',
                'template': '⏰ トライアル終了のお知らせ\n\n📅 終了日: {trial_end_date}\n💰 開始金額: ¥{amount:,}\n\n💳 継続をご希望の場合は、お支払い方法の設定をお願いします。'
            },
            'cancellation_confirmed': {
                'name': '解約確認',
                'template': '📋 解約が完了しました\n\n📅 解約日: {cancellation_date}\n📝 理由: {reason}\n\n🗑️ データは{deletion_days}日後に自動削除されます。\n📞 復旧をご希望の場合は、お気軽にお声かけください。'
            },
            'deletion_scheduled': {
                'name': 'データ削除予定',
                'template': '🗑️ データ削除予定のお知らせ\n\n📅 削除予定日: {deletion_date}\n⚠️ この日以降、データは復旧できません。\n\n📞 継続をご希望の場合は、お気軽にお声かけください。'
            }
        }
        
        self.company_service = CompanyService()
    
    def send_payment_notification(self, company_id, notification_type, payment_data=None):
        """支払い関連の通知を送信"""
        try:
            # 企業情報を取得
            company_result = self.company_service.get_company(company_id)
            if not company_result['success']:
                return {
                    'success': False,
                    'error': '企業が見つかりません'
                }
            
            company = company_result['company']
            
            # 通知テンプレートを取得
            if notification_type not in self.notification_types:
                return {
                    'success': False,
                    'error': f'不明な通知タイプ: {notification_type}'
                }
            
            template_info = self.notification_types[notification_type]
            
            # テンプレート変数を設定
            template_vars = {
                'company_name': company['company_name'],
                'next_billing_date': payment_data.get('next_billing_date', '未設定'),
                'amount': payment_data.get('amount', 0),
                'retry_date': payment_data.get('retry_date', '未設定'),
                'renewal_date': payment_data.get('renewal_date', '未設定'),
                'trial_end_date': payment_data.get('trial_end_date', '未設定'),
                'cancellation_date': payment_data.get('cancellation_date', '未設定'),
                'reason': payment_data.get('reason', '未設定'),
                'deletion_days': payment_data.get('deletion_days', 30),
                'deletion_date': payment_data.get('deletion_date', '未設定')
            }
            
            # メッセージを生成
            message = template_info['template'].format(**template_vars)
            
            # LINE通知を送信
            notification_data = {
                'company_name': company['company_name'],
                'notification_type': notification_type,
                'message': message,
                'sent_at': datetime.now().isoformat()
            }
            
            line_result = line_api_service.send_notification_to_company(
                company_id, notification_type, notification_data
            )
            
            # 通知履歴を記録
            self._record_notification(company_id, notification_type, notification_data)
            
            return {
                'success': True,
                'message': f'{template_info["name"]}通知を送信しました',
                'notification_data': notification_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'通知送信エラー: {str(e)}'
            }
    
    def send_trial_ending_reminder(self, company_id, days_before=3):
        """トライアル終了前のリマインダーを送信"""
        try:
            # 企業の支払い情報を取得
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT trial_end, current_period_end
                FROM company_payments
                WHERE company_id = %s
            ''', (company_id,))
            
            payment_info = c.fetchone()
            conn.close()
            
            if not payment_info:
                return {
                    'success': False,
                    'error': '支払い情報が見つかりません'
                }
            
            trial_end, current_period_end = payment_info
            
            if not trial_end:
                return {
                    'success': False,
                    'error': 'トライアル期間が設定されていません'
                }
            
            # トライアル終了日をチェック
            trial_end_date = trial_end
            if isinstance(trial_end_date, str):
                trial_end_date = datetime.fromisoformat(trial_end_date.replace('Z', '+00:00'))
            
            days_until_end = (trial_end_date - datetime.now()).days
            
            if days_until_end <= days_before:
                # リマインダーを送信
                payment_data = {
                    'trial_end_date': trial_end_date.strftime('%Y年%m月%d日'),
                    'amount': 3900  # 基本料金
                }
                
                return self.send_payment_notification(
                    company_id, 'trial_ending', payment_data
                )
            else:
                return {
                    'success': False,
                    'message': f'トライアル終了まで{days_until_end}日あります'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'トライアル終了リマインダーエラー: {str(e)}'
            }
    
    def send_renewal_reminder(self, company_id, days_before=7):
        """契約更新前のリマインダーを送信"""
        try:
            # 企業の支払い情報を取得
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT current_period_end
                FROM company_payments
                WHERE company_id = %s AND subscription_status = 'active'
            ''', (company_id,))
            
            payment_info = c.fetchone()
            conn.close()
            
            if not payment_info:
                return {
                    'success': False,
                    'error': 'アクティブな支払い情報が見つかりません'
                }
            
            current_period_end = payment_info[0]
            
            if not current_period_end:
                return {
                    'success': False,
                    'error': '更新日が設定されていません'
                }
            
            # 更新日をチェック
            renewal_date = current_period_end
            if isinstance(renewal_date, str):
                renewal_date = datetime.fromisoformat(renewal_date.replace('Z', '+00:00'))
            
            days_until_renewal = (renewal_date - datetime.now()).days
            
            if days_until_renewal <= days_before:
                # リマインダーを送信
                payment_data = {
                    'renewal_date': renewal_date.strftime('%Y年%m月%d日'),
                    'amount': 3900  # 基本料金
                }
                
                return self.send_payment_notification(
                    company_id, 'subscription_renewal', payment_data
                )
            else:
                return {
                    'success': False,
                    'message': f'契約更新まで{days_until_renewal}日あります'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'契約更新リマインダーエラー: {str(e)}'
            }
    
    def send_deletion_reminder(self, company_id, days_before=7):
        """データ削除前のリマインダーを送信"""
        try:
            # 解約履歴から削除予定日を取得
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT scheduled_deletion_date
                FROM company_cancellations
                WHERE company_id = %s AND scheduled_deletion_date IS NOT NULL
                ORDER BY cancelled_at DESC
                LIMIT 1
            ''', (company_id,))
            
            deletion_info = c.fetchone()
            conn.close()
            
            if not deletion_info:
                return {
                    'success': False,
                    'error': '削除予定が見つかりません'
                }
            
            scheduled_deletion_date = deletion_info[0]
            
            if not scheduled_deletion_date:
                return {
                    'success': False,
                    'error': '削除予定日が設定されていません'
                }
            
            # 削除予定日をチェック
            deletion_date = scheduled_deletion_date
            if isinstance(deletion_date, str):
                deletion_date = datetime.fromisoformat(deletion_date.replace('Z', '+00:00'))
            
            days_until_deletion = (deletion_date - datetime.now()).days
            
            if days_until_deletion <= days_before:
                # リマインダーを送信
                payment_data = {
                    'deletion_date': deletion_date.strftime('%Y年%m月%d日')
                }
                
                return self.send_payment_notification(
                    company_id, 'deletion_scheduled', payment_data
                )
            else:
                return {
                    'success': False,
                    'message': f'データ削除まで{days_until_deletion}日あります'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'データ削除リマインダーエラー: {str(e)}'
            }
    
    def _record_notification(self, company_id, notification_type, notification_data):
        """通知履歴を記録"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO company_notifications (
                    company_id, notification_type, notification_data, sent_at
                ) VALUES (%s, %s, %s, %s)
            ''', (
                company_id, notification_type, 
                json.dumps(notification_data, ensure_ascii=False),
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"通知履歴記録エラー: {e}")
    
    def get_notification_history(self, company_id=None, notification_type=None, limit=50):
        """通知履歴を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            query = '''
                SELECT cn.*, c.company_name
                FROM company_notifications cn
                JOIN companies c ON cn.company_id = c.id
                WHERE 1=1
            '''
            params = []
            
            if company_id:
                query += ' AND cn.company_id = %s'
                params.append(company_id)
            
            if notification_type:
                query += ' AND cn.notification_type = %s'
                params.append(notification_type)
            
            query += ' ORDER BY cn.sent_at DESC LIMIT %s'
            params.append(limit)
            
            c.execute(query, params)
            
            notifications = []
            for row in c.fetchall():
                notifications.append({
                    'id': row[0],
                    'company_id': row[1],
                    'company_name': row[5],
                    'notification_type': row[2],
                    'notification_data': json.loads(row[3]) if row[3] else {},
                    'sent_at': row[4].isoformat() if row[4] else None
                })
            
            conn.close()
            
            return {
                'success': True,
                'notifications': notifications,
                'count': len(notifications)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'通知履歴取得エラー: {str(e)}'
            }
    
    def get_notification_statistics(self):
        """通知統計を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 通知タイプ別の統計
            c.execute('''
                SELECT notification_type, COUNT(*) as count
                FROM company_notifications
                GROUP BY notification_type
                ORDER BY count DESC
            ''')
            
            type_stats = []
            for row in c.fetchall():
                type_stats.append({
                    'notification_type': row[0],
                    'count': row[1]
                })
            
            # 企業別の通知統計
            c.execute('''
                SELECT c.company_name, COUNT(cn.id) as count
                FROM companies c
                LEFT JOIN company_notifications cn ON c.id = cn.company_id
                GROUP BY c.id, c.company_name
                ORDER BY count DESC
                LIMIT 10
            ''')
            
            company_stats = []
            for row in c.fetchall():
                company_stats.append({
                    'company_name': row[0],
                    'count': row[1]
                })
            
            # 今日の通知数
            c.execute('''
                SELECT COUNT(*) as count
                FROM company_notifications
                WHERE DATE(sent_at) = CURRENT_DATE
            ''')
            
            today_count = c.fetchone()[0]
            
            conn.close()
            
            return {
                'success': True,
                'statistics': {
                    'type_stats': type_stats,
                    'company_stats': company_stats,
                    'today_count': today_count
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'通知統計取得エラー: {str(e)}'
            }

# インスタンスを作成
notification_service = NotificationService() 