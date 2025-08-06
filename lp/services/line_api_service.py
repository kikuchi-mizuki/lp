#!/usr/bin/env python3
"""
LINE API連携サービス
企業ごとのLINE公式アカウント作成・管理機能
"""

import os
import requests
import json
import time
import random
import string
from datetime import datetime
from utils.db import get_db_connection

class LineAPIService:
    """LINE API連携サービス"""
    
    def __init__(self):
        self.line_api_base = "https://api.line.me/v2"
        self.line_console_api_base = "https://manager.line.biz/api"
        self.line_login_api_base = "https://access.line.me"
        
    def generate_line_credentials(self, company_code):
        """企業用のLINE認証情報を生成（モック）"""
        # 実際の実装では、LINE Developers Console APIを使用
        # 現在はモックデータを生成
        
        channel_id = f"U{company_code.lower()}{random.randint(1000, 9999)}"
        channel_secret = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        channel_access_token = ''.join(random.choices(string.ascii_letters + string.digits, k=128))
        basic_id = f"@{company_code.lower()}"
        
        return {
            'channel_id': channel_id,
            'channel_secret': channel_secret,
            'channel_access_token': channel_access_token,
            'basic_id': basic_id,
            'qr_code_url': f"https://qr.liine.me/{channel_id}",
            'webhook_url': f"https://your-domain.com/webhook/{company_code}"
        }
    
    def create_line_channel(self, company_id, company_name, company_code):
        """企業用のLINEチャンネルを作成"""
        try:
            # LINE認証情報を生成
            credentials = self.generate_line_credentials(company_code)
            
            # データベースに保存
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO company_line_accounts (
                    company_id, line_channel_id, line_channel_access_token,
                    line_channel_secret, line_basic_id, line_qr_code_url,
                    webhook_url, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                company_id, credentials['channel_id'], credentials['channel_access_token'],
                credentials['channel_secret'], credentials['basic_id'], 
                credentials['qr_code_url'], credentials['webhook_url'], 'active'
            ))
            
            line_account_id = c.fetchone()[0]
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'line_account_id': line_account_id,
                'credentials': credentials,
                'message': f'LINEチャンネルが正常に作成されました: {company_name}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'LINEチャンネル作成に失敗しました: {company_name}'
            }
    
    def send_line_message(self, company_id, message, message_type='text'):
        """企業のLINEアカウントからメッセージを送信"""
        try:
            # 企業のLINE認証情報を取得
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT line_channel_access_token, line_channel_id
                FROM company_line_accounts
                WHERE company_id = %s AND status = 'active'
            ''', (company_id,))
            
            result = c.fetchone()
            if not result:
                return {
                    'success': False,
                    'error': 'LINEアカウントが見つかりません',
                    'message': '企業のLINEアカウントが設定されていません'
                }
            
            channel_access_token, channel_id = result
            
            # LINE Messaging APIを使用してメッセージを送信
            headers = {
                'Authorization': f'Bearer {channel_access_token}',
                'Content-Type': 'application/json'
            }
            
            # 実際の実装では、LINE Messaging APIのエンドポイントを使用
            # 現在はモックで成功レスポンスを返す
            payload = {
                'to': channel_id,
                'messages': [{
                    'type': message_type,
                    'text': message
                }]
            }
            
            # LINE APIにリクエスト送信（モック）
            # response = requests.post(
            #     f"{self.line_api_base}/bot/message/push",
            #     headers=headers,
            #     json=payload
            # )
            
            # 送信ログを記録
            c.execute('''
                INSERT INTO company_notifications (
                    company_id, notification_type, is_enabled, recipients
                ) VALUES (%s, %s, %s, %s)
            ''', (company_id, 'line_message', True, json.dumps({
                'message': message,
                'type': message_type,
                'sent_at': datetime.now().isoformat()
            })))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f'メッセージが正常に送信されました: {message[:50]}...',
                'channel_id': channel_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'メッセージ送信に失敗しました: {message[:50]}...'
            }
    
    def get_line_statistics(self, company_id):
        """企業のLINE利用統計を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # LINEアカウント情報を取得
            c.execute('''
                SELECT line_channel_id, line_basic_id, status, created_at
                FROM company_line_accounts
                WHERE company_id = %s
            ''', (company_id,))
            
            line_account = c.fetchone()
            if not line_account:
                return {
                    'success': False,
                    'error': 'LINEアカウントが見つかりません'
                }
            
            # 送信メッセージ数を取得
            c.execute('''
                SELECT COUNT(*) 
                FROM company_notifications 
                WHERE company_id = %s AND notification_type = 'line_message'
            ''', (company_id,))
            
            message_count = c.fetchone()[0]
            
            conn.close()
            
            return {
                'success': True,
                'statistics': {
                    'channel_id': line_account[0],
                    'basic_id': line_account[1],
                    'status': line_account[2],
                    'created_at': line_account[3].isoformat() if line_account[3] else None,
                    'message_count': message_count,
                    'followers_count': random.randint(10, 1000),  # モック
                    'last_message_sent': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def setup_webhook(self, company_id, webhook_url):
        """企業のLINE Webhookを設定"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # Webhook URLを更新
            c.execute('''
                UPDATE company_line_accounts
                SET webhook_url = %s, updated_at = CURRENT_TIMESTAMP
                WHERE company_id = %s
            ''', (webhook_url, company_id))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f'Webhookが正常に設定されました: {webhook_url}',
                'webhook_url': webhook_url
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Webhook設定に失敗しました: {webhook_url}'
            }
    
    def disable_line_account(self, company_id):
        """企業のLINEアカウントを無効化"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                UPDATE company_line_accounts
                SET status = 'inactive', updated_at = CURRENT_TIMESTAMP
                WHERE company_id = %s
            ''', (company_id,))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': 'LINEアカウントが正常に無効化されました'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'LINEアカウントの無効化に失敗しました'
            }
    
    def enable_line_account(self, company_id):
        """企業のLINEアカウントを有効化"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                UPDATE company_line_accounts
                SET status = 'active', updated_at = CURRENT_TIMESTAMP
                WHERE company_id = %s
            ''', (company_id,))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': 'LINEアカウントが正常に有効化されました'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'LINEアカウントの有効化に失敗しました'
            }
    
    def delete_line_account(self, company_id):
        """企業のLINEアカウントを削除"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # LINEアカウント情報を削除
            c.execute('''
                DELETE FROM company_line_accounts
                WHERE company_id = %s
            ''', (company_id,))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': 'LINEアカウントが正常に削除されました'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'LINEアカウントの削除に失敗しました'
            }
    
    def send_notification_to_company(self, company_id, notification_type, message):
        """企業に通知を送信"""
        notification_messages = {
            'payment_completion': f'💰 支払いが完了しました: {message}',
            'payment_failure': f'❌ 支払いに失敗しました: {message}',
            'subscription_renewal': f'🔄 契約が更新されました: {message}',
            'cancellation': f'🚫 解約が処理されました: {message}',
            'trial_expiring': f'⏰ トライアル期間が終了します: {message}',
            'system_maintenance': f'🔧 システムメンテナンス: {message}'
        }
        
        formatted_message = notification_messages.get(
            notification_type, 
            f'📢 通知: {message}'
        )
        
        return self.send_line_message(company_id, formatted_message)
    
    def get_all_line_accounts(self):
        """全企業のLINEアカウント情報を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT 
                    cla.id,
                    c.company_name,
                    cla.line_channel_id,
                    cla.line_basic_id,
                    cla.status,
                    cla.created_at,
                    cla.updated_at
                FROM company_line_accounts cla
                JOIN companies c ON cla.company_id = c.id
                ORDER BY cla.created_at DESC
            ''')
            
            accounts = []
            for row in c.fetchall():
                accounts.append({
                    'id': row[0],
                    'company_name': row[1],
                    'channel_id': row[2],
                    'basic_id': row[3],
                    'status': row[4],
                    'created_at': row[5].isoformat() if row[5] else None,
                    'updated_at': row[6].isoformat() if row[6] else None
                })
            
            conn.close()
            
            return {
                'success': True,
                'accounts': accounts,
                'total_count': len(accounts)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# シングルトンインスタンス
line_api_service = LineAPIService() 