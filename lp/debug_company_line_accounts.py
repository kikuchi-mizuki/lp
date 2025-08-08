#!/usr/bin/env python3
"""
企業のLINEアカウントデータを調査するデバッグスクリプト
"""

import os
import sys
from dotenv import load_dotenv

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import get_db_connection, get_db_type

def debug_company_line_accounts():
    """企業のLINEアカウントデータを調査"""
    print("=== 企業LINEアカウントデータ調査 ===")
    
    try:
        # 環境変数を読み込み
        load_dotenv()
        
        # データベース接続
        conn = get_db_connection()
        c = conn.cursor()
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        # 企業ID 12のデータを調査
        company_id = 12
        
        print(f"調査対象企業ID: {company_id}")
        
        # 全レコード数を確認
        c.execute(f'SELECT COUNT(*) FROM company_line_accounts WHERE company_id = {placeholder}', (company_id,))
        total_count = c.fetchone()[0]
        print(f"全レコード数: {total_count}")
        
        # アクティブなレコード数を確認
        c.execute(f'SELECT COUNT(*) FROM company_line_accounts WHERE company_id = {placeholder} AND status = {placeholder}', (company_id, 'active'))
        active_count = c.fetchone()[0]
        print(f"アクティブレコード数: {active_count}")
        
        # 非アクティブなレコード数を確認
        c.execute(f'SELECT COUNT(*) FROM company_line_accounts WHERE company_id = {placeholder} AND status = {placeholder}', (company_id, 'inactive'))
        inactive_count = c.fetchone()[0]
        print(f"非アクティブレコード数: {inactive_count}")
        
        # 最新の10件を表示
        print(f"\n=== 最新10件のレコード ===")
        c.execute(f'''
            SELECT id, content_type, status, created_at 
            FROM company_line_accounts 
            WHERE company_id = {placeholder} 
            ORDER BY created_at DESC 
            LIMIT 10
        ''', (company_id,))
        
        recent_records = c.fetchall()
        for i, record in enumerate(recent_records, 1):
            print(f"{i}. ID: {record[0]}, Content: {record[1]}, Status: {record[2]}, Created: {record[3]}")
        
        # コンテンツタイプ別の集計
        print(f"\n=== コンテンツタイプ別集計 ===")
        c.execute(f'''
            SELECT content_type, status, COUNT(*) 
            FROM company_line_accounts 
            WHERE company_id = {placeholder} 
            GROUP BY content_type, status 
            ORDER BY content_type, status
        ''', (company_id,))
        
        type_summary = c.fetchall()
        for record in type_summary:
            print(f"  {record[0]} ({record[1]}): {record[2]}件")
        
        # 重複チェック
        print(f"\n=== 重複チェック ===")
        c.execute(f'''
            SELECT content_type, status, COUNT(*) 
            FROM company_line_accounts 
            WHERE company_id = {placeholder} 
            GROUP BY content_type, status 
            HAVING COUNT(*) > 1
        ''', (company_id,))
        
        duplicates = c.fetchall()
        if duplicates:
            print("重複レコード発見:")
            for record in duplicates:
                print(f"  {record[0]} ({record[1]}): {record[2]}件")
        else:
            print("重複レコードなし")
        
        conn.close()
        print(f"\n=== 調査完了 ===")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_company_line_accounts()
