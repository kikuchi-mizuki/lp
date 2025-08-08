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
    
    # 接続情報は環境変数から取得
    database_url = os.getenv('RAILWAY_DATABASE_URL') or os.getenv('DATABASE_URL')
    if not database_url:
        raise RuntimeError('DATABASE_URL/RAILWAY_DATABASE_URL is not set')
    print(f'[DEBUG] Railway接続URL検出: {"set" if database_url else "unset"}')
    
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
            WHERE table_name IN ('companies', 'company_line_accounts', 'company_subscriptions')
            ORDER BY table_name, ordinal_position
        """)
        
        columns = c.fetchall()
        for col in columns:
            print(f"テーブル: {col[0]}, カラム: {col[1]}, 型: {col[2]}, NULL許可: {col[3]}")
        
        # 2. companiesテーブルの内容確認
        print("\n=== companiesテーブルの内容 ===")
        c.execute("SELECT id, company_name, email, status, created_at FROM companies ORDER BY id")
        companies = c.fetchall()
        
        if companies:
            for company in companies:
                print(f"ID: {company[0]}, 企業名: {company[1]}, メール: {company[2]}, ステータス: {company[3]}, 作成日: {company[4]}")
        else:
            print("companiesテーブルにデータがありません")
        
        # 3. company_line_accountsテーブルの内容確認
        print("\n=== company_line_accountsテーブルの内容 ===")
        c.execute("SELECT id, company_id, content_type, line_channel_id, status, created_at FROM company_line_accounts ORDER BY id")
        line_accounts = c.fetchall()
        
        if line_accounts:
            for account in line_accounts:
                print(f"ID: {account[0]}, 企業ID: {account[1]}, コンテンツタイプ: {account[2]}, LINEチャンネルID: {account[3]}, ステータス: {account[4]}, 作成日: {account[5]}")
        else:
            print("company_line_accountsテーブルにデータがありません")
        
        # 4. company_subscriptionsテーブルの内容確認
        print("\n=== company_subscriptionsテーブルの内容 ===")
        c.execute("SELECT id, company_id, content_type, subscription_status, current_period_end, created_at FROM company_subscriptions ORDER BY id")
        subscriptions = c.fetchall()
        
        if subscriptions:
            for subscription in subscriptions:
                print(f"ID: {subscription[0]}, 企業ID: {subscription[1]}, コンテンツタイプ: {subscription[2]}, ステータス: {subscription[3]}, 期限: {subscription[4]}, 作成日: {subscription[5]}")
        else:
            print("company_subscriptionsテーブルにデータがありません")
        
        # 5. 企業IDが1の場合の詳細確認
        print(f"\n=== 企業ID=1の詳細確認 ===")
        c.execute("SELECT id, company_name, email, status FROM companies WHERE id = 1")
        company_1 = c.fetchone()
        print(f"企業ID=1の情報: {company_1}")
        
        if company_1:
            company_id = company_1[0]
            # LINEアカウント情報
            c.execute("SELECT id, content_type, line_channel_id, status FROM company_line_accounts WHERE company_id = %s ORDER BY created_at DESC LIMIT 1", (company_id,))
            line_account_1 = c.fetchone()
            print(f"企業ID=1のLINEアカウント情報: {line_account_1}")
            
            # サブスクリプション情報
            c.execute("SELECT id, content_type, subscription_status, current_period_end FROM company_subscriptions WHERE company_id = %s ORDER BY created_at DESC LIMIT 1", (company_id,))
            subscription_1 = c.fetchone()
            print(f"企業ID=1のサブスクリプション情報: {subscription_1}")
        
        conn.close()
        
    except Exception as e:
        print(f'[ERROR] Railwayデータベース確認エラー: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_railway_database() 