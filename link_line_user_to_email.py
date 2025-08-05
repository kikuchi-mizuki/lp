#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LINEユーザーIDとメールアドレスを紐付けるスクリプト
"""

import os
import sys
sys.path.append('lp')

from utils.db import get_db_connection

def link_line_user_to_email():
    """LINEユーザーIDとメールアドレスを紐付け"""
    try:
        print("=== LINEユーザーIDとメールアドレス紐付け ===")
        
        # 対象データ
        line_user_id = "U1b9d0d75b0c770dc1107dde349d572f7"
        email = "mmms.dy.23@gmail.com"
        
        print(f"LINEユーザーID: {line_user_id}")
        print(f"メールアドレス: {email}")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 現在のデータベース状況を確認
        print(f"\n=== 現在のデータベース状況 ===")
        
        # usersテーブルを確認
        c.execute('SELECT id, email, line_user_id, stripe_subscription_id FROM users')
        users = c.fetchall()
        print(f"usersテーブル:")
        for user in users:
            print(f"  ID: {user[0]}, Email: {user[1]}, LINE_ID: {user[2]}, Stripe: {user[3]}")
        
        # companiesテーブルを確認
        c.execute('SELECT id, company_name, line_user_id, stripe_subscription_id FROM companies')
        companies = c.fetchall()
        print(f"\ncompaniesテーブル:")
        for company in companies:
            print(f"  ID: {company[0]}, 名前: {company[1]}, LINE_ID: {company[2]}, Stripe: {company[3]}")
        
        # 選択肢を提示
        print(f"\n=== 紐付け方法を選択してください ===")
        print("1. 既存のusersレコードにLINEユーザーIDを追加")
        print("2. 既存のcompaniesレコードにLINEユーザーIDを更新")
        print("3. 新しいusersレコードを作成")
        print("4. 新しいcompaniesレコードを作成")
        
        choice = input("選択してください (1-4): ").strip()
        
        if choice == "1":
            # 既存のusersレコードにLINEユーザーIDを追加
            user_id = input("更新するユーザーIDを入力してください: ").strip()
            
            if user_id:
                c.execute('UPDATE users SET line_user_id = %s WHERE id = %s', (line_user_id, user_id))
                conn.commit()
                print(f"✅ ユーザーID {user_id} にLINEユーザーID {line_user_id} を追加しました")
            else:
                print("❌ ユーザーIDが入力されていません")
                
        elif choice == "2":
            # 既存のcompaniesレコードにLINEユーザーIDを更新
            company_id = input("更新する企業IDを入力してください: ").strip()
            
            if company_id:
                c.execute('UPDATE companies SET line_user_id = %s WHERE id = %s', (line_user_id, company_id))
                conn.commit()
                print(f"✅ 企業ID {company_id} にLINEユーザーID {line_user_id} を更新しました")
            else:
                print("❌ 企業IDが入力されていません")
                
        elif choice == "3":
            # 新しいusersレコードを作成
            c.execute('''
                INSERT INTO users (email, line_user_id, stripe_customer_id, stripe_subscription_id, created_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            ''', (email, line_user_id, f"cus_{line_user_id[-8:]}", f"sub_{line_user_id[-8:]}"))
            
            user_id = c.lastrowid
            conn.commit()
            print(f"✅ 新しいユーザーレコードを作成しました: ID={user_id}, Email={email}")
            
        elif choice == "4":
            # 新しいcompaniesレコードを作成
            company_name = input("企業名を入力してください: ").strip()
            
            if company_name:
                c.execute('''
                    INSERT INTO companies (company_name, line_user_id, company_code, stripe_subscription_id, status, created_at)
                    VALUES (%s, %s, %s, %s, 'active', CURRENT_TIMESTAMP)
                ''', (company_name, line_user_id, f"company_{line_user_id[-8:]}", f"sub_{line_user_id[-8:]}"))
                
                company_id = c.lastrowid
                conn.commit()
                print(f"✅ 新しい企業レコードを作成しました: ID={company_id}, 名前={company_name}")
                
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
        
        # 更新後の確認
        print(f"\n=== 更新後の確認 ===")
        c.execute('SELECT id, email, line_user_id FROM users WHERE line_user_id = %s', (line_user_id,))
        user_result = c.fetchone()
        if user_result:
            print(f"usersテーブル: ID={user_result[0]}, Email={user_result[1]}, LINE_ID={user_result[2]}")
        
        c.execute('SELECT id, company_name, line_user_id FROM companies WHERE line_user_id = %s', (line_user_id,))
        company_result = c.fetchone()
        if company_result:
            print(f"companiesテーブル: ID={company_result[0]}, 名前={company_result[1]}, LINE_ID={company_result[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    link_line_user_to_email() 