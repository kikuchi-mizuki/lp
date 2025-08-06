import os
import json
import logging
from datetime import datetime, timedelta
from lp.utils.db import get_db_connection
from lp.services.notification_service import notification_service
from lp.services.company_service import CompanyService

class ReminderService:
    """自動リマインダーサービス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.company_service = CompanyService()
        
        # リマインダータイプの定義
        self.reminder_types = {
            'trial_ending': {
                'name': 'トライアル終了',
                'default_days': [7, 3, 1],
                'template': '⏰ トライアル終了のお知らせ\n\n📅 終了日: {trial_end_date}\n💰 開始金額: ¥{amount:,}\n\n💳 継続をご希望の場合は、お支払い方法の設定をお願いします。\n📞 サポートが必要でしたら、お気軽にお声かけください。'
            },
            'payment_due': {
                'name': '支払い期限',
                'default_days': [7, 3, 1],
                'template': '💰 支払い期限のお知らせ\n\n📅 支払い期限: {due_date}\n💰 請求金額: ¥{amount:,}\n\n💳 お支払い方法の確認をお願いします。\n📞 サポートが必要でしたら、お気軽にお声かけください。'
            },
            'subscription_renewal': {
                'name': '契約更新',
                'default_days': [14, 7, 3],
                'template': '📅 契約更新のお知らせ\n\n🔄 自動更新日: {renewal_date}\n💰 更新金額: ¥{amount:,}\n\n📱 解約をご希望の場合は、お気軽にお声かけください。'
            },
            'payment_failed': {
                'name': '支払い失敗',
                'default_days': [1, 3, 7],
                'template': '⚠️ 支払いに失敗しました\n\n💰 請求金額: ¥{amount:,}\n📅 再試行日: {retry_date}\n\n💳 お支払い方法の確認をお願いします。\n📞 サポートが必要でしたら、お気軽にお声かけください。'
            },
            'cancellation_reminder': {
                'name': '解約リマインダー',
                'default_days': [7, 3, 1],
                'template': '📋 解約予定のお知らせ\n\n📅 解約予定日: {cancellation_date}\n📝 理由: {reason}\n\n🗑️ データは{deletion_days}日後に自動削除されます。\n📞 継続をご希望の場合は、お気軽にお声かけください。'
            },
            'data_deletion': {
                'name': 'データ削除',
                'default_days': [7, 3, 1],
                'template': '🗑️ データ削除予定のお知らせ\n\n📅 削除予定日: {deletion_date}\n⚠️ この日以降、データは復旧できません。\n\n📞 継続をご希望の場合は、お気軽にお声かけください。'
            },
            'welcome': {
                'name': 'ウェルカム',
                'default_days': [0],
                'template': '🎉 ご登録ありがとうございます！\n\n📅 トライアル開始日: {start_date}\n📅 トライアル終了日: {trial_end_date}\n\n📱 サービスをご利用いただき、何かご質問がございましたら、お気軽にお声かけください。'
            },
            'usage_reminder': {
                'name': '利用状況',
                'default_days': [30, 15, 7],
                'template': '📊 利用状況のお知らせ\n\n📅 期間: {period_start} 〜 {period_end}\n📈 利用回数: {usage_count}回\n💰 請求金額: ¥{amount:,}\n\n📱 利用状況の詳細は、お気軽にお声かけください。'
            }
        }
    
    def create_reminder_schedule(self, company_id, reminder_type, custom_days=None, custom_message=None):
        """リマインダースケジュールを作成"""
        try:
            if reminder_type not in self.reminder_types:
                return {
                    'success': False,
                    'error': f'不明なリマインダータイプ: {reminder_type}'
                }
            
            # デフォルト日数またはカスタム日数を使用
            days = custom_days or self.reminder_types[reminder_type]['default_days']
            
            # 企業情報を取得
            company = self.company_service.get_company(company_id)
            if not company['success']:
                return {
                    'success': False,
                    'error': f'企業が見つかりません: {company_id}'
                }
            
            company_data = company['company']
            
            # リマインダー情報を準備
            reminder_data = {
                'company_id': company_id,
                'company_name': company_data['name'],
                'reminder_type': reminder_type,
                'reminder_name': self.reminder_types[reminder_type]['name'],
                'days_before': days,
                'custom_message': custom_message,
                'status': 'scheduled',
                'created_at': datetime.now().isoformat()
            }
            
            # データベースに保存
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO company_reminders 
                (company_id, reminder_type, reminder_name, days_before, custom_message, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                company_id,
                reminder_type,
                reminder_data['reminder_name'],
                json.dumps(days),
                custom_message,
                'scheduled',
                reminder_data['created_at']
            ))
            
            reminder_id = c.fetchone()[0]
            conn.commit()
            conn.close()
            
            reminder_data['id'] = reminder_id
            
            self.logger.info(f"リマインダースケジュール作成: company_id={company_id}, type={reminder_type}")
            
            return {
                'success': True,
                'reminder': reminder_data
            }
            
        except Exception as e:
            self.logger.error(f"リマインダースケジュール作成エラー: {e}")
            return {
                'success': False,
                'error': f'リマインダースケジュール作成エラー: {str(e)}'
            }
    
    def get_reminder_schedules(self, company_id=None, reminder_type=None, status=None):
        """リマインダースケジュール一覧を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            query = '''
                SELECT id, company_id, reminder_type, reminder_name, days_before, 
                       custom_message, status, created_at, last_sent_at, next_send_at
                FROM company_reminders
                WHERE 1=1
            '''
            params = []
            
            if company_id:
                query += ' AND company_id = %s'
                params.append(company_id)
            
            if reminder_type:
                query += ' AND reminder_type = %s'
                params.append(reminder_type)
            
            if status:
                query += ' AND status = %s'
                params.append(status)
            
            query += ' ORDER BY created_at DESC'
            
            c.execute(query, params)
            rows = c.fetchall()
            conn.close()
            
            reminders = []
            for row in rows:
                reminders.append({
                    'id': row[0],
                    'company_id': row[1],
                    'reminder_type': row[2],
                    'reminder_name': row[3],
                    'days_before': json.loads(row[4]) if row[4] else [],
                    'custom_message': row[5],
                    'status': row[6],
                    'created_at': row[7],
                    'last_sent_at': row[8],
                    'next_send_at': row[9]
                })
            
            return {
                'success': True,
                'reminders': reminders
            }
            
        except Exception as e:
            self.logger.error(f"リマインダースケジュール取得エラー: {e}")
            return {
                'success': False,
                'error': f'リマインダースケジュール取得エラー: {str(e)}'
            }
    
    def update_reminder_schedule(self, reminder_id, **updates):
        """リマインダースケジュールを更新"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 更新可能なフィールド
            allowed_fields = ['days_before', 'custom_message', 'status', 'next_send_at']
            update_fields = []
            params = []
            
            for field, value in updates.items():
                if field in allowed_fields:
                    if field == 'days_before':
                        update_fields.append(f"{field} = %s")
                        params.append(json.dumps(value))
                    else:
                        update_fields.append(f"{field} = %s")
                        params.append(value)
            
            if not update_fields:
                return {
                    'success': False,
                    'error': '更新するフィールドが指定されていません'
                }
            
            params.append(reminder_id)
            query = f'''
                UPDATE company_reminders 
                SET {', '.join(update_fields)}, updated_at = %s
                WHERE id = %s
            '''
            params.append(datetime.now().isoformat())
            
            c.execute(query, params)
            conn.commit()
            conn.close()
            
            self.logger.info(f"リマインダースケジュール更新: reminder_id={reminder_id}")
            
            return {
                'success': True,
                'message': 'リマインダースケジュールを更新しました'
            }
            
        except Exception as e:
            self.logger.error(f"リマインダースケジュール更新エラー: {e}")
            return {
                'success': False,
                'error': f'リマインダースケジュール更新エラー: {str(e)}'
            }
    
    def delete_reminder_schedule(self, reminder_id):
        """リマインダースケジュールを削除"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('DELETE FROM company_reminders WHERE id = %s', (reminder_id,))
            conn.commit()
            conn.close()
            
            self.logger.info(f"リマインダースケジュール削除: reminder_id={reminder_id}")
            
            return {
                'success': True,
                'message': 'リマインダースケジュールを削除しました'
            }
            
        except Exception as e:
            self.logger.error(f"リマインダースケジュール削除エラー: {e}")
            return {
                'success': False,
                'error': f'リマインダースケジュール削除エラー: {str(e)}'
            }
    
    def send_reminder(self, reminder_id):
        """リマインダーを送信"""
        try:
            # リマインダー情報を取得
            schedules = self.get_reminder_schedules()
            if not schedules['success']:
                return schedules
            
            reminder = None
            for r in schedules['reminders']:
                if r['id'] == reminder_id:
                    reminder = r
                    break
            
            if not reminder:
                return {
                    'success': False,
                    'error': f'リマインダーが見つかりません: {reminder_id}'
                }
            
            # 企業情報を取得
            company = self.company_service.get_company(reminder['company_id'])
            if not company['success']:
                return {
                    'success': False,
                    'error': f'企業が見つかりません: {reminder["company_id"]}'
                }
            
            company_data = company['company']
            
            # メッセージテンプレートを取得
            template = self.reminder_types[reminder['reminder_type']]['template']
            if reminder['custom_message']:
                template = reminder['custom_message']
            
            # メッセージを生成
            message = self._generate_reminder_message(
                template, 
                reminder['reminder_type'], 
                company_data
            )
            
            # LINE通知を送信
            notification_result = notification_service.send_payment_notification(
                reminder['company_id'],
                'reminder',
                {
                    'message': message,
                    'reminder_type': reminder['reminder_type'],
                    'reminder_name': reminder['reminder_name']
                }
            )
            
            if notification_result['success']:
                # 送信履歴を更新
                self._update_reminder_sent_history(reminder_id)
                
                self.logger.info(f"リマインダー送信成功: reminder_id={reminder_id}")
                
                return {
                    'success': True,
                    'message': 'リマインダーを送信しました',
                    'sent_at': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': f'リマインダー送信失敗: {notification_result.get("error", "不明なエラー")}'
                }
            
        except Exception as e:
            self.logger.error(f"リマインダー送信エラー: {e}")
            return {
                'success': False,
                'error': f'リマインダー送信エラー: {str(e)}'
            }
    
    def _generate_reminder_message(self, template, reminder_type, company_data):
        """リマインダーメッセージを生成"""
        try:
            # 基本情報
            message_data = {
                'company_name': company_data['name'],
                'amount': 3900,  # デフォルト金額
                'currency': 'jpy'
            }
            
            # リマインダータイプ別の情報を追加
            if reminder_type == 'trial_ending':
                # トライアル終了日を計算（例：7日後）
                trial_end = datetime.now() + timedelta(days=7)
                message_data.update({
                    'trial_end_date': trial_end.strftime('%Y年%m月%d日'),
                    'amount': 3900
                })
            
            elif reminder_type == 'payment_due':
                # 支払い期限を計算（例：7日後）
                due_date = datetime.now() + timedelta(days=7)
                message_data.update({
                    'due_date': due_date.strftime('%Y年%m月%d日'),
                    'amount': 3900
                })
            
            elif reminder_type == 'subscription_renewal':
                # 更新日を計算（例：7日後）
                renewal_date = datetime.now() + timedelta(days=7)
                message_data.update({
                    'renewal_date': renewal_date.strftime('%Y年%m月%d日'),
                    'amount': 3900
                })
            
            elif reminder_type == 'payment_failed':
                # 再試行日を計算（例：3日後）
                retry_date = datetime.now() + timedelta(days=3)
                message_data.update({
                    'retry_date': retry_date.strftime('%Y年%m月%d日'),
                    'amount': 3900
                })
            
            elif reminder_type == 'cancellation_reminder':
                # 解約予定日を計算（例：7日後）
                cancellation_date = datetime.now() + timedelta(days=7)
                message_data.update({
                    'cancellation_date': cancellation_date.strftime('%Y年%m月%d日'),
                    'reason': 'ユーザーリクエスト',
                    'deletion_days': 30
                })
            
            elif reminder_type == 'data_deletion':
                # 削除予定日を計算（例：7日後）
                deletion_date = datetime.now() + timedelta(days=7)
                message_data.update({
                    'deletion_date': deletion_date.strftime('%Y年%m月%d日')
                })
            
            elif reminder_type == 'welcome':
                # ウェルカムメッセージ用の情報
                start_date = datetime.now().strftime('%Y年%m月%d日')
                trial_end = datetime.now() + timedelta(days=7)
                message_data.update({
                    'start_date': start_date,
                    'trial_end_date': trial_end.strftime('%Y年%m月%d日')
                })
            
            elif reminder_type == 'usage_reminder':
                # 利用状況メッセージ用の情報
                period_start = (datetime.now() - timedelta(days=30)).strftime('%Y年%m月%d日')
                period_end = datetime.now().strftime('%Y年%m月%d日')
                message_data.update({
                    'period_start': period_start,
                    'period_end': period_end,
                    'usage_count': 15,  # 仮の利用回数
                    'amount': 3900
                })
            
            # テンプレートを置換
            message = template
            for key, value in message_data.items():
                placeholder = f'{{{key}}}'
                if placeholder in message:
                    if isinstance(value, (int, float)):
                        message = message.replace(placeholder, f'{value:,}')
                    else:
                        message = message.replace(placeholder, str(value))
            
            return message
            
        except Exception as e:
            self.logger.error(f"リマインダーメッセージ生成エラー: {e}")
            return "リマインダーメッセージの生成に失敗しました。"
    
    def _update_reminder_sent_history(self, reminder_id):
        """リマインダー送信履歴を更新"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            now = datetime.now().isoformat()
            
            c.execute('''
                UPDATE company_reminders 
                SET last_sent_at = %s, updated_at = %s
                WHERE id = %s
            ''', (now, now, reminder_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"リマインダー送信履歴更新エラー: {e}")
    
    def get_reminder_statistics(self, company_id=None):
        """リマインダー統計を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            query = '''
                SELECT 
                    reminder_type,
                    COUNT(*) as total_count,
                    COUNT(CASE WHEN status = 'scheduled' THEN 1 END) as scheduled_count,
                    COUNT(CASE WHEN status = 'sent' THEN 1 END) as sent_count,
                    COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_count
                FROM company_reminders
            '''
            params = []
            
            if company_id:
                query += ' WHERE company_id = %s'
                params.append(company_id)
            
            query += ' GROUP BY reminder_type ORDER BY total_count DESC'
            
            c.execute(query, params)
            rows = c.fetchall()
            conn.close()
            
            statistics = []
            for row in rows:
                statistics.append({
                    'reminder_type': row[0],
                    'total_count': row[1],
                    'scheduled_count': row[2],
                    'sent_count': row[3],
                    'cancelled_count': row[4]
                })
            
            return {
                'success': True,
                'statistics': statistics
            }
            
        except Exception as e:
            self.logger.error(f"リマインダー統計取得エラー: {e}")
            return {
                'success': False,
                'error': f'リマインダー統計取得エラー: {str(e)}'
            }
    
    def get_reminder_types(self):
        """リマインダータイプ一覧を取得"""
        return {
            'success': True,
            'reminder_types': self.reminder_types
        }

# インスタンスを作成
reminder_service = ReminderService() 