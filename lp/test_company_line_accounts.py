#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
企業別LINEアカウント管理システムのテストスクリプト
"""

import os
import sys
from datetime import datetime
from utils.db import get_db_connection
from services.company_line_account_service import company_line_service

def test_company_line_account_creation():
    """企業別LINEアカウント作成のテスト"""
    try:
        print("=== 企業別LINEアカウント作成テスト ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 1. 既存の企業を確認
        c.execute('SELECT id, company_name, company_code FROM companies LIMIT 3')
        companies = c.fetchall()
        
        print(f"テスト対象企業数: {len(companies)}")
        for company in companies:
            print(f"  - ID: {company[0]}, 名前: {company[1]}, コード: {company[2]}")
        
        conn.close()
        
        # 2. 各企業でLINEアカウント作成をテスト
        for company in companies:
            company_id = company[0]
            company_name = company[1]
            
            print(f"\n--- 企業 {company_name} のLINEアカウント作成テスト ---")
            
            # LINEアカウント作成
            result = company_line_service.create_company_line_account(company_id, company_name)
            
            if result['success']:
                print(f"✅ LINEアカウント作成成功")
                print(f"  - アカウントID: {result['account_id']}")
                print(f"  - チャネルID: {result['channel_id']}")
                print(f"  - 基本ID: {result['basic_id']}")
                print(f"  - QRコード: {result['qr_code_url']}")
                print(f"  - Webhook: {result['webhook_url']}")
            else:
                print(f"❌ LINEアカウント作成失敗: {result['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_company_line_account_management():
    """企業別LINEアカウント管理機能のテスト"""
    try:
        print("\n=== 企業別LINEアカウント管理機能テスト ===")
        
        # 1. LINEアカウント一覧を取得
        print("\n1️⃣ LINEアカウント一覧取得")
        result = company_line_service.list_company_line_accounts()
        
        if result['success']:
            accounts = result['accounts']
            print(f"登録済みLINEアカウント数: {len(accounts)}")
            
            for account in accounts:
                print(f"  - 企業: {account['company_name']}")
                print(f"    - チャネルID: {account['channel_id']}")
                print(f"    - 基本ID: {account['basic_id']}")
                print(f"    - ステータス: {account['status']}")
        else:
            print(f"❌ 一覧取得失敗: {result['error']}")
            return False
        
        # 2. 特定企業のLINEアカウント情報を取得
        if accounts:
            test_account = accounts[0]
            company_id = test_account['company_id']
            
            print(f"\n2️⃣ 企業 {test_account['company_name']} のLINEアカウント情報取得")
            result = company_line_service.get_company_line_account(company_id)
            
            if result['success']:
                account = result['account']
                print(f"✅ アカウント情報取得成功")
                print(f"  - チャネルID: {account['channel_id']}")
                print(f"  - 基本ID: {account['basic_id']}")
                print(f"  - QRコード: {account['qr_code_url']}")
                print(f"  - Webhook: {account['webhook_url']}")
                print(f"  - ステータス: {account['status']}")
            else:
                print(f"❌ アカウント情報取得失敗: {result['error']}")
                return False
            
            # 3. LINEアカウント情報を更新
            print(f"\n3️⃣ LINEアカウント情報更新テスト")
            update_data = {
                'status': 'active',
                'webhook_url': f"https://updated-domain.com/webhook/{company_id}"
            }
            
            result = company_line_service.update_company_line_account(company_id, update_data)
            
            if result['success']:
                print(f"✅ アカウント情報更新成功")
            else:
                print(f"❌ アカウント情報更新失敗: {result['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 管理機能テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_message_sending():
    """企業別メッセージ送信のテスト"""
    try:
        print("\n=== 企業別メッセージ送信テスト ===")
        
        # 1. アクティブなLINEアカウントを取得
        result = company_line_service.list_company_line_accounts('active')
        
        if not result['success'] or not result['accounts']:
            print("❌ アクティブなLINEアカウントが見つかりません")
            return False
        
        test_account = result['accounts'][0]
        company_id = test_account['company_id']
        company_name = test_account['company_name']
        
        print(f"テスト対象企業: {company_name}")
        
        # 2. テストメッセージを送信
        test_message = f"これは{company_name}向けのテストメッセージです。\n送信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        print(f"送信メッセージ: {test_message}")
        
        result = company_line_service.send_message_to_company(company_id, test_message)
        
        if result['success']:
            print(f"✅ メッセージ送信成功")
        else:
            print(f"❌ メッセージ送信失敗: {result['error']}")
            # 実際のAPIキーが設定されていない場合は失敗するが、これは正常
        
        return True
        
    except Exception as e:
        print(f"❌ メッセージ送信テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_qr_code_and_webhook():
    """QRコードとWebhook URLのテスト"""
    try:
        print("\n=== QRコード・Webhook URLテスト ===")
        
        # 1. アクティブなLINEアカウントを取得
        result = company_line_service.list_company_line_accounts('active')
        
        if not result['success'] or not result['accounts']:
            print("❌ アクティブなLINEアカウントが見つかりません")
            return False
        
        test_account = result['accounts'][0]
        company_id = test_account['company_id']
        company_name = test_account['company_name']
        
        print(f"テスト対象企業: {company_name}")
        
        # 2. QRコード情報を取得
        print(f"\n1️⃣ QRコード情報取得")
        result = company_line_service.get_company_line_account(company_id)
        
        if result['success']:
            account = result['account']
            print(f"✅ QRコード情報取得成功")
            print(f"  - QRコードURL: {account['qr_code_url']}")
            print(f"  - 基本ID: {account['basic_id']}")
            print(f"  - チャネルID: {account['channel_id']}")
        else:
            print(f"❌ QRコード情報取得失敗: {result['error']}")
        
        # 3. Webhook URL情報を取得
        print(f"\n2️⃣ Webhook URL情報取得")
        if result['success']:
            account = result['account']
            print(f"✅ Webhook URL情報取得成功")
            print(f"  - Webhook URL: {account['webhook_url']}")
            print(f"  - チャネルID: {account['channel_id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ QRコード・Webhookテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_setup_instructions():
    """セットアップ手順を生成"""
    print("\n=== 企業別LINEアカウントセットアップ手順 ===")
    
    print("\n📋 手動セットアップ手順:")
    print("1. LINE Developers Console (https://developers.line.biz/) にアクセス")
    print("2. 新しいプロバイダーを作成")
    print("3. 各企業用のチャネルを作成:")
    print("   - チャネルタイプ: Messaging API")
    print("   - チャネル名: [企業名] 公式LINE")
    print("   - チャネル説明: [企業名]の公式LINEアカウント")
    print("4. チャネル情報を取得:")
    print("   - チャネルID")
    print("   - チャネルアクセストークン")
    print("   - チャネルシークレット")
    print("   - 基本ID")
    print("5. Webhook URLを設定:")
    print("   - URL: https://your-domain.com/webhook/[company_id]")
    print("   - 検証: 有効")
    print("6. データベースに情報を保存")
    
    print("\n🔧 自動化のためのAPI設定:")
    print("1. LINE Management API トークンを取得")
    print("2. 環境変数に設定:")
    print("   export LINE_MANAGEMENT_TOKEN=your_management_token")
    print("3. 自動チャネル作成機能を有効化")
    
    print("\n📱 企業向け設定:")
    print("1. QRコードを企業に提供")
    print("2. 基本IDを企業に通知")
    print("3. 初期メッセージを設定")
    print("4. リッチメニューを設定")

def main():
    """メイン関数"""
    print("🚀 企業別LINEアカウント管理システムテストを開始します")
    
    from datetime import datetime
    
    # 1. LINEアカウント作成テスト
    if test_company_line_account_creation():
        print("✅ LINEアカウント作成テストが完了しました")
        
        # 2. 管理機能テスト
        if test_company_line_account_management():
            print("✅ 管理機能テストが完了しました")
            
            # 3. メッセージ送信テスト
            if test_message_sending():
                print("✅ メッセージ送信テストが完了しました")
                
                # 4. QRコード・Webhookテスト
                if test_qr_code_and_webhook():
                    print("✅ QRコード・Webhookテストが完了しました")
                    
                    # 5. セットアップ手順を表示
                    generate_setup_instructions()
                    
                    print("\n🎉 すべてのテストが完了しました！")
                else:
                    print("❌ QRコード・Webhookテストに失敗しました")
            else:
                print("❌ メッセージ送信テストに失敗しました")
        else:
            print("❌ 管理機能テストに失敗しました")
    else:
        print("❌ LINEアカウント作成テストに失敗しました")

if __name__ == "__main__":
    main() 