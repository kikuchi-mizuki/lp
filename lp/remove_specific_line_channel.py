#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
特定のLINEチャネルIDを削除するスクリプト
"""

from utils.db import get_db_connection

def remove_specific_line_channel():
    """特定のLINEチャネルID "2007858939" を削除"""
    try:
        print("=== 特定LINEチャネルID削除 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 削除前の確認
        c.execute('''
            SELECT cla.id, cla.company_id, c.company_name, cla.line_channel_id, cla.created_at
            FROM company_line_accounts cla
            JOIN companies c ON cla.company_id = c.id
            WHERE cla.line_channel_id = '2007858939'
        ''')
        
        target_record = c.fetchone()
        
        if target_record:
            print(f"削除対象レコード:")
            print(f"  - ID: {target_record[0]}")
            print(f"  - 企業ID: {target_record[1]}")
            print(f"  - 企業名: {target_record[2]}")
            print(f"  - LINEチャネルID: {target_record[3]}")
            print(f"  - 作成日時: {target_record[4]}")
            
            # 削除実行
            c.execute('''
                DELETE FROM company_line_accounts 
                WHERE line_channel_id = '2007858939'
            ''')
            
            deleted_count = c.rowcount
            conn.commit()
            conn.close()
            
            print(f"\n✅ LINEチャネルID '2007858939' の削除が完了しました！")
            print(f"削除件数: {deleted_count}件")
            
        else:
            print("❌ 削除対象のレコードが見つかりませんでした")
            conn.close()
            
    except Exception as e:
        print(f"❌ 削除エラー: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    remove_specific_line_channel() 