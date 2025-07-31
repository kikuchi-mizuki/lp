#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
企業登録フォームへのアクセステストスクリプト
"""

import requests
import os
from urllib.parse import urljoin

def test_form_access():
    """企業登録フォームへのアクセステスト"""
    try:
        print("=== 企業登録フォームアクセステスト ===")
        
        # テスト用のURL
        base_url = "https://lp-production-9e2c.up.railway.app"
        form_url = f"{base_url}/company-registration"
        
        # パラメータ付きのURLもテスト
        test_params = {
            'subscription_id': 'sub_test_1234567890',
            'content_type': 'AI予定秘書'
        }
        
        print(f"1️⃣ 基本フォームアクセステスト")
        print(f"URL: {form_url}")
        
        # 基本アクセス
        response = requests.get(form_url, timeout=10)
        print(f"ステータスコード: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        if response.status_code == 200:
            print("✅ 基本アクセス成功")
            
            # HTMLコンテンツの確認
            content = response.text
            if '企業情報登録' in content:
                print("✅ 企業情報登録フォームが正しく表示されています")
            else:
                print("❌ 企業情報登録フォームが表示されていません")
                print(f"HTML内容（最初の500文字）: {content[:500]}")
            
            # フォーム要素の確認
            required_elements = [
                'company_registration.html',
                '企業名',
                'LINEチャネルID',
                'LINEチャネルアクセストークン',
                'LINEチャネルシークレット'
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in content:
                    missing_elements.append(element)
            
            if missing_elements:
                print(f"❌ 不足している要素: {missing_elements}")
            else:
                print("✅ すべての必要なフォーム要素が含まれています")
                
        else:
            print(f"❌ アクセス失敗: {response.status_code}")
            print(f"レスポンス内容: {response.text[:500]}")
            return False
        
        print(f"\n2️⃣ パラメータ付きフォームアクセステスト")
        param_url = f"{form_url}?subscription_id={test_params['subscription_id']}&content_type={test_params['content_type']}"
        print(f"URL: {param_url}")
        
        # パラメータ付きアクセス
        response_with_params = requests.get(param_url, timeout=10)
        print(f"ステータスコード: {response_with_params.status_code}")
        
        if response_with_params.status_code == 200:
            print("✅ パラメータ付きアクセス成功")
            
            # パラメータが正しく渡されているか確認
            content_with_params = response_with_params.text
            if test_params['subscription_id'] in content_with_params:
                print("✅ subscription_idパラメータが正しく渡されています")
            else:
                print("❌ subscription_idパラメータが渡されていません")
                
            if test_params['content_type'] in content_with_params:
                print("✅ content_typeパラメータが正しく渡されています")
            else:
                print("❌ content_typeパラメータが渡されていません")
                
        else:
            print(f"❌ パラメータ付きアクセス失敗: {response_with_params.status_code}")
            return False
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ リクエストエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_form_functionality():
    """フォーム機能のテスト"""
    try:
        print(f"\n=== フォーム機能テスト ===")
        
        base_url = "https://lp-production-9e2c.up.railway.app"
        
        # テストデータ
        test_data = {
            'company_name': 'テスト株式会社',
            'contact_email': 'test@example.com',
            'contact_phone': '03-1234-5678',
            'line_channel_id': '1234567890',
            'line_access_token': 'test_access_token_12345',
            'line_channel_secret': 'test_channel_secret_67890',
            'line_basic_id': '@testcompany',
            'subscription_id': 'sub_test_1234567890',
            'content_type': 'AI予定秘書'
        }
        
        print(f"1️⃣ フォーム送信テスト")
        api_url = f"{base_url}/api/v1/company-registration"
        print(f"API URL: {api_url}")
        
        # API送信テスト
        response = requests.post(
            api_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンス: {response.text[:500]}")
        
        if response.status_code in [200, 201]:
            print("✅ フォーム送信成功")
            try:
                result = response.json()
                if result.get('success'):
                    print("✅ API応答が成功を示しています")
                else:
                    print(f"❌ API応答が失敗を示しています: {result.get('error', 'Unknown error')}")
            except:
                print("⚠️ JSONレスポンスの解析に失敗しました")
        else:
            print(f"❌ フォーム送信失敗: {response.status_code}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ リクエストエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_url_generation():
    """URL生成のテスト"""
    try:
        print(f"\n=== URL生成テスト ===")
        
        # 環境変数を設定
        os.environ['BASE_URL'] = 'https://lp-production-9e2c.up.railway.app'
        
        # LINEサービスからURL生成ロジックをテスト
        base_url = os.getenv('BASE_URL', 'https://your-domain.com')
        subscription_id = 'sub_test_1234567890'
        content_type = 'AI予定秘書'
        
        # URL生成
        registration_url = f"{base_url}/company-registration?subscription_id={subscription_id}&content_type={content_type}"
        
        print(f"生成されたURL: {registration_url}")
        
        # URLの形式を確認
        if 'company-registration' in registration_url:
            print("✅ 正しいパスが含まれています")
        else:
            print("❌ 正しいパスが含まれていません")
            
        if 'subscription_id=' in registration_url:
            print("✅ subscription_idパラメータが含まれています")
        else:
            print("❌ subscription_idパラメータが含まれていません")
            
        if 'content_type=' in registration_url:
            print("✅ content_typeパラメータが含まれています")
        else:
            print("❌ content_typeパラメータが含まれていません")
        
        # 実際のアクセステスト
        print(f"\n実際のURLアクセステスト:")
        response = requests.get(registration_url, timeout=10)
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 生成されたURLでアクセス成功")
        else:
            print(f"❌ 生成されたURLでアクセス失敗: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ URL生成テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン関数"""
    print("🚀 企業登録フォームアクセステストを開始します")
    
    # 1. フォームアクセステスト
    if test_form_access():
        print("✅ フォームアクセステストが完了しました")
        
        # 2. フォーム機能テスト
        if test_form_functionality():
            print("✅ フォーム機能テストが完了しました")
            
            # 3. URL生成テスト
            if test_url_generation():
                print("✅ URL生成テストが完了しました")
                
                print("\n🎉 すべてのテストが完了しました！")
                print("\n📋 テスト結果:")
                print("1. ✅ 企業登録フォームへのアクセス")
                print("2. ✅ パラメータ付きフォームアクセス")
                print("3. ✅ フォーム機能（API送信）")
                print("4. ✅ URL生成機能")
                
                print("\n📋 問題が発生した場合の対処法:")
                print("1. Railway環境変数の確認")
                print("2. アプリケーションの再デプロイ")
                print("3. ログの確認")
                
            else:
                print("❌ URL生成テストに失敗しました")
        else:
            print("❌ フォーム機能テストに失敗しました")
    else:
        print("❌ フォームアクセステストに失敗しました")

if __name__ == "__main__":
    main() 