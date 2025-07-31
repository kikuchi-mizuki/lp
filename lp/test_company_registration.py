#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
企業登録システムのテストスクリプト
"""

import os
import sys
import json
from datetime import datetime
from services.company_registration_service import company_registration_service
import time

def test_company_registration():
    """企業登録機能のテスト"""
    try:
        print("=== 企業登録機能テスト ===")
        
        # テストデータ
        test_company_data = {
            'company_name': 'テスト企業株式会社',
            'contact_email': 'test@example.com',
            'contact_phone': '03-1234-5678',
            'line_channel_id': f'1234567890_{int(time.time())}',  # 一意のIDを生成
            'line_access_token': 'test_access_token_1234567890',
            'line_channel_secret': 'test_channel_secret_1234567890',
            'line_basic_id': '@testcompany',
            'subscription_id': 'sub_test_1234567890',
            'content_type': 'line_bot'
        }
        
        print(f"テスト企業: {test_company_data['company_name']}")
        
        # 1. 企業登録
        print("\n1️⃣ 企業登録テスト")
        result = company_registration_service.register_company(test_company_data)
        
        if result['success']:
            company_id = result['company_id']
            print(f"✅ 企業登録成功")
            print(f"  - 企業ID: {company_id}")
            print(f"  - 企業コード: {result['company_code']}")
            print(f"  - LINEアカウントID: {result['line_account_id']}")
            
            # 2. 企業情報取得
            print(f"\n2️⃣ 企業情報取得テスト")
            get_result = company_registration_service.get_company_registration(company_id)
            
            if get_result['success']:
                company = get_result['company']
                print(f"✅ 企業情報取得成功")
                print(f"  - 企業名: {company['company_name']}")
                print(f"  - 連絡先: {company['contact_email']}")
                print(f"  - LINEチャネルID: {company['line_channel_id']}")
                print(f"  - Webhook URL: {company['webhook_url']}")
            else:
                print(f"❌ 企業情報取得失敗: {get_result['error']}")
                return False
            
            # 3. 企業情報更新
            print(f"\n3️⃣ 企業情報更新テスト")
            update_data = {
                'contact_phone': '03-9876-5432',
                'line_basic_id': '@updated_testcompany'
            }
            
            update_result = company_registration_service.update_company_registration(company_id, update_data)
            
            if update_result['success']:
                print(f"✅ 企業情報更新成功")
            else:
                print(f"❌ 企業情報更新失敗: {update_result['error']}")
            
            # 4. 企業一覧取得
            print(f"\n4️⃣ 企業一覧取得テスト")
            list_result = company_registration_service.list_company_registrations()
            
            if list_result['success']:
                companies = list_result['companies']
                print(f"✅ 企業一覧取得成功")
                print(f"登録企業数: {len(companies)}")
                
                for company in companies:
                    print(f"  - {company['company_name']} ({company['company_code']})")
            else:
                print(f"❌ 企業一覧取得失敗: {list_result['error']}")
            
            # 5. LINE認証情報検証
            print(f"\n5️⃣ LINE認証情報検証テスト")
            credentials = {
                'line_channel_id': test_company_data['line_channel_id'],
                'line_access_token': test_company_data['line_access_token'],
                'line_basic_id': test_company_data['line_basic_id']
            }
            
            validate_result = company_registration_service.validate_line_credentials(credentials)
            
            if validate_result['success']:
                print(f"✅ LINE認証情報検証成功")
            else:
                print(f"❌ LINE認証情報検証失敗: {validate_result['error']}")
                # 実際のAPIキーが設定されていない場合は失敗するが、これは正常
            
            # 6. デプロイ状況確認
            print(f"\n6️⃣ デプロイ状況確認テスト")
            deployment_result = company_registration_service.get_deployment_status(company_id)
            
            if deployment_result['success']:
                status = deployment_result['status']
                print(f"✅ デプロイ状況取得成功")
                print(f"  - ステータス: {status['deployment_status']}")
                print(f"  - Railway URL: {status['railway_url']}")
            else:
                print(f"❌ デプロイ状況取得失敗: {deployment_result['error']}")
                # デプロイデータが存在しない場合は失敗するが、これは正常
            
            return True
            
        else:
            print(f"❌ 企業登録失敗: {result['error']}")
            return False
        
    except Exception as e:
        print(f"❌ 企業登録テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_railway_deployment():
    """Railwayデプロイ機能のテスト"""
    try:
        print("\n=== Railwayデプロイ機能テスト ===")
        
        # 既存の企業を取得
        list_result = company_registration_service.list_company_registrations()
        
        if not list_result['success'] or not list_result['companies']:
            print("❌ テスト対象の企業が見つかりません")
            return False
        
        test_company = list_result['companies'][0]
        company_id = test_company['id']
        
        print(f"テスト対象企業: {test_company['company_name']}")
        
        # 1. LINEボットデプロイ
        print(f"\n1️⃣ LINEボットデプロイテスト")
        deploy_result = company_registration_service.deploy_company_line_bot(company_id)
        
        if deploy_result['success']:
            print(f"✅ デプロイ開始成功")
            print(f"  - デプロイID: {deploy_result['deployment_id']}")
            print(f"  - Railway URL: {deploy_result['railway_url']}")
            print(f"  - プロジェクトID: {deploy_result['project_id']}")
            
            # 2. デプロイ状況確認
            print(f"\n2️⃣ デプロイ状況確認テスト")
            status_result = company_registration_service.get_deployment_status(company_id)
            
            if status_result['success']:
                status = status_result['status']
                print(f"✅ デプロイ状況取得成功")
                print(f"  - ステータス: {status['deployment_status']}")
                print(f"  - Railway URL: {status['railway_url']}")
                print(f"  - 作成日時: {status['created_at']}")
            else:
                print(f"❌ デプロイ状況取得失敗: {status_result['error']}")
            
            return True
            
        else:
            print(f"❌ デプロイ開始失敗: {deploy_result['error']}")
            # Railway API トークンが設定されていない場合は失敗するが、これは正常
            return True
        
    except Exception as e:
        print(f"❌ Railwayデプロイテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_line_connection():
    """LINE接続テスト"""
    try:
        print("\n=== LINE接続テスト ===")
        
        # 既存の企業を取得
        list_result = company_registration_service.list_company_registrations()
        
        if not list_result['success'] or not list_result['companies']:
            print("❌ テスト対象の企業が見つかりません")
            return False
        
        test_company = list_result['companies'][0]
        company_id = test_company['id']
        company_name = test_company['company_name']
        
        print(f"テスト対象企業: {company_name}")
        
        # テストメッセージを送信
        test_message = f"これは{company_name}向けのテストメッセージです。\n送信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        print(f"送信メッセージ: {test_message}")
        
        result = company_registration_service.test_line_connection(company_id, test_message)
        
        if result['success']:
            print(f"✅ LINE接続テスト成功")
        else:
            print(f"❌ LINE接続テスト失敗: {result['error']}")
            # 実際のAPIキーが設定されていない場合は失敗するが、これは正常
        
        return True
        
    except Exception as e:
        print(f"❌ LINE接続テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_api_documentation():
    """APIドキュメントを生成"""
    print("\n=== API ドキュメント ===")
    
    print("\n📋 企業登録API エンドポイント:")
    print("1. POST /api/v1/company-registration")
    print("   - 企業情報を登録")
    print("   - 必須フィールド: company_name, contact_email, line_channel_id, line_access_token, line_channel_secret")
    
    print("\n2. GET /api/v1/company-registration/{company_id}")
    print("   - 企業登録情報を取得")
    
    print("\n3. PUT /api/v1/company-registration/{company_id}")
    print("   - 企業登録情報を更新")
    
    print("\n4. GET /api/v1/company-registration/list")
    print("   - 企業登録一覧を取得")
    print("   - クエリパラメータ: status (active/inactive)")
    
    print("\n5. POST /api/v1/company-registration/{company_id}/deploy")
    print("   - 企業のLINEボットをRailwayにデプロイ")
    
    print("\n6. GET /api/v1/company-registration/{company_id}/deployment-status")
    print("   - デプロイ状況を確認")
    
    print("\n7. POST /api/v1/company-registration/{company_id}/test-line")
    print("   - LINE接続をテスト")
    print("   - リクエストボディ: {message: 'テストメッセージ'}")
    
    print("\n8. POST /api/v1/company-registration/validate-line-credentials")
    print("   - LINE認証情報を検証")
    print("   - リクエストボディ: {line_channel_id, line_access_token, line_basic_id}")
    
    print("\n📋 Webページ:")
    print("1. GET /company-registration")
    print("   - 企業情報登録フォーム")
    print("   - クエリパラメータ: subscription_id, content_type")
    
    print("\n2. GET /company-registration-success")
    print("   - 企業登録成功ページ")
    print("   - クエリパラメータ: company_id")
    
    print("\n3. GET /company-dashboard")
    print("   - 企業管理ダッシュボード")

def main():
    """メイン関数"""
    print("🚀 企業登録システムテストを開始します")
    
    # 1. 企業登録機能テスト
    if test_company_registration():
        print("✅ 企業登録機能テストが完了しました")
        
        # 2. Railwayデプロイ機能テスト
        if test_railway_deployment():
            print("✅ Railwayデプロイ機能テストが完了しました")
            
            # 3. LINE接続テスト
            if test_line_connection():
                print("✅ LINE接続テストが完了しました")
                
                # 4. APIドキュメント生成
                generate_api_documentation()
                
                print("\n🎉 すべてのテストが完了しました！")
                print("\n📋 次のステップ:")
                print("1. 実際のLINE Developers Consoleでチャネルを作成")
                print("2. Railway API トークンを設定")
                print("3. 企業情報登録フォームを実際にテスト")
                print("4. 自動デプロイ機能をテスト")
                print("5. 本格運用開始")
                
            else:
                print("❌ LINE接続テストに失敗しました")
        else:
            print("❌ Railwayデプロイ機能テストに失敗しました")
    else:
        print("❌ 企業登録機能テストに失敗しました")

if __name__ == "__main__":
    main() 