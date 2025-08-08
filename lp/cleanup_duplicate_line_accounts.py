#!/usr/bin/env python3
"""
重複したLINEアカウントレコードをクリーンアップするスクリプト
"""

import os
import sys
from dotenv import load_dotenv

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import get_db_connection, get_db_type

def cleanup_duplicate_line_accounts():
    """重複したLINEアカウントレコードをクリーンアップ"""
    print("=== 重複LINEアカウントレコードクリーンアップ ===")
    
    try:
        # 環境変数を読み込み
        load_dotenv()
        
        # データベース接続
        conn = get_db_connection()
        c = conn.cursor()
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        # 企業ID 12のデータをクリーンアップ
        company_id = 12
        
        print(f"クリーンアップ対象企業ID: {company_id}")
        
        # クリーンアップ前の状況確認
        c.execute(f'SELECT COUNT(*) FROM company_line_accounts WHERE company_id = {placeholder}', (company_id,))
        before_count = c.fetchone()[0]
        print(f"クリーンアップ前のレコード数: {before_count}")
        
        # 重複レコードを特定（同じcontent_typeとstatusの組み合わせで最新以外を削除）
        print(f"\n=== 重複レコードの特定 ===")
        
        if db_type == 'postgresql':
            # PostgreSQL用のクエリ
            c.execute(f'''
                DELETE FROM company_line_accounts 
                WHERE id NOT IN (
                    SELECT MAX(id) 
                    FROM company_line_accounts 
                    WHERE company_id = {placeholder} 
                    GROUP BY content_type, status
                ) 
                AND company_id = {placeholder}
            ''', (company_id, company_id))
        else:
            # SQLite用のクエリ
            c.execute(f'''
                DELETE FROM company_line_accounts 
                WHERE id NOT IN (
                    SELECT MAX(id) 
                    FROM company_line_accounts 
                    WHERE company_id = {placeholder} 
                    GROUP BY content_type, status
                ) 
                AND company_id = {placeholder}
            ''', (company_id, company_id))
        
        deleted_count = c.rowcount
        print(f"削除されたレコード数: {deleted_count}")
        
        # クリーンアップ後の状況確認
        c.execute(f'SELECT COUNT(*) FROM company_line_accounts WHERE company_id = {placeholder}', (company_id,))
        after_count = c.fetchone()[0]
        print(f"クリーンアップ後のレコード数: {after_count}")
        
        # アクティブなレコード数を確認
        c.execute(f'SELECT COUNT(*) FROM company_line_accounts WHERE company_id = {placeholder} AND status = {placeholder}', (company_id, 'active'))
        active_count = c.fetchone()[0]
        print(f"アクティブレコード数: {active_count}")
        
        # 最新のレコードを表示
        print(f"\n=== クリーンアップ後の最新レコード ===")
        c.execute(f'''
            SELECT id, content_type, status, created_at 
            FROM company_line_accounts 
            WHERE company_id = {placeholder} 
            ORDER BY created_at DESC
        ''', (company_id,))
        
        remaining_records = c.fetchall()
        for i, record in enumerate(remaining_records, 1):
            print(f"{i}. ID: {record[0]}, Content: {record[1]}, Status: {record[2]}, Created: {record[3]}")
        
        # 変更をコミット
        conn.commit()
        print(f"\n=== クリーンアップ完了 ===")
        print(f"削除されたレコード: {deleted_count}件")
        print(f"残存レコード: {after_count}件")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    cleanup_duplicate_line_accounts()
