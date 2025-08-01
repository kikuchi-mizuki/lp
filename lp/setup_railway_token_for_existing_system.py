#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
既存システムにRailwayトークンを設定するスクリプト
"""

import os
import sys
import requests
import json

def setup_railway_token_for_existing_system():
    """既存システムにRailwayトークンを設定"""
    try:
        print("=== 既存システムにRailwayトークン設定 ===")
        
        print("📋 既存システム (lp-production-9e2c) にRailwayトークンを設定します")
        print("\n手順:")
        print("1. https://railway.app/dashboard にログイン")
        print("2. lp-production-9e2c プロジェクトを選択")
        print("3. Variables タブをクリック")
        print("4. 以下の変数を追加:")
        print("   - RAILWAY_TOKEN")
        print("   - RAILWAY_PROJECT_ID")
        print("   - BASE_DOMAIN")
        
        # Railwayトークンを取得
        print("\n📋 Railwayトークンを取得してください:")
        print("1. Railwayダッシュボードで右上のプロフィールアイコンをクリック")
        print("2. Account Settings → API")
        print("3. Generate Token でトークンを生成")
        print("4. 生成されたトークンをコピー")
        
        railway_token = input("\nRailwayトークンを入力してください: ").strip()
        
        if not railway_token:
            print("❌ Railwayトークンが入力されていません")
            return False
        
        # プロジェクトIDを取得
        print("\n📋 RailwayプロジェクトIDを取得してください:")
        print("1. Railwayダッシュボードでlp-production-9e2cプロジェクトを開く")
        print("2. URLからプロジェクトIDを確認")
        print("   例: https://railway.app/project/3e9475ce-ff6a-4443-ab6c-4eb21b7f4017")
        print("   プロジェクトID: 3e9475ce-ff6a-4443-ab6c-4eb21b7f4017")
        
        railway_project_id = input("\nRailwayプロジェクトIDを入力してください: ").strip()
        
        if not railway_project_id:
            print("❌ RailwayプロジェクトIDが入力されていません")
            return False
        
        # ベースドメイン
        base_domain = "lp-production-9e2c.up.railway.app"
        
        print(f"\n📊 設定内容:")
        print(f"  RAILWAY_TOKEN: {'設定済み' if railway_token else '未設定'}")
        print(f"  RAILWAY_PROJECT_ID: {railway_project_id}")
        print(f"  BASE_DOMAIN: {base_domain}")
        
        print(f"\n📋 既存システムのVariablesページで以下の変数を追加してください:")
        print(f"  RAILWAY_TOKEN = {railway_token}")
        print(f"  RAILWAY_PROJECT_ID = {railway_project_id}")
        print(f"  BASE_DOMAIN = {base_domain}")
        
        # ローカル環境にも設定
        env_file = '.env'
        env_content = f"""# 既存システム用Railway設定
RAILWAY_TOKEN={railway_token}
RAILWAY_PROJECT_ID={railway_project_id}
BASE_DOMAIN={base_domain}

# その他の環境変数（必要に応じて追加）
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"\n✅ ローカル設定を{env_file}に保存しました")
        
        # 環境変数としても設定
        os.environ['RAILWAY_TOKEN'] = railway_token
        os.environ['RAILWAY_PROJECT_ID'] = railway_project_id
        os.environ['BASE_DOMAIN'] = base_domain
        
        print("✅ ローカル環境変数としても設定しました")
        
        return True
        
    except Exception as e:
        print(f"❌ 設定エラー: {e}")
        return False

def test_railway_connection():
    """Railway接続をテスト"""
    try:
        print("\n=== Railway接続テスト ===")
        
        railway_token = os.getenv('RAILWAY_TOKEN')
        railway_project_id = os.getenv('RAILWAY_PROJECT_ID')
        
        if not railway_token or not railway_project_id:
            print("❌ Railway設定が不完全です")
            return False
        
        headers = {
            'Authorization': f'Bearer {railway_token}',
            'Content-Type': 'application/json'
        }
        
        query = """
        query {
            me {
                id
                email
                name
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
            if 'data' in data and 'me' in data['data']:
                user = data['data']['me']
                print(f"✅ Railway接続成功")
                print(f"  ユーザー: {user['name']} ({user['email']})")
                return True
            else:
                print("❌ Railwayトークンが無効です")
                return False
        else:
            print(f"❌ Railway APIエラー: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 接続テストエラー: {e}")
        return False

def verify_existing_system():
    """既存システムの設定を確認"""
    try:
        print("\n=== 既存システム設定確認 ===")
        
        base_url = "https://lp-production-9e2c.up.railway.app"
        
        # ヘルスチェック
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ 既存システムに正常に接続できました")
            
            # 環境変数確認
            try:
                response = requests.get(f"{base_url}/debug/railway_env", timeout=10)
                if response.status_code == 200:
                    env_data = response.json()
                    
                    railway_token = env_data.get('RAILWAY_TOKEN')
                    railway_project_id = env_data.get('RAILWAY_PROJECT_ID')
                    
                    if railway_token and railway_project_id:
                        print("✅ 既存システムにRailwayトークンが設定されています")
                        return True
                    else:
                        print("❌ 既存システムにRailwayトークンが設定されていません")
                        return False
                else:
                    print(f"⚠️ 環境変数確認エラー: {response.status_code}")
                    return False
            except Exception as e:
                print(f"⚠️ 環境変数確認エラー: {e}")
                return False
        else:
            print(f"❌ 既存システム接続エラー: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 既存システム確認エラー: {e}")
        return False

if __name__ == "__main__":
    if setup_railway_token_for_existing_system():
        print("\n🎉 Railwayトークン設定が完了しました！")
        
        # 接続テスト
        if test_railway_connection():
            print("\n✅ Railway接続テストが成功しました！")
            
            print("\n📝 次のステップ:")
            print("1. 既存システムのVariablesページで上記の変数を追加")
            print("2. 既存システムを再デプロイ")
            print("3. 企業登録フォームでテスト")
            print("\n💡 既存システムに設定後、企業登録時に自動的にRailwayトークンが使用されます")
        else:
            print("\n⚠️ Railway接続テストに失敗しました。")
            print("トークンが正しいか確認してください。")
    else:
        print("\n❌ Railwayトークン設定に失敗しました。") 