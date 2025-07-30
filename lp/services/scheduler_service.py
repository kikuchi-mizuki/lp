import os
import json
import schedule
import time
import threading
from datetime import datetime, timedelta
from utils.db import get_db_connection
from services.cancellation_service import cancellation_service
from services.notification_service import notification_service
from services.company_service import CompanyService

class SchedulerService:
    """自動スケジューラーサービス"""
    
    def __init__(self):
        self.company_service = CompanyService()
        self.is_running = False
        self.scheduler_thread = None
        
        # スケジュール設定
        self.schedule_config = {
            'data_deletion_check': {
                'interval': 'daily',
                'time': '02:00',  # 毎日午前2時
                'enabled': True
            },
            'trial_ending_reminder': {
                'interval': 'daily',
                'time': '09:00',  # 毎日午前9時
                'enabled': True
            },
            'renewal_reminder': {
                'interval': 'daily',
                'time': '10:00',  # 毎日午前10時
                'enabled': True
            },
            'deletion_reminder': {
                'interval': 'daily',
                'time': '11:00',  # 毎日午前11時
                'enabled': True
            },
            'notification_cleanup': {
                'interval': 'weekly',
                'day': 'sunday',
                'time': '03:00',  # 毎週日曜日午前3時
                'enabled': True
            }
        }
    
    def start_scheduler(self):
        """スケジューラーを開始"""
        if self.is_running:
            print("⚠️ スケジューラーは既に実行中です")
            return False
        
        try:
            # スケジュールを設定
            self._setup_schedules()
            
            # スケジューラーを開始
            self.is_running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            print("✅ 自動スケジューラーを開始しました")
            return True
            
        except Exception as e:
            print(f"❌ スケジューラー開始エラー: {e}")
            return False
    
    def stop_scheduler(self):
        """スケジューラーを停止"""
        if not self.is_running:
            print("⚠️ スケジューラーは実行されていません")
            return False
        
        try:
            self.is_running = False
            schedule.clear()
            
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
            
            print("✅ 自動スケジューラーを停止しました")
            return True
            
        except Exception as e:
            print(f"❌ スケジューラー停止エラー: {e}")
            return False
    
    def _setup_schedules(self):
        """スケジュールを設定"""
        # データ削除チェック（毎日午前2時）
        if self.schedule_config['data_deletion_check']['enabled']:
            schedule.every().day.at(self.schedule_config['data_deletion_check']['time']).do(
                self._check_and_execute_deletions
            )
        
        # トライアル終了リマインダー（毎日午前9時）
        if self.schedule_config['trial_ending_reminder']['enabled']:
            schedule.every().day.at(self.schedule_config['trial_ending_reminder']['time']).do(
                self._send_trial_ending_reminders
            )
        
        # 契約更新リマインダー（毎日午前10時）
        if self.schedule_config['renewal_reminder']['enabled']:
            schedule.every().day.at(self.schedule_config['renewal_reminder']['time']).do(
                self._send_renewal_reminders
            )
        
        # データ削除リマインダー（毎日午前11時）
        if self.schedule_config['deletion_reminder']['enabled']:
            schedule.every().day.at(self.schedule_config['deletion_reminder']['time']).do(
                self._send_deletion_reminders
            )
        
        # 通知履歴クリーンアップ（毎週日曜日午前3時）
        if self.schedule_config['notification_cleanup']['enabled']:
            schedule.every().sunday.at(self.schedule_config['notification_cleanup']['time']).do(
                self._cleanup_old_notifications
            )
    
    def _run_scheduler(self):
        """スケジューラーを実行"""
        print("🔄 スケジューラーを実行中...")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 1分間隔でチェック
            except Exception as e:
                print(f"❌ スケジューラー実行エラー: {e}")
                time.sleep(60)
    
    def _check_and_execute_deletions(self):
        """削除予定の企業をチェックして削除を実行"""
        try:
            print("🔍 削除予定企業をチェック中...")
            
            # 削除予定の企業を取得
            pending_result = cancellation_service.get_pending_deletions()
            
            if not pending_result['success']:
                print(f"❌ 削除予定取得エラー: {pending_result['error']}")
                return
            
            pending_deletions = pending_result['pending_deletions']
            print(f"📋 削除予定企業: {len(pending_deletions)}件")
            
            for pending in pending_deletions:
                company_id = pending['company_id']
                company_name = pending['company_name']
                deletion_date = pending['scheduled_deletion_date']
                
                print(f"🗑️ 企業削除実行: {company_name} (ID: {company_id})")
                
                # 削除を実行
                deletion_result = cancellation_service.execute_data_deletion(company_id)
                
                if deletion_result['success']:
                    print(f"✅ 企業削除完了: {company_name}")
                    
                    # 削除完了通知を記録
                    self._log_deletion_execution(company_id, company_name, deletion_date)
                else:
                    print(f"❌ 企業削除失敗: {company_name} - {deletion_result['error']}")
            
            print("✅ 削除チェック完了")
            
        except Exception as e:
            print(f"❌ 削除チェックエラー: {e}")
    
    def _send_trial_ending_reminders(self):
        """トライアル終了リマインダーを送信"""
        try:
            print("⏰ トライアル終了リマインダーを送信中...")
            
            # アクティブな企業を取得
            companies_result = self.company_service.list_companies()
            
            if not companies_result['success']:
                print(f"❌ 企業一覧取得エラー: {companies_result['error']}")
                return
            
            sent_count = 0
            for company in companies_result['companies']:
                company_id = company['id']
                
                # トライアル終了リマインダーを送信
                reminder_result = notification_service.send_trial_ending_reminder(company_id)
                
                if reminder_result['success']:
                    sent_count += 1
                    print(f"✅ トライアルリマインダー送信: {company['company_name']}")
                elif 'トライアル終了まで' in reminder_result.get('message', ''):
                    # リマインダー送信時期ではない場合
                    pass
                else:
                    print(f"⚠️ トライアルリマインダー送信失敗: {company['company_name']} - {reminder_result.get('error', '')}")
            
            print(f"✅ トライアル終了リマインダー送信完了: {sent_count}件")
            
        except Exception as e:
            print(f"❌ トライアルリマインダーエラー: {e}")
    
    def _send_renewal_reminders(self):
        """契約更新リマインダーを送信"""
        try:
            print("🔄 契約更新リマインダーを送信中...")
            
            # アクティブな企業を取得
            companies_result = self.company_service.list_companies()
            
            if not companies_result['success']:
                print(f"❌ 企業一覧取得エラー: {companies_result['error']}")
                return
            
            sent_count = 0
            for company in companies_result['companies']:
                company_id = company['id']
                
                # 契約更新リマインダーを送信
                reminder_result = notification_service.send_renewal_reminder(company_id)
                
                if reminder_result['success']:
                    sent_count += 1
                    print(f"✅ 契約更新リマインダー送信: {company['company_name']}")
                elif '契約更新まで' in reminder_result.get('message', ''):
                    # リマインダー送信時期ではない場合
                    pass
                else:
                    print(f"⚠️ 契約更新リマインダー送信失敗: {company['company_name']} - {reminder_result.get('error', '')}")
            
            print(f"✅ 契約更新リマインダー送信完了: {sent_count}件")
            
        except Exception as e:
            print(f"❌ 契約更新リマインダーエラー: {e}")
    
    def _send_deletion_reminders(self):
        """データ削除リマインダーを送信"""
        try:
            print("🗑️ データ削除リマインダーを送信中...")
            
            # 削除予定の企業を取得
            pending_result = cancellation_service.get_pending_deletions()
            
            if not pending_result['success']:
                print(f"❌ 削除予定取得エラー: {pending_result['error']}")
                return
            
            sent_count = 0
            for pending in pending_result['pending_deletions']:
                company_id = pending['company_id']
                company_name = pending['company_name']
                
                # データ削除リマインダーを送信
                reminder_result = notification_service.send_deletion_reminder(company_id)
                
                if reminder_result['success']:
                    sent_count += 1
                    print(f"✅ データ削除リマインダー送信: {company_name}")
                elif 'データ削除まで' in reminder_result.get('message', ''):
                    # リマインダー送信時期ではない場合
                    pass
                else:
                    print(f"⚠️ データ削除リマインダー送信失敗: {company_name} - {reminder_result.get('error', '')}")
            
            print(f"✅ データ削除リマインダー送信完了: {sent_count}件")
            
        except Exception as e:
            print(f"❌ データ削除リマインダーエラー: {e}")
    
    def _cleanup_old_notifications(self):
        """古い通知履歴をクリーンアップ"""
        try:
            print("🧹 古い通知履歴をクリーンアップ中...")
            
            # 30日以上前の通知履歴を削除
            cleanup_date = datetime.now() - timedelta(days=30)
            
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                DELETE FROM company_notifications
                WHERE sent_at < %s
            ''', (cleanup_date,))
            
            deleted_count = c.rowcount
            conn.commit()
            conn.close()
            
            print(f"✅ 通知履歴クリーンアップ完了: {deleted_count}件削除")
            
        except Exception as e:
            print(f"❌ 通知履歴クリーンアップエラー: {e}")
    
    def _log_deletion_execution(self, company_id, company_name, deletion_date):
        """削除実行をログに記録"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO company_notifications (
                    company_id, notification_type, notification_data, sent_at
                ) VALUES (%s, %s, %s, %s)
            ''', (
                company_id,
                'data_deletion_executed',
                json.dumps({
                    'company_name': company_name,
                    'scheduled_deletion_date': deletion_date,
                    'executed_at': datetime.now().isoformat(),
                    'message': f'企業「{company_name}」のデータ削除が実行されました'
                }, ensure_ascii=False),
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"削除実行ログ記録エラー: {e}")
    
    def get_scheduler_status(self):
        """スケジューラーの状態を取得"""
        try:
            return {
                'success': True,
                'is_running': self.is_running,
                'schedule_config': self.schedule_config,
                'next_jobs': []
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'スケジューラー状態取得エラー: {str(e)}'
            }
    
    def update_schedule_config(self, new_config):
        """スケジュール設定を更新"""
        try:
            self.schedule_config.update(new_config)
            
            # スケジューラーが実行中の場合は再起動
            if self.is_running:
                self.stop_scheduler()
                time.sleep(2)
                self.start_scheduler()
            
            return {
                'success': True,
                'message': 'スケジュール設定を更新しました'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'スケジュール設定更新エラー: {str(e)}'
            }
    
    def run_manual_task(self, task_name):
        """手動でタスクを実行"""
        try:
            if task_name == 'data_deletion_check':
                self._check_and_execute_deletions()
            elif task_name == 'trial_ending_reminder':
                self._send_trial_ending_reminders()
            elif task_name == 'renewal_reminder':
                self._send_renewal_reminders()
            elif task_name == 'deletion_reminder':
                self._send_deletion_reminders()
            elif task_name == 'notification_cleanup':
                self._cleanup_old_notifications()
            else:
                return {
                    'success': False,
                    'error': f'不明なタスク: {task_name}'
                }
            
            return {
                'success': True,
                'message': f'タスク「{task_name}」を実行しました'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'タスク実行エラー: {str(e)}'
            }

# インスタンスを作成
scheduler_service = SchedulerService() 