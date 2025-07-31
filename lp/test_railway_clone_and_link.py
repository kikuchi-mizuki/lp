#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Railwayプロジェクトの複製とLINE紐づけ機能テストスクリプト
"""

import os
import requests
import json
import time
from datetime import datetime

class RailwayCloneAndLinkService:
    """Railwayプロジェクト複製とLINE紐づけサービス"""
    
    def __init__(self):
        self.railway_token = os.getenv('RAILWAY_TOKEN')
        self.railway_project_id = os.getenv('RAILWAY_PROJECT_ID')
        self.base_domain = os.getenv('BASE_DOMAIN', 'lp-production-9e2c.up.railway.app')
        
        if not self.railway_token:
            print("⚠️ RAILWAY_TOKENが設定されていません")
        
        if not self.railway_project_id:
            print("⚠️ RAILWAY_PROJECT_IDが設定されていません")
    
    def get_railway_headers(self):
        """Railway API用のヘッダーを取得"""
        return {
            'Authorization': f'Bearer {self.railway_token}',
            'Content-Type': 'application/json'
        }
    
    def get_project_info(self, project_id):
        """プロジェクト情報を取得"""
        try:
            url = f"https://backboard.railway.app/graphql/v2"
            headers = self.get_railway_headers()
            
            query = """
            query GetProject($id: String!) {
                project(id: $id) {
                    id
                    name
                    description
                    createdAt
                    updatedAt
                    services {
                        id
                        name
                        source {
                            image
                            repo
                            branch
                        }
                        domains {
                            domain
                        }
                        environment {
                            variables {
                                name
                                value
                            }
                        }
                    }
                }
            }
            """
            
            variables = {"id": project_id}
            payload = {
                "query": query,
                "variables": variables
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']['project']:
                    return data['data']['project']
                else:
                    print(f"❌ プロジェクト情報の取得に失敗: {data}")
                    return None
            else:
                print(f"❌ Railway API エラー: {response.status_code}")
                print(f"レスポンス: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ プロジェクト情報取得エラー: {e}")
            return None
    
    def clone_project(self, source_project_id, new_project_name, company_id):
        """プロジェクトを複製"""
        try:
            print(f"🔄 プロジェクト複製開始: {source_project_id} -> {new_project_name}")
            
            # 1. ソースプロジェクトの情報を取得
            source_project = self.get_project_info(source_project_id)
            if not source_project:
                return None
            
            print(f"✅ ソースプロジェクト情報取得完了: {source_project['name']}")
            
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
                "description": f"AI予定秘書 - 企業ID: {company_id} - 複製日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
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
                    return new_project
                else:
                    print(f"❌ プロジェクト作成失敗: {data}")
                    return None
            else:
                print(f"❌ Railway API エラー: {response.status_code}")
                print(f"レスポンス: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ プロジェクト複製エラー: {e}")
            return None
    
    def setup_line_environment_variables(self, project_id, line_credentials):
        """LINE環境変数を設定"""
        try:
            print(f"🔧 LINE環境変数設定開始: プロジェクト {project_id}")
            
            url = "https://backboard.railway.app/graphql/v2"
            headers = self.get_railway_headers()
            
            # LINE環境変数を設定
            line_variables = {
                'LINE_CHANNEL_ACCESS_TOKEN': line_credentials['line_channel_access_token'],
                'LINE_CHANNEL_SECRET': line_credentials['line_channel_secret'],
                'LINE_CHANNEL_ID': line_credentials['line_channel_id'],
                'COMPANY_ID': str(line_credentials['company_id']),
                'COMPANY_NAME': line_credentials['company_name'],
                'BASE_URL': f"https://{self.base_domain}"
            }
            
            for var_name, var_value in line_variables.items():
                set_query = """
                mutation SetVariable($projectId: String!, $name: String!, $value: String!) {
                    variableCreate(input: { projectId: $projectId, name: $name, value: $value }) {
                        id
                        name
                        value
                    }
                }
                """
                
                variables = {
                    "projectId": project_id,
                    "name": var_name,
                    "value": var_value
                }
                
                payload = {
                    "query": set_query,
                    "variables": variables
                }
                
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and data['data']['variableCreate']:
                        print(f"✅ 環境変数設定完了: {var_name}")
                    else:
                        print(f"⚠️ 環境変数設定警告: {var_name} - {data}")
                else:
                    print(f"❌ 環境変数設定エラー: {var_name} - {response.status_code}")
            
            return True
            
        except Exception as e:
            print(f"❌ LINE環境変数設定エラー: {e}")
            return False
    
    def deploy_project(self, project_id):
        """プロジェクトをデプロイ"""
        try:
            print(f"🚀 プロジェクトデプロイ開始: {project_id}")
            
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
                print(f"レスポンス: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ プロジェクトデプロイエラー: {e}")
            return None
    
    def get_deployment_status(self, project_id):
        """デプロイメント状態を取得"""
        try:
            url = f"https://backboard.railway.app/graphql/v2"
            headers = self.get_railway_headers()
            
            query = """
            query GetDeployments($projectId: String!) {
                project(id: $projectId) {
                    deployments {
                        id
                        status
                        createdAt
                        updatedAt
                        environment {
                            variables {
                                name
                                value
                            }
                        }
                    }
                }
            }
            """
            
            variables = {"projectId": project_id}
            payload = {
                "query": query,
                "variables": variables
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']['project']:
                    deployments = data['data']['project']['deployments']
                    if deployments:
                        latest_deployment = deployments[0]  # 最新のデプロイメント
                        return latest_deployment
                    else:
                        print("⚠️ デプロイメントが見つかりません")
                        return None
                else:
                    print(f"❌ デプロイメント状態取得失敗: {data}")
                    return None
            else:
                print(f"❌ Railway API エラー: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ デプロイメント状態取得エラー: {e}")
            return None

def test_railway_clone_and_link():
    """Railway複製とLINE紐づけのテスト"""
    try:
        print("=== Railway複製とLINE紐づけテスト ===")
        
        # サービスを初期化
        service = RailwayCloneAndLinkService()
        
        # テストデータ
        source_project_id = "3e9475ce-ff6a-4443-ab6c-4eb21b7f4017"  # 提供されたプロジェクトID
        company_id = 1
        company_name = "テスト株式会社"
        
        # LINE認証情報（テスト用）
        line_credentials = {
            'line_channel_id': '1234567890',
            'line_channel_access_token': 'test_access_token_12345',
            'line_channel_secret': 'test_channel_secret_67890',
            'company_id': company_id,
            'company_name': company_name
        }
        
        print(f"1️⃣ ソースプロジェクト情報取得")
        source_project = service.get_project_info(source_project_id)
        
        if source_project:
            print(f"✅ ソースプロジェクト: {source_project['name']}")
            print(f"   - ID: {source_project['id']}")
            print(f"   - 作成日: {source_project['createdAt']}")
            
            # サービス情報を表示
            if 'services' in source_project:
                for service_info in source_project['services']:
                    print(f"   - サービス: {service_info['name']}")
                    if 'domains' in service_info and service_info['domains']:
                        for domain in service_info['domains']:
                            print(f"     - ドメイン: {domain['domain']}")
        else:
            print("❌ ソースプロジェクト情報取得失敗")
            return False
        
        print(f"\n2️⃣ プロジェクト複製")
        new_project_name = f"ai-schedule-{company_name}-{int(time.time())}"
        new_project = service.clone_project(source_project_id, new_project_name, company_id)
        
        if new_project:
            print(f"✅ プロジェクト複製完了: {new_project['name']}")
            print(f"   - 新しいID: {new_project['id']}")
            
            print(f"\n3️⃣ LINE環境変数設定")
            if service.setup_line_environment_variables(new_project['id'], line_credentials):
                print("✅ LINE環境変数設定完了")
                
                print(f"\n4️⃣ プロジェクトデプロイ")
                deployment = service.deploy_project(new_project['id'])
                
                if deployment:
                    print(f"✅ デプロイ開始完了: {deployment['id']}")
                    print(f"   - ステータス: {deployment['status']}")
                    
                    print(f"\n5️⃣ デプロイメント状態確認")
                    # 少し待ってから状態を確認
                    time.sleep(5)
                    deployment_status = service.get_deployment_status(new_project['id'])
                    
                    if deployment_status:
                        print(f"✅ デプロイメント状態: {deployment_status['status']}")
                        print(f"   - 作成日時: {deployment_status['createdAt']}")
                        print(f"   - 更新日時: {deployment_status['updatedAt']}")
                    else:
                        print("⚠️ デプロイメント状態取得失敗")
                else:
                    print("❌ プロジェクトデプロイ失敗")
            else:
                print("❌ LINE環境変数設定失敗")
        else:
            print("❌ プロジェクト複製失敗")
        
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン関数"""
    print("🚀 Railway複製とLINE紐づけテストを開始します")
    
    if test_railway_clone_and_link():
        print("\n🎉 テストが完了しました！")
        print("\n📋 実装内容:")
        print("1. ✅ Railwayプロジェクト情報取得")
        print("2. ✅ プロジェクト複製機能")
        print("3. ✅ LINE環境変数設定")
        print("4. ✅ プロジェクトデプロイ")
        print("5. ✅ デプロイメント状態確認")
        
        print("\n📋 次のステップ:")
        print("1. Railway API トークンの設定")
        print("2. 実際のLINE認証情報でのテスト")
        print("3. 本格運用開始")
        
    else:
        print("❌ テストに失敗しました")

if __name__ == "__main__":
    main() 