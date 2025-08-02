#!/usr/bin/env python3
"""
GitHub API統合テスト
"""

import requests
import json
import time

def test_github_repo_access():
    """GitHubリポジトリへのアクセスをテスト"""
    
    print("=== GitHub API リポジトリアクセステスト ===")
    
    # GitHub APIエンドポイント
    repo_url = "https://api.github.com/repos/kikuchi-mizuki/task-bot"
    
    print(f"1. リポジトリ情報を取得: {repo_url}")
    
    try:
        response = requests.get(repo_url, timeout=30)
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            repo_data = response.json()
            print(f"✅ リポジトリアクセス成功")
            print(f"   リポジトリ名: {repo_data['name']}")
            print(f"   説明: {repo_data['description']}")
            print(f"   言語: {repo_data['language']}")
            print(f"   デフォルトブランチ: {repo_data['default_branch']}")
            print(f"   クローンURL: {repo_data['clone_url']}")
            print(f"   SSH URL: {repo_data['ssh_url']}")
            return True
        else:
            print(f"❌ リポジトリアクセス失敗: {response.status_code}")
            print(f"レスポンス: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ リポジトリアクセスエラー: {e}")
        return False

def test_railway_github_integration():
    """RailwayとGitHubの統合をテスト"""
    
    railway_token = "727e6c11-507b-4b5f-9f8c-1e90c266d730"
    
    print("\n=== Railway GitHub統合テスト ===")
    
    # GraphQLエンドポイント
    url = "https://backboard.railway.app/graphql/v2"
    
    # ヘッダー
    headers = {
        "Authorization": f"Bearer {railway_token}",
        "Content-Type": "application/json"
    }
    
    # 1. プロジェクトを作成
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
        "name": f"test-github-integration-{int(time.time())}".replace("-", ""),
        "description": "GitHub統合テスト用プロジェクト"
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
            print(f"レスポンス: {data}")
            if 'data' in data and data['data'] and data['data']['projectCreate']:
                project = data['data']['projectCreate']
                project_id = project['id']
                print(f"✅ プロジェクト作成成功: {project['name']} (ID: {project_id})")
            else:
                print(f"❌ プロジェクト作成失敗: {data}")
                return
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            print(f"レスポンス: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ プロジェクト作成エラー: {e}")
        return
    
    # 2. 異なるソース形式でサービス作成を試行
    print("\n2. 異なるソース形式でサービス作成を試行...")
    
    source_formats = [
        "https://github.com/kikuchi-mizuki/task-bot",
        "github://kikuchi-mizuki/task-bot",
        "git@github.com:kikuchi-mizuki/task-bot.git",
        "kikuchi-mizuki/task-bot"
    ]
    
    for i, source in enumerate(source_formats, 1):
        print(f"\n   方法{i}: {source}")
        
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
            "source": source
        }
        
        payload = {
            "query": service_create_query,
            "variables": variables
        }
        
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
                print(f"   レスポンス: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ エラー: {e}")
    
    print("\n❌ すべての方法が失敗しました")
    return False

def test_railway_permissions():
    """Railway APIの権限をテスト"""
    
    railway_token = "727e6c11-507b-4b5f-9f8c-1e90c266d730"
    
    print("\n=== Railway API 権限テスト ===")
    
    url = "https://backboard.railway.app/graphql/v2"
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
        }
    }
    """
    
    payload = {
        "query": user_query
    }
    
    print("1. ユーザー情報取得...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['me']:
                user = data['data']['me']
                print(f"✅ ユーザー情報取得成功")
                print(f"   ID: {user['id']}")
                print(f"   メール: {user['email']}")
                print(f"   名前: {user['name']}")
            else:
                print(f"❌ ユーザー情報取得失敗: {data}")
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            
    except Exception as e:
        print(f"❌ ユーザー情報取得エラー: {e}")

if __name__ == "__main__":
    # 1. GitHubリポジトリアクセステスト
    github_access = test_github_repo_access()
    
    # 2. Railway権限テスト
    test_railway_permissions()
    
    # 3. Railway GitHub統合テスト
    if github_access:
        test_railway_github_integration()
    else:
        print("\n❌ GitHubリポジトリにアクセスできないため、Railway統合テストをスキップします") 