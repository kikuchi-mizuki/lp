#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Railwayプロジェクト作成テストスクリプト
"""

import os
import requests
import json
import time
from datetime import datetime

def test_railway_project_creation():
    """Railwayプロジェクト作成をテスト"""
    try:
        print("=== Railwayプロジェクト作成テスト ===")
        
        # 環境変数を確認
        railway_token = os.getenv('RAILWAY_TOKEN')
        railway_project_id = os.getenv('RAILWAY_PROJECT_ID')
        base_domain = os.getenv('BASE_DOMAIN')
        
        print(f"📊 環境変数確認:")
        print(f"  RAILWAY_TOKEN: {'設定済み' if railway_token else '未設定'}")
        print(f"  RAILWAY_PROJECT_ID: {railway_project_id}")
        print(f"  BASE_DOMAIN: {base_domain}")
        
        if not railway_token:
            print("❌ RAILWAY_TOKENが設定されていません")
            return False
        
        # 新しいプロジェクト名を生成
        new_project_name = f"ai-schedule-test-{int(time.time())}"
        
        print(f"\n🚀 新しいプロジェクト作成開始:")
        print(f"  プロジェクト名: {new_project_name}")
        
        # Railway APIでプロジェクトを作成
        url = "https://backboard.railway.app/graphql/v2"
        headers = {
            'Authorization': f'Bearer {railway_token}',
            'Content-Type': 'application/json'
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
            "name": new_project_name,
            "description": f"テストプロジェクト - 作成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        payload = {
            "query": create_query,
            "variables": variables
        }
        
        print(f"📡 APIリクエスト送信中...")
        print(f"  URL: {url}")
        print(f"  ヘッダー: {headers}")
        print(f"  ペイロード: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"\n📊 レスポンス:")
        print(f"  ステータスコード: {response.status_code}")
        print(f"  レスポンスヘッダー: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  レスポンスデータ: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if 'data' in data and data['data']['projectCreate']:
                new_project = data['data']['projectCreate']
                print(f"\n✅ プロジェクト作成成功!")
                print(f"  プロジェクトID: {new_project['id']}")
                print(f"  プロジェクト名: {new_project['name']}")
                print(f"  説明: {new_project['description']}")
                
                # プロジェクトのURLを表示
                project_url = f"https://railway.app/project/{new_project['id']}"
                print(f"  プロジェクトURL: {project_url}")
                
                return True
            else:
                print(f"\n❌ プロジェクト作成失敗:")
                print(f"  エラー: {data}")
                return False
        else:
            print(f"\n❌ APIリクエスト失敗:")
            print(f"  エラー: {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False

if __name__ == "__main__":
    test_railway_project_creation() 