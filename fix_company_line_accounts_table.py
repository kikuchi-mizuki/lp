#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
company_line_accountsテーブルの不足カラムを手動で追加
"""

import sys
sys.path.append('lp')
from utils.db import get_db_connection

def fix_company_line_accounts_table():
    """不足しているカラムを手動で追加"""
    try:
        print("=== company_line_accountsテーブルの修正 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 現在のテーブル構造を確認
        c.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'company_line_accounts'
            ORDER BY ordinal_position
        """)
        
        existing_columns = [row[0] for row in c.fetchall()]
        print("現在のカラム:", existing_columns)
        
        # 不足しているカラムを追加
        missing_columns = [
            "environment_variables TEXT"
        ]
        
        for column_def in missing_columns:
            column_name = column_def.split()[0]
            if column_name not in existing_columns:
                try:
                    c.execute(f"ALTER TABLE company_line_accounts ADD COLUMN {column_def}")
                    conn.commit()
                    print(f"✅ カラム追加: {column_name}")
                except Exception as e:
                    print(f"❌ カラム追加エラー {column_name}: {e}")
                    conn.rollback()
            else:
                print(f"⚠️ カラム既存: {column_name}")
        
        # 最終的なテーブル構造を確認
        c.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'company_line_accounts'
            ORDER BY ordinal_position
        """)
        
        final_columns = c.fetchall()
        print("\n最終的なテーブル構造:")
        for column_name, data_type in final_columns:
            print(f"  - {column_name}: {data_type}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ テーブル修正エラー: {e}")
        return False

if __name__ == "__main__":
    fix_company_line_accounts_table() 