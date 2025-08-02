#!/usr/bin/env python3
"""
実際にサービスを追加するスクリプト
"""

import os
import sys
import time
import requests
import json
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.company_registration_service import CompanyRegistrationService

def create_actual_service():
    """実際にサービスを作成"""
    try:
        print("🚀 実際のサービス作成を開始します...")
        print("=" * 50)
        
        # サービスインスタンスを作成
        service = CompanyRegistrationService()
        
        # Railwayトークンの確認
        if not service.railway_token:
            print("❌ Railwayトークンが設定されていません")
            return False
        
        print(f"✅ Railwayトークン確認: {service.railway_token[:8]}...")
        
        # 1. 新しいプロジェクトを作成
        print("\n📦 1. 新しいプロジェクトを作成中...")
        
        project_name = f"actual-service-{int(time.time())}"
        
        url = "https://backboard.railway.app/graphql/v2"
        headers = service.get_railway_headers()
        
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
            "name": project_name,
            "description": f"実際のサービス作成テスト - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        payload = {
            "query": create_query,
            "variables": variables
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['projectCreate']:
                project = data['data']['projectCreate']
                project_id = project['id']
                print(f"✅ プロジェクト作成成功: {project['name']} (ID: {project_id})")
            else:
                print(f"❌ プロジェクト作成失敗: {data}")
                return False
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            return False
        
        # 2. サービスを追加（複数の方法を試行）
        print(f"\n🔧 2. サービス追加を試行中...")
        print(f"プロジェクトID: {project_id}")
        
        # 方法1: Railway API（複数形式）
        print("\n🔄 方法1: Railway API（複数形式）を試行中...")
        
        service_added = False
        
        # 複数のソース形式を試行
        source_formats = [
            "https://github.com/kikuchi-mizuki/task-bot",
            "github://kikuchi-mizuki/task-bot",
            "kikuchi-mizuki/task-bot",
            "git@github.com:kikuchi-mizuki/task-bot.git"
        ]
        
        for i, source in enumerate(source_formats, 1):
            print(f"   試行 {i}: {source}")
            
            add_service_query = """
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
            """
            
            variables = {
                "projectId": project_id,
                "source": source
            }
            
            payload = {
                "query": add_service_query,
                "variables": variables
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and data['data']['serviceCreate']:
                        service_info = data['data']['serviceCreate']
                        print(f"   ✅ 成功: {service_info['name']} (ID: {service_info['id']})")
                        service_added = True
                        break
                    else:
                        print(f"   ❌ 失敗: {data}")
                else:
                    print(f"   ❌ HTTPエラー: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ エラー: {e}")
        
        if service_added:
            print("\n🎉 サービス追加が成功しました！")
            
            # 3. 環境変数を設定
            print("\n⚙️ 3. 環境変数を設定中...")
            
            env_variables = {
                "LINE_CHANNEL_ACCESS_TOKEN": "915352d9dd5bbd718a3127e4c89ff528",
                "LINE_CHANNEL_SECRET": "7DrmRKzZYZRT7uHBgKB7i8OMfaCDtSOBFWMTfW6v6pdB4ZyhqTwbGEOKxuFe+9ndg9Zvk59k8+NdLL/dUj/rhgj7jn76K4M8fk8EhmpSCEdbfssoNzvwxzAO2mV7UoWCFO7yH/KuCEC4Ngp5Qe6M1AdB04t89/1O/w1cDnyilFU=",
                "LINE_CHANNEL_ID": "2007858939",
                "COMPANY_ID": "33",
                "COMPANY_NAME": "株式会社サンプル",
                "BASE_URL": "https://task-bot-production.up.railway.app"
            }
            
            # 環境変数設定のGraphQLクエリ
            for var_name, var_value in env_variables.items():
                set_env_query = """
                mutation SetVariable($projectId: String!, $serviceId: String!, $name: String!, $value: String!) {
                    variableCreate(input: {
                        projectId: $projectId,
                        serviceId: $serviceId,
                        name: $name,
                        value: $value
                    }) {
                        id
                        name
                        value
                    }
                }
                """
                
                variables = {
                    "projectId": project_id,
                    "serviceId": service_info['id'],
                    "name": var_name,
                    "value": var_value
                }
                
                payload = {
                    "query": set_env_query,
                    "variables": variables
                }
                
                try:
                    response = requests.post(url, headers=headers, json=payload, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'data' in data and data['data']['variableCreate']:
                            print(f"   ✅ {var_name}: 設定成功")
                        else:
                            print(f"   ⚠️ {var_name}: 設定失敗（手動設定が必要）")
                    else:
                        print(f"   ⚠️ {var_name}: HTTPエラー {response.status_code}")
                        
                except Exception as e:
                    print(f"   ⚠️ {var_name}: エラー {e}")
            
            # 4. デプロイを開始
            print("\n🚀 4. デプロイを開始中...")
            
            deploy_query = """
            mutation DeployService($serviceId: String!) {
                serviceDeploy(input: { serviceId: $serviceId }) {
                    id
                    status
                }
            }
            """
            
            variables = {
                "serviceId": service_info['id']
            }
            
            payload = {
                "query": deploy_query,
                "variables": variables
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and data['data']['serviceDeploy']:
                        deploy_info = data['data']['serviceDeploy']
                        print(f"✅ デプロイ開始成功: {deploy_info['id']}")
                        print(f"   ステータス: {deploy_info['status']}")
                    else:
                        print("⚠️ デプロイ開始失敗（手動デプロイが必要）")
                else:
                    print(f"⚠️ デプロイ開始HTTPエラー: {response.status_code}")
                    
            except Exception as e:
                print(f"⚠️ デプロイ開始エラー: {e}")
            
            print("\n🎯 === サービス作成完了 ===")
            print(f"プロジェクトID: {project_id}")
            print(f"プロジェクト名: {project_name}")
            print(f"サービスID: {service_info['id']}")
            print(f"サービス名: {service_info['name']}")
            print(f"プロジェクトURL: https://railway.app/project/{project_id}")
            
            return True
            
        else:
            print("\n❌ すべてのサービス追加方法が失敗しました")
            
            # 5. GitHub Actionsワークフローを作成
            print("\n📝 5. GitHub Actionsワークフローを作成中...")
            
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
            
            workflow_dir = ".github/workflows"
            os.makedirs(workflow_dir, exist_ok=True)
            workflow_file = f"{workflow_dir}/railway-deploy-{project_id}.yml"
            
            with open(workflow_file, 'w') as f:
                f.write(workflow_content)
            
            print(f"✅ GitHub Actionsワークフロー作成: {workflow_file}")
            print("\n📋 次のステップ:")
            print("1. ワークフローファイルをGitHubにプッシュ")
            print("2. GitHub SecretsにRAILWAY_TOKENを設定")
            print("3. ワークフローを手動実行")
            
            return False
            
    except Exception as e:
        print(f"❌ サービス作成エラー: {e}")
        return False

def main():
    """メイン関数"""
    print("実際のサービス作成を開始します...")
    
    success = create_actual_service()
    
    if success:
        print("\n🎉 サービス作成が完了しました！")
        print("Railwayダッシュボードで確認してください。")
    else:
        print("\n⚠️ サービス作成に問題があります")
        print("GitHub Actionsワークフローを使用してください。")

if __name__ == "__main__":
    main() 