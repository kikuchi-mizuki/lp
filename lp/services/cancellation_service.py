import os
import json
from datetime import datetime, timedelta
from lp.utils.db import get_db_connection
from lp.services.line_api_service import line_api_service
from lp.services.stripe_payment_service import stripe_payment_service
from lp.services.content_management_service import content_management_service

class CancellationService:
    """企業解約・データ削除サービス"""
    
    def __init__(self):
        self.cancellation_reasons = {
            'cost': '料金が高い',
            'not_used': '使用頻度が低い',
            'not_satisfied': '機能に不満',
            'switching': '他社サービスに移行',
            'business_closed': '事業廃止',
            'other': 'その他'
        }
    
    def process_company_cancellation(self, company_id, reason='other', notes=''):
        """企業の解約処理を実行"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 企業情報を取得
            c.execute('''
                SELECT company_name, company_code, stripe_customer_id, stripe_subscription_id
                FROM companies c
                LEFT JOIN company_payments cp ON c.id = cp.company_id
                WHERE c.id = %s AND c.deleted_at IS NULL
            ''', (company_id,))
            
            company_info = c.fetchone()
            if not company_info:
                conn.close()
                return {
                    'success': False,
                    'error': '企業が見つかりません'
                }
            
            company_name, company_code, stripe_customer_id, stripe_subscription_id = company_info
            
            # 解約履歴を記録
            c.execute('''
                INSERT INTO company_cancellations (
                    company_id, cancellation_reason, cancellation_notes,
                    stripe_customer_id, stripe_subscription_id, cancelled_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                company_id, reason, notes, stripe_customer_id, 
                stripe_subscription_id, datetime.now()
            ))
            
            # Stripeでサブスクリプションをキャンセル
            if stripe_subscription_id:
                try:
                    stripe_payment_service.cancel_subscription(company_id)
                except Exception as e:
                    print(f"Stripe解約エラー: {e}")
            
            # 企業ステータスを解約済みに更新
            c.execute('''
                UPDATE companies 
                SET status = 'cancelled', updated_at = %s
                WHERE id = %s
            ''', (datetime.now(), company_id))
            
            # 支払い情報を更新
            c.execute('''
                UPDATE company_payments 
                SET subscription_status = 'cancelled', updated_at = %s
                WHERE company_id = %s
            ''', (datetime.now(), company_id))
            
            # LINEアカウントを無効化
            c.execute('''
                UPDATE company_line_accounts 
                SET status = 'disabled', updated_at = %s
                WHERE company_id = %s
            ''', (datetime.now(), company_id))
            
            # コンテンツを無効化
            c.execute('''
                UPDATE company_contents 
                SET status = 'cancelled', updated_at = %s
                WHERE company_id = %s
            ''', (datetime.now(), company_id))
            
            conn.commit()
            conn.close()
            
            # LINE通知を送信
            try:
                line_api_service.send_notification_to_company(
                    company_id,
                    'cancellation_confirmed',
                    {
                        'company_name': company_name,
                        'cancellation_date': datetime.now().strftime('%Y年%m月%d日'),
                        'reason': self.cancellation_reasons.get(reason, reason)
                    }
                )
            except Exception as e:
                print(f"LINE通知エラー: {e}")
            
            return {
                'success': True,
                'message': f'企業「{company_name}」の解約処理が完了しました',
                'company_id': company_id,
                'cancellation_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return {
                'success': False,
                'error': f'解約処理エラー: {str(e)}'
            }
    
    def schedule_data_deletion(self, company_id, deletion_days=30):
        """企業データの削除をスケジュール"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            deletion_date = datetime.now() + timedelta(days=deletion_days)
            
            # 削除スケジュールを記録
            c.execute('''
                UPDATE company_cancellations 
                SET scheduled_deletion_date = %s, updated_at = %s
                WHERE company_id = %s
                ORDER BY cancelled_at DESC
                LIMIT 1
            ''', (deletion_date, datetime.now(), company_id))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f'データ削除が{deletion_days}日後にスケジュールされました',
                'deletion_date': deletion_date.isoformat()
            }
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return {
                'success': False,
                'error': f'削除スケジュールエラー: {str(e)}'
            }
    
    def execute_data_deletion(self, company_id):
        """企業データの完全削除を実行"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 企業情報を取得（削除前）
            c.execute('''
                SELECT company_name, company_code
                FROM companies 
                WHERE id = %s
            ''', (company_id,))
            
            company_info = c.fetchone()
            if not company_info:
                conn.close()
                return {
                    'success': False,
                    'error': '企業が見つかりません'
                }
            
            company_name, company_code = company_info
            
            # 関連データを削除（論理削除）
            tables_to_delete = [
                'company_notifications',
                'company_contents', 
                'company_line_accounts',
                'company_payments',
                'company_cancellations'
            ]
            
            for table in tables_to_delete:
                c.execute(f'DELETE FROM {table} WHERE company_id = %s', (company_id,))
            
            # 企業を論理削除
            c.execute('''
                UPDATE companies 
                SET deleted_at = %s, status = 'deleted'
                WHERE id = %s
            ''', (datetime.now(), company_id))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f'企業「{company_name}」のデータ削除が完了しました',
                'deleted_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return {
                'success': False,
                'error': f'データ削除エラー: {str(e)}'
            }
    
    def get_cancellation_history(self, company_id=None):
        """解約履歴を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            if company_id:
                c.execute('''
                    SELECT cc.*, c.company_name, c.company_code
                    FROM company_cancellations cc
                    JOIN companies c ON cc.company_id = c.id
                    WHERE cc.company_id = %s
                    ORDER BY cc.cancelled_at DESC
                ''', (company_id,))
            else:
                c.execute('''
                    SELECT cc.*, c.company_name, c.company_code
                    FROM company_cancellations cc
                    JOIN companies c ON cc.company_id = c.id
                    ORDER BY cc.cancelled_at DESC
                ''')
            
            cancellations = []
            for row in c.fetchall():
                cancellations.append({
                    'id': row[0],
                    'company_id': row[1],
                    'company_name': row[6],
                    'company_code': row[7],
                    'cancellation_reason': row[2],
                    'cancellation_notes': row[3],
                    'stripe_customer_id': row[4],
                    'stripe_subscription_id': row[5],
                    'cancelled_at': row[8].isoformat() if row[8] else None,
                    'scheduled_deletion_date': row[9].isoformat() if row[9] else None,
                    'created_at': row[10].isoformat() if row[10] else None,
                    'updated_at': row[11].isoformat() if row[11] else None
                })
            
            conn.close()
            
            return {
                'success': True,
                'cancellations': cancellations,
                'count': len(cancellations)
            }
            
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            return {
                'success': False,
                'error': f'解約履歴取得エラー: {str(e)}'
            }
    
    def get_pending_deletions(self):
        """削除予定の企業を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT cc.*, c.company_name, c.company_code
                FROM company_cancellations cc
                JOIN companies c ON cc.company_id = c.id
                WHERE cc.scheduled_deletion_date <= %s
                AND c.deleted_at IS NULL
                ORDER BY cc.scheduled_deletion_date ASC
            ''', (datetime.now(),))
            
            pending_deletions = []
            for row in c.fetchall():
                pending_deletions.append({
                    'company_id': row[1],
                    'company_name': row[6],
                    'company_code': row[7],
                    'cancelled_at': row[8].isoformat() if row[8] else None,
                    'scheduled_deletion_date': row[9].isoformat() if row[9] else None
                })
            
            conn.close()
            
            return {
                'success': True,
                'pending_deletions': pending_deletions,
                'count': len(pending_deletions)
            }
            
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            return {
                'success': False,
                'error': f'削除予定取得エラー: {str(e)}'
            }
    
    def cancel_deletion_schedule(self, company_id):
        """削除スケジュールをキャンセル"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                UPDATE company_cancellations 
                SET scheduled_deletion_date = NULL, updated_at = %s
                WHERE company_id = %s
                ORDER BY cancelled_at DESC
                LIMIT 1
            ''', (datetime.now(), company_id))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': '削除スケジュールがキャンセルされました'
            }
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return {
                'success': False,
                'error': f'スケジュールキャンセルエラー: {str(e)}'
            }

# インスタンスを作成
cancellation_service = CancellationService() 