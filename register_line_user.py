#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LINEユーザーIDをデータベースに登録するスクリプト
"""

import os
import sys
sys.path.append('lp')

from utils.db import get_db_connection

def register_line_user():
    """LINEユーザーIDをデータベースに登録"""
    try:
        print("=== LINEユーザーID登録 ===")
        
        # あなたのLINEユーザーID
        line_user_id = "U1b9d0d75b0c770dc1107dde349d572f7"
        
        print(f"登録対象LINEユーザーID: {line_user_id}")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 既存の企業データを確認
        c.execute('SELECT id, company_name, line_user_id FROM companies ORDER BY id')
        companies = c.fetchall()
        
        print(f"\n=== 既存の企業データ ===")
        for company in companies:
            print(f"企業ID: {company[0]}, 名前: {company[1]}, LINE_ID: {company[2]}")
        
        # 選択肢を提示
        print(f"\n=== 登録方法を選択してください ===")
        print("1. 既存の企業データに紐付ける")
        print("2. 新しい企業データを作成する")
        
        choice = input("選択してください (1 or 2): ").strip()
        
        if choice == "1":
            # 既存の企業データに紐付ける
            company_id = input("紐付ける企業IDを入力してください: ").strip()
            
            if company_id:
                c.execute('UPDATE companies SET line_user_id = %s WHERE id = %s', (line_user_id, company_id))
                conn.commit()
                print(f"✅ 企業ID {company_id} にLINEユーザーID {line_user_id} を紐付けました")
            else:
                print("❌ 企業IDが入力されていません")
                
        elif choice == "2":
            # 新しい企業データを作成
            company_name = input("企業名を入力してください: ").strip()
            
            if company_name:
                c.execute('''
                    INSERT INTO companies (company_name, line_user_id, company_code, status, created_at)
                    VALUES (%s, %s, %s, 'active', CURRENT_TIMESTAMP)
                ''', (company_name, line_user_id, f"company_{line_user_id[-8:]}"))
                
                company_id = c.lastrowid
                conn.commit()
                print(f"✅ 新しい企業データを作成しました: ID={company_id}, 名前={company_name}")
                
                # 決済データも作成
                c.execute('''
                    INSERT INTO company_payments (company_id, stripe_customer_id, stripe_subscription_id, subscription_status, created_at)
                    VALUES (%s, %s, %s, 'active', CURRENT_TIMESTAMP)
                ''', (company_id, f"cus_{line_user_id[-8:]}", f"sub_{line_user_id[-8:]}"))
                
                conn.commit()
                print(f"✅ 決済データも作成しました: status=active")
            else:
                print("❌ 企業名が入力されていません")
        else:
            print("❌ 無効な選択です")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    register_line_user() 