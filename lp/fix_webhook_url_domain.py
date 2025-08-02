#!/usr/bin/env python3
"""
Webhook URLのドメインを修正するスクリプト
"""

from utils.db import get_db_connection

def fix_webhook_url_domain():
    """Webhook URLのドメインを正しいものに修正"""
    try:
        print("=== Webhook URLドメイン修正 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 現在のWebhook URLを確認
        c.execute('''
            SELECT cla.id, cla.company_id, c.company_name, cla.webhook_url
            FROM company_line_accounts cla
            JOIN companies c ON cla.company_id = c.id
        ''')
        
        records = c.fetchall()
        
        if not records:
            print("❌ 修正対象のレコードが見つかりません")
            return False
        
        print(f"📊 修正対象レコード数: {len(records)}件")
        
        corrected_count = 0
        for record_id, company_id, company_name, current_webhook_url in records:
            print(f"\n🔍 企業ID {company_id}: {company_name}")
            print(f"  現在のWebhook URL: {current_webhook_url}")
            
            # 正しいドメインでWebhook URLを生成
            correct_webhook_url = f"https://lp-production-9e2c.up.railway.app/webhook/{company_id}"
            print(f"  正しいWebhook URL: {correct_webhook_url}")
            
            # ドメインが間違っている場合のみ修正
            if current_webhook_url and 'task-bot-production.up.railway.app' in current_webhook_url:
                c.execute('''
                    UPDATE company_line_accounts 
                    SET webhook_url = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                ''', (correct_webhook_url, record_id))
                
                print(f"  ✅ Webhook URLを修正しました")
                corrected_count += 1
            else:
                print(f"  ⏭️ 既に正しいドメインのためスキップ")
        
        # 変更をコミット
        conn.commit()
        conn.close()
        
        print(f"\n🎉 Webhook URLドメイン修正完了！")
        print(f"修正件数: {corrected_count}件")
        
        return True
        
    except Exception as e:
        print(f"❌ Webhook URL修正エラー: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def verify_webhook_urls():
    """修正後のWebhook URLを確認"""
    try:
        print("\n=== Webhook URL確認 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT cla.company_id, c.company_name, cla.webhook_url
            FROM company_line_accounts cla
            JOIN companies c ON cla.company_id = c.id
        ''')
        
        records = c.fetchall()
        
        print(f"📊 確認対象レコード数: {len(records)}件")
        
        all_correct = True
        for company_id, company_name, webhook_url in records:
            print(f"\n🔍 企業ID {company_id}: {company_name}")
            print(f"  Webhook URL: {webhook_url}")
            
            # 正しいドメインかチェック
            if webhook_url and 'lp-production-9e2c.up.railway.app' in webhook_url:
                print(f"  ✅ 正しいドメイン")
            else:
                print(f"  ❌ 間違ったドメイン")
                all_correct = False
        
        conn.close()
        
        if all_correct:
            print(f"\n🎉 すべてのWebhook URLが正しいドメインです！")
        else:
            print(f"\n⚠️ 一部のWebhook URLに問題があります")
        
        return all_correct
        
    except Exception as e:
        print(f"❌ Webhook URL確認エラー: {e}")
        return False

def main():
    """メイン関数"""
    print("Webhook URLドメイン修正を開始します...")
    
    # 1. Webhook URLを修正
    if fix_webhook_url_domain():
        print("\n✅ Webhook URL修正が完了しました")
        
        # 2. 修正結果を確認
        if verify_webhook_urls():
            print("\n🎉 すべてのWebhook URLが正しく修正されました！")
        else:
            print("\n⚠️ 一部のWebhook URLに問題が残っています")
    else:
        print("\n❌ Webhook URL修正に失敗しました")

if __name__ == "__main__":
    main() 