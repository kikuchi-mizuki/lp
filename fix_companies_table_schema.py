#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
企業テーブルにemailフィールドを追加するマイグレーションスクリプト
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def fix_companies_table_schema():
    """企業テーブルにemailフィールドを追加"""
    try:
        print("=== 企業テーブルスキーマ修正 ===")
        
        # 接続情報
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            database_url = "postgresql://postgres:WZgnjZezoefHmxbwRjUbiPhajtwubmUs@gondola.proxy.rlwy.net:16797/railway"
        
        print(f"[DEBUG] データベース接続: {database_url[:50]}...")
        
        # データベース接続
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        
        # 現在のテーブル構造を確認
        c.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'companies' 
            ORDER BY ordinal_position
        """)
        columns = c.fetchall()
        print(f"📊 現在のcompaniesテーブル構造:")
        for col in columns:
            print(f"  {col[0]}: {col[1]}")
        
        # emailカラムが存在するかチェック
        email_exists = any(col[0] == 'email' for col in columns)
        
        if not email_exists:
            print("📝 emailカラムを追加中...")
            c.execute('ALTER TABLE companies ADD COLUMN email VARCHAR(255)')
            conn.commit()
            print("✅ emailカラムを追加しました")
        else:
            print("✅ emailカラムは既に存在します")
        
        # 既存の企業データにemailを設定（usersテーブルから取得）
        print("📝 既存企業データにemailを設定中...")
        c.execute("""
            UPDATE companies 
            SET email = u.email 
            FROM users u 
            WHERE companies.stripe_subscription_id = u.stripe_subscription_id 
            AND companies.email IS NULL
        """)
        updated_count = c.rowcount
        conn.commit()
        print(f"✅ {updated_count}件の企業データにemailを設定しました")
        
        # 更新後の確認
        c.execute('SELECT id, company_name, email, line_user_id, stripe_subscription_id FROM companies ORDER BY id')
        companies = c.fetchall()
        print(f"📊 更新後の企業データ:")
        for company in companies:
            print(f"  ID: {company[0]}, 名前: {company[1]}, Email: {company[2]}, LINE: {company[3]}, Stripe: {company[4]}")
        
        conn.close()
        print("✅ 企業テーブルスキーマ修正完了")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_companies_table_schema() 