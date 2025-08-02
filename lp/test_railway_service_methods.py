#!/usr/bin/env python3
"""
Railway API サービス追加方法のテスト
"""

import requests
import json
import time

def test_different_service_methods():
    """Railway APIの異なるサービス追加方法をテスト"""
    
    railway_token = "727e6c11-507b-4b5f-9f8c-1e90c266d730"
    
    print("=== Railway API サービス追加方法テスト ===")
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
        "name": f"test-methods-project-{int(time.time())}",
        "description": "サービス追加方法テスト用プロジェクト"
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
    
    # 2. 方法1: serviceCreate ミューテーション
    print("\n2. 方法1: serviceCreate ミューテーション...")
    service_create_query = """
    mutation ServiceCreate($projectId: String!, $source: String!) {
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
        "query": service_create_query,
        "variables": variables
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンス: {response.text[:300]}...")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['serviceCreate']:
                service = data['data']['serviceCreate']
                print(f"✅ 方法1成功: {service['name']} (ID: {service['id']})")
            else:
                print(f"❌ 方法1失敗: {data}")
        else:
            print(f"❌ 方法1HTTPエラー: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 方法1エラー: {e}")
    
    # 3. 方法2: 異なるソース形式
    print("\n3. 方法2: 異なるソース形式...")
    service_create_query2 = """
    mutation ServiceCreate($projectId: String!, $source: String!) {
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
        "source": "github://kikuchi-mizuki/task-bot"
    }
    
    payload = {
        "query": service_create_query2,
        "variables": variables
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンス: {response.text[:300]}...")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['serviceCreate']:
                service = data['data']['serviceCreate']
                print(f"✅ 方法2成功: {service['name']} (ID: {service['id']})")
            else:
                print(f"❌ 方法2失敗: {data}")
        else:
            print(f"❌ 方法2HTTPエラー: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 方法2エラー: {e}")
    
    # 4. 方法3: 利用可能なミューテーションを確認
    print("\n4. 利用可能なミューテーションを確認...")
    introspection_query = """
    query IntrospectionQuery {
        __schema {
            mutationType {
                fields {
                    name
                    description
                }
            }
        }
    }
    """
    
    payload = {
        "query": introspection_query
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['__schema']:
                mutations = data['data']['__schema']['mutationType']['fields']
                service_mutations = [m for m in mutations if 'service' in m['name'].lower()]
                print(f"✅ サービス関連ミューテーション: {[m['name'] for m in service_mutations]}")
            else:
                print(f"❌ イントロスペクション失敗: {data}")
        else:
            print(f"❌ イントロスペクションHTTPエラー: {response.status_code}")
            
    except Exception as e:
        print(f"❌ イントロスペクションエラー: {e}")

if __name__ == "__main__":
    test_different_service_methods() 