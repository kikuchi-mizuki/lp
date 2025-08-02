#!/usr/bin/env python3
"""
Railway API 400エラーの根本原因調査
"""

import requests
import json
import time

def debug_railway_api_root_cause():
    """Railway APIの400エラーの根本原因を調査"""
    
    railway_token = "727e6c11-507b-4b5f-9f8c-1e90c266d730"
    
    print("=== Railway API 400エラー根本原因調査 ===")
    print(f"Railway Token: {railway_token[:8]}...")
    
    url = "https://backboard.railway.app/graphql/v2"
    
    # 1. トークンの権限を確認
    print("\n1. トークン権限確認...")
    
    headers = {
        "Authorization": f"Bearer {railway_token}",
        "Content-Type": "application/json"
    }
    
    # ユーザー情報を取得
    user_query = """
    query GetUser {
        me {
            id
            email
            name
            teams {
                id
                name
            }
        }
    }
    """
    
    payload = {
        "query": user_query
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンス: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['me']:
                user = data['data']['me']
                print(f"✅ ユーザー情報取得成功")
                print(f"   ID: {user['id']}")
                print(f"   メール: {user['email']}")
                print(f"   名前: {user['name']}")
                if user.get('teams'):
                    print(f"   チーム: {[team['name'] for team in user['teams']]}")
            else:
                print(f"❌ ユーザー情報取得失敗: {data}")
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            
    except Exception as e:
        print(f"❌ ユーザー情報取得エラー: {e}")
    
    # 2. プロジェクト一覧を取得
    print("\n2. プロジェクト一覧取得...")
    
    projects_query = """
    query GetProjects {
        projects {
            id
            name
            description
            createdAt
        }
    }
    """
    
    payload = {
        "query": projects_query
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['projects']:
                projects = data['data']['projects']
                print(f"✅ プロジェクト一覧取得成功: {len(projects)}件")
                for project in projects[:3]:
                    print(f"   - {project['name']} (ID: {project['id']})")
            else:
                print(f"❌ プロジェクト一覧取得失敗: {data}")
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            print(f"レスポンス: {response.text}")
            
    except Exception as e:
        print(f"❌ プロジェクト一覧取得エラー: {e}")
    
    # 3. サービス作成の詳細エラーを調査
    print("\n3. サービス作成詳細エラー調査...")
    
    # まずプロジェクトを作成
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
        "name": f"debugroot{int(time.time())}",
        "description": "根本原因調査用プロジェクト"
    }
    
    payload = {
        "query": create_query,
        "variables": variables
    }
    
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
    
    # 4. 異なるサービス作成方法を詳細にテスト
    print("\n4. サービス作成方法詳細テスト...")
    
    # 方法1: 基本的なサービス作成
    print("\n   方法1: 基本的なサービス作成")
    service_create_query1 = """
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
        "query": service_create_query1,
        "variables": variables
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"   ステータスコード: {response.status_code}")
        print(f"   レスポンス: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['serviceCreate']:
                service = data['data']['serviceCreate']
                print(f"   ✅ 成功: {service['name']} (ID: {service['id']})")
            else:
                print(f"   ❌ 失敗: {data}")
        else:
            print(f"   ❌ HTTPエラー: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ エラー: {e}")
    
    # 方法2: 異なるソース形式
    print("\n   方法2: 異なるソース形式")
    source_formats = [
        "github://kikuchi-mizuki/task-bot",
        "git@github.com:kikuchi-mizuki/task-bot.git",
        "kikuchi-mizuki/task-bot"
    ]
    
    for i, source in enumerate(source_formats, 1):
        print(f"     形式{i}: {source}")
        
        variables = {
            "projectId": project_id,
            "source": source
        }
        
        payload = {
            "query": service_create_query1,
            "variables": variables
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            print(f"     ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']['serviceCreate']:
                    service = data['data']['serviceCreate']
                    print(f"     ✅ 成功: {service['name']} (ID: {service['id']})")
                    break
                else:
                    print(f"     ❌ 失敗: {data}")
            else:
                print(f"     ❌ HTTPエラー: {response.status_code}")
                
        except Exception as e:
            print(f"     ❌ エラー: {e}")
    
    # 5. GitHubリポジトリのアクセス権限を確認
    print("\n5. GitHubリポジトリアクセス権限確認...")
    
    github_url = "https://api.github.com/repos/kikuchi-mizuki/task-bot"
    
    try:
        response = requests.get(github_url, timeout=30)
        print(f"GitHub API ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            repo_data = response.json()
            print(f"✅ GitHubリポジトリアクセス成功")
            print(f"   リポジトリ名: {repo_data['name']}")
            print(f"   プライベート: {repo_data['private']}")
            print(f"   フォーク: {repo_data['fork']}")
            print(f"   デフォルトブランチ: {repo_data['default_branch']}")
        else:
            print(f"❌ GitHubリポジトリアクセス失敗: {response.status_code}")
            print(f"レスポンス: {response.text}")
            
    except Exception as e:
        print(f"❌ GitHubリポジトリアクセスエラー: {e}")
    
    # 6. Railway APIのスキーマを確認
    print("\n6. Railway APIスキーマ確認...")
    
    schema_query = """
    query IntrospectionQuery {
        __schema {
            mutationType {
                fields {
                    name
                    description
                    args {
                        name
                        type {
                            name
                            kind
                            ofType {
                                name
                                kind
                            }
                        }
                    }
                }
            }
        }
    }
    """
    
    payload = {
        "query": schema_query
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"スキーマ確認 ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['__schema']:
                mutations = data['data']['__schema']['mutationType']['fields']
                service_mutations = [m for m in mutations if 'service' in m['name'].lower()]
                print(f"✅ サービス関連ミューテーション: {[m['name'] for m in service_mutations]}")
                
                # serviceCreateの詳細を確認
                service_create = [m for m in mutations if m['name'] == 'serviceCreate']
                if service_create:
                    mutation = service_create[0]
                    print(f"serviceCreate詳細:")
                    print(f"  説明: {mutation['description']}")
                    print(f"  引数:")
                    for arg in mutation['args']:
                        arg_type = arg['type']
                        type_name = arg_type['name'] or arg_type['ofType']['name'] if arg_type['ofType'] else 'Unknown'
                        print(f"    - {arg['name']}: {type_name}")
            else:
                print(f"❌ スキーマ取得失敗: {data}")
        else:
            print(f"❌ スキーマ確認HTTPエラー: {response.status_code}")
            
    except Exception as e:
        print(f"❌ スキーマ確認エラー: {e}")

if __name__ == "__main__":
    debug_railway_api_root_cause() 