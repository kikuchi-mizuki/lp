#!/usr/bin/env python3
"""
Webhook URLを新しいシンプルなエンドポイントに更新するスクリプト
"""

import os
from utils.db import get_db_connection

def update_webhook_url_to_simple():
    """Webhook URLを新しいシンプルなエンドポイントに更新"""
    try:
        print("=== Webhook URL更新（シンプルエンドポイント） ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 1. 現在の企業情報を確認
        c.execute('''
            SELECT c.id, c.company_name, c.company_code, cla.webhook_url, cla.line_channel_id
            FROM companies c
            LEFT JOIN company_line_accounts cla ON c.id = cla.company_id
            ORDER BY c.id DESC
        ''')
        
        companies = c.fetchall()
        
        if not companies:
            print("❌ 企業データが見つかりません")
            return False
        
        print(f"📊 企業データ数: {len(companies)}件")
        
        # 2. 各企業のWebhook URLを更新
        for company_id, company_name, company_code, webhook_url, line_channel_id in companies:
            print(f"\n🔍 企業ID {company_id}: {company_name}")
            print(f"  現在のWebhook URL: {webhook_url}")
            
            # 新しいシンプルなWebhookエンドポイントを使用
            new_webhook_url = "https://lp-production-9e2c.up.railway.app/ai-schedule/webhook"
            
            print(f"  更新後のWebhook URL: {new_webhook_url}")
            
            # Webhook URLを更新
            c.execute('''
                UPDATE company_line_accounts 
                SET webhook_url = %s, updated_at = CURRENT_TIMESTAMP
                WHERE company_id = %s
            ''', (new_webhook_url, company_id))
            
            print(f"  ✅ Webhook URLを更新しました")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ すべての企業のWebhook URL更新が完了しました")
        
        # 3. 更新後の確認
        print(f"\n📋 更新後のWebhook URL設定:")
        print(f"  推奨Webhook URL: {new_webhook_url}")
        print(f"  説明: AI予定秘書専用のシンプルなWebhookエンドポイント")
        
        return True
        
    except Exception as e:
        print(f"❌ Webhook URL更新エラー: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    """メイン関数"""
    print("Webhook URL更新（シンプルエンドポイント）を開始します...")
    
    if update_webhook_url_to_simple():
        print("\n✅ Webhook URL更新が完了しました")
        print("\n📝 次のステップ:")
        print("1. LINE Developers ConsoleでWebhook URLを更新")
        print("2. Webhook URLの検証を実行")
        print("3. LINEボットの動作確認")
    else:
        print("\n❌ Webhook URL更新に失敗しました")

if __name__ == "__main__":
    main() 