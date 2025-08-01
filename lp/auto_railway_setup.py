#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Railwayトークン自動設定スクリプト
"""

import os
import sys
import requests
import json

def auto_railway_setup():
    """Railwayトークンを自動設定"""
    try:
        print("=== Railwayトークン自動設定 ===")
        
        # 現在の設定を確認
        railway_token = os.getenv('RAILWAY_TOKEN')
        railway_project_id = os.getenv('RAILWAY_PROJECT_ID')
        
        if railway_token and railway_project_id:
            print("✅ Railwayトークンは既に設定されています")
            print(f"  RAILWAY_TOKEN: {'設定済み'}")
            print(f"  RAILWAY_PROJECT_ID: {railway_project_id}")
            return True
        
        print("🚀 Railwayトークンを自動設定します...")
        
        # 方法1: 既存システムから取得を試行
        print("\n📋 方法1: 既存システムから取得を試行中...")
        
        base_url = "https://lp-production-9e2c.up.railway.app"
        
        try:
            # ヘルスチェック
            response = requests.get(f"{base_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ システムに正常に接続できました")
                
                # 環境変数取得を試行
                try:
                    response = requests.get(f"{base_url}/debug/railway_env", timeout=10)
                    if response.status_code == 200:
                        env_data = response.json()
                        
                        railway_token = env_data.get('RAILWAY_TOKEN')
                        railway_project_id = env_data.get('RAILWAY_PROJECT_ID')
                        base_domain = env_data.get('BASE_DOMAIN')
                        
                        if railway_token and railway_project_id:
                            print("✅ 既存システムからRailwayトークンを取得しました")
                            save_railway_config(railway_token, railway_project_id, base_domain)
                            return True
                        else:
                            print("⚠️ 既存システムにRailwayトークンが設定されていません")
                    else:
                        print(f"⚠️ 環境変数取得エラー: {response.status_code}")
                except Exception as e:
                    print(f"⚠️ 環境変数取得エラー: {e}")
            else:
                print(f"⚠️ システム接続エラー: {response.status_code}")
        except Exception as e:
            print(f"⚠️ システム接続エラー: {e}")
        
        # 方法2: デフォルト設定を使用
        print("\n📋 方法2: デフォルト設定を使用...")
        
        # 一般的なRailwayプロジェクトIDのパターンを試行
        default_project_id = "3e9475ce-ff6a-4443-ab6c-4eb21b7f4017"  # 例
        base_domain = "lp-production-9e2c.up.railway.app"
        
        print("⚠️ デフォルト設定を使用します")
        print("注意: この設定は動作しない可能性があります")
        print("手動で正しいトークンを設定することを推奨します")
        
        # ユーザーに確認
        confirm = input("\nデフォルト設定を使用しますか？ (yes/no): ").strip().lower()
        if confirm == 'yes':
            # ダミートークン（実際には動作しません）
            dummy_token = "dummy_railway_token_for_testing"
            save_railway_config(dummy_token, default_project_id, base_domain)
            print("⚠️ ダミートークンを設定しました（実際の使用には正しいトークンが必要です）")
            return True
        else:
            print("❌ 自動設定をキャンセルしました")
            return False
            
    except Exception as e:
        print(f"❌ 自動設定エラー: {e}")
        return False

def save_railway_config(railway_token, railway_project_id, base_domain):
    """Railway設定を保存"""
    try:
        # .envファイルに保存
        env_file = '.env'
        env_content = f"""# Railway設定（自動設定）
RAILWAY_TOKEN={railway_token}
RAILWAY_PROJECT_ID={railway_project_id}
BASE_DOMAIN={base_domain}

# その他の環境変数（必要に応じて追加）
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Railway設定を{env_file}に保存しました")
        
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
        
        return True
        
    except Exception as e:
        print(f"❌ 設定保存エラー: {e}")
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
        
        # ダミートークンの場合はスキップ
        if railway_token == "dummy_railway_token_for_testing":
            print("⚠️ ダミートークンのため接続テストをスキップします")
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
    if auto_railway_setup():
        print("\n🎉 Railwayトークン自動設定が完了しました！")
        
        # 接続テスト
        if test_railway_connection():
            print("\n✅ すべての設定が正常に完了しました！")
            print("\n📝 次のステップ:")
            print("1. 企業登録フォームにアクセス")
            print("2. 企業情報を入力")
            print("3. フォーム送信時にRailwayプロジェクトが自動複製されます")
        else:
            print("\n⚠️ 接続テストに失敗しました。")
            print("手動で正しいRailwayトークンを設定してください:")
            print("python quick_railway_setup.py")
    else:
        print("\n❌ Railwayトークン自動設定に失敗しました。")
        print("手動で設定してください: python quick_railway_setup.py") 