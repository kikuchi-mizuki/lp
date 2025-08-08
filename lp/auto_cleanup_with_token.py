#!/usr/bin/env python3
"""
Railway本番環境のデータを自動的に削除するスクリプト
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# 本番環境のデータベース接続情報
DATABASE_URL = "postgresql://postgres:5UBDpKGFzxxx6@gondola.proxy.rlwy.net:16797/railway"

def clear_company_data():
    """データベースのデータを自動クリーンアップ"""
    print("🚀 本番環境のデータベースクリーンアップを開始します")
    
    try:
        # データベース接続
        conn = psycopg2.connect(DATABASE_URL)
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

if __name__ == "__main__":
    success = clear_company_data()
    if success:
        print("\n🎉 データベースのクリーンアップが完了しました！")
    else:
        print("\n❌ データベースのクリーンアップに失敗しました")
        sys.exit(1)
