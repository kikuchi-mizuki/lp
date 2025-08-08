#!/usr/bin/env python3
"""
company_subscriptionsテーブルの総料金を修正するスクリプト
"""

import os
import psycopg2
from dotenv import load_dotenv

def fix_company_subscription_pricing():
    """company_subscriptionsテーブルの総料金を修正"""
    print("=== company_subscriptions料金修正 ===")
    
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
        
        # 修正前のデータを確認
        print("\n=== 修正前のデータ ===")
        c.execute("""
            SELECT id, company_id, content_type, subscription_status, 
                   base_price, additional_price, total_price
            FROM company_subscriptions
            WHERE company_id = 5
            ORDER BY created_at DESC
        """)
        records = c.fetchall()
        
        for record in records:
            print(f"\nID: {record[0]}")
            print(f"企業ID: {record[1]}")
            print(f"コンテンツ: {record[2]}")
            print(f"ステータス: {record[3]}")
            print(f"基本料金: {record[4]}")
            print(f"追加料金: {record[5]}")
            print(f"総料金: {record[6]}")
            print("-" * 50)
        
        # ID: 8の総料金を修正（基本料金3,900円 + 追加料金1,500円 = 5,400円）
        print("\n=== 修正実行 ===")
        c.execute("""
            UPDATE company_subscriptions 
            SET total_price = base_price + additional_price
            WHERE id = 8
        """)
        
        # 修正後のデータを確認
        print("\n=== 修正後のデータ ===")
        c.execute("""
            SELECT id, company_id, content_type, subscription_status, 
                   base_price, additional_price, total_price
            FROM company_subscriptions
            WHERE company_id = 5
            ORDER BY created_at DESC
        """)
        records = c.fetchall()
        
        for record in records:
            print(f"\nID: {record[0]}")
            print(f"企業ID: {record[1]}")
            print(f"コンテンツ: {record[2]}")
            print(f"ステータス: {record[3]}")
            print(f"基本料金: {record[4]}")
            print(f"追加料金: {record[5]}")
            print(f"総料金: {record[6]}")
            print("-" * 50)
        
        # 変更をコミット
        conn.commit()
        print("\n✅ 修正完了")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_company_subscription_pricing()
