#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
データベースの実際の構造を確認するスクリプト
"""

import os
import sys
from utils.db import get_db_connection, get_db_type

def check_database_structure():
    """データベースの構造を確認"""
    try:
        print("=== データベース構造確認 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        db_type = get_db_type()
        print(f"データベースタイプ: {db_type}")
        
        if db_type == 'postgresql':
            # PostgreSQLの場合
            print("\n1️⃣ テーブル一覧")
            c.execute('''
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            ''')
            
            tables = c.fetchall()
            print(f"テーブル数: {len(tables)}")
            for table in tables:
                print(f"  - {table[0]}")
            
            # 各テーブルの構造を確認
            for table in tables:
                table_name = table[0]
                print(f"\n2️⃣ {table_name}テーブルの構造")
                
                c.execute(f'''
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position
                ''')
                
                columns = c.fetchall()
                print(f"カラム数: {len(columns)}")
                for col in columns:
                    nullable = "NULL可" if col[2] == 'YES' else "NULL不可"
                    default = f" DEFAULT {col[3]}" if col[3] else ""
                    print(f"  - {col[0]}: {col[1]} ({nullable}){default}")
                
                # 制約も確認
                c.execute(f'''
                    SELECT conname, contype, pg_get_constraintdef(oid) as definition
                    FROM pg_constraint 
                    WHERE conrelid = '{table_name}'::regclass
                ''')
                
                constraints = c.fetchall()
                if constraints:
                    print(f"制約数: {len(constraints)}")
                    for constraint in constraints:
                        constraint_type = {
                            'p': 'PRIMARY KEY',
                            'f': 'FOREIGN KEY',
                            'u': 'UNIQUE',
                            'c': 'CHECK'
                        }.get(constraint[1], constraint[1])
                        print(f"  - {constraint[0]}: {constraint_type} - {constraint[2]}")
                else:
                    print("制約: なし")
                
                # サンプルデータも確認
                c.execute(f'SELECT COUNT(*) FROM {table_name}')
                count = c.fetchone()[0]
                print(f"データ数: {count}")
                
                if count > 0:
                    c.execute(f'SELECT * FROM {table_name} LIMIT 3')
                    sample_data = c.fetchall()
                    print("サンプルデータ:")
                    for i, row in enumerate(sample_data, 1):
                        print(f"  {i}. {row}")
        
        else:
            # SQLiteの場合
            print("\n1️⃣ テーブル一覧")
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            
            tables = c.fetchall()
            print(f"テーブル数: {len(tables)}")
            for table in tables:
                print(f"  - {table[0]}")
            
            # 各テーブルの構造を確認
            for table in tables:
                table_name = table[0]
                print(f"\n2️⃣ {table_name}テーブルの構造")
                
                c.execute(f"PRAGMA table_info({table_name})")
                columns = c.fetchall()
                
                print(f"カラム数: {len(columns)}")
                for col in columns:
                    nullable = "NULL可" if col[3] == 0 else "NULL不可"
                    default = f" DEFAULT {col[4]}" if col[4] else ""
                    print(f"  - {col[1]}: {col[2]} ({nullable}){default}")
                
                # サンプルデータも確認
                c.execute(f'SELECT COUNT(*) FROM {table_name}')
                count = c.fetchone()[0]
                print(f"データ数: {count}")
                
                if count > 0:
                    c.execute(f'SELECT * FROM {table_name} LIMIT 3')
                    sample_data = c.fetchall()
                    print("サンプルデータ:")
                    for i, row in enumerate(sample_data, 1):
                        print(f"  {i}. {row}")
        
        conn.close()
        
        print("\n🎉 データベース構造確認が完了しました")
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_specific_tables():
    """特定のテーブルの詳細確認"""
    try:
        print("\n=== 特定テーブルの詳細確認 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # usersテーブル
        print("\n1️⃣ usersテーブル")
        try:
            c.execute('SELECT * FROM users LIMIT 5')
            users = c.fetchall()
            print(f"ユーザー数: {len(users)}")
            for user in users:
                print(f"  - {user}")
        except Exception as e:
            print(f"❌ usersテーブルエラー: {e}")
        
        # subscription_periodsテーブル
        print("\n2️⃣ subscription_periodsテーブル")
        try:
            c.execute('SELECT * FROM subscription_periods LIMIT 5')
            periods = c.fetchall()
            print(f"サブスクリプション期間数: {len(periods)}")
            for period in periods:
                print(f"  - {period}")
        except Exception as e:
            print(f"❌ subscription_periodsテーブルエラー: {e}")
        
        # companiesテーブル
        print("\n3️⃣ companiesテーブル")
        try:
            c.execute('SELECT * FROM companies LIMIT 5')
            companies = c.fetchall()
            print(f"企業数: {len(companies)}")
            for company in companies:
                print(f"  - {company}")
        except Exception as e:
            print(f"❌ companiesテーブルエラー: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 詳細確認エラー: {e}")

def main():
    """メイン関数"""
    print("🚀 データベース構造確認を開始します")
    
    if check_database_structure():
        check_specific_tables()
    else:
        print("❌ データベース構造確認に失敗しました")

if __name__ == "__main__":
    main() 