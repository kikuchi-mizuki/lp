#!/usr/bin/env python3
"""
company_subscriptionsテーブルの状態を確認するスクリプト
"""

import os
import psycopg2
from dotenv import load_dotenv

def check_company_subscriptions():
    """company_subscriptionsテーブルの状態を確認"""
    print("=== company_subscriptionsテーブル確認 ===")
    
    try:
        # 環境変数を読み込み
        load_dotenv()
        
        # データベース接続
        database_url = os.getenv("RAILWAY_DATABASE_URL") or os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL/RAILWAY_DATABASE_URL is not set")
        
        print(f"[DEBUG] 接続URL: {database_url[:50]}...")
        
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        
        # テーブル構造を確認
        print("\n=== テーブル構造確認 ===")
        c.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'company_subscriptions'
            ORDER BY ordinal_position
        """)
        columns = c.fetchall()
        
        if not columns:
            print("❌ company_subscriptionsテーブルが存在しません")
            return
        
        print("✅ company_subscriptionsテーブルが存在します")
        print("\nカラム一覧:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} ({'NULL可' if col[2] == 'YES' else 'NULL不可'})")
        
        # データ数を確認
        print("\n=== データ数確認 ===")
        c.execute("SELECT COUNT(*) FROM company_subscriptions")
        count = c.fetchone()[0]
        print(f"総レコード数: {count}")
        
        if count > 0:
            # データ一覧を表示
            print("\n=== データ一覧 ===")
            c.execute("""
                SELECT id, company_id, stripe_subscription_id, subscription_status, 
                       current_period_end, created_at, base_price, additional_price, total_price
                FROM company_subscriptions
                ORDER BY created_at DESC
            """)
            records = c.fetchall()
            
            for record in records:
                print(f"\nID: {record[0]}")
                print(f"企業ID: {record[1]}")
                print(f"StripeサブスクリプションID: {record[2]}")
                print(f"ステータス: {record[3]}")
                print(f"期間終了: {record[4]}")
                print(f"作成日時: {record[5]}")
                print(f"基本料金: {record[6]}")
                print(f"追加料金: {record[7]}")
                print(f"総料金: {record[8]}")
                print("-" * 50)
        
        # 企業ID=5のデータを確認
        print("\n=== 企業ID=5の確認 ===")
        c.execute("SELECT * FROM company_subscriptions WHERE company_id = 5")
        company_5_records = c.fetchall()
        
        if company_5_records:
            print(f"✅ 企業ID=5のデータが{len(company_5_records)}件存在します")
            for record in company_5_records:
                print(f"  レコード: {record}")
        else:
            print("❌ 企業ID=5のデータが存在しません")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_company_subscriptions()
