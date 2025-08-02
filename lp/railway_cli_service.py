#!/usr/bin/env python3
"""
Railway CLIを使用したサービス追加
"""

import subprocess
import json
import os
import time

def check_railway_cli():
    """Railway CLIがインストールされているかチェック"""
    try:
        result = subprocess.run(['railway', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Railway CLI: {result.stdout.strip()}")
            return True
        else:
            print("❌ Railway CLIが見つかりません")
            return False
    except FileNotFoundError:
        print("❌ Railway CLIがインストールされていません")
        return False

def login_railway_cli(token):
    """Railway CLIにログイン"""
    try:
        print("🔐 Railway CLIにログイン中...")
        result = subprocess.run(['railway', 'login', '--token', token], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Railway CLIログイン成功")
            return True
        else:
            print(f"❌ Railway CLIログイン失敗: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Railway CLIログインエラー: {e}")
        return False

def add_service_with_cli(project_id, source_repo):
    """Railway CLIを使用してサービスを追加"""
    try:
        print(f"🔧 Railway CLIでサービス追加開始: プロジェクト {project_id}")
        
        # プロジェクトを選択
        select_cmd = ['railway', 'link', '--project', project_id]
        result = subprocess.run(select_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ プロジェクト選択失敗: {result.stderr}")
            return None
        
        print("✅ プロジェクト選択成功")
        
        # サービスを追加
        add_cmd = ['railway', 'service', 'add', source_repo]
        result = subprocess.run(add_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Railway CLIでサービス追加成功")
            return {"success": True, "method": "railway_cli"}
        else:
            print(f"❌ Railway CLIでサービス追加失敗: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Railway CLIサービス追加エラー: {e}")
        return None

def test_railway_cli_method():
    """Railway CLIを使用したサービス追加をテスト"""
    
    railway_token = "727e6c11-507b-4b5f-9f8c-1e90c266d730"
    
    print("=== Railway CLI サービス追加テスト ===")
    
    # 1. Railway CLIの確認
    if not check_railway_cli():
        print("Railway CLIをインストールしてください:")
        print("npm install -g @railway/cli")
        return
    
    # 2. Railway CLIにログイン
    if not login_railway_cli(railway_token):
        return
    
    # 3. テスト用プロジェクトを作成（GraphQL APIを使用）
    print("\n3. テスト用プロジェクトを作成中...")
    
    import requests
    
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
        "name": f"test-cli-project-{int(time.time())}",
        "description": "Railway CLIテスト用プロジェクト"
    }
    
    payload = {
        "query": create_query,
        "variables": variables
    }
    
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
    
    # 4. Railway CLIでサービスを追加
    print("\n4. Railway CLIでサービスを追加中...")
    result = add_service_with_cli(project_id, "https://github.com/kikuchi-mizuki/task-bot")
    
    if result:
        print("✅ Railway CLIでのサービス追加テスト成功")
    else:
        print("❌ Railway CLIでのサービス追加テスト失敗")

if __name__ == "__main__":
    test_railway_cli_method() 