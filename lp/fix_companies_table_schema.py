#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
companiesテーブルのスキーマ修正スクリプト
"""

import os
import sys
from utils.db import get_db_connection, get_db_type

def fix_companies_table_schema():
    """companiesテーブルのスキーマを修正"""
    try:
        print("=== companiesテーブルスキーマ修正 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        db_type = get_db_type()
        print(f"データベースタイプ: {db_type}")
        
        if db_type == 'postgresql':
            # PostgreSQL用のスキーマ修正
            
            # 1. 既存のテーブル構造を確認
            c.execute('''
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'companies'
                ORDER BY ordinal_position
            ''')
            
            existing_columns = [row[0] for row in c.fetchall()]
            print(f"既存のカラム: {existing_columns}")
            
            # 2. 不足しているカラムを追加
            if 'contact_email' not in existing_columns:
                print("contact_emailカラムを追加中...")
                c.execute('''
                    ALTER TABLE companies 
                    ADD COLUMN contact_email VARCHAR(255)
                ''')
                print("✅ contact_emailカラムを追加しました")
            
            if 'contact_phone' not in existing_columns:
                print("contact_phoneカラムを追加中...")
                c.execute('''
                    ALTER TABLE companies 
                    ADD COLUMN contact_phone VARCHAR(50)
                ''')
                print("✅ contact_phoneカラムを追加しました")
            
            if 'status' not in existing_columns:
                print("statusカラムを追加中...")
                c.execute('''
                    ALTER TABLE companies 
                    ADD COLUMN status VARCHAR(50) DEFAULT 'active'
                ''')
                print("✅ statusカラムを追加しました")
            
            if 'created_at' not in existing_columns:
                print("created_atカラムを追加中...")
                c.execute('''
                    ALTER TABLE companies 
                    ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ''')
                print("✅ created_atカラムを追加しました")
            
            if 'updated_at' not in existing_columns:
                print("updated_atカラムを追加中...")
                c.execute('''
                    ALTER TABLE companies 
                    ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ''')
                print("✅ updated_atカラムを追加しました")
            
            # 3. company_paymentsテーブルが存在しない場合は作成
            c.execute('''
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'company_payments'
                )
            ''')
            
            if not c.fetchone()[0]:
                print("company_paymentsテーブルを作成中...")
                c.execute('''
                    CREATE TABLE company_payments (
                        id SERIAL PRIMARY KEY,
                        company_id INTEGER NOT NULL,
                        stripe_subscription_id VARCHAR(255),
                        content_type VARCHAR(100),
                        amount INTEGER,
                        status VARCHAR(50) DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
                    )
                ''')
                print("✅ company_paymentsテーブルを作成しました")
            
        else:
            # SQLite用のスキーマ修正
            c.execute('PRAGMA table_info(companies)')
            existing_columns = [row[1] for row in c.fetchall()]
            print(f"既存のカラム: {existing_columns}")
            
            # 不足しているカラムを追加
            if 'contact_email' not in existing_columns:
                print("contact_emailカラムを追加中...")
                c.execute('ALTER TABLE companies ADD COLUMN contact_email TEXT')
                print("✅ contact_emailカラムを追加しました")
            
            if 'contact_phone' not in existing_columns:
                print("contact_phoneカラムを追加中...")
                c.execute('ALTER TABLE companies ADD COLUMN contact_phone TEXT')
                print("✅ contact_phoneカラムを追加しました")
            
            if 'status' not in existing_columns:
                print("statusカラムを追加中...")
                c.execute('ALTER TABLE companies ADD COLUMN status TEXT DEFAULT "active"')
                print("✅ statusカラムを追加しました")
            
            if 'created_at' not in existing_columns:
                print("created_atカラムを追加中...")
                c.execute('ALTER TABLE companies ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
                print("✅ created_atカラムを追加しました")
            
            if 'updated_at' not in existing_columns:
                print("updated_atカラムを追加中...")
                c.execute('ALTER TABLE companies ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
                print("✅ updated_atカラムを追加しました")
        
        conn.commit()
        conn.close()
        
        print("✅ companiesテーブルのスキーマ修正が完了しました")
        
        # 修正後のテーブル構造を確認
        verify_table_structure()
        
        return True
        
    except Exception as e:
        print(f"❌ スキーマ修正エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_table_structure():
    """テーブル構造を確認"""
    try:
        print("\n=== 修正後のテーブル構造確認 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        db_type = get_db_type()
        
        if db_type == 'postgresql':
            # PostgreSQL用の構造確認
            c.execute('''
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'companies'
                ORDER BY ordinal_position
            ''')
            
            columns = c.fetchall()
            
            print("📋 companies テーブル構造:")
            for column in columns:
                print(f"  - {column[0]}: {column[1]} ({'NULL可' if column[2] == 'YES' else 'NULL不可'})")
                if column[3]:
                    print(f"    デフォルト値: {column[3]}")
            
        else:
            # SQLite用の構造確認
            c.execute('PRAGMA table_info(companies)')
            columns = c.fetchall()
            
            print("📋 companies テーブル構造:")
            for column in columns:
                print(f"  - {column[1]}: {column[2]} ({'NULL可' if column[3] == 0 else 'NULL不可'})")
                if column[4]:
                    print(f"    デフォルト値: {column[4]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ テーブル構造確認エラー: {e}")

def main():
    """メイン関数"""
    print("🚀 companiesテーブルスキーマ修正を開始します")
    
    # スキーマ修正
    if fix_companies_table_schema():
        print("✅ スキーマ修正が完了しました")
        
        print("\n🎉 companiesテーブルの準備が完了しました！")
        print("\n📋 次のステップ:")
        print("1. 企業登録システムのテストを再実行")
        print("2. 企業情報登録フォームをテスト")
        print("3. 自動デプロイ機能をテスト")
        
    else:
        print("❌ スキーマ修正に失敗しました")

if __name__ == "__main__":
    main() 