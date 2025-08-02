#!/usr/bin/env python3
"""
Railway Webhook APIを使用したサービス追加テスト
"""

import requests
import json
import time

def test_railway_webhook_method():
    """Railway Webhook APIを使用したサービス追加をテスト"""
    
    railway_token = "727e6c11-507b-4b5f-9f8c-1e90c266d730"
    
    print("=== Railway Webhook API サービス追加テスト ===")
    print(f"Railway Token: {railway_token[:8]}...")
    
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
        "name": f"testwebhook{int(time.time())}",
        "description": "Webhook APIテスト用プロジェクト"
    }
    
    payload = {
        "query": create_query,
        "variables": variables
    }
    
    print("1. プロジェクト作成...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'] and data['data']['projectCreate']:
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
    
    # 2. 方法1: テンプレートサービスを使用
    print("\n2. 方法1: テンプレートサービスを使用...")
    template_query = """
    mutation TemplateServiceCreate($projectId: String!, $templateId: String!) {
        templateServiceCreate(input: { 
            projectId: $projectId, 
            templateId: $templateId 
        }) {
            id
            name
            status
        }
    }
    """
    
    variables = {
        "projectId": project_id,
        "templateId": "python"  # Pythonテンプレートを試行
    }
    
    payload = {
        "query": template_query,
        "variables": variables
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンス: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['templateServiceCreate']:
                service = data['data']['templateServiceCreate']
                print(f"✅ テンプレートサービス作成成功: {service['name']} (ID: {service['id']})")
            else:
                print(f"❌ テンプレートサービス作成失敗: {data}")
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            
    except Exception as e:
        print(f"❌ テンプレートサービス作成エラー: {e}")
    
    # 3. 方法2: 異なるヘッダーでサービス作成を試行
    print("\n3. 方法2: 異なるヘッダーでサービス作成...")
    
    # 異なるヘッダーの組み合わせを試行
    header_variations = [
        {
            "Authorization": f"Bearer {railway_token}",
            "Content-Type": "application/json"
        },
        {
            "Authorization": f"Bearer {railway_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        {
            "Authorization": f"Bearer {railway_token}",
            "Content-Type": "application/json",
            "User-Agent": "Railway-API-Client"
        }
    ]
    
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
    
    for i, headers in enumerate(header_variations, 1):
        print(f"   ヘッダー変形{i}を試行中...")
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            print(f"   ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']['serviceCreate']:
                    service = data['data']['serviceCreate']
                    print(f"   ✅ 成功: {service['name']} (ID: {service['id']})")
                    return True
                else:
                    print(f"   ❌ 失敗: {data}")
            else:
                print(f"   ❌ HTTPエラー: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ エラー: {e}")
    
    # 4. 方法3: 異なるエンドポイントを試行
    print("\n4. 方法3: 異なるエンドポイントを試行...")
    
    endpoints = [
        "https://backboard.railway.app/graphql/v2",
        "https://backboard.railway.app/graphql",
        "https://api.railway.app/graphql/v2"
    ]
    
    for i, endpoint in enumerate(endpoints, 1):
        print(f"   エンドポイント{i}: {endpoint}")
        
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            print(f"   ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']['serviceCreate']:
                    service = data['data']['serviceCreate']
                    print(f"   ✅ 成功: {service['name']} (ID: {service['id']})")
                    return True
                else:
                    print(f"   ❌ 失敗: {data}")
            else:
                print(f"   ❌ HTTPエラー: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ エラー: {e}")
    
    print("\n❌ すべての方法が失敗しました")
    return False

if __name__ == "__main__":
    test_railway_webhook_method() 