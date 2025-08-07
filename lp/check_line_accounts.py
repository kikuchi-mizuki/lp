#!/usr/bin/env python3
"""
company_line_accountsテーブルの構造とデータを確認するスクリプト
"""
import os, sys
from dotenv import load_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
from utils.db import get_db_connection, get_db_type

def check_line_accounts():
    print("🚀 company_line_accountsテーブルの確認を開始します")
    try:
        conn = get_db_connection()
        c = conn.cursor()
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        print("=== テーブル構造確認 ===")
        c.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'company_line_accounts' 
            ORDER BY ordinal_position
        """)
        columns = c.fetchall()
        print("company_line_accountsテーブルの構造:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} ({'NULL可' if col[2] == 'YES' else 'NULL不可'})")
        
        print("\n=== データ確認 ===")
        c.execute(f'SELECT * FROM company_line_accounts WHERE company_id = {placeholder}', (5,))
        line_accounts = c.fetchall()
        if line_accounts:
            print(f"企業ID=5のLINEアカウント数: {len(line_accounts)}")
            for account in line_accounts:
                print(f"  - ID: {account[0]}, 企業ID: {account[1]}, コンテンツ: {account[2]}, チャンネルID: {account[3]}, ステータス: {account[5]}")
        else:
            print("❌ 企業ID=5のLINEアカウントが見つかりません")
        
        print("\n=== 全データ確認 ===")
        c.execute('SELECT * FROM company_line_accounts')
        all_accounts = c.fetchall()
        print(f"全LINEアカウント数: {len(all_accounts)}")
        for account in all_accounts:
            print(f"  - ID: {account[0]}, 企業ID: {account[1]}, コンテンツ: {account[2]}, ステータス: {account[5]}")
        
        conn.close()
        print("\n✅ company_line_accountsテーブル確認完了")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_line_accounts()
