#!/usr/bin/env python3
"""
Railway API サービス追加テスト
"""

import requests
import json
import time

def test_service_addition():
    """Railway APIでサービス追加をテスト"""
    
    railway_token = "727e6c11-507b-4b5f-9f8c-1e90c266d730"
    
    print("=== Railway API サービス追加テスト ===")
    print(f"Railway Token: {railway_token[:8]}...")
    
    # GraphQLエンドポイント
    url = "https://backboard.railway.app/graphql/v2"
    
    # ヘッダー
    headers = {
        "Authorization": f"Bearer {railway_token}",
        "Content-Type": "application/json"
    }
    
    # 1. 新しいプロジェクトを作成
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
        "name": f"test-service-project-{int(time.time())}",
        "description": "サービス追加テスト用プロジェクト"
    }
    
    payload = {
        "query": create_query,
        "variables": variables
    }
    
    print("\n1. プロジェクト作成...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['projectCreate']:
                project = data['data']['projectCreate']
                project_id = project['id']
                print(f"✅ プロジェクト作成成功: {project['name']} (ID: {project_id})")
            else:
                print(f"❌ プロジェクト作成失敗: {data}")
                return
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ プロジェクト作成エラー: {e}")
        return
    
    # 2. サービスを追加
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
        "source": "https://github.com/kikuchi-mizuki/task-bot"
    }
    
    payload = {
        "query": add_service_query,
        "variables": variables
    }
    
    print("\n2. サービス追加テスト...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンス: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['serviceCreate']:
                service = data['data']['serviceCreate']
                print(f"✅ サービス追加成功: {service['name']} (ID: {service['id']})")
            else:
                print(f"❌ サービス追加失敗: {data}")
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            
    except Exception as e:
        print(f"❌ サービス追加エラー: {e}")

if __name__ == "__main__":
    test_service_addition() 