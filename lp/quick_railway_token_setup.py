#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Railwayトークン素早く設定スクリプト
"""

import os
import sys

def quick_railway_token_setup():
    """Railwayトークンを素早く設定"""
    try:
        print("=== Railwayトークン素早く設定 ===")
        
        print("📋 手順:")
        print("1. RailwayダッシュボードのTokensページで「Create」をクリック")
        print("2. 生成されたトークンをコピー")
        print("3. 以下に入力してください")
        
        # Railwayトークンを入力
        railway_token = input("\n生成されたRailwayトークンを入力してください: ").strip()
        
        if not railway_token:
            print("❌ Railwayトークンが入力されていません")
            return False
        
        # プロジェクトIDを入力
        print("\n📋 RailwayプロジェクトIDを取得してください:")
        print("1. Railwayダッシュボードでlp-production-9e2cプロジェクトを開く")
        print("2. URLからプロジェクトIDを確認")
        print("   例: https://railway.app/project/3e9475ce-ff6a-4443-ab6c-4eb21b7f4017")
        
        railway_project_id = input("\nプロジェクトIDを入力してください: ").strip()
        
        if not railway_project_id:
            print("❌ プロジェクトIDが入力されていません")
            return False
        
        # ベースドメイン
        base_domain = "lp-production-9e2c.up.railway.app"
        
        # .envファイルに保存
        env_file = '.env'
        env_content = f"""# Railway設定
RAILWAY_TOKEN={railway_token}
RAILWAY_PROJECT_ID={railway_project_id}
BASE_DOMAIN={base_domain}

# その他の環境変数（必要に応じて追加）
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"\n✅ Railway設定を{env_file}に保存しました")
        
        # 環境変数としても設定
        os.environ['RAILWAY_TOKEN'] = railway_token
        os.environ['RAILWAY_PROJECT_ID'] = railway_project_id
        os.environ['BASE_DOMAIN'] = base_domain
        
        print("✅ 環境変数としても設定しました")
        
        # 設定確認
        print(f"\n📊 設定内容:")
        print(f"  RAILWAY_TOKEN: {'設定済み' if os.getenv('RAILWAY_TOKEN') else '未設定'}")
        print(f"  RAILWAY_PROJECT_ID: {os.getenv('RAILWAY_PROJECT_ID') or '未設定'}")
        print(f"  BASE_DOMAIN: {os.getenv('BASE_DOMAIN') or '未設定'}")
        
        print(f"\n📋 既存システムのVariablesページで以下の変数を追加してください:")
        print(f"  RAILWAY_TOKEN = {railway_token}")
        print(f"  RAILWAY_PROJECT_ID = {railway_project_id}")
        print(f"  BASE_DOMAIN = {base_domain}")
        
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
        
        import requests
        
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

if __name__ == "__main__":
    if quick_railway_token_setup():
        print("\n🎉 Railwayトークン設定が完了しました！")
        
        # 接続テスト
        if test_railway_connection():
            print("\n✅ Railway接続テストが成功しました！")
            print("\n📝 次のステップ:")
            print("1. 既存システムのVariablesページで上記の変数を追加")
            print("2. 既存システムを再デプロイ")
            print("3. 企業登録フォームでテスト")
            print("\n💡 これで企業登録時に自動的にRailwayプロジェクトが複製されます")
        else:
            print("\n⚠️ Railway接続テストに失敗しました。")
            print("トークンが正しいか確認してください。")
    else:
        print("\n❌ Railwayトークン設定に失敗しました。") 