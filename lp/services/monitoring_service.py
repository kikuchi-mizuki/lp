import os
import json
import logging
from datetime import datetime, timedelta
from utils.db import get_db_connection
from services.dashboard_service import dashboard_service

# psutilの条件付きインポート
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil is not available. System monitoring features will be limited.")

class MonitoringService:
    """システム監視サービス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.monitoring_dir = "monitoring"
        
        # 監視ディレクトリを作成
        if not os.path.exists(self.monitoring_dir):
            os.makedirs(self.monitoring_dir)
        
        # ログファイルの設定
        self.setup_logging()
    
    def setup_logging(self):
        """ログ設定"""
        log_file = os.path.join(self.monitoring_dir, 'system_monitoring.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def get_system_health(self):
        """システム全体の健全性を取得"""
        try:
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'healthy',
                'checks': {}
            }
            
            # データベース接続チェック
            db_health = self.check_database_health()
            health_status['checks']['database'] = db_health
            
            # システムリソースチェック
            resource_health = self.check_system_resources()
            health_status['checks']['system_resources'] = resource_health
            
            # アプリケーションサービスチェック
            app_health = self.check_application_services()
            health_status['checks']['application_services'] = app_health
            
            # 外部サービスチェック
            external_health = self.check_external_services()
            health_status['checks']['external_services'] = external_health
            
            # 全体的なステータスを決定
            failed_checks = sum(1 for check in health_status['checks'].values() 
                              if check.get('status') == 'error')
            
            if failed_checks > 0:
                health_status['overall_status'] = 'degraded' if failed_checks < 2 else 'error'
            
            return {
                'success': True,
                'health_status': health_status
            }
            
        except Exception as e:
            self.logger.error(f"システム健全性チェックエラー: {e}")
            return {
                'success': False,
                'error': f'システム健全性チェックエラー: {str(e)}'
            }
    
    def check_database_health(self):
        """データベース健全性チェック"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 接続テスト
            c.execute('SELECT 1')
            connection_test = c.fetchone()[0] == 1
            
            # テーブル存在チェック
            c.execute('''
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            ''')
            tables = [row[0] for row in c.fetchall()]
            required_tables = [
                'companies', 'company_payments', 'company_contents',
                'company_notifications', 'company_cancellations',
                'subscription_periods', 'usage_logs'
            ]
            missing_tables = [table for table in required_tables if table not in tables]
            
            # データベースサイズチェック
            c.execute('''
                SELECT pg_size_pretty(pg_database_size(current_database()))
            ''')
            db_size = c.fetchone()[0]
            
            # 接続数チェック
            c.execute('SELECT count(*) FROM pg_stat_activity')
            active_connections = c.fetchone()[0]
            
            conn.close()
            
            status = 'healthy'
            if not connection_test or missing_tables:
                status = 'error'
            elif active_connections > 50:  # 接続数が多すぎる場合
                status = 'warning'
            
            return {
                'status': status,
                'connection_test': connection_test,
                'missing_tables': missing_tables,
                'database_size': db_size,
                'active_connections': active_connections,
                'total_tables': len(tables)
            }
            
        except Exception as e:
            self.logger.error(f"データベース健全性チェックエラー: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_system_resources(self):
        """システムリソースチェック"""
        if not PSUTIL_AVAILABLE:
            return {
                'status': 'warning',
                'message': 'psutil not available - system monitoring limited'
            }
        
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # メモリ使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # ディスク使用率
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # ネットワークI/O
            network = psutil.net_io_counters()
            
            # ステータス判定
            status = 'healthy'
            if cpu_percent > 80 or memory_percent > 80 or disk_percent > 90:
                status = 'warning'
            if cpu_percent > 95 or memory_percent > 95 or disk_percent > 95:
                status = 'error'
            
            return {
                'status': status,
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_available': memory.available,
                'memory_total': memory.total,
                'disk_percent': disk_percent,
                'disk_free': disk.free,
                'disk_total': disk.total,
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv
            }
            
        except Exception as e:
            self.logger.error(f"システムリソースチェックエラー: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_application_services(self):
        """アプリケーションサービスチェック"""
        if not PSUTIL_AVAILABLE:
            return {
                'status': 'warning',
                'message': 'psutil not available - process monitoring limited'
            }
        
        try:
            services_status = {}
            
            # Flaskアプリケーションのプロセスチェック
            flask_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'python' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if 'app.py' in cmdline or 'flask' in cmdline:
                            flask_processes.append({
                                'pid': proc.info['pid'],
                                'memory_percent': proc.memory_percent(),
                                'cpu_percent': proc.cpu_percent()
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            services_status['flask_app'] = {
                'status': 'healthy' if flask_processes else 'error',
                'process_count': len(flask_processes),
                'processes': flask_processes
            }
            
            # ポート使用状況チェック
            port_5000_in_use = False
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('127.0.0.1', 5000))
                port_5000_in_use = result == 0
                sock.close()
            except:
                pass
            
            services_status['port_5000'] = {
                'status': 'healthy' if port_5000_in_use else 'error',
                'in_use': port_5000_in_use
            }
            
            # 全体的なステータス
            overall_status = 'healthy'
            if not flask_processes or not port_5000_in_use:
                overall_status = 'error'
            
            return {
                'status': overall_status,
                'services': services_status
            }
            
        except Exception as e:
            self.logger.error(f"アプリケーションサービスチェックエラー: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_external_services(self):
        """外部サービスチェック"""
        try:
            external_services = {}
            
            # Stripe API接続チェック
            try:
                import stripe
                stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
                if stripe.api_key:
                    # Stripeアカウント情報を取得
                    account = stripe.Account.retrieve()
                    external_services['stripe'] = {
                        'status': 'healthy',
                        'account_id': account.id,
                        'charges_enabled': account.charges_enabled
                    }
                else:
                    external_services['stripe'] = {
                        'status': 'warning',
                        'error': 'STRIPE_SECRET_KEY not configured'
                    }
            except Exception as e:
                external_services['stripe'] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            # LINE API接続チェック
            try:
                line_channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
                if line_channel_access_token:
                    import requests
                    response = requests.get(
                        'https://api.line.me/v2/bot/profile/U1b9d0d75b0c770dc1107dde349d572f7',
                        headers={'Authorization': f'Bearer {line_channel_access_token}'},
                        timeout=5
                    )
                    external_services['line_api'] = {
                        'status': 'healthy' if response.status_code == 200 else 'error',
                        'response_code': response.status_code
                    }
                else:
                    external_services['line_api'] = {
                        'status': 'warning',
                        'error': 'LINE_CHANNEL_ACCESS_TOKEN not configured'
                    }
            except Exception as e:
                external_services['line_api'] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            # 全体的なステータス
            error_count = sum(1 for service in external_services.values() 
                            if service['status'] == 'error')
            warning_count = sum(1 for service in external_services.values() 
                              if service['status'] == 'warning')
            
            overall_status = 'healthy'
            if error_count > 0:
                overall_status = 'error'
            elif warning_count > 0:
                overall_status = 'warning'
            
            return {
                'status': overall_status,
                'services': external_services
            }
            
        except Exception as e:
            self.logger.error(f"外部サービスチェックエラー: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_performance_metrics(self):
        """パフォーマンスメトリクスを取得"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'system_metrics': {},
                'application_metrics': {},
                'database_metrics': {}
            }
            
            # システムメトリクス
            metrics['system_metrics'] = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
            
            # アプリケーションメトリクス
            flask_processes = []
            total_memory = 0
            total_cpu = 0
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'python' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if 'app.py' in cmdline or 'flask' in cmdline:
                            memory_percent = proc.memory_percent()
                            cpu_percent = proc.cpu_percent()
                            total_memory += memory_percent
                            total_cpu += cpu_percent
                            
                            flask_processes.append({
                                'pid': proc.info['pid'],
                                'memory_percent': memory_percent,
                                'cpu_percent': cpu_percent
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            metrics['application_metrics'] = {
                'flask_processes': flask_processes,
                'total_memory_percent': total_memory,
                'total_cpu_percent': total_cpu,
                'process_count': len(flask_processes)
            }
            
            # データベースメトリクス
            try:
                conn = get_db_connection()
                c = conn.cursor()
                
                # テーブルサイズ
                c.execute('''
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                ''')
                
                table_sizes = []
                for row in c.fetchall():
                    table_sizes.append({
                        'table': row[1],
                        'size': row[2]
                    })
                
                # 接続数
                c.execute('SELECT count(*) FROM pg_stat_activity')
                active_connections = c.fetchone()[0]
                
                # データベースサイズ
                c.execute('SELECT pg_size_pretty(pg_database_size(current_database()))')
                db_size = c.fetchone()[0]
                
                conn.close()
                
                metrics['database_metrics'] = {
                    'table_sizes': table_sizes,
                    'active_connections': active_connections,
                    'database_size': db_size
                }
                
            except Exception as e:
                metrics['database_metrics'] = {
                    'error': str(e)
                }
            
            return {
                'success': True,
                'metrics': metrics
            }
            
        except Exception as e:
            self.logger.error(f"パフォーマンスメトリクス取得エラー: {e}")
            return {
                'success': False,
                'error': f'パフォーマンスメトリクス取得エラー: {str(e)}'
            }
    
    def get_error_logs(self, hours=24, level='ERROR'):
        """エラーログを取得"""
        try:
            log_file = os.path.join(self.monitoring_dir, 'system_monitoring.log')
            
            if not os.path.exists(log_file):
                return {
                    'success': True,
                    'logs': [],
                    'message': 'ログファイルが存在しません'
                }
            
            # 指定時間前のタイムスタンプ
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            logs = []
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        # ログ行を解析
                        if level in line:
                            # タイムスタンプを抽出
                            timestamp_str = line.split(' - ')[0]
                            log_time = datetime.fromisoformat(timestamp_str.replace(' ', 'T'))
                            
                            if log_time >= cutoff_time:
                                logs.append({
                                    'timestamp': log_time.isoformat(),
                                    'level': level,
                                    'message': line.strip()
                                })
                    except:
                        continue
            
            # 最新のログから順に並べ替え
            logs.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return {
                'success': True,
                'logs': logs[:100],  # 最新100件まで
                'total_count': len(logs)
            }
            
        except Exception as e:
            self.logger.error(f"エラーログ取得エラー: {e}")
            return {
                'success': False,
                'error': f'エラーログ取得エラー: {str(e)}'
            }
    
    def create_alert(self, alert_type, message, severity='info'):
        """アラートを作成"""
        try:
            alert = {
                'id': f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'type': alert_type,
                'message': message,
                'severity': severity,
                'timestamp': datetime.now().isoformat(),
                'resolved': False
            }
            
            # アラートをファイルに保存
            alert_file = os.path.join(self.monitoring_dir, 'alerts.json')
            
            alerts = []
            if os.path.exists(alert_file):
                with open(alert_file, 'r', encoding='utf-8') as f:
                    alerts = json.load(f)
            
            alerts.append(alert)
            
            # 古いアラートを削除（100件まで保持）
            if len(alerts) > 100:
                alerts = alerts[-100:]
            
            with open(alert_file, 'w', encoding='utf-8') as f:
                json.dump(alerts, f, ensure_ascii=False, indent=2)
            
            # ログに記録
            self.logger.warning(f"アラート作成: {alert_type} - {message}")
            
            return {
                'success': True,
                'alert': alert
            }
            
        except Exception as e:
            self.logger.error(f"アラート作成エラー: {e}")
            return {
                'success': False,
                'error': f'アラート作成エラー: {str(e)}'
            }
    
    def get_alerts(self, resolved=None):
        """アラート一覧を取得"""
        try:
            alert_file = os.path.join(self.monitoring_dir, 'alerts.json')
            
            if not os.path.exists(alert_file):
                return {
                    'success': True,
                    'alerts': []
                }
            
            with open(alert_file, 'r', encoding='utf-8') as f:
                alerts = json.load(f)
            
            # 解決済みフィルタリング
            if resolved is not None:
                alerts = [alert for alert in alerts if alert['resolved'] == resolved]
            
            # 最新のアラートから順に並べ替え
            alerts.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return {
                'success': True,
                'alerts': alerts
            }
            
        except Exception as e:
            self.logger.error(f"アラート取得エラー: {e}")
            return {
                'success': False,
                'error': f'アラート取得エラー: {str(e)}'
            }
    
    def resolve_alert(self, alert_id):
        """アラートを解決済みにする"""
        try:
            alert_file = os.path.join(self.monitoring_dir, 'alerts.json')
            
            if not os.path.exists(alert_file):
                return {
                    'success': False,
                    'error': 'アラートファイルが存在しません'
                }
            
            with open(alert_file, 'r', encoding='utf-8') as f:
                alerts = json.load(f)
            
            # 指定されたアラートを検索
            for alert in alerts:
                if alert['id'] == alert_id:
                    alert['resolved'] = True
                    alert['resolved_at'] = datetime.now().isoformat()
                    break
            else:
                return {
                    'success': False,
                    'error': '指定されたアラートが見つかりません'
                }
            
            with open(alert_file, 'w', encoding='utf-8') as f:
                json.dump(alerts, f, ensure_ascii=False, indent=2)
            
            return {
                'success': True,
                'message': f'アラート {alert_id} を解決済みにしました'
            }
            
        except Exception as e:
            self.logger.error(f"アラート解決エラー: {e}")
            return {
                'success': False,
                'error': f'アラート解決エラー: {str(e)}'
            }

    def check_line_api_errors(self):
        """LINE APIエラーの監視"""
        try:
            # error.logからLINE API関連のエラーを確認
            error_log_path = os.path.join(os.path.dirname(__file__), '..', 'error.log')
            
            if not os.path.exists(error_log_path):
                return {
                    'success': True,
                    'line_errors': [],
                    'message': 'エラーログファイルが存在しません'
                }
            
            # 過去1時間のLINE APIエラーを確認
            cutoff_time = datetime.now() - timedelta(hours=1)
            line_errors = []
            
            with open(error_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'LINE' in line and ('ERROR' in line or 'エラー' in line):
                        try:
                            # タイムスタンプを抽出
                            if ' - ' in line:
                                timestamp_str = line.split(' - ')[0]
                                log_time = datetime.fromisoformat(timestamp_str.replace(' ', 'T'))
                                
                                if log_time >= cutoff_time:
                                    line_errors.append({
                                        'timestamp': log_time.isoformat(),
                                        'message': line.strip()
                                    })
                        except:
                            continue
            
            # 最新のエラーから順に並べ替え
            line_errors.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return {
                'success': True,
                'line_errors': line_errors[:50],  # 最新50件まで
                'total_count': len(line_errors)
            }
            
        except Exception as e:
            self.logger.error(f"LINE APIエラー監視エラー: {e}")
            return {
                'success': False,
                'error': f'LINE APIエラー監視エラー: {str(e)}'
            }
    
    def check_stripe_errors(self):
        """Stripeエラーの監視"""
        try:
            # error.logからStripe関連のエラーを確認
            error_log_path = os.path.join(os.path.dirname(__file__), '..', 'error.log')
            
            if not os.path.exists(error_log_path):
                return {
                    'success': True,
                    'stripe_errors': [],
                    'message': 'エラーログファイルが存在しません'
                }
            
            # 過去1時間のStripeエラーを確認
            cutoff_time = datetime.now() - timedelta(hours=1)
            stripe_errors = []
            
            with open(error_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'Stripe' in line and ('ERROR' in line or 'エラー' in line):
                        try:
                            # タイムスタンプを抽出
                            if ' - ' in line:
                                timestamp_str = line.split(' - ')[0]
                                log_time = datetime.fromisoformat(timestamp_str.replace(' ', 'T'))
                                
                                if log_time >= cutoff_time:
                                    stripe_errors.append({
                                        'timestamp': log_time.isoformat(),
                                        'message': line.strip()
                                    })
                        except:
                            continue
            
            # 最新のエラーから順に並べ替え
            stripe_errors.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return {
                'success': True,
                'stripe_errors': stripe_errors[:50],  # 最新50件まで
                'total_count': len(stripe_errors)
            }
            
        except Exception as e:
            self.logger.error(f"Stripeエラー監視エラー: {e}")
            return {
                'success': False,
                'error': f'Stripeエラー監視エラー: {str(e)}'
            }

# インスタンスを作成
monitoring_service = MonitoringService() 