#!/usr/bin/env python3
"""
Railway CLIを使用して本番環境のデータを自動的に削除するスクリプト
"""
import os
import sys
import subprocess
import psycopg2

def get_railway_database_url():
    """Railway CLIを使用してデータベースURLを取得"""
    try:
        result = subprocess.run(
            ["railway", "variables", "get", "DATABASE_URL"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Railway CLIエラー: {e}")
        print(f"エラー出力: {e.stderr}")
        return None

def clear_company_data(database_url):
    """データベースのデータを自動クリーンアップ"""
    print("🚀 本番環境のデータベースクリーンアップを開始します")
    
    try:
        # データベース接続
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        print("✅ データベースに接続しました")
        
        # company_line_accountsのデータを削除
        cur.execute("DELETE FROM company_line_accounts")
        line_accounts_count = cur.rowcount
        print(f"✅ company_line_accountsから{line_accounts_count}件のデータを削除しました")
        
        # company_monthly_subscriptionsのデータを削除
        cur.execute("DELETE FROM company_monthly_subscriptions")
        subscriptions_count = cur.rowcount
        print(f"✅ company_monthly_subscriptionsから{subscriptions_count}件のデータを削除しました")
        
        # company_subscriptionsのデータを削除（古いテーブル）
        try:
            cur.execute("DELETE FROM company_subscriptions")
            subscriptions_old_count = cur.rowcount
            print(f"✅ company_subscriptionsから{subscriptions_old_count}件のデータを削除しました")
        except psycopg2.Error:
            print("ℹ️ company_subscriptionsテーブルは存在しないか、すでに削除されています")
        
        # 変更をコミット
        conn.commit()
        print("\n✅ すべてのデータを正常に削除しました")
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        if 'conn' in locals():
            conn.rollback()
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if 'cur' in locals() and cur:
            cur.close()
        if 'conn' in locals() and conn:
            conn.close()
            print("🔒 データベース接続を閉じました")

def main():
    print("🚂 Railway CLIを使用してデータベースクリーンアップを開始します")
    
    # Railway CLIからデータベースURLを取得
    database_url = get_railway_database_url()
    if not database_url:
        print("❌ データベースURLの取得に失敗しました")
        print("Railway CLIがインストールされていることを確認してください")
        print("インストール方法: npm i -g @railway/cli")
        sys.exit(1)
    
    # データベースクリーンアップを実行
    success = clear_company_data(database_url)
    
    if success:
        print("\n🎉 データベースのクリーンアップが完了しました！")
    else:
        print("\n❌ データベースのクリーンアップに失敗しました")
        sys.exit(1)

if __name__ == "__main__":
    main()
