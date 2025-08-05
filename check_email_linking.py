#!/usr/bin/env python3
"""
メールアドレス連携処理のデバッグスクリプト
"""

import os
import psycopg2
from dotenv import load_dotenv

def check_email_linking():
    """メールアドレス連携処理をデバッグ"""
    print("=== メールアドレス連携処理デバッグ ===")
    
    # テスト用メールアドレス
    test_email = "mmms.dy.23@gmail.com"
    test_line_user_id = "U1b9d0d75b0c770dc1107dde349d572f7"
    
    print(f"テストメールアドレス: {test_email}")
    print(f"テストLINEユーザーID: {test_line_user_id}")
    
    # データベース接続
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        database_url = "postgresql://postgres:WZgnjZezoefHmxbwRjUbiPhajtwubmUs@gondola.proxy.rlwy.net:16797/railway"
    
    print(f"使用するデータベースURL: {database_url[:50]}...")
    
    try:
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        print("✅ データベース接続成功")
        
        # 1. メールアドレス正規化テスト
        def normalize_email(email):
            import unicodedata
            email = email.strip().lower()
            email = unicodedata.normalize('NFKC', email)
            return email
        
        normalized_email = normalize_email(test_email)
        print(f"正規化後のメールアドレス: {normalized_email}")
        
        # 2. usersテーブル検索
        print("\n=== usersテーブル検索 ===")
        c.execute('SELECT id, line_user_id, email FROM users WHERE email = %s', (normalized_email,))
        user = c.fetchone()
        if user:
            user_id, line_user_id, email = user
            print(f"✅ usersテーブルで発見: id={user_id}, line_user_id={line_user_id}, email={email}")
        else:
            print(f"❌ usersテーブルで見つかりません: email={normalized_email}")
        
        # 3. companiesテーブル検索
        print("\n=== companiesテーブル検索 ===")
        c.execute('SELECT id, company_name, line_user_id, email FROM companies WHERE email = %s', (normalized_email,))
        company = c.fetchone()
        if company:
            company_id, company_name, line_user_id, email = company
            print(f"✅ companiesテーブルで発見: id={company_id}, name={company_name}, line_user_id={line_user_id}, email={email}")
        else:
            print(f"❌ companiesテーブルで見つかりません: email={normalized_email}")
        
        # 4. LINEユーザーIDでの企業検索
        print(f"\n=== LINEユーザーIDでの企業検索 ===")
        c.execute('SELECT id, company_name, line_user_id, email FROM companies WHERE line_user_id = %s', (test_line_user_id,))
        company_by_line = c.fetchone()
        if company_by_line:
            company_id, company_name, line_user_id, email = company_by_line
            print(f"✅ LINEユーザーIDで企業発見: id={company_id}, name={company_name}, line_user_id={line_user_id}, email={email}")
        else:
            print(f"❌ LINEユーザーIDで企業が見つかりません: line_user_id={test_line_user_id}")
        
        # 5. 全企業データ確認
        print("\n=== 全企業データ確認 ===")
        c.execute('SELECT id, company_name, line_user_id, email FROM companies ORDER BY created_at DESC LIMIT 5')
        companies = c.fetchall()
        for company in companies:
            company_id, company_name, line_user_id, email = company
            print(f"企業: id={company_id}, name={company_name}, line_user_id={line_user_id}, email={email}")
        
        # 6. 全ユーザーデータ確認
        print("\n=== 全ユーザーデータ確認 ===")
        c.execute('SELECT id, line_user_id, email FROM users ORDER BY created_at DESC LIMIT 5')
        users = c.fetchall()
        for user in users:
            user_id, line_user_id, email = user
            print(f"ユーザー: id={user_id}, line_user_id={line_user_id}, email={email}")
        
        conn.close()
        print("\n✅ デバッグ完了")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_email_linking() 