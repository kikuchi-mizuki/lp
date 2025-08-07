#!/usr/bin/env python3
"""
AI経理秘書を削除するスクリプト
"""
import os, sys
from dotenv import load_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
from utils.db import get_db_connection, get_db_type

def remove_ai_accounting():
    print("🚀 AI経理秘書の削除を開始します")
    try:
        conn = get_db_connection()
        c = conn.cursor()
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        print("=== 削除前の状況確認 ===")
        c.execute(f'SELECT * FROM company_content_additions WHERE company_id = {placeholder}', (5,))
        content_additions = c.fetchall()
        for addition in content_additions:
            print(f"  - ID: {addition[0]}, コンテンツ: {addition[2]}, 追加料金: {addition[3]}円, ステータス: {addition[4]}")
        
        print("\n=== AI経理秘書を削除 ===")
        c.execute(f'DELETE FROM company_content_additions WHERE company_id = {placeholder} AND content_type = {placeholder}', (5, 'AI経理秘書'))
        deleted_count = c.rowcount
        print(f"✅ {deleted_count}件のAI経理秘書を削除しました")
        
        conn.commit()
        
        print("\n=== 削除後の状況確認 ===")
        c.execute(f'SELECT * FROM company_content_additions WHERE company_id = {placeholder}', (5,))
        remaining_additions = c.fetchall()
        for addition in remaining_additions:
            print(f"  - ID: {addition[0]}, コンテンツ: {addition[2]}, 追加料金: {addition[3]}円, ステータス: {addition[4]}")
        
        conn.close()
        print("\n✅ AI経理秘書の削除完了")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    remove_ai_accounting()
