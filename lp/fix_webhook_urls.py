#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
既存の企業データのWebhook URLを修正するスクリプト
"""

import os
from utils.db import get_db_connection

def fix_webhook_urls():
    """既存のWebhook URLを正しいドメインに更新"""
    try:
        print("=== Webhook URL修正スクリプト ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 現在のドメインを取得
        base_domain = os.getenv('BASE_DOMAIN', 'lp-production-9e2c.up.railway.app')
        print(f"📋 使用するドメイン: {base_domain}")
        
        # 1. 企業一覧を取得
        c.execute('''
            SELECT c.id, c.company_name, cla.webhook_url
            FROM companies c
            LEFT JOIN company_line_accounts cla ON c.id = cla.company_id
            ORDER BY c.id
        ''')
        
        companies = c.fetchall()
        print(f"📊 企業データ数: {len(companies)}件")
        
        updated_count = 0
        for company_id, company_name, current_webhook_url in companies:
            print(f"\n🔍 企業ID {company_id}: {company_name}")
            print(f"  現在のWebhook URL: {current_webhook_url}")
            
            # 新しいWebhook URLを生成
            new_webhook_url = f"https://{base_domain}/webhook/{company_id}"
            print(f"  新しいWebhook URL: {new_webhook_url}")
            
            # 古いURLの場合のみ更新
            if current_webhook_url and 'your-domain.com' in current_webhook_url:
                c.execute('''
                    UPDATE company_line_accounts 
                    SET webhook_url = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE company_id = %s
                ''', (new_webhook_url, company_id))
                
                print(f"  ✅ Webhook URLを更新しました")
                updated_count += 1
            else:
                print(f"  ⏭️ 既に正しいURLのためスキップ")
        
        # 変更をコミット
        conn.commit()
        conn.close()
        
        print(f"\n🎉 Webhook URL修正完了！")
        print(f"  更新件数: {updated_count}件")
        print(f"  対象企業数: {len(companies)}件")
        
        return True
        
    except Exception as e:
        print(f"❌ Webhook URL修正エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_webhook_urls():
    """Webhook URLの修正結果を確認"""
    try:
        print("\n=== Webhook URL修正結果確認 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT c.id, c.company_name, cla.webhook_url, cla.updated_at
            FROM companies c
            LEFT JOIN company_line_accounts cla ON c.id = cla.company_id
            ORDER BY c.id
        ''')
        
        companies = c.fetchall()
        conn.close()
        
        print(f"📊 企業データ確認: {len(companies)}件")
        
        for company_id, company_name, webhook_url, updated_at in companies:
            print(f"\n📋 企業ID {company_id}: {company_name}")
            print(f"  Webhook URL: {webhook_url}")
            print(f"  更新日時: {updated_at}")
            
            if webhook_url and 'your-domain.com' in webhook_url:
                print(f"  ⚠️ まだ古いURLが残っています")
            else:
                print(f"  ✅ 正しいURLです")
        
        return True
        
    except Exception as e:
        print(f"❌ 確認エラー: {e}")
        return False

def main():
    """メイン関数"""
    print("🚀 Webhook URL修正を開始します")
    
    # 1. Webhook URLを修正
    if fix_webhook_urls():
        print("\n✅ Webhook URL修正が完了しました")
        
        # 2. 修正結果を確認
        verify_webhook_urls()
        
        print("\n🎉 すべての処理が完了しました！")
        print("\n📋 次のステップ:")
        print("1. 企業登録成功ページを再読み込み")
        print("2. 設定情報が正しく表示されることを確認")
        print("3. LINEボットデプロイ機能をテスト")
        
    else:
        print("\n❌ Webhook URL修正に失敗しました")

if __name__ == "__main__":
    main() 