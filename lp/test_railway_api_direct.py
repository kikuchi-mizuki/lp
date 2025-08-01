#!/usr/bin/env python3
"""
Railway API GraphQLエンドポイントの直接テスト
"""

import requests
import json
import os

def test_railway_api():
    """Railway APIのGraphQLエンドポイントをテスト"""
    
    # 環境変数から設定を取得
    railway_token = "727e6c11-507b-4b5f-9f8c-1e90c266d730"
    
    print("=== Railway API GraphQL 直接テスト ===")
    print(f"Railway Token: {railway_token[:8]}...")
    
    # GraphQLエンドポイント
    url = "https://backboard.railway.app/graphql/v2"
    
    # ヘッダー
    headers = {
        "Authorization": f"Bearer {railway_token}",
        "Content-Type": "application/json"
    }
    
    # 1. プロジェクト一覧を取得するクエリ
    projects_query = """
    query GetProjects {
        projects {
            id
            name
            description
        }
    }
    """
    
    payload = {
        "query": projects_query
    }
    
    print("\n1. プロジェクト一覧取得テスト...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンス: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'projects' in data['data']:
                projects = data['data']['projects']
                print(f"✅ プロジェクト一覧取得成功: {len(projects)}件のプロジェクト")
                for project in projects[:3]:  # 最初の3件を表示
                    print(f"  - {project['name']} (ID: {project['id']})")
            else:
                print(f"❌ プロジェクト一覧取得失敗: {data}")
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            
    except Exception as e:
        print(f"❌ リクエストエラー: {e}")
    
    # 2. 新しいプロジェクト作成テスト
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
        "name": f"test-project-{int(__import__('time').time())}",
        "description": "Railway API テスト用プロジェクト"
    }
    
    payload = {
        "query": create_query,
        "variables": variables
    }
    
    print("\n2. プロジェクト作成テスト...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンス: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['projectCreate']:
                project = data['data']['projectCreate']
                print(f"✅ プロジェクト作成成功: {project['name']} (ID: {project['id']})")
            else:
                print(f"❌ プロジェクト作成失敗: {data}")
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            
    except Exception as e:
        print(f"❌ リクエストエラー: {e}")

if __name__ == "__main__":
    test_railway_api() 