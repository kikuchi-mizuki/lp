#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
企業情報取得APIのデバッグスクリプト
"""

import requests
import json
import sys

def test_company_info_api():
    """企業情報取得APIをテスト"""
    try:
        print("=== 企業情報取得API デバッグ ===")
        
        # 1. 企業一覧を取得して企業IDを確認
        print("\n1️⃣ 企業一覧を取得")
        response = requests.get('https://lp-production-9e2c.up.railway.app/api/v1/company-registration/list')
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                companies = data['data']
                print(f"✅ 企業一覧取得成功: {len(companies)}件")
                
                if companies:
                    # 最初の企業のIDを使用
                    company_id = companies[0]['company_id']
                    print(f"📋 テスト対象企業ID: {company_id}")
                    
                    # 2. 特定の企業情報を取得
                    print(f"\n2️⃣ 企業ID {company_id} の詳細情報を取得")
                    detail_response = requests.get(f'https://lp-production-9e2c.up.railway.app/api/v1/company-registration/{company_id}')
                    
                    if detail_response.status_code == 200:
                        detail_data = detail_response.json()
                        if detail_data['success']:
                            company_info = detail_data['data']
                            print("✅ 企業詳細情報取得成功:")
                            print(f"  - 企業名: {company_info.get('company_name', 'N/A')}")
                            print(f"  - 企業コード: {company_info.get('company_code', 'N/A')}")
                            print(f"  - LINEチャネルID: {company_info.get('line_channel_id', 'N/A')}")
                            print(f"  - Webhook URL: {company_info.get('webhook_url', 'N/A')}")
                            print(f"  - ステータス: {company_info.get('status', 'N/A')}")
                            
                            return company_id
                        else:
                            print(f"❌ 企業詳細情報取得失敗: {detail_data['error']}")
                    else:
                        print(f"❌ 企業詳細情報取得HTTPエラー: {detail_response.status_code}")
                        print(f"レスポンス: {detail_response.text}")
                else:
                    print("⚠️ 企業データが存在しません")
                    return None
            else:
                print(f"❌ 企業一覧取得失敗: {data['error']}")
        else:
            print(f"❌ 企業一覧取得HTTPエラー: {response.status_code}")
            print(f"レスポンス: {response.text}")
            
        return None
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_company_registration_flow():
    """企業登録フロー全体をテスト"""
    try:
        print("\n=== 企業登録フロー全体テスト ===")
        
        # テスト用の企業データ
        test_company_data = {
            'company_name': f'テスト企業_{int(time.time())}',
            'contact_email': 'test@example.com',
            'contact_phone': '090-1234-5678',
            'line_channel_id': f'1234567890_{int(time.time())}',
            'line_access_token': 'test_access_token_12345',
            'line_channel_secret': 'test_channel_secret_67890',
            'line_basic_id': 'test_basic_id',
            'subscription_id': 'sub_test_123',
            'content_type': 'AI予定秘書'
        }
        
        print("1️⃣ 企業登録APIをテスト")
        response = requests.post(
            'https://lp-production-9e2c.up.railway.app/api/v1/company-registration',
            headers={'Content-Type': 'application/json'},
            json=test_company_data
        )
        
        if response.status_code == 201:
            data = response.json()
            if data['success']:
                company_id = data['data']['company_id']
                print(f"✅ 企業登録成功: 企業ID {company_id}")
                
                # 登録直後に企業情報を取得
                print(f"\n2️⃣ 登録直後の企業情報を取得")
                detail_response = requests.get(f'https://lp-production-9e2c.up.railway.app/api/v1/company-registration/{company_id}')
                
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    if detail_data['success']:
                        company_info = detail_data['data']
                        print("✅ 企業情報取得成功:")
                        print(f"  - 企業名: {company_info.get('company_name', 'N/A')}")
                        print(f"  - 企業コード: {company_info.get('company_code', 'N/A')}")
                        print(f"  - LINEチャネルID: {company_info.get('line_channel_id', 'N/A')}")
                        print(f"  - Webhook URL: {company_info.get('webhook_url', 'N/A')}")
                        
                        return company_id
                    else:
                        print(f"❌ 企業情報取得失敗: {detail_data['error']}")
                else:
                    print(f"❌ 企業情報取得HTTPエラー: {detail_response.status_code}")
            else:
                print(f"❌ 企業登録失敗: {data['error']}")
        else:
            print(f"❌ 企業登録HTTPエラー: {response.status_code}")
            print(f"レスポンス: {response.text}")
            
        return None
        
    except Exception as e:
        print(f"❌ フローテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """メイン関数"""
    print("🚀 企業情報取得APIデバッグを開始します")
    
    # 1. 既存の企業情報をテスト
    existing_company_id = test_company_info_api()
    
    if not existing_company_id:
        print("\n📝 既存の企業データがないため、新規登録をテストします")
        import time
        new_company_id = test_company_registration_flow()
        
        if new_company_id:
            print(f"\n🎉 テスト完了！企業ID {new_company_id} で企業情報が正常に取得できます")
        else:
            print("\n❌ 企業登録・情報取得テストに失敗しました")
    else:
        print(f"\n🎉 既存の企業ID {existing_company_id} で企業情報が正常に取得できます")

if __name__ == "__main__":
    main() 