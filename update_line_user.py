#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LINEユーザーIDを直接データベースに更新
"""

import os
import sys
sys.path.append('lp')

from utils.db import get_db_connection

def update_line_user():
    """LINEユーザーIDを更新"""
    try:
        print("=== LINEユーザーID更新 ===")
        
        # あなたのLINEユーザーID
        line_user_id = "U1b9d0d75b0c770dc1107dde349d572f7"
        
        print(f"更新対象LINEユーザーID: {line_user_id}")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 既存の企業データを確認
        c.execute('SELECT id, company_name, line_user_id FROM companies ORDER BY id')
        companies = c.fetchall()
        
        print(f"\n=== 既存の企業データ ===")
        for company in companies:
            print(f"企業ID: {company[0]}, 名前: {company[1]}, LINE_ID: {company[2]}")
        
        # 企業ID 1にLINEユーザーIDを更新
        company_id = 1
        c.execute('UPDATE companies SET line_user_id = %s WHERE id = %s', (line_user_id, company_id))
        conn.commit()
        
        print(f"✅ 企業ID {company_id} にLINEユーザーID {line_user_id} を更新しました")
        
        # 更新後の確認
        c.execute('SELECT id, company_name, line_user_id FROM companies WHERE id = %s', (company_id,))
        updated_company = c.fetchone()
        print(f"更新後: 企業ID: {updated_company[0]}, 名前: {updated_company[1]}, LINE_ID: {updated_company[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_line_user() 