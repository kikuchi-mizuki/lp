#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
企業情報登録サービス
"""

import os
import requests
import json
import time
import hashlib
import subprocess
from datetime import datetime
from utils.db import get_db_connection
from services.company_line_account_service import company_line_service

class CompanyRegistrationService:
    """企業情報登録サービス"""
    
    def __init__(self):
        self.railway_token = os.getenv('RAILWAY_TOKEN')
        self.railway_project_id = os.getenv('RAILWAY_PROJECT_ID')
        self.base_domain = os.getenv('BASE_DOMAIN', 'your-domain.com')
        
    def register_company(self, data):
        """企業情報を登録"""
        try:
            print(f"=== 企業 {data['company_name']} の登録開始 ===")
            
            conn = get_db_connection()
            c = conn.cursor()
            
            # 1. 企業コードを生成
            company_code = self.generate_company_code(data['company_name'])
            
            # 2. 企業情報をデータベースに保存
            c.execute('''
                INSERT INTO companies (
                    company_name, company_code, email, contact_email, contact_phone,
                    status, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                data['company_name'],
                company_code,
                data['contact_email'],  # emailカラムにも同じ値を設定
                data['contact_email'],
                data.get('contact_phone', ''),
                'active',
                datetime.now(),
                datetime.now()
            ))
            
            company_id = c.fetchone()[0]
            
            # 3. LINEアカウント情報を生成・保存
            line_data = {
                'line_channel_id': data['line_channel_id'],
                'line_channel_access_token': data['line_access_token'],
                'line_channel_secret': data['line_channel_secret'],
                'line_basic_id': data.get('line_basic_id', ''),
                'webhook_url': f"https://{self.base_domain}/webhook/{company_id}",
                'qr_code_url': f"https://qr.liqr.com/{data['line_channel_id']}"
            }
            
            c.execute('''
                INSERT INTO company_line_accounts (
                    company_id, line_channel_id, line_channel_access_token,
                    line_channel_secret, line_basic_id, line_qr_code_url,
                    webhook_url, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                company_id,
                line_data['line_channel_id'],
                line_data['line_channel_access_token'],
                line_data['line_channel_secret'],
                line_data['line_basic_id'],
                line_data['qr_code_url'],
                line_data['webhook_url'],
                'active'
            ))
            
            line_account_id = c.fetchone()[0]
            
            # 4. サブスクリプション情報を保存（決済完了後の場合）
            if data.get('subscription_id'):
                c.execute('''
                    INSERT INTO company_payments (
                        company_id, stripe_customer_id, stripe_subscription_id, content_type,
                        amount, status, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (
                    company_id,
                    f"cus_{company_id}_{int(time.time())}",  # 仮のcustomer_idを生成
                    data['subscription_id'],
                    data.get('content_type', 'line_bot'),
                    1500,  # 月額料金
                    'active',
                    datetime.now()
                ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ 企業 {data['company_name']} の登録完了")
            print(f"  - 企業ID: {company_id}")
            print(f"  - 企業コード: {company_code}")
            print(f"  - LINEアカウントID: {line_account_id}")
            
            return {
                'success': True,
                'company_id': company_id,
                'line_account_id': line_account_id,
                'company_code': company_code
            }
            
        except Exception as e:
            print(f"❌ 企業登録エラー: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return {
                'success': False,
                'error': f'企業登録エラー: {str(e)}'
            }
    
    def get_company_registration(self, company_id):
        """企業登録情報を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT c.id, c.company_name, c.company_code, c.contact_email,
                       c.contact_phone, c.status, c.created_at,
                       cla.line_channel_id, cla.line_basic_id, cla.webhook_url,
                       cla.line_qr_code_url, cla.status as line_status
                FROM companies c
                LEFT JOIN company_line_accounts cla ON c.id = cla.company_id
                WHERE c.id = %s
            ''', (company_id,))
            
            company = c.fetchone()
            conn.close()
            
            if company:
                return {
                    'success': True,
                    'company': {
                        'id': company[0],
                        'company_name': company[1],
                        'company_code': company[2],
                        'contact_email': company[3],
                        'contact_phone': company[4],
                        'status': company[5],
                        'created_at': company[6],
                        'line_channel_id': company[7],
                        'line_basic_id': company[8],
                        'webhook_url': company[9],
                        'qr_code_url': company[10],
                        'line_status': company[11]
                    }
                }
            else:
                return {
                    'success': False,
                    'error': '企業が見つかりません'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'企業情報取得エラー: {str(e)}'
            }
    
    def update_company_registration(self, company_id, update_data):
        """企業登録情報を更新"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 企業情報の更新
            if 'company_name' in update_data or 'contact_email' in update_data:
                update_fields = []
                update_values = []
                
                if 'company_name' in update_data:
                    update_fields.append("company_name = %s")
                    update_values.append(update_data['company_name'])
                
                if 'contact_email' in update_data:
                    update_fields.append("contact_email = %s")
                    update_values.append(update_data['contact_email'])
                
                if 'contact_phone' in update_data:
                    update_fields.append("contact_phone = %s")
                    update_values.append(update_data['contact_phone'])
                
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                update_values.append(company_id)
                
                query = f'''
                    UPDATE companies 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                '''
                
                c.execute(query, update_values)
            
            # LINEアカウント情報の更新
            line_update_fields = []
            line_update_values = []
            
            line_fields = [
                'line_channel_id', 'line_access_token', 'line_channel_secret',
                'line_basic_id', 'webhook_url', 'qr_code_url'
            ]
            
            for field in line_fields:
                if field in update_data:
                    line_update_fields.append(f"{field} = %s")
                    line_update_values.append(update_data[field])
            
            if line_update_fields:
                line_update_fields.append("updated_at = CURRENT_TIMESTAMP")
                line_update_values.append(company_id)
                
                line_query = f'''
                    UPDATE company_line_accounts 
                    SET {', '.join(line_update_fields)}
                    WHERE company_id = %s
                '''
                
                c.execute(line_query, line_update_values)
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': '企業情報を更新しました'
            }
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return {
                'success': False,
                'error': f'企業情報更新エラー: {str(e)}'
            }
    
    def list_company_registrations(self, status='active'):
        """企業登録一覧を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            query = '''
                SELECT c.id, c.company_name, c.company_code, c.contact_email,
                       c.status, c.created_at, cla.line_channel_id, cla.line_basic_id
                FROM companies c
                LEFT JOIN company_line_accounts cla ON c.id = cla.company_id
            '''
            
            params = []
            if status:
                query += ' WHERE c.status = %s'
                params.append(status)
            
            query += ' ORDER BY c.created_at DESC'
            
            c.execute(query, params)
            companies = c.fetchall()
            conn.close()
            
            return {
                'success': True,
                'companies': [
                    {
                        'id': company[0],
                        'company_name': company[1],
                        'company_code': company[2],
                        'contact_email': company[3],
                        'status': company[4],
                        'created_at': company[5],
                        'line_channel_id': company[6],
                        'line_basic_id': company[7]
                    }
                    for company in companies
                ]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'企業一覧取得エラー: {str(e)}'
            }
    
    def deploy_company_line_bot(self, company_id):
        """企業のLINEボットをRailwayにデプロイ"""
        try:
            print(f"=== 企業 {company_id} のLINEボットデプロイ開始 ===")
            
            # 1. 企業情報を取得
            company_result = self.get_company_registration(company_id)
            if not company_result['success']:
                return company_result
            
            company = company_result['company']
            
            # 2. Railwayプロジェクトを作成
            deployment_result = self.create_railway_project(company)
            if not deployment_result['success']:
                return deployment_result
            
            # 3. デプロイ状況をデータベースに保存
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO company_deployments (
                    company_id, railway_project_id, railway_url, deployment_status,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                company_id,
                deployment_result['project_id'],
                deployment_result['railway_url'],
                'deploying',
                datetime.now(),
                datetime.now()
            ))
            
            deployment_id = c.fetchone()[0]
            conn.commit()
            conn.close()
            
            print(f"✅ デプロイ開始完了")
            print(f"  - デプロイID: {deployment_id}")
            print(f"  - Railway URL: {deployment_result['railway_url']}")
            
            return {
                'success': True,
                'deployment_id': deployment_id,
                'railway_url': deployment_result['railway_url'],
                'project_id': deployment_result['project_id']
            }
            
        except Exception as e:
            print(f"❌ デプロイエラー: {e}")
            return {
                'success': False,
                'error': f'デプロイエラー: {str(e)}'
            }
    
    def create_railway_project(self, company):
        """Railwayプロジェクトを作成"""
        try:
            if not self.railway_token:
                return {
                    'success': False,
                    'error': 'Railwayトークンが設定されていません'
                }
            
            # Railway APIを使用してプロジェクトを作成
            headers = {
                'Authorization': f'Bearer {self.railway_token}',
                'Content-Type': 'application/json'
            }
            
            project_data = {
                'name': f"{company['company_name']}-line-bot",
                'description': f"{company['company_name']}のLINE公式アカウント"
            }
            
            response = requests.post(
                'https://railway.app/api/v2/projects',
                headers=headers,
                json=project_data,
                timeout=30
            )
            
            if response.status_code == 201:
                project_info = response.json()
                return {
                    'success': True,
                    'project_id': project_info['id'],
                    'railway_url': f"https://{project_info['name']}.railway.app"
                }
            else:
                return {
                    'success': False,
                    'error': f'Railway API エラー: {response.status_code} - {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Railwayプロジェクト作成エラー: {str(e)}'
            }
    
    def get_deployment_status(self, company_id):
        """デプロイ状況を確認"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT deployment_status, railway_url, created_at, updated_at
                FROM company_deployments
                WHERE company_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            ''', (company_id,))
            
            deployment = c.fetchone()
            conn.close()
            
            if deployment:
                return {
                    'success': True,
                    'status': {
                        'deployment_status': deployment[0],
                        'railway_url': deployment[1],
                        'created_at': deployment[2],
                        'updated_at': deployment[3]
                    }
                }
            else:
                return {
                    'success': False,
                    'error': 'デプロイ情報が見つかりません'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'デプロイ状況取得エラー: {str(e)}'
            }
    
    def test_line_connection(self, company_id, test_message):
        """LINE接続をテスト"""
        try:
            # LINE Messaging APIを使用してテストメッセージを送信
            result = company_line_service.send_message_to_company(company_id, test_message)
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'LINE接続テストエラー: {str(e)}'
            }
    
    def validate_line_credentials(self, credentials):
        """LINE認証情報を検証"""
        try:
            headers = {
                'Authorization': f'Bearer {credentials["line_access_token"]}',
                'Content-Type': 'application/json'
            }
            
            # LINE Messaging APIのプロフィール取得で認証をテスト
            response = requests.get(
                'https://api.line.me/v2/bot/profile/U1234567890abcdef',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'channel_info': {
                        'channel_id': credentials['line_channel_id'],
                        'basic_id': credentials.get('line_basic_id', ''),
                        'status': 'valid'
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f'LINE認証エラー: {response.status_code} - {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'認証情報検証エラー: {str(e)}'
            }
    
    def generate_company_code(self, company_name):
        """企業コードを生成"""
        # 企業名からコードを生成
        clean_name = ''.join(c for c in company_name if c.isalnum()).upper()
        timestamp = str(int(time.time()))[-6:]
        hash_object = hashlib.md5(company_name.encode())
        hash_hex = hash_object.hexdigest()[:4].upper()
        
        return f"{clean_name[:8]}{timestamp}{hash_hex}"

# インスタンスを作成
company_registration_service = CompanyRegistrationService() 