#!/usr/bin/env python3
"""
Railway本番環境のデータベース状態を確認するスクリプト
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def check_railway_database():
    """Railway本番環境のデータベース状態を確認"""
    
    # Railway本番環境のデータベース接続情報
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        database_url = "postgresql://postgres:WZgnjZezoefHmxbwRjUbiPhajtwubmUs@gondola.proxy.rlwy.net:16797/railway"
    
    print(f'[DEBUG] Railway接続URL: {database_url}')
    
    try:
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        
        print(f'[DEBUG] Railwayデータベース接続成功')
        print(f'[DEBUG] 接続先ホスト: {conn.info.host}')
        print(f'[DEBUG] 接続先データベース: {conn.info.dbname}')
        print(f'[DEBUG] 接続先ユーザー: {conn.info.user}')
        
        # 1. テーブル構造の確認
        print("\n=== テーブル構造の確認 ===")
        c.execute("""
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name IN ('companies', 'company_payments', 'users', 'usage_logs')
            ORDER BY table_name, ordinal_position
        """)
        
        columns = c.fetchall()
        for col in columns:
            print(f"テーブル: {col[0]}, カラム: {col[1]}, 型: {col[2]}, NULL許可: {col[3]}")
        
        # 2. companiesテーブルの内容確認
        print("\n=== companiesテーブルの内容 ===")
        c.execute("SELECT id, company_name, email, line_user_id, stripe_subscription_id, status, created_at FROM companies ORDER BY id")
        companies = c.fetchall()
        
        if companies:
            for company in companies:
                print(f"ID: {company[0]}, 企業名: {company[1]}, メール: {company[2]}, LINE_ID: {company[3]}, Stripe_ID: {company[4]}, ステータス: {company[5]}, 作成日: {company[6]}")
        else:
            print("companiesテーブルにデータがありません")
        
        # 3. company_paymentsテーブルの内容確認
        print("\n=== company_paymentsテーブルの内容 ===")
        c.execute("SELECT id, company_id, subscription_status, current_period_end, created_at FROM company_payments ORDER BY id")
        payments = c.fetchall()
        
        if payments:
            for payment in payments:
                print(f"ID: {payment[0]}, 企業ID: {payment[1]}, ステータス: {payment[2]}, 期限: {payment[3]}, 作成日: {payment[4]}")
        else:
            print("company_paymentsテーブルにデータがありません")
        
        # 4. usersテーブルの内容確認
        print("\n=== usersテーブルの内容 ===")
        c.execute("SELECT id, email, line_user_id, stripe_subscription_id, created_at FROM users ORDER BY id")
        users = c.fetchall()
        
        if users:
            for user in users:
                print(f"ID: {user[0]}, メール: {user[1]}, LINE_ID: {user[2]}, Stripe_ID: {user[3]}, 作成日: {user[4]}")
        else:
            print("usersテーブルにデータがありません")
        
        # 5. 特定のLINEユーザーIDでの検索テスト
        target_line_user_id = "U1b9d0d75b0c770dc1107dde349d572f7"
        print(f"\n=== 特定LINEユーザーIDでの検索テスト: {target_line_user_id} ===")
        
        # companiesテーブルでの検索
        c.execute("SELECT id, company_name, line_user_id FROM companies WHERE line_user_id = %s", (target_line_user_id,))
        company_result = c.fetchone()
        print(f"companiesテーブル検索結果: {company_result}")
        
        # usersテーブルでの検索
        c.execute("SELECT id, email, line_user_id FROM users WHERE line_user_id = %s", (target_line_user_id,))
        user_result = c.fetchone()
        print(f"usersテーブル検索結果: {user_result}")
        
        # 6. 企業IDが1の場合の詳細確認
        print(f"\n=== 企業ID=1の詳細確認 ===")
        c.execute("SELECT id, company_name, line_user_id, stripe_subscription_id FROM companies WHERE id = 1")
        company_1 = c.fetchone()
        print(f"企業ID=1の情報: {company_1}")
        
        if company_1:
            company_id = company_1[0]
            c.execute("SELECT id, subscription_status, current_period_end FROM company_payments WHERE company_id = %s ORDER BY created_at DESC LIMIT 1", (company_id,))
            payment_1 = c.fetchone()
            print(f"企業ID=1の最新決済情報: {payment_1}")
        
        conn.close()
        
    except Exception as e:
        print(f'[ERROR] Railwayデータベース確認エラー: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_railway_database() 