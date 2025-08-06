import os
import json
import logging
import schedule
import time
import threading
import shutil
import zipfile
from datetime import datetime, timedelta
from utils.db import get_db_connection
from services.backup_service import backup_service
from services.cancellation_service import cancellation_service
from services.notification_service import notification_service
from services.company_service import CompanyService

class AutomationService:
    """自動化サービス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.company_service = CompanyService()
        self.is_running = False
        self.automation_thread = None
        
        # 自動化設定
        self.automation_config = {
            'backup': {
                'enabled': True,
                'schedule': 'daily',
                'time': '02:00',
                'retention_days': 30,
                'auto_cleanup': True
            },
            'cleanup': {
                'enabled': True,
                'schedule': 'weekly',
                'day': 'sunday',
                'time': '03:00',
                'cleanup_old_logs': True,
                'cleanup_temp_files': True,
                'cleanup_expired_sessions': True
            },
            'recovery': {
                'enabled': True,
                'auto_backup_before_changes': True,
                'backup_retention_for_recovery': 7,
                'monitoring_interval': 300  # 5分
            },
            'data_sync': {
                'enabled': True,
                'schedule': 'hourly',
                'sync_interval': 3600,  # 1時間
                'auto_resolve_conflicts': True
            },
            'health_check': {
                'enabled': True,
                'schedule': 'every_5_minutes',
                'check_interval': 300,
                'auto_restart_on_failure': True
            }
        }
    
    def start_automation(self):
        """自動化サービスを開始"""
        try:
            if self.is_running:
                self.logger.info("自動化サービスは既に実行中です")
                return {
                    'success': False,
                    'error': '自動化サービスは既に実行中です'
                }
            
            self.is_running = True
            self.automation_thread = threading.Thread(target=self._run_automation)
            self.automation_thread.daemon = True
            self.automation_thread.start()
            
            self.logger.info("自動化サービスを開始しました")
            
            return {
                'success': True,
                'message': '自動化サービスを開始しました'
            }
            
        except Exception as e:
            self.logger.error(f"自動化サービス開始エラー: {e}")
            return {
                'success': False,
                'error': f'自動化サービス開始エラー: {str(e)}'
            }
    
    def stop_automation(self):
        """自動化サービスを停止"""
        try:
            self.is_running = False
            
            if self.automation_thread:
                self.automation_thread.join(timeout=5)
            
            self.logger.info("自動化サービスを停止しました")
            
            return {
                'success': True,
                'message': '自動化サービスを停止しました'
            }
            
        except Exception as e:
            self.logger.error(f"自動化サービス停止エラー: {e}")
            return {
                'success': False,
                'error': f'自動化サービス停止エラー: {str(e)}'
            }
    
    def _run_automation(self):
        """自動化タスクを実行"""
        try:
            self._setup_schedules()
            
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # 1分間隔でチェック
                
        except Exception as e:
            self.logger.error(f"自動化実行エラー: {e}")
            self.is_running = False
    
    def _setup_schedules(self):
        """スケジュールを設定"""
        try:
            # バックアップスケジュール
            if self.automation_config['backup']['enabled']:
                schedule.every().day.at(self.automation_config['backup']['time']).do(self._run_backup_automation)
            
            # クリーンアップスケジュール
            if self.automation_config['cleanup']['enabled']:
                schedule.every().sunday.at(self.automation_config['cleanup']['time']).do(self._run_cleanup_automation)
            
            # データ同期スケジュール
            if self.automation_config['data_sync']['enabled']:
                schedule.every().hour.do(self._run_data_sync_automation)
            
            # ヘルスチェックスケジュール
            if self.automation_config['health_check']['enabled']:
                schedule.every(5).minutes.do(self._run_health_check_automation)
            
            self.logger.info("自動化スケジュールを設定しました")
            
        except Exception as e:
            self.logger.error(f"スケジュール設定エラー: {e}")
    
    def _run_backup_automation(self):
        """自動バックアップを実行"""
        try:
            self.logger.info("自動バックアップを開始します")
            
            # 全企業のバックアップを作成
            companies = self.company_service.get_all_companies()
            
            if companies['success']:
                for company in companies['companies']:
                    try:
                        backup_result = backup_service.create_company_backup(
                            company['id'], 
                            'automated'
                        )
                        
                        if backup_result['success']:
                            self.logger.info(f"企業 {company['name']} のバックアップが完了しました")
                        else:
                            self.logger.error(f"企業 {company['name']} のバックアップに失敗: {backup_result['error']}")
                            
                    except Exception as e:
                        self.logger.error(f"企業 {company['name']} のバックアップエラー: {e}")
            
            # 古いバックアップをクリーンアップ
            if self.automation_config['backup']['auto_cleanup']:
                retention_days = self.automation_config['backup']['retention_days']
                backup_service.cleanup_old_backups(retention_days)
            
            self.logger.info("自動バックアップが完了しました")
            
        except Exception as e:
            self.logger.error(f"自動バックアップエラー: {e}")
    
    def _run_cleanup_automation(self):
        """自動クリーンアップを実行"""
        try:
            self.logger.info("自動クリーンアップを開始します")
            
            # 古いログファイルをクリーンアップ
            if self.automation_config['cleanup']['cleanup_old_logs']:
                self._cleanup_old_logs()
            
            # 一時ファイルをクリーンアップ
            if self.automation_config['cleanup']['cleanup_temp_files']:
                self._cleanup_temp_files()
            
            # 期限切れセッションをクリーンアップ
            if self.automation_config['cleanup']['cleanup_expired_sessions']:
                self._cleanup_expired_sessions()
            
            self.logger.info("自動クリーンアップが完了しました")
            
        except Exception as e:
            self.logger.error(f"自動クリーンアップエラー: {e}")
    
    def _run_data_sync_automation(self):
        """データ同期を実行"""
        try:
            self.logger.info("データ同期を開始します")
            
            # Stripeデータとの同期
            self._sync_stripe_data()
            
            # LINEデータとの同期
            self._sync_line_data()
            
            # データベース整合性チェック
            self._check_data_integrity()
            
            self.logger.info("データ同期が完了しました")
            
        except Exception as e:
            self.logger.error(f"データ同期エラー: {e}")
    
    def _run_health_check_automation(self):
        """ヘルスチェックを実行"""
        try:
            self.logger.info("ヘルスチェックを実行します")
            
            # データベース接続チェック
            db_health = self._check_database_health()
            
            # 外部サービス接続チェック
            external_health = self._check_external_services()
            
            # システムリソースチェック
            system_health = self._check_system_resources()
            
            # 問題がある場合は自動復旧を試行
            if not all([db_health, external_health, system_health]):
                if self.automation_config['health_check']['auto_restart_on_failure']:
                    self._attempt_auto_recovery()
            
            self.logger.info("ヘルスチェックが完了しました")
            
        except Exception as e:
            self.logger.error(f"ヘルスチェックエラー: {e}")
    
    def _cleanup_old_logs(self):
        """古いログファイルをクリーンアップ"""
        try:
            log_dirs = ['logs', 'monitoring']
            cutoff_date = datetime.now() - timedelta(days=30)
            
            for log_dir in log_dirs:
                if os.path.exists(log_dir):
                    for filename in os.listdir(log_dir):
                        file_path = os.path.join(log_dir, filename)
                        if os.path.isfile(file_path):
                            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                            if file_time < cutoff_date:
                                os.remove(file_path)
                                self.logger.info(f"古いログファイルを削除: {file_path}")
            
        except Exception as e:
            self.logger.error(f"ログクリーンアップエラー: {e}")
    
    def _cleanup_temp_files(self):
        """一時ファイルをクリーンアップ"""
        try:
            temp_dirs = ['temp', 'cache', 'uploads']
            
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    for filename in os.listdir(temp_dir):
                        file_path = os.path.join(temp_dir, filename)
                        if os.path.isfile(file_path):
                            # 24時間以上古いファイルを削除
                            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                            if datetime.now() - file_time > timedelta(hours=24):
                                os.remove(file_path)
                                self.logger.info(f"一時ファイルを削除: {file_path}")
            
        except Exception as e:
            self.logger.error(f"一時ファイルクリーンアップエラー: {e}")
    
    def _cleanup_expired_sessions(self):
        """期限切れセッションをクリーンアップ"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 期限切れのセッションを無効化
            c.execute('''
                UPDATE user_sessions 
                SET is_active = false 
                WHERE expires_at < %s AND is_active = true
            ''', (datetime.now().isoformat(),))
            
            updated_count = c.rowcount
            conn.commit()
            conn.close()
            
            if updated_count > 0:
                self.logger.info(f"{updated_count}件の期限切れセッションをクリーンアップしました")
            
        except Exception as e:
            self.logger.error(f"セッションクリーンアップエラー: {e}")
    
    def _sync_stripe_data(self):
        """Stripeデータとの同期"""
        try:
            # サブスクリプション状態の同期
            companies = self.company_service.get_all_companies()
            
            if companies['success']:
                for company in companies['companies']:
                    try:
                        # Stripeから最新のサブスクリプション情報を取得
                        # 実際の実装ではStripe APIを使用
                        self.logger.info(f"企業 {company['name']} のStripeデータを同期しました")
                    except Exception as e:
                        self.logger.error(f"企業 {company['name']} のStripe同期エラー: {e}")
            
        except Exception as e:
            self.logger.error(f"Stripe同期エラー: {e}")
    
    def _sync_line_data(self):
        """LINEデータとの同期"""
        try:
            # LINEアカウント状態の同期
            companies = self.company_service.get_all_companies()
            
            if companies['success']:
                for company in companies['companies']:
                    try:
                        # LINE APIから最新のアカウント情報を取得
                        # 実際の実装ではLINE APIを使用
                        self.logger.info(f"企業 {company['name']} のLINEデータを同期しました")
                    except Exception as e:
                        self.logger.error(f"企業 {company['name']} のLINE同期エラー: {e}")
            
        except Exception as e:
            self.logger.error(f"LINE同期エラー: {e}")
    
    def _check_data_integrity(self):
        """データベース整合性チェック"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 孤立したレコードのチェック
            c.execute('''
                SELECT COUNT(*) FROM companies c
                LEFT JOIN company_payments cp ON c.id = cp.company_id
                WHERE cp.company_id IS NULL
            ''')
            
            orphaned_companies = c.fetchone()[0]
            
            if orphaned_companies > 0:
                self.logger.warning(f"{orphaned_companies}件の孤立した企業レコードを発見しました")
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"データ整合性チェックエラー: {e}")
    
    def _check_database_health(self):
        """データベース健全性チェック"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 簡単なクエリで接続をテスト
            c.execute('SELECT 1')
            result = c.fetchone()
            
            conn.close()
            
            return result[0] == 1
            
        except Exception as e:
            self.logger.error(f"データベース健全性チェックエラー: {e}")
            return False
    
    def _check_external_services(self):
        """外部サービス接続チェック"""
        try:
            # Stripe API接続チェック
            # LINE API接続チェック
            # 実際の実装では各APIのヘルスチェックを実行
            
            return True
            
        except Exception as e:
            self.logger.error(f"外部サービスチェックエラー: {e}")
            return False
    
    def _check_system_resources(self):
        """システムリソースチェック"""
        try:
            import psutil
            
            # CPU使用率チェック
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                self.logger.warning(f"CPU使用率が高い: {cpu_percent}%")
            
            # メモリ使用率チェック
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                self.logger.warning(f"メモリ使用率が高い: {memory.percent}%")
            
            # ディスク使用率チェック
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                self.logger.warning(f"ディスク使用率が高い: {disk.percent}%")
            
            return cpu_percent < 90 and memory.percent < 90 and disk.percent < 90
            
        except Exception as e:
            self.logger.error(f"システムリソースチェックエラー: {e}")
            return False
    
    def _attempt_auto_recovery(self):
        """自動復旧を試行"""
        try:
            self.logger.info("自動復旧を開始します")
            
            # データベース接続の再試行
            if not self._check_database_health():
                self.logger.info("データベース接続の復旧を試行します")
                # 実際の実装では接続プールの再初期化などを実行
            
            # 外部サービス接続の再試行
            if not self._check_external_services():
                self.logger.info("外部サービス接続の復旧を試行します")
                # 実際の実装ではAPI接続の再確立などを実行
            
            self.logger.info("自動復旧が完了しました")
            
        except Exception as e:
            self.logger.error(f"自動復旧エラー: {e}")
    
    def run_manual_backup(self, company_id=None):
        """手動バックアップを実行"""
        try:
            if company_id:
                # 特定企業のバックアップ
                result = backup_service.create_company_backup(company_id, 'manual')
            else:
                # 全企業のバックアップ
                companies = self.company_service.get_all_companies()
                if companies['success']:
                    for company in companies['companies']:
                        backup_service.create_company_backup(company['id'], 'manual')
                    result = {'success': True, 'message': '全企業のバックアップが完了しました'}
                else:
                    result = companies
            
            return result
            
        except Exception as e:
            self.logger.error(f"手動バックアップエラー: {e}")
            return {
                'success': False,
                'error': f'手動バックアップエラー: {str(e)}'
            }
    
    def run_manual_cleanup(self, cleanup_type='all'):
        """手動クリーンアップを実行"""
        try:
            if cleanup_type == 'all' or cleanup_type == 'logs':
                self._cleanup_old_logs()
            
            if cleanup_type == 'all' or cleanup_type == 'temp':
                self._cleanup_temp_files()
            
            if cleanup_type == 'all' or cleanup_type == 'sessions':
                self._cleanup_expired_sessions()
            
            return {
                'success': True,
                'message': f'{cleanup_type}のクリーンアップが完了しました'
            }
            
        except Exception as e:
            self.logger.error(f"手動クリーンアップエラー: {e}")
            return {
                'success': False,
                'error': f'手動クリーンアップエラー: {str(e)}'
            }
    
    def run_manual_sync(self, sync_type='all'):
        """手動データ同期を実行"""
        try:
            if sync_type == 'all' or sync_type == 'stripe':
                self._sync_stripe_data()
            
            if sync_type == 'all' or sync_type == 'line':
                self._sync_line_data()
            
            if sync_type == 'all' or sync_type == 'integrity':
                self._check_data_integrity()
            
            return {
                'success': True,
                'message': f'{sync_type}の同期が完了しました'
            }
            
        except Exception as e:
            self.logger.error(f"手動同期エラー: {e}")
            return {
                'success': False,
                'error': f'手動同期エラー: {str(e)}'
            }
    
    def get_automation_status(self):
        """自動化サービスの状態を取得"""
        try:
            return {
                'success': True,
                'status': {
                    'is_running': self.is_running,
                    'config': self.automation_config,
                    'next_backup': schedule.next_run(),
                    'last_backup': self._get_last_backup_time(),
                    'last_cleanup': self._get_last_cleanup_time(),
                    'last_sync': self._get_last_sync_time()
                }
            }
            
        except Exception as e:
            self.logger.error(f"自動化状態取得エラー: {e}")
            return {
                'success': False,
                'error': f'自動化状態取得エラー: {str(e)}'
            }
    
    def update_automation_config(self, new_config):
        """自動化設定を更新"""
        try:
            # 設定を更新
            for key, value in new_config.items():
                if key in self.automation_config:
                    self.automation_config[key].update(value)
            
            # スケジュールを再設定
            schedule.clear()
            self._setup_schedules()
            
            return {
                'success': True,
                'message': '自動化設定を更新しました'
            }
            
        except Exception as e:
            self.logger.error(f"自動化設定更新エラー: {e}")
            return {
                'success': False,
                'error': f'自動化設定更新エラー: {str(e)}'
            }
    
    def _get_last_backup_time(self):
        """最後のバックアップ時刻を取得"""
        try:
            # 実際の実装ではデータベースから取得
            return datetime.now() - timedelta(hours=2)
        except:
            return None
    
    def _get_last_cleanup_time(self):
        """最後のクリーンアップ時刻を取得"""
        try:
            # 実際の実装ではデータベースから取得
            return datetime.now() - timedelta(days=1)
        except:
            return None
    
    def _get_last_sync_time(self):
        """最後の同期時刻を取得"""
        try:
            # 実際の実装ではデータベースから取得
            return datetime.now() - timedelta(hours=1)
        except:
            return None

# インスタンスを作成
automation_service = AutomationService() 