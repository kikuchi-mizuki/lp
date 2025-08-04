#!/usr/bin/env python3
"""
Webhookエンドポイントの自動確認スクリプト
"""

import requests
import time

def check_endpoint(base_url, endpoint):
    """エンドポイントの存在を確認"""
    url = f"{base_url}{endpoint}"
    try:
        response = requests.get(url, timeout=10)
        return {
            'endpoint': endpoint,
            'url': url,
            'status_code': response.status_code,
            'exists': response.status_code != 404,
            'content': response.text[:200] if response.status_code != 404 else None
        }
    except Exception as e:
        return {
            'endpoint': endpoint,
            'url': url,
            'status_code': None,
            'exists': False,
            'error': str(e)
        }

def check_webhook_endpoints():
    """Webhookエンドポイントを自動確認"""
    base_url = "https://task-bot-production-3d6c.up.railway.app"
    
    print("🔍 Webhookエンドポイントの自動確認を開始します...")
    print(f"📡 ベースURL: {base_url}")
    print("=" * 60)
    
    # 確認するエンドポイントのリスト
    endpoints = [
        "/",
        "/webhook",
        "/line/webhook",
        "/ai-schedule/webhook",
        "/callback",
        "/line/callback",
        "/bot/webhook",
        "/api/webhook",
        "/api/line/webhook",
        "/health",
        "/status",
        "/ping"
    ]
    
    found_endpoints = []
    
    for endpoint in endpoints:
        print(f"🔍 確認中: {endpoint}")
        result = check_endpoint(base_url, endpoint)
        
        if result['exists']:
            print(f"✅ 発見: {endpoint} (ステータス: {result['status_code']})")
            if result['content']:
                print(f"   内容: {result['content']}")
            found_endpoints.append(result)
        else:
            print(f"❌ 未発見: {endpoint}")
        
        time.sleep(0.5)  # サーバーに負荷をかけないよう少し待機
    
    print("\n" + "=" * 60)
    print("📋 結果サマリー")
    print("=" * 60)
    
    if found_endpoints:
        print("✅ 発見されたエンドポイント:")
        for endpoint in found_endpoints:
            print(f"  - {endpoint['endpoint']} (ステータス: {endpoint['status_code']})")
        
        print("\n🎯 Webhook URLの候補:")
        for endpoint in found_endpoints:
            if 'webhook' in endpoint['endpoint'].lower() or endpoint['endpoint'] == '/callback':
                print(f"  📡 {endpoint['url']}")
    else:
        print("❌ 利用可能なエンドポイントが見つかりませんでした")
        print("💡 アプリケーションのルーティング設定を確認する必要があります")
    
    print("\n🔧 次のステップ:")
    if found_endpoints:
        webhook_candidates = [ep for ep in found_endpoints if 'webhook' in ep['endpoint'].lower() or ep['endpoint'] == '/callback']
        if webhook_candidates:
            print("1. 上記のWebhook URL候補をLINE Developers Consoleで試してください")
            print("2. 最も適切なURLを選択してWebhookを設定してください")
        else:
            print("1. アプリケーションにWebhookエンドポイントを追加する必要があります")
    else:
        print("1. アプリケーションのルーティング設定を確認してください")
        print("2. Webhookエンドポイントを追加してください")

if __name__ == "__main__":
    check_webhook_endpoints() 