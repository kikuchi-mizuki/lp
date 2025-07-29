#!/usr/bin/env python3
import os
import requests
import json

def get_railway_db_url():
    """RailwayのデータベースURLを取得"""
    try:
        print("=== RailwayデータベースURL取得 ===")
        
        # Railway APIトークン（環境変数から取得）
        railway_token = os.getenv('RAILWAY_TOKEN')
        if not railway_token:
            print("❌ RAILWAY_TOKEN環境変数が設定されていません")
            print("RailwayのWebサイトからAPIトークンを取得して設定してください")
            return None
        
        # プロジェクトID（環境変数から取得）
        project_id = os.getenv('RAILWAY_PROJECT_ID')
        if not project_id:
            print("❌ RAILWAY_PROJECT_ID環境変数が設定されていません")
            print("RailwayのプロジェクトページからプロジェクトIDを取得して設定してください")
            return None
        
        # Railway APIでプロジェクトのサービスを取得
        headers = {
            'Authorization': f'Bearer {railway_token}',
            'Content-Type': 'application/json'
        }
        
        url = f'https://backboard.railway.app/graphql/v2'
        
        # GraphQLクエリ
        query = '''
        query GetProject($id: String!) {
            project(id: $id) {
                services {
                    nodes {
                        id
                        name
                        serviceInstances {
                            nodes {
                                id
                                environment {
                                    variables {
                                        nodes {
                                            name
                                            value
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        '''
        
        variables = {
            'id': project_id
        }
        
        response = requests.post(url, headers=headers, json={
            'query': query,
            'variables': variables
        })
        
        if response.status_code == 200:
            data = response.json()
            
            if 'errors' in data:
                print(f"❌ GraphQLエラー: {data['errors']}")
                return None
            
            project = data['data']['project']
            services = project['services']['nodes']
            
            print(f"📋 プロジェクト内のサービス:")
            for service in services:
                service_name = service['name']
                print(f"  - {service_name}")
                
                instances = service['serviceInstances']['nodes']
                for instance in instances:
                    env_vars = instance['environment']['variables']['nodes']
                    
                    # DATABASE_URLを探す
                    for var in env_vars:
                        if var['name'] == 'DATABASE_URL':
                            db_url = var['value']
                            print(f"    📊 DATABASE_URL: {db_url}")
                            return db_url
            
            print("❌ DATABASE_URLが見つかりませんでした")
            return None
            
        else:
            print(f"❌ APIリクエストエラー: {response.status_code}")
            print(f"レスポンス: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    db_url = get_railway_db_url()
    if db_url:
        print(f"\n✅ データベースURL取得成功:")
        print(f"DATABASE_URL={db_url}")
    else:
        print(f"\n❌ データベースURL取得失敗") 