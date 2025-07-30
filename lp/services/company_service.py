"""
企業管理システム サービス層
"""

import os
import stripe
import uuid
import json
from datetime import datetime, timedelta
from utils.db import get_db_connection
from services.stripe_service import check_subscription_status

class CompanyService:
    """企業管理サービス"""
    
    def __init__(self):
        self.stripe = stripe
        self.stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    
    def generate_company_code(self, company_name):
        """企業コードを生成"""
        # 企業名から英数字のみを抽出し、大文字に変換
        base_code = ''.join(c for c in company_name.upper() if c.isalnum())
        # 8文字に制限
        base_code = base_code[:8]
        # ユニークなサフィックスを追加
        suffix = str(uuid.uuid4())[:4].upper()
        return f"{base_code}{suffix}"
    
    def create_company(self, company_data):
        """企業を新規作成"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 企業コードを生成
            company_code = self.generate_company_code(company_data['company_name'])
            
            # 企業基本情報を登録
            c.execute('''
                INSERT INTO companies (
                    company_name, company_code, email, phone, address, 
                    industry, employee_count, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                company_data['company_name'],
                company_code,
                company_data['email'],
                company_data.get('phone'),
                company_data.get('address'),
                company_data.get('industry'),
                company_data.get('employee_count'),
                'active'
            ))
            
            company_id = c.fetchone()[0]
            
            # 初期通知設定を作成
            self._create_default_notifications(company_id)
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'company_id': company_id,
                'company_code': company_code
            }
            
        except Exception as e:
            print(f"企業作成エラー: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_default_notifications(self, company_id):
        """デフォルト通知設定を作成"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # デフォルト通知タイプ
            notification_types = [
                'payment_success',
                'payment_failed',
                'subscription_created',
                'subscription_cancelled',
                'content_added',
                'content_removed'
            ]
            
            for notification_type in notification_types:
                c.execute('''
                    INSERT INTO company_notifications (
                        company_id, notification_type, is_enabled, recipients
                    ) VALUES (%s, %s, %s, %s)
                ''', (
                    company_id,
                    notification_type,
                    True,
                    json.dumps({'email': True, 'line': True})
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"通知設定作成エラー: {e}")
    
    def get_company(self, company_id):
        """企業情報を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 企業基本情報
            c.execute('''
                SELECT id, company_name, company_code, email, phone, 
                       address, industry, employee_count, status, 
                       created_at, updated_at
                FROM companies 
                WHERE id = %s
            ''', (company_id,))
            
            company = c.fetchone()
            if not company:
                return {'success': False, 'error': '企業が見つかりません'}
            
            # LINEアカウント情報
            c.execute('''
                SELECT line_channel_id, line_basic_id, line_qr_code_url, 
                       webhook_url, status
                FROM company_line_accounts 
                WHERE company_id = %s
            ''', (company_id,))
            
            line_account = c.fetchone()
            
            # 決済情報
            c.execute('''
                SELECT stripe_customer_id, stripe_subscription_id, 
                       subscription_status, current_period_start, 
                       current_period_end, trial_start, trial_end
                FROM company_payments 
                WHERE company_id = %s
            ''', (company_id,))
            
            payment = c.fetchone()
            
            # コンテンツ情報
            c.execute('''
                SELECT content_type, content_name, status, usage_count, 
                       last_used_at
                FROM company_contents 
                WHERE company_id = %s
            ''', (company_id,))
            
            contents = c.fetchall()
            
            conn.close()
            
            return {
                'success': True,
                'company': {
                    'id': company[0],
                    'company_name': company[1],
                    'company_code': company[2],
                    'email': company[3],
                    'phone': company[4],
                    'address': company[5],
                    'industry': company[6],
                    'employee_count': company[7],
                    'status': company[8],
                    'created_at': company[9],
                    'updated_at': company[10],
                    'line_account': {
                        'channel_id': line_account[0] if line_account else None,
                        'basic_id': line_account[1] if line_account else None,
                        'qr_code_url': line_account[2] if line_account else None,
                        'webhook_url': line_account[3] if line_account else None,
                        'status': line_account[4] if line_account else None
                    } if line_account else None,
                    'payment': {
                        'customer_id': payment[0] if payment else None,
                        'subscription_id': payment[1] if payment else None,
                        'status': payment[2] if payment else None,
                        'current_period_start': payment[3] if payment else None,
                        'current_period_end': payment[4] if payment else None,
                        'trial_start': payment[5] if payment else None,
                        'trial_end': payment[6] if payment else None
                    } if payment else None,
                    'contents': [
                        {
                            'type': content[0],
                            'name': content[1],
                            'status': content[2],
                            'usage_count': content[3],
                            'last_used_at': content[4]
                        } for content in contents
                    ]
                }
            }
            
        except Exception as e:
            print(f"企業情報取得エラー: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_company(self, company_id, update_data):
        """企業情報を更新"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 更新可能なフィールド
            allowed_fields = [
                'company_name', 'email', 'phone', 'address', 
                'industry', 'employee_count', 'status'
            ]
            
            update_fields = []
            update_values = []
            
            for field in allowed_fields:
                if field in update_data:
                    update_fields.append(f"{field} = %s")
                    update_values.append(update_data[field])
            
            if not update_fields:
                return {'success': False, 'error': '更新するフィールドがありません'}
            
            update_values.append(datetime.now())
            update_values.append(company_id)
            
            query = f'''
                UPDATE companies 
                SET {', '.join(update_fields)}, updated_at = %s
                WHERE id = %s
            '''
            
            c.execute(query, update_values)
            
            if c.rowcount == 0:
                return {'success': False, 'error': '企業が見つかりません'}
            
            conn.commit()
            conn.close()
            
            return {'success': True}
            
        except Exception as e:
            print(f"企業情報更新エラー: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_company(self, company_id):
        """企業を削除（論理削除）"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 企業ステータスを削除済みに変更
            c.execute('''
                UPDATE companies 
                SET status = 'deleted', updated_at = %s
                WHERE id = %s
            ''', (datetime.now(), company_id))
            
            if c.rowcount == 0:
                return {'success': False, 'error': '企業が見つかりません'}
            
            # 解約履歴に記録
            c.execute('''
                INSERT INTO company_cancellations (
                    company_id, cancellation_reason, cancelled_by
                ) VALUES (%s, %s, %s)
            ''', (company_id, '管理者による削除', 'system'))
            
            conn.commit()
            conn.close()
            
            return {'success': True}
            
        except Exception as e:
            print(f"企業削除エラー: {e}")
            return {'success': False, 'error': str(e)}
    
    def list_companies(self, page=1, limit=20, status=None):
        """企業一覧を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 基本クエリ
            query = '''
                SELECT id, company_name, company_code, email, status, 
                       created_at, updated_at
                FROM companies
            '''
            params = []
            
            # ステータスフィルター
            if status:
                query += ' WHERE status = %s'
                params.append(status)
            
            # ページネーション
            offset = (page - 1) * limit
            query += ' ORDER BY created_at DESC LIMIT %s OFFSET %s'
            params.extend([limit, offset])
            
            c.execute(query, params)
            companies = c.fetchall()
            
            # 総件数を取得
            count_query = 'SELECT COUNT(*) FROM companies'
            if status:
                count_query += ' WHERE status = %s'
                c.execute(count_query, [status])
            else:
                c.execute(count_query)
            
            total_count = c.fetchone()[0]
            
            conn.close()
            
            return {
                'success': True,
                'companies': [
                    {
                        'id': company[0],
                        'company_name': company[1],
                        'company_code': company[2],
                        'email': company[3],
                        'status': company[4],
                        'created_at': company[5],
                        'updated_at': company[6]
                    } for company in companies
                ],
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total_count': total_count,
                    'total_pages': (total_count + limit - 1) // limit
                }
            }
            
        except Exception as e:
            print(f"企業一覧取得エラー: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_company_by_code(self, company_code):
        """企業コードで企業を検索"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT id, company_name, company_code, email, status
                FROM companies 
                WHERE company_code = %s
            ''', (company_code,))
            
            company = c.fetchone()
            conn.close()
            
            if not company:
                return {'success': False, 'error': '企業が見つかりません'}
            
            return {
                'success': True,
                'company': {
                    'id': company[0],
                    'company_name': company[1],
                    'company_code': company[2],
                    'email': company[3],
                    'status': company[4]
                }
            }
            
        except Exception as e:
            print(f"企業コード検索エラー: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_company_statistics(self, company_id):
        """企業の統計情報を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # コンテンツ利用統計
            c.execute('''
                SELECT 
                    COUNT(*) as total_contents,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_contents,
                    SUM(usage_count) as total_usage
                FROM company_contents 
                WHERE company_id = %s
            ''', (company_id,))
            
            content_stats = c.fetchone()
            
            # 決済統計
            c.execute('''
                SELECT subscription_status, current_period_start, current_period_end
                FROM company_payments 
                WHERE company_id = %s
            ''', (company_id,))
            
            payment_stats = c.fetchone()
            
            conn.close()
            
            return {
                'success': True,
                'statistics': {
                    'contents': {
                        'total': content_stats[0] if content_stats else 0,
                        'active': content_stats[1] if content_stats else 0,
                        'total_usage': content_stats[2] if content_stats else 0
                    },
                    'payment': {
                        'status': payment_stats[0] if payment_stats else None,
                        'period_start': payment_stats[1] if payment_stats else None,
                        'period_end': payment_stats[2] if payment_stats else None
                    }
                }
            }
            
        except Exception as e:
            print(f"統計情報取得エラー: {e}")
            return {'success': False, 'error': str(e)} 