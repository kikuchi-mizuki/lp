#!/usr/bin/env python3
"""
自動サービス作成スクリプト
"""

import requests
import json
import time
import os
import subprocess

def create_service_with_github_workflow():
    """GitHub Actionsを使用してサービスを作成"""
    
    railway_token = "727e6c11-507b-4b5f-9f8c-1e90c266d730"
    
    print("=== GitHub Actions 自動サービス作成 ===")
    
    # 1. プロジェクトを作成
    url = "https://backboard.railway.app/graphql/v2"
    headers = {
        "Authorization": f"Bearer {railway_token}",
        "Content-Type": "application/json"
    }
    
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
        "name": f"autoservice{int(time.time())}",
        "description": "自動サービス作成テスト"
    }
    
    payload = {
        "query": create_query,
        "variables": variables
    }
    
    print("1. Railwayプロジェクト作成...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'] and data['data']['projectCreate']:
                project = data['data']['projectCreate']
                project_id = project['id']
                project_name = project['name']
                print(f"✅ プロジェクト作成成功: {project_name} (ID: {project_id})")
            else:
                print(f"❌ プロジェクト作成失敗: {data}")
                return None
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ プロジェクト作成エラー: {e}")
        return None
    
    # 2. GitHub Actionsワークフローを作成
    print("\n2. GitHub Actionsワークフロー作成...")
    
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
    workflow_file = f"{workflow_dir}/railway-deploy.yml"
    
    with open(workflow_file, 'w') as f:
        f.write(workflow_content)
    
    print(f"✅ ワークフローファイル作成: {workflow_file}")
    
    # 3. 環境変数を設定
    print("\n3. Railway環境変数設定...")
    
    env_variables = {
        'RAILWAY_TOKEN': railway_token,
        'PROJECT_ID': project_id,
        'PROJECT_NAME': project_name
    }
    
    for var_name, var_value in env_variables.items():
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
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                print(f"✅ 環境変数設定: {var_name}")
            else:
                print(f"⚠️ 環境変数設定失敗: {var_name}")
        except Exception as e:
            print(f"⚠️ 環境変数設定エラー: {var_name} - {e}")
    
    # 4. デプロイを開始
    print("\n4. デプロイ開始...")
    
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
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['projectDeploy']:
                deployment = data['data']['projectDeploy']
                print(f"✅ デプロイ開始成功: {deployment['id']}")
            else:
                print(f"⚠️ デプロイ開始失敗: {data}")
        else:
            print(f"⚠️ デプロイ開始HTTPエラー: {response.status_code}")
    except Exception as e:
        print(f"⚠️ デプロイ開始エラー: {e}")
    
    return {
        "project_id": project_id,
        "project_name": project_name,
        "railway_url": f"https://{project_name}.up.railway.app"
    }

def create_service_with_railway_cli():
    """Railway CLIを使用してサービスを作成"""
    
    print("\n=== Railway CLI 自動サービス作成 ===")
    
    # Railway CLIがインストールされているかチェック
    try:
        result = subprocess.run(['railway', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Railway CLIがインストールされていません")
            print("インストール方法: npm install -g @railway/cli")
            return None
    except FileNotFoundError:
        print("❌ Railway CLIが見つかりません")
        print("インストール方法: npm install -g @railway/cli")
        return None
    
    print("✅ Railway CLI確認完了")
    
    # Railway CLIにログイン
    railway_token = "727e6c11-507b-4b5f-9f8c-1e90c266d730"
    
    try:
        result = subprocess.run(['railway', 'login', '--token', railway_token], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Railway CLIログイン失敗: {result.stderr}")
            return None
        print("✅ Railway CLIログイン成功")
    except Exception as e:
        print(f"❌ Railway CLIログインエラー: {e}")
        return None
    
    # 新しいプロジェクトを作成
    try:
        project_name = f"cli-autoservice-{int(time.time())}"
        result = subprocess.run(['railway', 'init', '--name', project_name], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ プロジェクト初期化失敗: {result.stderr}")
            return None
        print(f"✅ プロジェクト初期化成功: {project_name}")
    except Exception as e:
        print(f"❌ プロジェクト初期化エラー: {e}")
        return None
    
    # サービスを追加
    try:
        result = subprocess.run(['railway', 'service', 'add', 'https://github.com/kikuchi-mizuki/task-bot'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ サービス追加失敗: {result.stderr}")
            return None
        print("✅ サービス追加成功")
    except Exception as e:
        print(f"❌ サービス追加エラー: {e}")
        return None
    
    # デプロイ
    try:
        result = subprocess.run(['railway', 'deploy'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ デプロイ失敗: {result.stderr}")
            return None
        print("✅ デプロイ成功")
    except Exception as e:
        print(f"❌ デプロイエラー: {e}")
        return None
    
    return {"method": "railway_cli", "project_name": project_name}

if __name__ == "__main__":
    print("自動サービス作成を開始します...")
    
    # 方法1: GitHub Actions
    result1 = create_service_with_github_workflow()
    
    # 方法2: Railway CLI
    result2 = create_service_with_railway_cli()
    
    if result1:
        print(f"\n✅ 方法1成功: {result1}")
    if result2:
        print(f"\n✅ 方法2成功: {result2}")
    
    if not result1 and not result2:
        print("\n❌ すべての方法が失敗しました") 