#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
企業登録自動テストスクリプト
"""

import requests
import json
import time
from datetime import datetime

def test_company_registration_auto():
    """企業登録の自動テスト"""
    try:
        print("=== 企業登録自動テスト ===")
        
        # テストデータ
        test_data = {
            'company_name': f'テスト企業自動{int(time.time())}',
            'contact_email': f'test{int(time.time())}@example.com',
            'contact_phone': '090-1234-5678',
            'line_channel_id': f'2007858{int(time.time()) % 1000:03d}',
            'line_access_token': 'test_access_token_12345',
            'line_channel_secret': 'test_channel_secret_12345',
            'line_basic_id': 'test_basic_id_12345',
            'content_type': 'AI予定秘書'
        }
        
        print(f"📋 テストデータ:")
        print(f"  企業名: {test_data['company_name']}")
        print(f"  メール: {test_data['contact_email']}")
        print(f"  LINEチャネルID: {test_data['line_channel_id']}")
        print(f"  コンテンツタイプ: {test_data['content_type']}")
        
        # 企業登録APIを呼び出し
        url = "https://lp-production-9e2c.up.railway.app/api/company-registration"
        headers = {
            'Content-Type': 'application/json'
        }
        
        print(f"\n🚀 企業登録APIを呼び出し中...")
        print(f"  URL: {url}")
        
        response = requests.post(url, headers=headers, json=test_data, timeout=30)
        
        print(f"📊 レスポンス:")
        print(f"  ステータスコード: {response.status_code}")
        print(f"  レスポンスヘッダー: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 企業登録成功!")
            print(f"  レスポンス: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 成功ページにリダイレクト
            if 'company_id' in result:
                success_url = f"https://lp-production-9e2c.up.railway.app/company-registration-success?company_id={result['company_id']}"
                print(f"\n📋 成功ページにアクセス:")
                print(f"  URL: {success_url}")
                
                success_response = requests.get(success_url, timeout=30)
                print(f"  成功ページステータス: {success_response.status_code}")
                
                if success_response.status_code == 200:
                    print("✅ 成功ページに正常にアクセスできました")
                else:
                    print(f"⚠️ 成功ページアクセスエラー: {success_response.status_code}")
            
        else:
            print(f"❌ 企業登録失敗:")
            print(f"  エラーレスポンス: {response.text}")
            
            # エラーページの内容を確認
            try:
                error_data = response.json()
                print(f"  エラー詳細: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"  エラー内容: {response.text[:500]}")
        
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False

if __name__ == "__main__":
    test_company_registration_auto() 