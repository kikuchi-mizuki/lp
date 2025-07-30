#!/usr/bin/env python3
"""
企業管理システム テストスクリプト
"""

import requests
import json
import sys

def test_company_creation():
    """企業作成のテスト"""
    print("=== 企業管理システム テスト ===")
    
    # テスト用の企業データ
    test_company_data = {
        "company_name": "テスト株式会社",
        "email": "test@example.com",
        "phone": "03-1234-5678",
        "address": "東京都渋谷区テスト1-2-3",
        "industry": "IT",
        "employee_count": 50
    }
    
    # APIエンドポイント
    base_url = "http://localhost:5000"
    api_url = f"{base_url}/api/v1/companies"
    
    print(f"📡 APIエンドポイント: {api_url}")
    print(f"📋 テストデータ: {json.dumps(test_company_data, ensure_ascii=False, indent=2)}")
    
    try:
        # 企業作成APIを呼び出し
        print("\n🚀 企業作成APIを呼び出し中...")
        response = requests.post(
            api_url,
            json=test_company_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📊 レスポンスステータス: {response.status_code}")
        print(f"📄 レスポンスヘッダー: {dict(response.headers)}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ 成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 作成された企業IDを取得
            if 'company_id' in result:
                company_id = result['company_id']
                print(f"\n🔍 作成された企業ID: {company_id}")
                
                # 企業情報取得のテスト
                test_get_company(base_url, company_id)
                
                # 企業一覧取得のテスト
                test_list_companies(base_url)
                
                # 企業統計情報取得のテスト
                test_get_company_statistics(base_url, company_id)
                
                # LINEアカウント情報取得のテスト
                test_get_line_account(base_url, company_id)
                
        else:
            print(f"❌ エラー: {response.status_code}")
            print(f"📄 エラーレスポンス: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 接続エラー: サーバーが起動していない可能性があります")
        print("💡 ヒント: python app.py でサーバーを起動してください")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")

def test_get_company(base_url, company_id):
    """企業情報取得のテスト"""
    print(f"\n🔍 企業情報取得テスト (ID: {company_id})")
    
    try:
        response = requests.get(f"{base_url}/api/v1/companies/{company_id}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 企業情報取得成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ 企業情報取得失敗: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ 企業情報取得エラー: {e}")

def test_list_companies(base_url):
    """企業一覧取得のテスト"""
    print(f"\n📋 企業一覧取得テスト")
    
    try:
        response = requests.get(f"{base_url}/api/v1/companies")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 企業一覧取得成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ 企業一覧取得失敗: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ 企業一覧取得エラー: {e}")

def test_get_company_statistics(base_url, company_id):
    """企業統計情報取得のテスト"""
    print(f"\n📊 企業統計情報取得テスト (ID: {company_id})")
    
    try:
        response = requests.get(f"{base_url}/api/v1/companies/{company_id}/statistics")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 統計情報取得成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ 統計情報取得失敗: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ 統計情報取得エラー: {e}")

def test_get_line_account(base_url, company_id):
    """LINEアカウント情報取得のテスト"""
    print(f"\n📱 LINEアカウント情報取得テスト (ID: {company_id})")
    
    try:
        response = requests.get(f"{base_url}/api/v1/companies/{company_id}/line-account")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ LINEアカウント情報取得成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ LINEアカウント情報取得失敗: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ LINEアカウント情報取得エラー: {e}")

def test_company_update(base_url, company_id):
    """企業情報更新のテスト"""
    print(f"\n✏️ 企業情報更新テスト (ID: {company_id})")
    
    update_data = {
        "phone": "03-9876-5432",
        "employee_count": 100
    }
    
    try:
        response = requests.put(
            f"{base_url}/api/v1/companies/{company_id}",
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 企業情報更新成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ 企業情報更新失敗: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ 企業情報更新エラー: {e}")

def test_line_message_send(base_url, company_id):
    """LINEメッセージ送信のテスト"""
    print(f"\n💬 LINEメッセージ送信テスト (ID: {company_id})")
    
    message_data = {
        "message": {
            "to": "all",
            "messages": [
                {
                    "type": "text",
                    "text": "テストメッセージです。企業管理システムからの送信です。"
                }
            ]
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/companies/{company_id}/line-account/message",
            json=message_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ メッセージ送信成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ メッセージ送信失敗: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ メッセージ送信エラー: {e}")

if __name__ == "__main__":
    print("企業管理システムのテストを開始します...")
    print("注意: このテストを実行する前に、Flaskサーバーが起動していることを確認してください")
    print("サーバー起動方法: python app.py")
    print()
    
    # メインテスト実行
    test_company_creation()
    
    print("\n🎉 テスト完了！")
    print("\n📝 次のステップ:")
    print("1. 企業管理ダッシュボードの作成")
    print("2. コンテンツ管理機能の実装")
    print("3. 決済連携機能の実装")
    print("4. 通知システムの実装") 