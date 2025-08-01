#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RailwayプロジェクトIDを確認するスクリプト
"""

import os
import requests
import json

def check_railway_project_id():
    """RailwayプロジェクトIDを確認"""
    try:
        print("=== RailwayプロジェクトID確認 ===")
        
        # 現在の環境変数を確認
        railway_token = os.getenv('RAILWAY_TOKEN')
        railway_project_id = os.getenv('RAILWAY_PROJECT_ID')
        base_domain = os.getenv('BASE_DOMAIN', 'lp-production-9e2c.up.railway.app')
        
        print(f"📊 現在の設定:")
        print(f"  RAILWAY_TOKEN: {'設定済み' if railway_token else '未設定'}")
        print(f"  RAILWAY_PROJECT_ID: {railway_project_id or '未設定'}")
        print(f"  BASE_DOMAIN: {base_domain}")
        
        if not railway_token:
            print("\n❌ RAILWAY_TOKENが設定されていません")
            print("以下の手順で設定してください:")
            print("1. https://railway.app/dashboard にログイン")
            print("2. 右上のプロフィールアイコン → Account Settings → API")
            print("3. Generate Token でトークンを生成")
            print("4. Railwayダッシュボードの Variables で設定")
            return
        
        # Railway APIでプロジェクト一覧を取得
        headers = {
            'Authorization': f'Bearer {railway_token}',
            'Content-Type': 'application/json'
        }
        
        query = """
        query {
            projects {
                id
                name
                description
                createdAt
            }
        }
        """
        
        response = requests.post(
            'https://backboard.railway.app/graphql/v2',
            headers=headers,
            json={'query': query},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'projects' in data['data']:
                projects = data['data']['projects']
                
                print(f"\n📋 利用可能なプロジェクト ({len(projects)}件):")
                for i, project in enumerate(projects, 1):
                    print(f"  {i}. {project['name']}")
                    print(f"     ID: {project['id']}")
                    print(f"     説明: {project['description'] or 'なし'}")
                    print(f"     作成日: {project['createdAt']}")
                    print()
                
                # 現在のドメインに一致するプロジェクトを探す
                matching_project = None
                for project in projects:
                    if 'lp-production' in project['name'].lower():
                        matching_project = project
                        break
                
                if matching_project:
                    print(f"🎯 推奨プロジェクトID: {matching_project['id']}")
                    print(f"   プロジェクト名: {matching_project['name']}")
                    
                    if railway_project_id != matching_project['id']:
                        print(f"\n⚠️ 現在の設定と推奨設定が異なります")
                        print(f"   現在: {railway_project_id or '未設定'}")
                        print(f"   推奨: {matching_project['id']}")
                else:
                    print("⚠️ 現在のドメインに一致するプロジェクトが見つかりません")
                    
            else:
                print("❌ プロジェクト情報の取得に失敗しました")
        else:
            print(f"❌ Railway APIエラー: {response.status_code}")
            print(f"レスポンス: {response.text}")
            
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    check_railway_project_id() 