#!/usr/bin/env python3
import os
import urllib.parse
import socket
import ssl
import json

# 環境変数からDATABASE_URLを取得
def get_database_url():
    env_path = '/workspace/.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('DATABASE_URL='):
                    return line.split('=', 1)[1].strip()
    return None

def parse_database_url(url):
    """データベースURLをパースして接続情報を取得"""
    parsed = urllib.parse.urlparse(url)
    return {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path[1:],  # 先頭の/を除去
        'username': parsed.username,
        'password': parsed.password
    }

def check_status_via_http():
    """HTTPエンドポイント経由で状況を確認"""
    
    print("=== データベース状況確認（HTTP経由） ===\n")
    
    # データベースURL確認
    db_url = get_database_url()
    if not db_url:
        print("❌ DATABASE_URLが見つかりません")
        return
    
    db_info = parse_database_url(db_url)
    print(f"📊 接続先データベース:")
    print(f"   - ホスト: {db_info['host']}")
    print(f"   - ポート: {db_info['port']}")
    print(f"   - データベース: {db_info['database']}")
    print(f"   - ユーザー: {db_info['username']}")
    
    # アプリケーションのデバッグエンドポイントを呼び出す方法を提案
    print(f"\n🔍 確認方法:")
    print(f"   1. アプリケーションが動作中の場合、以下のエンドポイントにアクセス:")
    print(f"      https://lp-production-9e2c.up.railway.app/debug/status")
    
    print(f"\n   2. または以下のcurlコマンドで確認:")
    print(f"      curl https://lp-production-9e2c.up.railway.app/debug/companies")
    
    # 簡単なテスト接続を試す
    print(f"\n🌐 接続テスト:")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((db_info['host'], db_info['port']))
        sock.close()
        
        if result == 0:
            print(f"   ✅ データベースホストに接続可能")
        else:
            print(f"   ❌ データベースホストに接続できません")
    except Exception as e:
        print(f"   ❌ 接続テスト失敗: {e}")

def check_via_app_endpoint():
    """アプリケーションのデバッグエンドポイント経由で確認"""
    
    print(f"\n=== アプリケーション経由での確認 ===")
    
    try:
        import urllib.request
        
        # デバッグエンドポイントのURLリスト
        endpoints = [
            "https://lp-production-9e2c.up.railway.app/debug/companies",
            "https://lp-production-9e2c.up.railway.app/debug/contents",
            "https://lp-production-9e2c.up.railway.app/debug/status"
        ]
        
        for endpoint in endpoints:
            print(f"\n📡 {endpoint} にアクセス中...")
            try:
                with urllib.request.urlopen(endpoint, timeout=10) as response:
                    if response.status == 200:
                        data = response.read().decode('utf-8')
                        print(f"   ✅ レスポンス取得成功")
                        print(f"   📄 データ: {data[:200]}..." if len(data) > 200 else f"   📄 データ: {data}")
                    else:
                        print(f"   ❌ HTTPエラー: {response.status}")
            except Exception as e:
                print(f"   ❌ エンドポイントアクセス失敗: {e}")
    
    except ImportError:
        print(f"   ℹ️  urllib.requestが利用できません")

if __name__ == "__main__":
    check_status_via_http()
    check_via_app_endpoint()
    
    print(f"\n🚀 推奨アクション:")
    print(f"   1. LINEでコンテンツを追加")
    print(f"   2. アプリケーションログを確認")
    print(f"   3. Stripe請求書の変化を確認")
    print(f"   4. 上記デバッグエンドポイントで状況を確認")