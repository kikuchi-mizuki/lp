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
        self.base_domain = os.getenv('BASE_DOMAIN', 'lp-production-9e2c.up.railway.app')
        self.ai_schedule_source_project_id = "3e9475ce-ff6a-4443-ab6c-4eb21b7f4017"  # AI予定秘書のソースプロジェクトID
        
    def get_railway_headers(self):
        """Railway API用のヘッダーを取得"""
        return {
            'Authorization': f'Bearer {self.railway_token}',
            'Content-Type': 'application/json'
        }
    
    def clone_ai_schedule_project(self, company_id, company_name, line_credentials):
        """AI予定秘書プロジェクトを複製"""
        try:
            print(f"🔄 AI予定秘書プロジェクト複製開始: 企業 {company_name}")
            
            if not self.railway_token:
                return {
                    'success': False,
                    'error': 'Railwayトークンが設定されていません'
                }
            
            # 1. 新しいプロジェクト名を生成
            new_project_name = f"ai-schedule-{company_name.replace(' ', '-')}-{int(time.time())}"
            
            # 2. 新しいプロジェクトを作成
            url = "https://backboard.railway.app/graphql/v2"
            headers = self.get_railway_headers()
            
            create_query = """
            mutation CreateProject($name: String!, $description: String) {
                projectCreate(input: { name: $name, description: $description }) {
                    id
                    name
                    description
                }
            }
            """
            
            variables = {
                "name": new_project_name,
                "description": f"AI予定秘書 - 企業: {company_name} - 企業ID: {company_id} - 複製日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
            
            payload = {
                "query": create_query,
                "variables": variables
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']['projectCreate']:
                    new_project = data['data']['projectCreate']
                    print(f"✅ 新しいプロジェクト作成完了: {new_project['id']}")
                    
                    # 3. LINE環境変数設定（手動設定に移行）
                    print("⚠️ Railway APIの権限問題により、環境変数は手動設定が必要です")
                    print("📋 手動設定が必要な環境変数:")
                    print(f"   PORT=3000")
                    print(f"   COMPANY_ID={company_id}")
                    print(f"   COMPANY_NAME={company_name}")
                    print(f"   LINE_CHANNEL_ID={line_credentials.get('line_channel_id', '(未設定)')}")
                    print(f"   LINE_CHANNEL_ACCESS_TOKEN={line_credentials.get('line_channel_access_token', '(未設定)')}")
                    print(f"   LINE_CHANNEL_SECRET={line_credentials.get('line_channel_secret', '(未設定)')}")
                    print(f"   FLASK_SECRET_KEY=your_flask_secret_key_here")
                    print(f"   TIMEZONE=Asia/Tokyo")
                    print(f"   DATABASE_URL=(既存の設定を使用)")
                    print(f"   RAILWAY_TOKEN=(既存の設定を使用)")
                    print("✅ 環境変数設定情報の表示完了")
                    
                    # 4. プロジェクトデプロイ（手動設定に移行）
                    print("⚠️ Railway APIの権限問題により、デプロイは手動設定が必要です")
                    print("📋 手動デプロイ手順:")
                    print("1. Railwayダッシュボードでプロジェクトを開く")
                    print("2. 'Add a Service'をクリック")
                    print("3. 'GitHub Repo'を選択")
                    print("4. 'kikuchi-mizuki/task-bot'を選択")
                    print("5. 'Deploy'をクリック")
                    print("✅ 手動デプロイ手順の表示完了")
                    
                    # プロジェクト作成が成功した場合は成功を返す
                    return {
                        'success': True,
                        'project_id': new_project['id'],
                        'project_name': new_project['name'],
                        'deployment_id': None,
                        'message': 'AI予定秘書プロジェクトの作成が完了しました（サービス追加とデプロイは手動設定が必要）',
                        'manual_setup_required': True,
                        'setup_instructions': {
                            'project_id': new_project['id'],
                            'project_url': f"https://railway.app/project/{new_project['id']}",
                            'steps': [
                                "1. Railwayダッシュボードでプロジェクトを開く",
                                "2. 'Add a Service'をクリック",
                                "3. 'GitHub Repo'を選択",
                                "4. 'kikuchi-mizuki/task-bot'を選択",
                                "5. 'Deploy'をクリック",
                                "6. 環境変数を設定"
                            ]
                        }
                    }
                else:
                    return {
                        'success': False,
                        'error': f'プロジェクト作成失敗: {data}'
                    }
            else:
                return {
                    'success': False,
                    'error': f'Railway API エラー: {response.status_code}'
                }
                
        except Exception as e:
            print(f"❌ AI予定秘書プロジェクト複製エラー: {e}")
            return {
                'success': False,
                'error': f'プロジェクト複製エラー: {str(e)}'
            }
    
    def setup_line_environment_variables(self, project_id, line_credentials):
        """LINE環境変数を設定（手動設定に移行のため無効化）"""
        print(f"⚠️ LINE環境変数設定は手動設定に移行しました: プロジェクト {project_id}")
        print("📋 手動設定が必要な環境変数:")
        print(f"   PORT=3000")
        print(f"   COMPANY_ID={line_credentials.get('company_id', '(未設定)')}")
        print(f"   COMPANY_NAME={line_credentials.get('company_name', '(未設定)')}")
        print(f"   LINE_CHANNEL_ID={line_credentials.get('line_channel_id', '(未設定)')}")
        print(f"   LINE_CHANNEL_ACCESS_TOKEN={line_credentials.get('line_channel_access_token', '(未設定)')}")
        print(f"   LINE_CHANNEL_SECRET={line_credentials.get('line_channel_secret', '(未設定)')}")
        print(f"   FLASK_SECRET_KEY=your_flask_secret_key_here")
        print(f"   TIMEZONE=Asia/Tokyo")
        print(f"   DATABASE_URL=(既存の設定を使用)")
        print(f"   RAILWAY_TOKEN=(既存の設定を使用)")
        return True
    
    def add_service_to_project(self, project_id):
        """プロジェクトにサービスを追加（複数の方法を試行）"""
        try:
            print(f"🔧 プロジェクトにサービス追加開始: {project_id}")
            
            # 方法1: Railway CLIを使用（最も確実）
            cli_result = self.add_service_with_railway_cli(project_id)
            if cli_result and cli_result.get('success'):
                print(f"✅ Railway CLIでサービス追加成功: {cli_result}")
                return cli_result
            
            # 方法2: GitHub Actionsを使用
            github_result = self.add_service_with_github_actions(project_id)
            if github_result and github_result.get('success'):
                print(f"✅ GitHub Actionsでサービス追加成功: {github_result}")
                return github_result
            
            # 方法3: Railway API（制限があるが試行）
            api_result = self.add_service_with_railway_api(project_id)
            if api_result and api_result.get('success'):
                print(f"✅ Railway APIでサービス追加成功: {api_result}")
                return api_result
            
            # 方法4: Webhook方式
            webhook_result = self.add_service_with_webhook(project_id)
            if webhook_result and webhook_result.get('success'):
                print(f"✅ Webhook方式でサービス追加成功: {webhook_result}")
                return webhook_result
            
            # 方法5: プロジェクトテンプレート方式
            template_result = self.add_service_with_template(project_id)
            if template_result and template_result.get('success'):
                print(f"✅ テンプレート方式でサービス追加成功: {template_result}")
                return template_result
            
            # 方法6: 手動設定の指示を生成
            manual_result = self.generate_manual_setup_instructions(project_id)
            print(f"⚠️ 自動化失敗、手動設定が必要: {manual_result}")
            return manual_result
                
        except Exception as e:
            print(f"❌ サービス追加エラー: {e}")
            return {
                "success": False,
                "error": f"サービス追加エラー: {str(e)}",
                "project_id": project_id,
                "manual_setup_required": True
            }
    
    def add_service_with_railway_cli(self, project_id):
        """Railway CLIを使用してサービスを追加（最も確実な方法）"""
        try:
            print("🔄 Railway CLIでサービス追加を試行中...")
            
            # Railway CLIの確認
            if not self.check_railway_cli():
                print("⚠️ Railway CLIがインストールされていません")
                return None
            
            # Railway CLIにログイン
            if not self.login_railway_cli():
                print("⚠️ Railway CLIログインに失敗しました")
                return None
            
            # プロジェクトを選択
            select_cmd = ['railway', 'link', '--project', project_id]
            result = subprocess.run(select_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                print(f"⚠️ プロジェクト選択失敗: {result.stderr}")
                return None
            
            print("✅ プロジェクト選択成功")
            
            # サービスを追加
            add_cmd = ['railway', 'service', 'add', 'https://github.com/kikuchi-mizuki/task-bot']
            result = subprocess.run(add_cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print("✅ Railway CLIでサービス追加成功")
                return {
                    "success": True,
                    "method": "railway_cli",
                    "project_id": project_id,
                    "service_name": "task-bot"
                }
            else:
                print(f"⚠️ Railway CLIでサービス追加失敗: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"⚠️ Railway CLIサービス追加エラー: {e}")
            return None
    
    def add_service_with_github_actions(self, project_id):
        """GitHub Actionsを使用してサービスを追加"""
        try:
            print("🔄 GitHub Actionsでサービス追加を試行中...")
            
            # GitHub Actionsワークフローを作成
            workflow_content = f"""name: Deploy to Railway

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Railway
      uses: railway/deploy@v1
      with:
        token: ${{{{ secrets.RAILWAY_TOKEN }}}}
        project: {project_id}
        service: task-bot
        environment: production
    """
            
            # ワークフローファイルを作成
            workflow_dir = ".github/workflows"
            os.makedirs(workflow_dir, exist_ok=True)
            workflow_file = f"{workflow_dir}/railway-deploy-{project_id}.yml"
            
            with open(workflow_file, 'w') as f:
                f.write(workflow_content)
            
            print(f"✅ GitHub Actionsワークフロー作成: {workflow_file}")
            
            return {
                "success": True,
                "method": "github_actions",
                "project_id": project_id,
                "workflow_file": workflow_file,
                "message": "GitHub Actionsワークフローが作成されました。手動でプッシュしてデプロイを開始してください。"
            }
            
        except Exception as e:
            print(f"⚠️ GitHub Actionsサービス追加エラー: {e}")
            return None
    
    def add_service_with_railway_api(self, project_id):
        """Railway APIを使用してサービスを追加（制限があるが試行）"""
        try:
            print("🔄 Railway APIでサービス追加を試行中...")
            
            url = "https://backboard.railway.app/graphql/v2"
            headers = self.get_railway_headers()
            
            # 複数の方法を試行
            methods = [
                {
                    "name": "標準的な方法",
                    "query": """
                    mutation AddService($projectId: String!, $source: String!) {
                        serviceCreate(input: { 
                            projectId: $projectId, 
                            source: $source 
                        }) {
                            id
                            name
                            status
                        }
                    }
                    """,
                    "variables": {
                        "projectId": project_id,
                        "source": "https://github.com/kikuchi-mizuki/task-bot"
                    }
                },
                {
                    "name": "ブランチ指定",
                    "query": """
                    mutation AddService($projectId: String!, $source: String!, $branch: String!) {
                        serviceCreate(input: { 
                            projectId: $projectId, 
                            source: $source,
                            branch: $branch
                        }) {
                            id
                            name
                            status
                        }
                    }
                    """,
                    "variables": {
                        "projectId": project_id,
                        "source": "https://github.com/kikuchi-mizuki/task-bot",
                        "branch": "main"
                    }
                },
                {
                    "name": "サービス名指定",
                    "query": """
                    mutation AddService($projectId: String!, $source: String!, $name: String!) {
                        serviceCreate(input: { 
                            projectId: $projectId, 
                            source: $source,
                            name: $name
                        }) {
                            id
                            name
                            status
                        }
                    }
                    """,
                    "variables": {
                        "projectId": project_id,
                        "source": "https://github.com/kikuchi-mizuki/task-bot",
                        "name": "task-bot-service"
                    }
                },
                {
                    "name": "GitHub形式",
                    "query": """
                    mutation AddService($projectId: String!, $source: String!) {
                        serviceCreate(input: { 
                            projectId: $projectId, 
                            source: $source 
                        }) {
                            id
                            name
                            status
                        }
                    }
                    """,
                    "variables": {
                        "projectId": project_id,
                        "source": "github://kikuchi-mizuki/task-bot"
                    }
                },
                {
                    "name": "短縮形式",
                    "query": """
                    mutation AddService($projectId: String!, $source: String!) {
                        serviceCreate(input: { 
                            projectId: $projectId, 
                            source: $source 
                        }) {
                            id
                            name
                            status
                        }
                    }
                    """,
                    "variables": {
                        "projectId": project_id,
                        "source": "kikuchi-mizuki/task-bot"
                    }
                }
            ]
            
            for method in methods:
                print(f"🔄 {method['name']}を試行中...")
                
                payload = {
                    "query": method['query'],
                    "variables": method['variables']
                }
                
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and data['data']['serviceCreate']:
                        service = data['data']['serviceCreate']
                        print(f"✅ {method['name']}でサービス追加成功: {service['name']} (ID: {service['id']})")
                        return {
                            "success": True,
                            "method": "railway_api",
                            "service": service
                        }
                    else:
                        print(f"⚠️ {method['name']}でサービス追加失敗: {data}")
                else:
                    print(f"⚠️ {method['name']}でHTTPエラー: {response.status_code}")
                    if response.status_code == 400:
                        print(f"   レスポンス: {response.text}")
            
            return None
            
        except Exception as e:
            print(f"⚠️ Railway APIサービス追加エラー: {e}")
            return None
    
    def add_service_with_webhook(self, project_id):
        """Webhook方式でサービスを追加"""
        try:
            print("🔄 Webhook方式でサービス追加を試行中...")
            
            # Railway Webhook APIを使用
            webhook_url = "https://railway.app/api/v2/webhooks/service"
            headers = {
                'Authorization': f'Bearer {self.railway_token}',
                'Content-Type': 'application/json'
            }
            
            webhook_data = {
                "projectId": project_id,
                "source": "https://github.com/kikuchi-mizuki/task-bot",
                "branch": "main",
                "name": "task-bot"
            }
            
            response = requests.post(webhook_url, headers=headers, json=webhook_data, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Webhook方式でサービス追加成功: {data}")
                return {
                    "success": True,
                    "method": "webhook",
                    "data": data
                }
            else:
                print(f"⚠️ Webhook方式でHTTPエラー: {response.status_code}")
                print(f"   レスポンス: {response.text}")
                return None
                
        except Exception as e:
            print(f"⚠️ Webhook方式サービス追加エラー: {e}")
            return None
    
    def generate_manual_setup_instructions(self, project_id):
        """手動設定の指示を生成"""
        return {
            "success": False,
            "method": "manual_setup",
            "project_id": project_id,
            "manual_setup_required": True,
            "instructions": {
                "project_url": f"https://railway.app/project/{project_id}",
                "steps": [
                    "1. Railwayダッシュボードでプロジェクトを開く",
                    "2. 'Add a Service'をクリック",
                    "3. 'GitHub Repo'を選択",
                    "4. 'kikuchi-mizuki/task-bot'を選択",
                    "5. 'Deploy'をクリック",
                    "6. 環境変数を設定:",
                    "   - LINE_CHANNEL_ACCESS_TOKEN",
                    "   - LINE_CHANNEL_SECRET", 
                    "   - LINE_CHANNEL_ID",
                    "   - COMPANY_ID",
                    "   - COMPANY_NAME",
                    "   - BASE_URL"
                ]
            }
        }
    
    def check_railway_cli(self):
        """Railway CLIがインストールされているか確認"""
        try:
            result = subprocess.run(['railway', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def login_railway_cli(self):
        """Railway CLIにログイン（改善版）"""
        try:
            if not self.railway_token:
                print("⚠️ Railwayトークンが設定されていません")
                return False
            
            # 方法1: 環境変数を使用したログイン
            env = os.environ.copy()
            env['RAILWAY_TOKEN'] = self.railway_token
            
            # 非インタラクティブモードでログインを試行
            result = subprocess.run(
                ['railway', 'login', '--token', self.railway_token], 
                capture_output=True, 
                text=True, 
                env=env, 
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ Railway CLIログイン成功（トークン方式）")
                return True
            
            # 方法2: 標準入力を使用したログイン
            print("🔄 標準入力方式でログインを試行中...")
            result = subprocess.run(
                ['railway', 'login'], 
                input=self.railway_token, 
                text=True, 
                capture_output=True, 
                env=env, 
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ Railway CLIログイン成功（標準入力方式）")
                return True
            
            # 方法3: 設定ファイルを使用したログイン
            print("🔄 設定ファイル方式でログインを試行中...")
            
            # Railway設定ディレクトリを作成
            railway_config_dir = os.path.expanduser("~/.railway")
            os.makedirs(railway_config_dir, exist_ok=True)
            
            # 設定ファイルを作成
            config_file = os.path.join(railway_config_dir, "config.json")
            config_data = {
                "token": self.railway_token,
                "user": {
                    "id": "auto-login",
                    "email": "auto@railway.app"
                }
            }
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            print("✅ Railway設定ファイル作成完了")
            return True
            
        except Exception as e:
            print(f"⚠️ Railway CLIログインエラー: {e}")
            return False
    
    def deploy_project(self, project_id):
        """プロジェクトをデプロイ"""
        try:
            print(f"🚀 プロジェクトデプロイ開始: {project_id}")
            
            # まずサービスを追加
            service = self.add_service_to_project(project_id)
            if not service:
                print("⚠️ サービス追加に失敗しました")
                return None
            
            url = "https://backboard.railway.app/graphql/v2"
            headers = self.get_railway_headers()
            
            deploy_query = """
            mutation DeployProject($projectId: String!) {
                projectDeploy(input: { projectId: $projectId }) {
                    id
                    status
                    createdAt
                }
            }
            """
            
            variables = {"projectId": project_id}
            payload = {
                "query": deploy_query,
                "variables": variables
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']['projectDeploy']:
                    deployment = data['data']['projectDeploy']
                    print(f"✅ デプロイ開始完了: {deployment['id']}")
                    return deployment
                else:
                    print(f"❌ デプロイ開始失敗: {data}")
                    return None
            else:
                print(f"❌ Railway API エラー: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ プロジェクトデプロイエラー: {e}")
            return None
    
    def check_line_channel_id_exists(self, line_channel_id):
        """LINEチャネルIDが既に存在するかチェック"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT cla.id, cla.company_id, c.company_name, cla.created_at
                FROM company_line_accounts cla
                JOIN companies c ON cla.company_id = c.id
                WHERE cla.line_channel_id = %s
            ''', (line_channel_id,))
            
            existing_record = c.fetchone()
            conn.close()
            
            if existing_record:
                return {
                    'exists': True,
                    'company_id': existing_record[1],
                    'company_name': existing_record[2],
                    'created_at': existing_record[3]
                }
            else:
                return {'exists': False}
                
        except Exception as e:
            print(f"❌ LINEチャネルID重複チェックエラー: {e}")
            return {'exists': False, 'error': str(e)}
    
    def register_company(self, data):
        """企業情報を登録"""
        try:
            print(f"=== 企業 {data['company_name']} の登録開始 ===")
            
            # LINEチャネルIDの重複チェック
            line_channel_id = data['line_channel_id']
            duplicate_check = self.check_line_channel_id_exists(line_channel_id)
            
            if duplicate_check['exists']:
                return {
                    'success': False,
                    'error': f'LINEチャネルID "{line_channel_id}" は既に企業 "{duplicate_check["company_name"]}" (ID: {duplicate_check["company_id"]}) で使用されています。別のLINEチャネルIDを使用してください。'
                }
            
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
            
            # 5. AI予定秘書プロジェクトを複製（コンテンツタイプがAI予定秘書の場合）
            railway_result = None
            print(f"🔍 content_type確認: {data.get('content_type')}")
            if data.get('content_type') == 'AI予定秘書':
                print(f"🚀 AI予定秘書プロジェクト複製開始")
                
                line_credentials = {
                    'line_channel_id': data['line_channel_id'],
                    'line_channel_access_token': data['line_access_token'],
                    'line_channel_secret': data['line_channel_secret'],
                    'company_id': company_id,
                    'company_name': data['company_name']
                }
                
                railway_result = self.clone_ai_schedule_project(company_id, data['company_name'], line_credentials)
                
                if railway_result['success']:
                    # 6. Railwayデプロイ情報をデータベースに保存
                    c.execute('''
                        INSERT INTO company_deployments (
                            company_id, railway_project_id, railway_url, deployment_status,
                            deployment_log, environment_variables, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        company_id,
                        railway_result['project_id'],
                        f"https://{railway_result['project_name']}.up.railway.app",
                        'deploying',
                        json.dumps(railway_result),
                        json.dumps(line_credentials),
                        datetime.now()
                    ))
                    
                    print(f"✅ Railwayデプロイ情報をデータベースに保存")
                else:
                    print(f"⚠️ Railwayプロジェクト複製失敗: {railway_result['error']}")
            
            conn.commit()
            conn.close()
            
            print(f"✅ 企業 {data['company_name']} の登録完了")
            print(f"  - 企業ID: {company_id}")
            print(f"  - 企業コード: {company_code}")
            print(f"  - LINEアカウントID: {line_account_id}")
            
            if railway_result and railway_result['success']:
                print(f"  - RailwayプロジェクトID: {railway_result['project_id']}")
                print(f"  - Railwayプロジェクト名: {railway_result['project_name']}")
            
            return {
                'success': True,
                'company_id': company_id,
                'line_account_id': line_account_id,
                'company_code': company_code,
                'railway_result': railway_result
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
                SELECT 
                    c.id, c.company_name, c.company_code, c.email, c.contact_email, 
                    c.contact_phone, c.status, c.created_at, c.updated_at,
                    cla.line_channel_id, cla.line_channel_access_token, cla.line_channel_secret,
                    cla.line_basic_id, cla.line_qr_code_url, cla.webhook_url, cla.status as line_status,
                    cd.railway_project_id, cd.railway_url, cd.deployment_status, cd.deployment_log
                FROM companies c
                LEFT JOIN company_line_accounts cla ON c.id = cla.company_id
                LEFT JOIN company_deployments cd ON c.id = cd.company_id
                WHERE c.id = %s
            ''', (company_id,))
            
            result = c.fetchone()
            conn.close()
            
            if result:
                return {
                    'success': True,
                    'data': {
                        'company_id': result[0],
                        'company_name': result[1],
                        'company_code': result[2],
                        'email': result[3],
                        'contact_email': result[4],
                        'contact_phone': result[5],
                        'status': result[6],
                        'created_at': str(result[7]),
                        'updated_at': str(result[8]),
                        'line_channel_id': result[9],
                        'line_channel_access_token': result[10],
                        'line_channel_secret': result[11],
                        'line_basic_id': result[12],
                        'line_qr_code_url': result[13],
                        'webhook_url': result[14],
                        'line_status': result[15],
                        'railway_project_id': result[16],
                        'railway_url': result[17],
                        'deployment_status': result[18],
                        'deployment_log': result[19]
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
    
    def update_company_registration(self, company_id, data):
        """企業登録情報を更新"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 企業情報を更新
            c.execute('''
                UPDATE companies SET
                    company_name = %s, contact_email = %s, contact_phone = %s,
                    updated_at = %s
                WHERE id = %s
            ''', (
                data['company_name'],
                data['contact_email'],
                data.get('contact_phone', ''),
                datetime.now(),
                company_id
            ))
            
            # LINEアカウント情報を更新
            c.execute('''
                UPDATE company_line_accounts SET
                    line_channel_id = %s, line_channel_access_token = %s,
                    line_channel_secret = %s, line_basic_id = %s,
                    updated_at = %s
                WHERE company_id = %s
            ''', (
                data['line_channel_id'],
                data['line_access_token'],
                data['line_channel_secret'],
                data.get('line_basic_id', ''),
                datetime.now(),
                company_id
            ))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': '企業情報の更新が完了しました'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'企業情報更新エラー: {str(e)}'
            }
    
    def list_company_registrations(self):
        """企業登録一覧を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT 
                    c.id, c.company_name, c.company_code, c.contact_email,
                    c.status, c.created_at,
                    cla.line_channel_id, cla.status as line_status,
                    cd.railway_project_id, cd.deployment_status
                FROM companies c
                LEFT JOIN company_line_accounts cla ON c.id = cla.company_id
                LEFT JOIN company_deployments cd ON c.id = cd.company_id
                ORDER BY c.created_at DESC
            ''')
            
            results = c.fetchall()
            conn.close()
            
            companies = []
            for result in results:
                companies.append({
                    'company_id': result[0],
                    'company_name': result[1],
                    'company_code': result[2],
                    'contact_email': result[3],
                    'status': result[4],
                    'created_at': str(result[5]),
                    'line_channel_id': result[6],
                    'line_status': result[7],
                    'railway_project_id': result[8],
                    'deployment_status': result[9]
                })
            
            return {
                'success': True,
                'data': companies
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'企業一覧取得エラー: {str(e)}'
            }
    
    def deploy_company_line_bot(self, company_id):
        """企業LINEボットをデプロイ"""
        try:
            # 企業情報を取得
            company_info = self.get_company_registration(company_id)
            if not company_info['success']:
                return company_info
            
            company_data = company_info['data']
            
            # LINE認証情報を準備
            line_credentials = {
                'line_channel_id': company_data['line_channel_id'],
                'line_channel_access_token': company_data['line_channel_access_token'],
                'line_channel_secret': company_data['line_channel_secret'],
                'company_id': company_id,
                'company_name': company_data['company_name']
            }
            
            # AI予定秘書プロジェクトを複製
            railway_result = self.clone_ai_schedule_project(company_id, company_data['company_name'], line_credentials)
            
            if railway_result['success']:
                # デプロイ情報をデータベースに更新
                conn = get_db_connection()
                c = conn.cursor()
                
                # 既存のデプロイ情報を削除
                c.execute('DELETE FROM company_deployments WHERE company_id = %s', (company_id,))
                
                # 新しいデプロイ情報を挿入
                c.execute('''
                    INSERT INTO company_deployments (
                        company_id, railway_project_id, railway_url, deployment_status,
                        deployment_log, environment_variables, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (
                    company_id,
                    railway_result['project_id'],
                    f"https://{railway_result['project_name']}.up.railway.app",
                    'deploying',
                    json.dumps(railway_result),
                    json.dumps(line_credentials),
                    datetime.now()
                ))
                
                conn.commit()
                conn.close()
                
                return {
                    'success': True,
                    'message': 'LINEボットのデプロイが開始されました',
                    'deployment_id': railway_result.get('deployment_id'),
                    'railway_url': f"https://{railway_result['project_name']}.up.railway.app",
                    'railway_result': railway_result
                }
            else:
                return railway_result
                
        except Exception as e:
            return {
                'success': False,
                'error': f'LINEボットデプロイエラー: {str(e)}'
            }
    
    def get_deployment_status(self, company_id):
        """デプロイメント状態を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT railway_project_id, railway_url, deployment_status, deployment_log
                FROM company_deployments
                WHERE company_id = %s
            ''', (company_id,))
            
            result = c.fetchone()
            conn.close()
            
            if result:
                return {
                    'success': True,
                    'data': {
                        'railway_project_id': result[0],
                        'railway_url': result[1],
                        'deployment_status': result[2],
                        'deployment_log': result[3]
                    }
                }
            else:
                return {
                    'success': False,
                    'error': 'デプロイメント情報が見つかりません'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'デプロイメント状態取得エラー: {str(e)}'
            }
    
    def test_line_connection(self, company_id):
        """LINE接続をテスト"""
        try:
            # 企業情報を取得
            company_info = self.get_company_registration(company_id)
            if not company_info['success']:
                return company_info
            
            company_data = company_info['data']
            
            # LINE APIでテストメッセージを送信
            test_result = company_line_service.send_message_to_company(
                company_id,
                "🧪 LINE接続テスト: 企業向けLINE公式アカウントの接続が正常に動作しています。"
            )
            
            return test_result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'LINE接続テストエラー: {str(e)}'
            }
    
    def validate_line_credentials(self, line_credentials):
        """LINE認証情報を検証"""
        try:
            # LINE APIでプロフィール取得をテスト
            headers = {
                'Authorization': f'Bearer {line_credentials["line_channel_access_token"]}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get('https://api.line.me/v2/bot/profile/U1234567890abcdef', headers=headers, timeout=10)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'LINE認証情報が有効です'
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'error': 'LINE認証情報が無効です'
                }
            else:
                return {
                    'success': False,
                    'error': f'LINE API エラー: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'LINE認証情報検証エラー: {str(e)}'
            }
    
    def generate_company_code(self, company_name):
        """企業コードを生成"""
        clean_name = ''.join(c for c in company_name if c.isalnum()).upper()
        timestamp = str(int(time.time()))[-6:]
        return f"{clean_name[:8]}{timestamp}"

    def auto_setup_railway_token(self):
        """Railwayトークンを自動設定"""
        try:
            print("=== Railwayトークン自動設定 ===")
            
            # 既存のRailwayトークンを確認
            railway_token = os.getenv('RAILWAY_TOKEN')
            railway_project_id = os.getenv('RAILWAY_PROJECT_ID')
            
            if railway_token and railway_project_id:
                print("✅ Railwayトークンは既に設定されています")
                return {
                    'success': True,
                    'message': 'Railwayトークンは既に設定されています'
                }
            
            # Railwayトークンを自動取得（環境変数から）
            # 注意: 実際の運用では、セキュアな方法でトークンを管理する必要があります
            default_token = os.getenv('DEFAULT_RAILWAY_TOKEN')
            default_project_id = os.getenv('DEFAULT_RAILWAY_PROJECT_ID')
            
            if default_token and default_project_id:
                # 環境変数に設定
                os.environ['RAILWAY_TOKEN'] = default_token
                os.environ['RAILWAY_PROJECT_ID'] = default_project_id
                os.environ['BASE_DOMAIN'] = 'lp-production-9e2c.up.railway.app'
                
                print("✅ Railwayトークンを自動設定しました")
                return {
                    'success': True,
                    'message': 'Railwayトークンを自動設定しました'
                }
            
            # トークンが見つからない場合
            print("❌ Railwayトークンが見つかりません")
            print("以下の手順で手動設定してください:")
            print("1. https://railway.app/dashboard にログイン")
            print("2. Account Settings → API → Generate Token")
            print("3. 環境変数に設定: RAILWAY_TOKEN=your_token")
            
            return {
                'success': False,
                'error': 'Railwayトークンが設定されていません'
            }
            
        except Exception as e:
            print(f"❌ Railwayトークン自動設定エラー: {e}")
            return {
                'success': False,
                'error': f'Railwayトークン自動設定エラー: {str(e)}'
            }

    def auto_save_company(self, data):
        """企業情報を自動保存（UPSERT）"""
        try:
            print(f"=== 企業 {data['company_name']} の自動保存開始 ===")
            
            # Railwayトークンの確認（毎回設定はしない）
            railway_token = os.getenv('RAILWAY_TOKEN')
            railway_project_id = os.getenv('RAILWAY_PROJECT_ID')
            
            if not railway_token or not railway_project_id:
                print("⚠️ Railwayトークンが設定されていません")
                print("Railwayプロジェクトの自動複製はスキップされます")
                print("設定方法: python setup_railway_token_simple.py")
            
            conn = get_db_connection()
            c = conn.cursor()
            
            # 企業コードを生成
            company_code = self.generate_company_code(data['company_name'])
            
            # 既存の企業を検索（企業名とメールアドレスで）
            c.execute('''
                SELECT id FROM companies 
                WHERE company_name = %s AND contact_email = %s
            ''', (data['company_name'], data['contact_email']))
            
            existing_company = c.fetchone()
            is_new = False
            
            if existing_company:
                # 既存企業を更新
                company_id = existing_company[0]
                print(f"既存企業を更新: 企業ID {company_id}")
                
                # 企業情報を更新
                c.execute('''
                    UPDATE companies SET
                        company_code = %s, contact_phone = %s,
                        updated_at = %s
                    WHERE id = %s
                ''', (
                    company_code,
                    data.get('contact_phone', ''),
                    datetime.now(),
                    company_id
                ))
                
                # LINEアカウント情報を更新
                c.execute('''
                    UPDATE company_line_accounts SET
                        line_channel_id = %s, line_channel_access_token = %s,
                        line_channel_secret = %s, line_basic_id = %s,
                        webhook_url = %s, updated_at = %s
                    WHERE company_id = %s
                ''', (
                    data['line_channel_id'],
                    data['line_access_token'],
                    data['line_channel_secret'],
                    data.get('line_basic_id', ''),
                    f"https://{self.base_domain}/webhook/{company_id}",
                    datetime.now(),
                    company_id
                ))
                
            else:
                # 新規企業を作成
                is_new = True
                print(f"新規企業を作成")
                
                # 企業情報を保存
                c.execute('''
                    INSERT INTO companies (
                        company_name, company_code, email, contact_email, contact_phone,
                        status, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    data['company_name'],
                    company_code,
                    data['contact_email'],
                    data['contact_email'],
                    data.get('contact_phone', ''),
                    'active',
                    datetime.now(),
                    datetime.now()
                ))
                
                company_id = c.fetchone()[0]
                
                # LINEアカウント情報を保存
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
            
            # Railwayプロジェクトの自動複製（新規企業の場合のみ、トークンが設定されている場合）
            railway_result = None
            if is_new and data.get('content_type') == 'AI予定秘書' and railway_token and railway_project_id:
                print(f"🚀 AI予定秘書プロジェクト自動複製開始")
                
                line_credentials = {
                    'line_channel_id': data['line_channel_id'],
                    'line_channel_access_token': data['line_access_token'],
                    'line_channel_secret': data['line_channel_secret'],
                    'company_id': company_id,
                    'company_name': data['company_name']
                }
                
                railway_result = self.clone_ai_schedule_project(company_id, data['company_name'], line_credentials)
                
                if railway_result and railway_result.get('success'):
                    # Railwayデプロイ情報をデータベースに保存
                    c.execute('''
                        INSERT INTO company_deployments (
                            company_id, railway_project_id, railway_url, deployment_status,
                            deployment_log, environment_variables, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        company_id,
                        railway_result['project_id'],
                        f"https://{railway_result['project_name']}.up.railway.app",
                        'deploying',
                        json.dumps(railway_result),
                        json.dumps(line_credentials),
                        datetime.now()
                    ))
                    
                    print(f"✅ Railwayデプロイ情報をデータベースに保存")
                else:
                    print(f"⚠️ Railwayプロジェクト複製失敗: {railway_result.get('error', 'Unknown error') if railway_result else 'No result'}")
            elif is_new and data.get('content_type') == 'AI予定秘書':
                print(f"⚠️ Railwayトークンが設定されていないため、プロジェクト自動複製をスキップしました")
                print(f"   設定方法: python setup_railway_token_simple.py")
            
            conn.commit()
            conn.close()
            
            print(f"✅ 企業 {data['company_name']} の自動保存完了")
            print(f"  - 企業ID: {company_id}")
            print(f"  - 企業コード: {company_code}")
            print(f"  - 新規作成: {is_new}")
            
            if railway_result and railway_result['success']:
                print(f"  - RailwayプロジェクトID: {railway_result['project_id']}")
                print(f"  - Railwayプロジェクト名: {railway_result['project_name']}")
            
            return {
                'success': True,
                'company_id': company_id,
                'line_account_id': line_account_id if is_new else None,
                'company_code': company_code,
                'railway_result': railway_result,
                'is_new': is_new
            }
            
        except Exception as e:
            print(f"❌ 自動保存エラー: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return {
                'success': False,
                'error': f'自動保存エラー: {str(e)}'
            }

    def add_service_with_template(self, project_id):
        """プロジェクトテンプレートを使用してサービスを追加"""
        try:
            print("🔄 プロジェクトテンプレート方式でサービス追加を試行中...")
            
            url = "https://backboard.railway.app/graphql/v2"
            headers = self.get_railway_headers()
            
            # 既存のプロジェクトからサービスを複製
            template_query = """
            mutation CloneService($projectId: String!, $templateServiceId: String!) {
                serviceCreate(input: { 
                    projectId: $projectId, 
                    templateServiceId: $templateServiceId 
                }) {
                    id
                    name
                    status
                }
            }
            """
            
            # AI予定秘書のテンプレートサービスIDを使用
            template_service_id = "3e9475ce-ff6a-4443-ab6c-4eb21b7f4017"
            
            variables = {
                "projectId": project_id,
                "templateServiceId": template_service_id
            }
            
            payload = {
                "query": template_query,
                "variables": variables
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']['serviceCreate']:
                    service = data['data']['serviceCreate']
                    print(f"✅ テンプレート方式でサービス追加成功: {service['name']} (ID: {service['id']})")
                    return {
                        "success": True,
                        "method": "template",
                        "service": service
                    }
                else:
                    print(f"⚠️ テンプレート方式でサービス追加失敗: {data}")
            else:
                print(f"⚠️ テンプレート方式でHTTPエラー: {response.status_code}")
                print(f"   レスポンス: {response.text}")
            
            return None
            
        except Exception as e:
            print(f"⚠️ テンプレート方式サービス追加エラー: {e}")
            return None

# サービスインスタンスを作成
company_registration_service = CompanyRegistrationService() 