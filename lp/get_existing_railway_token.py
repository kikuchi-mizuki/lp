#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
既存のRailwayシステムからトークンを取得するスクリプト
"""

import os
import requests
import json

def get_existing_railway_token():
    """既存のRailwayシステムからトークンを取得"""
    try:
        print("=== 既存Railwayシステムからトークン取得 ===")
        
        # 現在のシステムのURL
        base_url = "https://lp-production-9e2c.up.railway.app"
        
        print(f"📊 対象システム: {base_url}")
        
        # システムの環境変数を確認
        print("\n📋 システムの環境変数を確認中...")
        
        # ヘルスチェック
        try:
            response = requests.get(f"{base_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ システムに正常に接続できました")
            else:
                print(f"⚠️ システム接続エラー: {response.status_code}")
        except Exception as e:
            print(f"❌ システム接続エラー: {e}")
            return False
        
        # Railway環境変数の確認
        try:
            response = requests.get(f"{base_url}/debug/railway_env", timeout=10)
            if response.status_code == 200:
                env_data = response.json()
                print("✅ システムの環境変数を取得しました")
                
                # Railway関連の環境変数を確認
                railway_token = env_data.get('RAILWAY_TOKEN')
                railway_project_id = env_data.get('RAILWAY_PROJECT_ID')
                base_domain = env_data.get('BASE_DOMAIN')
                
                if railway_token and railway_project_id:
                    print(f"\n📊 取得した設定:")
                    print(f"  RAILWAY_TOKEN: {'設定済み' if railway_token else '未設定'}")
                    print(f"  RAILWAY_PROJECT_ID: {railway_project_id}")
                    print(f"  BASE_DOMAIN: {base_domain}")
                    
                    # .envファイルに保存
                    env_file = '.env'
                    env_content = f"""# 既存Railwayシステムから取得した設定
RAILWAY_TOKEN={railway_token}
RAILWAY_PROJECT_ID={railway_project_id}
BASE_DOMAIN={base_domain}

# その他の環境変数（必要に応じて追加）
"""
                    
                    with open(env_file, 'w') as f:
                        f.write(env_content)
                    
                    print(f"\n✅ 設定を{env_file}に保存しました")
                    
                    # 環境変数としても設定
                    os.environ['RAILWAY_TOKEN'] = railway_token
                    os.environ['RAILWAY_PROJECT_ID'] = railway_project_id
                    os.environ['BASE_DOMAIN'] = base_domain
                    
                    print("✅ 環境変数としても設定しました")
                    
                    return True
                else:
                    print("❌ Railwayトークンが設定されていません")
                    return False
                    
            else:
                print(f"❌ 環境変数取得エラー: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 環境変数取得エラー: {e}")
            return False
            
    except Exception as e:
        print(f"❌ エラー: {e}")
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

if __name__ == "__main__":
    if get_existing_railway_token():
        print("\n🎉 既存システムからRailwayトークンを取得しました！")
        
        # 接続テスト
        if test_railway_connection():
            print("\n✅ すべての設定が正常に完了しました！")
            print("\n📝 次のステップ:")
            print("1. 企業登録フォームにアクセス")
            print("2. 企業情報を入力")
            print("3. フォーム送信時に既存のRailwayトークンでプロジェクトが自動複製されます")
            print("\n💡 既存システムのRailwayトークンを使用するため、追加設定は不要です。")
        else:
            print("\n⚠️ 接続テストに失敗しました。設定を確認してください。")
    else:
        print("\n❌ 既存システムからRailwayトークンの取得に失敗しました。")
        print("手動で設定してください: python quick_railway_setup.py") 