#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
企業別LINEアカウント作成・管理サービス
"""

import os
import requests
import json
import time
from datetime import datetime
from utils.db import get_db_connection

class CompanyLineAccountService:
    """企業別LINEアカウント管理サービス"""
    
    def __init__(self):
        self.line_management_api_url = "https://api.line.me/v2/bot/channel"
        self.line_management_token = os.getenv('LINE_MANAGEMENT_TOKEN')
        
    def create_company_line_account(self, company_id, company_name):
        """企業用のLINEアカウントを作成"""
        try:
            print(f"=== 企業 {company_name} のLINEアカウント作成開始 ===")
            
            conn = get_db_connection()
            c = conn.cursor()
            
            # 1. 企業情報を取得
            c.execute('''
                SELECT id, company_name, company_code, email
                FROM companies 
                WHERE id = %s
            ''', (company_id,))
            
            company = c.fetchone()
            if not company:
                return {
                    'success': False,
                    'error': '企業が見つかりません'
                }
            
            company_id, company_name, company_code, email = company
            
            # 2. 既存のLINEアカウントをチェック
            c.execute('''
                SELECT id, line_channel_id, status
                FROM company_line_accounts 
                WHERE company_id = %s
            ''', (company_id,))
            
            existing_account = c.fetchone()
            if existing_account:
                return {
                    'success': False,
                    'error': '既にLINEアカウントが存在します',
                    'account_id': existing_account[0]
                }
            
            # 3. LINE Developers Console APIを使用してチャネルを作成
            # 注意: 実際のLINE Developers Console APIは制限があるため、
            # 手動でチャネルを作成し、情報を保存する方法を推奨
            
            # 4. チャネル情報を生成（実際のAPIキーは手動で設定）
            channel_id = f"U{company_code.lower()}"
            access_token = f"access_token_{company_code.lower()}"
            channel_secret = f"secret_{company_code.lower()}"
            basic_id = f"@{company_code.lower()}"
            
            # 5. QRコードURLを生成
            qr_code_url = f"https://qr.liqr.com/{channel_id}"
            
            # Webhook URLを生成
            base_domain = os.getenv('BASE_DOMAIN', 'lp-production-9e2c.up.railway.app')
            webhook_url = f"https://{base_domain}/webhook/{company_id}"
            
            # 7. データベースに保存
            c.execute('''
                INSERT INTO company_line_accounts (
                    company_id, line_channel_id, line_channel_access_token,
                    line_channel_secret, line_basic_id, line_qr_code_url,
                    webhook_url, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                company_id, channel_id, access_token, channel_secret,
                basic_id, qr_code_url, webhook_url, 'active'
            ))
            
            account_id = c.fetchone()[0]
            
            # 8. 企業情報を更新
            c.execute('''
                UPDATE companies 
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', (company_id,))
            
            conn.commit()
            conn.close()
            
            print(f"✅ 企業 {company_name} のLINEアカウント作成完了")
            print(f"  - チャネルID: {channel_id}")
            print(f"  - 基本ID: {basic_id}")
            print(f"  - QRコード: {qr_code_url}")
            
            return {
                'success': True,
                'account_id': account_id,
                'channel_id': channel_id,
                'basic_id': basic_id,
                'qr_code_url': qr_code_url,
                'webhook_url': webhook_url
            }
            
        except Exception as e:
            print(f"❌ LINEアカウント作成エラー: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return {
                'success': False,
                'error': f'LINEアカウント作成エラー: {str(e)}'
            }
    
    def get_company_line_account(self, company_id):
        """企業のLINEアカウント情報を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT cla.id, cla.line_channel_id, cla.line_channel_access_token,
                       cla.line_basic_id, cla.line_qr_code_url, cla.webhook_url,
                       cla.status, cla.created_at, c.company_name
                FROM company_line_accounts cla
                JOIN companies c ON cla.company_id = c.id
                WHERE cla.company_id = %s
            ''', (company_id,))
            
            account = c.fetchone()
            conn.close()
            
            if account:
                return {
                    'success': True,
                    'account': {
                        'id': account[0],
                        'channel_id': account[1],
                        'access_token': account[2],
                        'basic_id': account[3],
                        'qr_code_url': account[4],
                        'webhook_url': account[5],
                        'status': account[6],
                        'created_at': account[7],
                        'company_name': account[8]
                    }
                }
            else:
                return {
                    'success': False,
                    'error': 'LINEアカウントが見つかりません'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'LINEアカウント取得エラー: {str(e)}'
            }
    
    def update_company_line_account(self, company_id, update_data):
        """企業のLINEアカウント情報を更新"""
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
            
            for field, value in update_data.items():
                if field in allowed_fields and value is not None:
                    update_fields.append(f"{field} = %s")
                    update_values.append(value)
            
            if not update_fields:
                return {
                    'success': False,
                    'error': '更新するフィールドがありません'
                }
            
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            update_values.append(company_id)
            
            query = f'''
                UPDATE company_line_accounts 
                SET {', '.join(update_fields)}
                WHERE company_id = %s
            '''
            
            c.execute(query, update_values)
            
            if c.rowcount == 0:
                conn.close()
                return {
                    'success': False,
                    'error': '更新対象のLINEアカウントが見つかりません'
                }
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': 'LINEアカウント情報を更新しました'
            }
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return {
                'success': False,
                'error': f'LINEアカウント更新エラー: {str(e)}'
            }
    
    def delete_company_line_account(self, company_id):
        """企業のLINEアカウントを削除"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # アカウント情報を取得
            c.execute('''
                SELECT line_channel_id, line_basic_id
                FROM company_line_accounts 
                WHERE company_id = %s
            ''', (company_id,))
            
            account = c.fetchone()
            if not account:
                conn.close()
                return {
                    'success': False,
                    'error': '削除対象のLINEアカウントが見つかりません'
                }
            
            # 論理削除（ステータスをinactiveに変更）
            c.execute('''
                UPDATE company_line_accounts 
                SET status = 'inactive', updated_at = CURRENT_TIMESTAMP
                WHERE company_id = %s
            ''', (company_id,))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f'LINEアカウント {account[0]} を削除しました'
            }
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return {
                'success': False,
                'error': f'LINEアカウント削除エラー: {str(e)}'
            }
    
    def list_company_line_accounts(self, status=None):
        """企業のLINEアカウント一覧を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            query = '''
                SELECT cla.id, cla.company_id, cla.line_channel_id,
                       cla.line_basic_id, cla.status, cla.created_at,
                       c.company_name, c.company_code
                FROM company_line_accounts cla
                JOIN companies c ON cla.company_id = c.id
            '''
            
            params = []
            if status:
                query += ' WHERE cla.status = %s'
                params.append(status)
            
            query += ' ORDER BY cla.created_at DESC'
            
            c.execute(query, params)
            accounts = c.fetchall()
            conn.close()
            
            return {
                'success': True,
                'accounts': [
                    {
                        'id': account[0],
                        'company_id': account[1],
                        'channel_id': account[2],
                        'basic_id': account[3],
                        'status': account[4],
                        'created_at': account[5],
                        'company_name': account[6],
                        'company_code': account[7]
                    }
                    for account in accounts
                ]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'LINEアカウント一覧取得エラー: {str(e)}'
            }
    
    def send_message_to_company(self, company_id, message):
        """企業のLINEアカウントにメッセージを送信"""
        try:
            # 企業のLINEアカウント情報を取得
            account_result = self.get_company_line_account(company_id)
            if not account_result['success']:
                return account_result
            
            account = account_result['account']
            
            # LINE Messaging APIを使用してメッセージを送信
            headers = {
                'Authorization': f'Bearer {account["access_token"]}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'to': account['channel_id'],
                'messages': [
                    {
                        'type': 'text',
                        'text': message
                    }
                ]
            }
            
            response = requests.post(
                'https://api.line.me/v2/bot/message/push',
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'メッセージを送信しました'
                }
            else:
                return {
                    'success': False,
                    'error': f'LINE API エラー: {response.status_code} - {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'メッセージ送信エラー: {str(e)}'
            }

# インスタンスを作成
company_line_service = CompanyLineAccountService() 