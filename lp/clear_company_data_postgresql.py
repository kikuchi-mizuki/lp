#!/usr/bin/env python3
"""
PostgreSQLの企業データを削除するスクリプト
"""

from utils.db import get_db_connection

def clear_company_data():
    """企業関連のデータを削除"""
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        print("🗑️ PostgreSQLの企業データを削除中...")
        
        # 削除前のデータ数を確認
        c.execute("SELECT COUNT(*) FROM companies")
        company_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM company_line_accounts")
        line_account_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM company_deployments")
        deployment_count = c.fetchone()[0]
        
        print(f"📊 削除前のデータ数:")
        print(f"  - 企業数: {company_count}")
        print(f"  - LINEアカウント数: {line_account_count}")
        print(f"  - デプロイメント数: {deployment_count}")
        
        # 確認
        if company_count == 0:
            print("ℹ️ 削除する企業データがありません")
            return
        
        # 削除実行
        print("\n🗑️ データを削除中...")
        
        # 外部キー制約があるため、子テーブルから削除
        c.execute("DELETE FROM company_deployments")
        print(f"✅ company_deploymentsテーブルのデータを削除しました")
        
        c.execute("DELETE FROM company_line_accounts")
        print(f"✅ company_line_accountsテーブルのデータを削除しました")
        
        c.execute("DELETE FROM companies")
        print(f"✅ companiesテーブルのデータを削除しました")
        
        conn.commit()
        
        # 削除後の確認
        c.execute("SELECT COUNT(*) FROM companies")
        remaining_companies = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM company_line_accounts")
        remaining_line_accounts = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM company_deployments")
        remaining_deployments = c.fetchone()[0]
        
        print(f"\n📊 削除後のデータ数:")
        print(f"  - 企業数: {remaining_companies}")
        print(f"  - LINEアカウント数: {remaining_line_accounts}")
        print(f"  - デプロイメント数: {remaining_deployments}")
        
        print("\n✅ PostgreSQLの企業データ削除が完了しました！")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        conn.rollback()
    finally:
        conn.close()

def show_company_data():
    """企業データを表示"""
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        print("📋 現在の企業データ:")
        
        c.execute("""
            SELECT c.id, c.company_name, c.company_code, c.created_at,
                   cla.line_channel_id, cla.webhook_url
            FROM companies c
            LEFT JOIN company_line_accounts cla ON c.id = cla.company_id
            ORDER BY c.id DESC
        """)
        
        companies = c.fetchall()
        
        if not companies:
            print("  ℹ️ 企業データがありません")
            return
        
        for company in companies:
            company_id, company_name, company_code, created_at, line_channel_id, webhook_url = company
            print(f"\n  📋 企業ID: {company_id}")
            print(f"     企業名: {company_name}")
            print(f"     企業コード: {company_code}")
            print(f"     作成日時: {created_at}")
            print(f"     LINEチャネルID: {line_channel_id or '未設定'}")
            print(f"     Webhook URL: {webhook_url or '未設定'}")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
    finally:
        conn.close()

def main():
    """メイン関数"""
    print("🗑️ PostgreSQL企業データ削除ツール")
    print("=" * 50)
    
    # 現在のデータを表示
    show_company_data()
    
    print("\n" + "=" * 50)
    
    # 削除確認
    confirm = input("⚠️ 本当に企業データを削除しますか？ (y/N): ")
    
    if confirm.lower() == 'y':
        clear_company_data()
    else:
        print("❌ 削除をキャンセルしました")

if __name__ == "__main__":
    main() 