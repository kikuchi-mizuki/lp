#!/usr/bin/env python3
"""
Railwayのデバッグエンドポイントを使って問題を確認するスクリプト
"""

import requests
import json

def check_railway_debug():
    """Railwayのデバッグ情報を確認"""
    
    # RailwayのアプリURL（実際のURLに変更してください）
    railway_url = "https://lp-production-9e2c.up.railway.app"
    
    print("🔍 Railwayデバッグ情報確認")
    print("=" * 50)
    
    try:
        # 1. アプリの健康状態を確認
        print("📊 ステップ1: アプリの健康状態を確認")
        health_response = requests.get(f"{railway_url}/", timeout=10)
        print(f"   ステータスコード: {health_response.status_code}")
        print(f"   レスポンス: {health_response.text[:200]}...")
        
        # 2. エラーログを確認
        print("\n📋 ステップ2: エラーログを確認")
        try:
            error_response = requests.get(f"{railway_url}/error_log", timeout=10)
            if error_response.status_code == 200:
                print("   エラーログ:")
                print(f"   {error_response.text[:500]}...")
            else:
                print(f"   エラーログ取得失敗: {error_response.status_code}")
        except Exception as e:
            print(f"   エラーログ取得エラー: {e}")
        
        # 3. 最近のユーザー一覧を確認
        print("\n👥 ステップ3: 最近のユーザー一覧を確認")
        try:
            users_response = requests.get(f"{railway_url}/debug/users", timeout=10)
            if users_response.status_code == 200:
                users_data = users_response.json()
                print("   最近のユーザー:")
                for user in users_data.get('users', [])[:5]:
                    print(f"   - ID: {user.get('id')}, メール: {user.get('email')}, LINE_ID: {user.get('line_user_id')}")
            else:
                print(f"   ユーザー一覧取得失敗: {users_response.status_code}")
        except Exception as e:
            print(f"   ユーザー一覧取得エラー: {e}")
        
        # 4. 環境変数の確認（一部）
        print("\n🔧 ステップ4: 環境変数の確認")
        try:
            env_response = requests.get(f"{railway_url}/debug/environment", timeout=10)
            if env_response.status_code == 200:
                env_data = env_response.json()
                print("   環境変数:")
                print(f"   - DATABASE_URL: {'設定済み' if env_data.get('DATABASE_URL') else '未設定'}")
                print(f"   - STRIPE_SECRET_KEY: {'設定済み' if env_data.get('STRIPE_SECRET_KEY') else '未設定'}")
                print(f"   - LINE_CHANNEL_ACCESS_TOKEN: {'設定済み' if env_data.get('LINE_CHANNEL_ACCESS_TOKEN') else '未設定'}")
            else:
                print(f"   環境変数取得失敗: {env_response.status_code}")
        except Exception as e:
            print(f"   環境変数取得エラー: {e}")
        
    except Exception as e:
        print(f"❌ Railway接続エラー: {e}")

def check_specific_user(line_user_id):
    """特定のユーザーの詳細情報を確認"""
    
    railway_url = "https://lp-production-9e2c.up.railway.app"
    
    print(f"\n🔍 ユーザー詳細確認: {line_user_id}")
    print("=" * 50)
    
    try:
        # ユーザーの詳細情報を取得
        user_response = requests.get(f"{railway_url}/debug/user/{line_user_id}", timeout=10)
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            print("✅ ユーザー情報取得成功:")
            print(f"   データベース情報: {user_data.get('database_info', 'なし')}")
            print(f"   決済状況: {user_data.get('payment_status', 'なし')}")
            print(f"   Stripe情報: {user_data.get('stripe_info', 'なし')}")
            print(f"   エラー: {user_data.get('error', 'なし')}")
        else:
            print(f"❌ ユーザー情報取得失敗: {user_response.status_code}")
            print(f"   レスポンス: {user_response.text}")
            
    except Exception as e:
        print(f"❌ ユーザー情報取得エラー: {e}")

if __name__ == "__main__":
    # Railwayの全体的な状況を確認
    check_railway_debug()
    
    # 特定のユーザーIDを指定して確認（実際のLINEユーザーIDに変更してください）
    print("\n" + "="*60)
    print("特定のユーザーを確認する場合は、以下のように実行してください:")
    print("python check_railway_debug.py <LINE_USER_ID>")
    print("例: python check_railway_debug.py U1234567890abcdef") 