"""
企業用LINEアカウント管理サービス
"""

import os
import requests
import json
from datetime import datetime
from utils.db import get_db_connection

class CompanyLineService:
    """企業用LINEアカウント管理サービス"""
    
    def __init__(self):
        self.line_api_base = "https://api.line.me/v2"
        self.line_console_api_base = "https://developers.line.biz/api/v2"
        self.line_console_token = os.getenv('LINE_CONSOLE_ACCESS_TOKEN')
    
    def create_line_account(self, company_id, company_data):
        """企業用LINE公式アカウントを作成"""
        try:
            # LINE Developers Console APIでチャンネル作成
            channel_data = {
                'name': f"{company_data['company_name']} - AIコレクションズ",
                'description': f"{company_data['company_name']}専用のAIコレクションズ公式アカウント",
                'category': 'business',
                'permissions': ['messaging_api']
            }
            
            # LINE Console APIでチャンネル作成（実際のAPIは異なる可能性があります）
            # 注意: 実際のLINE Console APIの仕様に合わせて調整が必要です
            headers = {
                'Authorization': f'Bearer {self.line_console_token}',
                'Content-Type': 'application/json'
            }
            
            # 実際の実装では、LINE Developers ConsoleのAPIを使用
            # ここではモック実装として、ダミーデータを返します
            mock_channel_data = {
                'channelId': f"U{company_id:012d}",
                'channelAccessToken': f"token_{company_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'channelSecret': f"secret_{company_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'basicId': f"@{company_data['company_name'].lower().replace(' ', '')}_{company_id}",
                'qrCodeUrl': f"https://line.me/R/ti/p/@{company_data['company_name'].lower().replace(' ', '')}_{company_id}",
                'webhookUrl': f"https://api.example.com/webhook/company/{company_id}"
            }
            
            # データベースに保存
            success = self._save_line_account(company_id, mock_channel_data)
            
            if success:
                return {
                    'success': True,
                    'line_account': mock_channel_data
                }
            else:
                return {'success': False, 'error': 'LINEアカウントの保存に失敗しました'}
            
        except Exception as e:
            print(f"LINEアカウント作成エラー: {e}")
            return {'success': False, 'error': str(e)}
    
    def _save_line_account(self, company_id, line_data):
        """LINEアカウント情報をデータベースに保存"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO company_line_accounts (
                    company_id, line_channel_id, line_channel_access_token,
                    line_channel_secret, line_basic_id, line_qr_code_url,
                    webhook_url, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                company_id,
                line_data['channelId'],
                line_data['channelAccessToken'],
                line_data['channelSecret'],
                line_data['basicId'],
                line_data['qrCodeUrl'],
                line_data['webhookUrl'],
                'active'
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"LINEアカウント保存エラー: {e}")
            return False
    
    def get_line_account(self, company_id):
        """企業のLINEアカウント情報を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT line_channel_id, line_channel_access_token, line_channel_secret,
                       line_basic_id, line_qr_code_url, webhook_url, status,
                       created_at, updated_at
                FROM company_line_accounts 
                WHERE company_id = %s
            ''', (company_id,))
            
            line_account = c.fetchone()
            conn.close()
            
            if not line_account:
                return {'success': False, 'error': 'LINEアカウントが見つかりません'}
            
            return {
                'success': True,
                'line_account': {
                    'channel_id': line_account[0],
                    'channel_access_token': line_account[1],
                    'channel_secret': line_account[2],
                    'basic_id': line_account[3],
                    'qr_code_url': line_account[4],
                    'webhook_url': line_account[5],
                    'status': line_account[6],
                    'created_at': line_account[7],
                    'updated_at': line_account[8]
                }
            }
            
        except Exception as e:
            print(f"LINEアカウント取得エラー: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_line_account(self, company_id, update_data):
        """LINEアカウント情報を更新"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 更新可能なフィールド
            allowed_fields = [
                'line_channel_access_token', 'line_channel_secret',
                'line_basic_id', 'line_qr_code_url', 'webhook_url', 'status'
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
                UPDATE company_line_accounts 
                SET {', '.join(update_fields)}, updated_at = %s
                WHERE company_id = %s
            '''
            
            c.execute(query, update_values)
            
            if c.rowcount == 0:
                return {'success': False, 'error': 'LINEアカウントが見つかりません'}
            
            conn.commit()
            conn.close()
            
            return {'success': True}
            
        except Exception as e:
            print(f"LINEアカウント更新エラー: {e}")
            return {'success': False, 'error': str(e)}
    
    def disable_line_account(self, company_id):
        """LINEアカウントを無効化"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                UPDATE company_line_accounts 
                SET status = 'disabled', updated_at = %s
                WHERE company_id = %s
            ''', (datetime.now(), company_id))
            
            if c.rowcount == 0:
                return {'success': False, 'error': 'LINEアカウントが見つかりません'}
            
            conn.commit()
            conn.close()
            
            return {'success': True}
            
        except Exception as e:
            print(f"LINEアカウント無効化エラー: {e}")
            return {'success': False, 'error': str(e)}
    
    def enable_line_account(self, company_id):
        """LINEアカウントを有効化"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                UPDATE company_line_accounts 
                SET status = 'active', updated_at = %s
                WHERE company_id = %s
            ''', (datetime.now(), company_id))
            
            if c.rowcount == 0:
                return {'success': False, 'error': 'LINEアカウントが見つかりません'}
            
            conn.commit()
            conn.close()
            
            return {'success': True}
            
        except Exception as e:
            print(f"LINEアカウント有効化エラー: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_line_message(self, company_id, message_data):
        """企業のLINEアカウントからメッセージを送信"""
        try:
            # LINEアカウント情報を取得
            line_account_result = self.get_line_account(company_id)
            if not line_account_result['success']:
                return line_account_result
            
            line_account = line_account_result['line_account']
            
            # LINE Messaging APIでメッセージ送信
            headers = {
                'Authorization': f'Bearer {line_account["channel_access_token"]}',
                'Content-Type': 'application/json'
            }
            
            # メッセージデータの構築
            if isinstance(message_data, str):
                # テキストメッセージの場合
                payload = {
                    'to': message_data.get('to', 'all'),  # 全ユーザーに送信
                    'messages': [
                        {
                            'type': 'text',
                            'text': message_data
                        }
                    ]
                }
            else:
                # 構造化されたメッセージの場合
                payload = {
                    'to': message_data.get('to', 'all'),
                    'messages': message_data.get('messages', [])
                }
            
            # LINE Messaging APIに送信
            response = requests.post(
                f"{self.line_api_base}/bot/message/push",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                return {'success': True, 'message': 'メッセージ送信完了'}
            else:
                return {
                    'success': False, 
                    'error': f'LINE API エラー: {response.status_code} - {response.text}'
                }
            
        except Exception as e:
            print(f"LINEメッセージ送信エラー: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_line_statistics(self, company_id):
        """LINEアカウントの統計情報を取得"""
        try:
            # LINEアカウント情報を取得
            line_account_result = self.get_line_account(company_id)
            if not line_account_result['success']:
                return line_account_result
            
            line_account = line_account_result['line_account']
            
            # LINE Messaging APIで統計情報を取得
            headers = {
                'Authorization': f'Bearer {line_account["channel_access_token"]}',
                'Content-Type': 'application/json'
            }
            
            # 友達数取得
            friends_response = requests.get(
                f"{self.line_api_base}/bot/profile",
                headers=headers
            )
            
            # 実際の実装では、LINE APIから統計情報を取得
            # ここではモックデータを返します
            mock_stats = {
                'friends_count': 0,
                'messages_sent': 0,
                'messages_received': 0,
                'last_activity': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'statistics': mock_stats
            }
            
        except Exception as e:
            print(f"LINE統計情報取得エラー: {e}")
            return {'success': False, 'error': str(e)}
    
    def setup_webhook(self, company_id, webhook_url):
        """Webhook URLを設定"""
        try:
            # LINEアカウント情報を取得
            line_account_result = self.get_line_account(company_id)
            if not line_account_result['success']:
                return line_account_result
            
            line_account = line_account_result['line_account']
            
            # LINE Messaging APIでWebhook URLを設定
            headers = {
                'Authorization': f'Bearer {line_account["channel_access_token"]}',
                'Content-Type': 'application/json'
            }
            
            webhook_data = {
                'endpoint': webhook_url
            }
            
            response = requests.put(
                f"{self.line_api_base}/bot/channel/webhook/endpoint",
                headers=headers,
                json=webhook_data
            )
            
            if response.status_code == 200:
                # データベースのWebhook URLも更新
                update_result = self.update_line_account(company_id, {
                    'webhook_url': webhook_url
                })
                
                if update_result['success']:
                    return {'success': True, 'message': 'Webhook設定完了'}
                else:
                    return update_result
            else:
                return {
                    'success': False,
                    'error': f'Webhook設定エラー: {response.status_code} - {response.text}'
                }
            
        except Exception as e:
            print(f"Webhook設定エラー: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_line_account(self, company_id):
        """LINEアカウントを削除"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                DELETE FROM company_line_accounts 
                WHERE company_id = %s
            ''', (company_id,))
            
            if c.rowcount == 0:
                return {'success': False, 'error': 'LINEアカウントが見つかりません'}
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': 'LINEアカウント削除完了'}
            
        except Exception as e:
            print(f"LINEアカウント削除エラー: {e}")
            return {'success': False, 'error': str(e)} 