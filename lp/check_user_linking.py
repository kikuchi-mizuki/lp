#!/usr/bin/env python3
"""
ユーザーの紐付け状況を確認するスクリプト
"""

import os
import sys
sys.path.append('.')

from utils.db import get_db_connection

def check_user_linking():
    """ユーザーの紐付け状況を確認"""
    try:
        print("=== ユーザー紐付け状況確認 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 全企業データを取得
        c.execute('SELECT id, company_name, email, line_user_id FROM companies ORDER BY id')
        companies = c.fetchall()
        
        print(f"\n企業データ数: {len(companies)}")
        print("\n=== 企業データ一覧 ===")
        
        linked_count = 0
        unlinked_count = 0
        
        for company in companies:
            company_id, company_name, email, line_user_id = company
            status = "✅ 紐付け済み" if line_user_id else "❌ 未紐付け"
            print(f"ID: {company_id}")
            print(f"企業名: {company_name}")
            print(f"メール: {email}")
            print(f"LINEユーザーID: {line_user_id}")
            print(f"状態: {status}")
            print("-" * 50)
            
            if line_user_id:
                linked_count += 1
            else:
                unlinked_count += 1
        
        print(f"\n=== 統計 ===")
        print(f"紐付け済み: {linked_count}件")
        print(f"未紐付け: {unlinked_count}件")
        print(f"総数: {len(companies)}件")
        
        # 特定のLINEユーザーIDで検索
        if len(sys.argv) > 1:
            line_user_id = sys.argv[1]
            print(f"\n=== 特定ユーザー検索: {line_user_id} ===")
            
            c.execute('SELECT id, company_name, email FROM companies WHERE line_user_id = %s', (line_user_id,))
            user_companies = c.fetchall()
            
            if user_companies:
                print("紐付け済み企業:")
                for company in user_companies:
                    company_id, company_name, email = company
                    print(f"  - ID: {company_id}, 企業名: {company_name}, メール: {email}")
            else:
                print("紐付け済み企業が見つかりません")
        
        conn.close()
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

def fix_user_linking():
    """ユーザー紐付けを修正"""
    try:
        print("\n=== ユーザー紐付け修正 ===")
        
        # メールアドレスを入力
        email = input("メールアドレスを入力してください: ")
        line_user_id = input("LINEユーザーIDを入力してください: ")
        
        if not email or not line_user_id:
            print("メールアドレスとLINEユーザーIDを入力してください")
            return
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業データを検索
        c.execute('SELECT id, company_name FROM companies WHERE email = %s', (email,))
        company = c.fetchone()
        
        if company:
            company_id, company_name = company
            print(f"企業データ発見: ID={company_id}, 企業名={company_name}")
            
            # 紐付けを更新
            c.execute('UPDATE companies SET line_user_id = %s WHERE id = %s', (line_user_id, company_id))
            conn.commit()
            print(f"紐付け完了: {line_user_id} -> {company_name}")
        else:
            print(f"メールアドレス {email} の企業データが見つかりません")
        
        conn.close()
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("ユーザー紐付け確認・修正ツール")
    print("1. 紐付け状況を確認")
    print("2. 紐付けを修正")
    print("3. 終了")
    
    choice = input("選択してください (1-3): ")
    
    if choice == "1":
        check_user_linking()
    elif choice == "2":
        fix_user_linking()
    elif choice == "3":
        print("終了します")
    else:
        print("無効な選択です")
