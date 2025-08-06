import os
import json
import zipfile
import shutil
from datetime import datetime, timedelta
from lp.utils.db import get_db_connection
from lp.services.company_service import CompanyService
from lp.services.cancellation_service import cancellation_service

class BackupService:
    """データバックアップサービス"""
    
    def __init__(self):
        self.company_service = CompanyService()
        self.backup_dir = "backups"
        
        # バックアップディレクトリを作成
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_company_backup(self, company_id, backup_type='full'):
        """企業データのバックアップを作成"""
        try:
            # 企業情報を取得
            company_result = self.company_service.get_company(company_id)
            if not company_result['success']:
                return {
                    'success': False,
                    'error': '企業が見つかりません'
                }
            
            company = company_result['company']
            company_name = company['company_name']
            
            # バックアップファイル名を生成
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"company_{company_id}_{company_name}_{timestamp}_{backup_type}.zip"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # バックアップデータを収集
            backup_data = {
                'company_info': company,
                'backup_metadata': {
                    'backup_type': backup_type,
                    'created_at': datetime.now().isoformat(),
                    'company_id': company_id,
                    'company_name': company_name
                }
            }
            
            # 企業関連データを取得
            conn = get_db_connection()
            c = conn.cursor()
            
            # LINEアカウント情報
            c.execute('''
                SELECT * FROM company_line_accounts
                WHERE company_id = %s
            ''', (company_id,))
            line_accounts = []
            for row in c.fetchall():
                line_accounts.append({
                    'id': row[0],
                    'company_id': row[1],
                    'line_account_id': row[2],
                    'line_account_name': row[3],
                    'created_at': row[4].isoformat() if row[4] else None
                })
            backup_data['line_accounts'] = line_accounts
            
            # 支払い情報
            c.execute('''
                SELECT * FROM company_payments
                WHERE company_id = %s
            ''', (company_id,))
            payments = []
            for row in c.fetchall():
                payments.append({
                    'id': row[0],
                    'company_id': row[1],
                    'stripe_customer_id': row[2],
                    'stripe_subscription_id': row[3],
                    'subscription_status': row[4],
                    'current_period_start': row[5].isoformat() if row[5] else None,
                    'current_period_end': row[6].isoformat() if row[6] else None,
                    'trial_start': row[7].isoformat() if row[7] else None,
                    'trial_end': row[8].isoformat() if row[8] else None,
                    'created_at': row[9].isoformat() if row[9] else None,
                    'updated_at': row[10].isoformat() if row[10] else None
                })
            backup_data['payments'] = payments
            
            # コンテンツ情報
            c.execute('''
                SELECT * FROM company_contents
                WHERE company_id = %s
            ''', (company_id,))
            contents = []
            for row in c.fetchall():
                contents.append({
                    'id': row[0],
                    'company_id': row[1],
                    'content_type': row[2],
                    'content_name': row[3],
                    'content_url': row[4],
                    'is_active': row[5],
                    'created_at': row[6].isoformat() if row[6] else None,
                    'updated_at': row[7].isoformat() if row[7] else None
                })
            backup_data['contents'] = contents
            
            # 通知履歴
            c.execute('''
                SELECT * FROM company_notifications
                WHERE company_id = %s
                ORDER BY sent_at DESC
                LIMIT 100
            ''', (company_id,))
            notifications = []
            for row in c.fetchall():
                notifications.append({
                    'id': row[0],
                    'company_id': row[1],
                    'notification_type': row[2],
                    'notification_data': json.loads(row[3]) if row[3] else {},
                    'sent_at': row[4].isoformat() if row[4] else None
                })
            backup_data['notifications'] = notifications
            
            # 解約履歴
            c.execute('''
                SELECT * FROM company_cancellations
                WHERE company_id = %s
            ''', (company_id,))
            cancellations = []
            for row in c.fetchall():
                cancellations.append({
                    'id': row[0],
                    'company_id': row[1],
                    'cancellation_reason': row[2],
                    'cancellation_notes': row[3],
                    'scheduled_deletion_date': row[4].isoformat() if row[4] else None,
                    'cancelled_at': row[5].isoformat() if row[5] else None
                })
            backup_data['cancellations'] = cancellations
            
            # サブスクリプション期間
            c.execute('''
                SELECT * FROM subscription_periods
                WHERE user_id IN (
                    SELECT id FROM users WHERE company_id = %s
                )
            ''', (company_id,))
            subscription_periods = []
            for row in c.fetchall():
                subscription_periods.append({
                    'id': row[0],
                    'user_id': row[1],
                    'stripe_subscription_id': row[2],
                    'status': row[3],
                    'current_period_start': row[4].isoformat() if row[4] else None,
                    'current_period_end': row[5].isoformat() if row[5] else None,
                    'trial_start': row[6].isoformat() if row[6] else None,
                    'trial_end': row[7].isoformat() if row[7] else None,
                    'created_at': row[8].isoformat() if row[8] else None,
                    'updated_at': row[9].isoformat() if row[9] else None
                })
            backup_data['subscription_periods'] = subscription_periods
            
            # 使用ログ
            c.execute('''
                SELECT * FROM usage_logs
                WHERE user_id IN (
                    SELECT id FROM users WHERE company_id = %s
                )
                ORDER BY created_at DESC
                LIMIT 100
            ''', (company_id,))
            usage_logs = []
            for row in c.fetchall():
                usage_logs.append({
                    'id': row[0],
                    'user_id': row[1],
                    'content_type': row[2],
                    'action': row[3],
                    'details': json.loads(row[4]) if row[4] else {},
                    'created_at': row[5].isoformat() if row[5] else None
                })
            backup_data['usage_logs'] = usage_logs
            
            conn.close()
            
            # ZIPファイルを作成
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # メタデータをJSONファイルとして追加
                zipf.writestr('backup_metadata.json', json.dumps(backup_data, ensure_ascii=False, indent=2))
                
                # 各データを個別のJSONファイルとして追加
                for data_type, data in backup_data.items():
                    if data_type != 'backup_metadata':
                        zipf.writestr(f'{data_type}.json', json.dumps(data, ensure_ascii=False, indent=2))
            
            # バックアップ履歴を記録
            self._record_backup_history(company_id, backup_path, backup_type, len(backup_data))
            
            return {
                'success': True,
                'message': f'企業「{company_name}」のバックアップを作成しました',
                'backup_file': backup_filename,
                'backup_path': backup_path,
                'backup_size': os.path.getsize(backup_path),
                'data_count': len(backup_data)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'バックアップ作成エラー: {str(e)}'
            }
    
    def restore_company_backup(self, backup_file_path, restore_mode='preview'):
        """企業データのバックアップを復元"""
        try:
            if not os.path.exists(backup_file_path):
                return {
                    'success': False,
                    'error': 'バックアップファイルが見つかりません'
                }
            
            # ZIPファイルを読み込み
            with zipfile.ZipFile(backup_file_path, 'r') as zipf:
                # メタデータを読み込み
                metadata_content = zipf.read('backup_metadata.json')
                backup_data = json.loads(metadata_content.decode('utf-8'))
            
            company_id = backup_data['backup_metadata']['company_id']
            company_name = backup_data['backup_metadata']['company_name']
            
            if restore_mode == 'preview':
                # プレビューモード
                return {
                    'success': True,
                    'message': f'企業「{company_name}」のバックアップ復元プレビュー',
                    'company_info': backup_data['company_info'],
                    'data_summary': {
                        'line_accounts': len(backup_data.get('line_accounts', [])),
                        'payments': len(backup_data.get('payments', [])),
                        'contents': len(backup_data.get('contents', [])),
                        'notifications': len(backup_data.get('notifications', [])),
                        'cancellations': len(backup_data.get('cancellations', [])),
                        'subscription_periods': len(backup_data.get('subscription_periods', [])),
                        'usage_logs': len(backup_data.get('usage_logs', []))
                    },
                    'backup_metadata': backup_data['backup_metadata']
                }
            
            elif restore_mode == 'restore':
                # 実際の復元処理
                conn = get_db_connection()
                c = conn.cursor()
                
                try:
                    # 既存の企業データを確認
                    c.execute('SELECT id FROM companies WHERE id = %s', (company_id,))
                    existing_company = c.fetchone()
                    
                    if not existing_company:
                        # 企業が存在しない場合は作成
                        company_info = backup_data['company_info']
                        c.execute('''
                            INSERT INTO companies (
                                company_name, industry, employee_count, 
                                contact_email, contact_phone, address, 
                                created_at, updated_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ''', (
                            company_info['company_name'],
                            company_info.get('industry', ''),
                            company_info.get('employee_count', 0),
                            company_info.get('contact_email', ''),
                            company_info.get('contact_phone', ''),
                            company_info.get('address', ''),
                            datetime.now(),
                            datetime.now()
                        ))
                        print(f"✅ 企業「{company_name}」を作成しました")
                    
                    # LINEアカウント情報を復元
                    for line_account in backup_data.get('line_accounts', []):
                        c.execute('''
                            INSERT INTO company_line_accounts (
                                company_id, line_account_id, line_account_name, created_at
                            ) VALUES (%s, %s, %s, %s)
                            ON CONFLICT (company_id, line_account_id) DO NOTHING
                        ''', (
                            company_id,
                            line_account['line_account_id'],
                            line_account['line_account_name'],
                            datetime.now()
                        ))
                    
                    # 支払い情報を復元
                    for payment in backup_data.get('payments', []):
                        c.execute('''
                            INSERT INTO company_payments (
                                company_id, stripe_customer_id, stripe_subscription_id,
                                subscription_status, current_period_start, current_period_end,
                                trial_start, trial_end, created_at, updated_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (company_id) DO UPDATE SET
                                stripe_customer_id = EXCLUDED.stripe_customer_id,
                                stripe_subscription_id = EXCLUDED.stripe_subscription_id,
                                subscription_status = EXCLUDED.subscription_status,
                                current_period_start = EXCLUDED.current_period_start,
                                current_period_end = EXCLUDED.current_period_end,
                                trial_start = EXCLUDED.trial_start,
                                trial_end = EXCLUDED.trial_end,
                                updated_at = EXCLUDED.updated_at
                        ''', (
                            company_id,
                            payment['stripe_customer_id'],
                            payment['stripe_subscription_id'],
                            payment['subscription_status'],
                            datetime.fromisoformat(payment['current_period_start']) if payment['current_period_start'] else None,
                            datetime.fromisoformat(payment['current_period_end']) if payment['current_period_end'] else None,
                            datetime.fromisoformat(payment['trial_start']) if payment['trial_start'] else None,
                            datetime.fromisoformat(payment['trial_end']) if payment['trial_end'] else None,
                            datetime.now(),
                            datetime.now()
                        ))
                    
                    # コンテンツ情報を復元
                    for content in backup_data.get('contents', []):
                        c.execute('''
                            INSERT INTO company_contents (
                                company_id, content_type, content_name, content_url,
                                is_active, created_at, updated_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (company_id, content_type) DO UPDATE SET
                                content_name = EXCLUDED.content_name,
                                content_url = EXCLUDED.content_url,
                                is_active = EXCLUDED.is_active,
                                updated_at = EXCLUDED.updated_at
                        ''', (
                            company_id,
                            content['content_type'],
                            content['content_name'],
                            content['content_url'],
                            content['is_active'],
                            datetime.now(),
                            datetime.now()
                        ))
                    
                    # 通知履歴を復元（最新100件のみ）
                    for notification in backup_data.get('notifications', [])[:100]:
                        c.execute('''
                            INSERT INTO company_notifications (
                                company_id, notification_type, notification_data, sent_at
                            ) VALUES (%s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                        ''', (
                            company_id,
                            notification['notification_type'],
                            json.dumps(notification['notification_data'], ensure_ascii=False),
                            datetime.fromisoformat(notification['sent_at']) if notification['sent_at'] else datetime.now()
                        ))
                    
                    # 解約履歴を復元
                    for cancellation in backup_data.get('cancellations', []):
                        c.execute('''
                            INSERT INTO company_cancellations (
                                company_id, cancellation_reason, cancellation_notes,
                                scheduled_deletion_date, cancelled_at
                            ) VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                        ''', (
                            company_id,
                            cancellation['cancellation_reason'],
                            cancellation['cancellation_notes'],
                            datetime.fromisoformat(cancellation['scheduled_deletion_date']) if cancellation['scheduled_deletion_date'] else None,
                            datetime.fromisoformat(cancellation['cancelled_at']) if cancellation['cancelled_at'] else datetime.now()
                        ))
                    
                    conn.commit()
                    conn.close()
                    
                    return {
                        'success': True,
                        'message': f'企業「{company_name}」のバックアップを復元しました',
                        'restored_data': {
                            'line_accounts': len(backup_data.get('line_accounts', [])),
                            'payments': len(backup_data.get('payments', [])),
                            'contents': len(backup_data.get('contents', [])),
                            'notifications': len(backup_data.get('notifications', [])),
                            'cancellations': len(backup_data.get('cancellations', []))
                        }
                    }
                    
                except Exception as e:
                    conn.rollback()
                    conn.close()
                    raise e
            
            else:
                return {
                    'success': False,
                    'error': f'不明な復元モード: {restore_mode}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'バックアップ復元エラー: {str(e)}'
            }
    
    def list_backups(self, company_id=None):
        """バックアップ一覧を取得"""
        try:
            backups = []
            
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.zip') and filename.startswith('company_'):
                    file_path = os.path.join(self.backup_dir, filename)
                    file_stat = os.stat(file_path)
                    
                    # ファイル名から情報を解析
                    parts = filename.replace('.zip', '').split('_')
                    if len(parts) >= 4:
                        backup_company_id = int(parts[1])
                        backup_company_name = parts[2]
                        backup_timestamp = parts[3]
                        backup_type = parts[4] if len(parts) > 4 else 'full'
                        
                        # 企業IDでフィルタリング
                        if company_id and backup_company_id != company_id:
                            continue
                        
                        backups.append({
                            'filename': filename,
                            'file_path': file_path,
                            'company_id': backup_company_id,
                            'company_name': backup_company_name,
                            'backup_type': backup_type,
                            'created_at': datetime.strptime(backup_timestamp, '%Y%m%d%H%M%S').isoformat(),
                            'file_size': file_stat.st_size,
                            'file_size_mb': round(file_stat.st_size / (1024 * 1024), 2)
                        })
            
            # 作成日時でソート（新しい順）
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
            return {
                'success': True,
                'backups': backups,
                'count': len(backups)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'バックアップ一覧取得エラー: {str(e)}'
            }
    
    def delete_backup(self, backup_filename):
        """バックアップファイルを削除"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            if not os.path.exists(backup_path):
                return {
                    'success': False,
                    'error': 'バックアップファイルが見つかりません'
                }
            
            os.remove(backup_path)
            
            return {
                'success': True,
                'message': f'バックアップファイル「{backup_filename}」を削除しました'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'バックアップ削除エラー: {str(e)}'
            }
    
    def cleanup_old_backups(self, days_to_keep=30):
        """古いバックアップファイルをクリーンアップ"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.zip') and filename.startswith('company_'):
                    file_path = os.path.join(self.backup_dir, filename)
                    file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_modified < cutoff_date:
                        os.remove(file_path)
                        deleted_count += 1
            
            return {
                'success': True,
                'message': f'{deleted_count}件の古いバックアップファイルを削除しました',
                'deleted_count': deleted_count
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'バックアップクリーンアップエラー: {str(e)}'
            }
    
    def _record_backup_history(self, company_id, backup_path, backup_type, data_count):
        """バックアップ履歴を記録"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO company_notifications (
                    company_id, notification_type, notification_data, sent_at
                ) VALUES (%s, %s, %s, %s)
            ''', (
                company_id,
                'backup_created',
                json.dumps({
                    'backup_path': backup_path,
                    'backup_type': backup_type,
                    'data_count': data_count,
                    'file_size': os.path.getsize(backup_path),
                    'message': f'バックアップが作成されました（{backup_type}）'
                }, ensure_ascii=False),
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"バックアップ履歴記録エラー: {e}")

# インスタンスを作成
backup_service = BackupService() 