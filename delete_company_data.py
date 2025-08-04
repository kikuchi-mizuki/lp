#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PostgreSQLの企業情報を削除するスクリプト
"""

import sys
sys.path.append('lp')
from utils.db import get_db_connection

def list_all_companies():
    """全企業の一覧を表示"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業情報を取得
        c.execute('''
            SELECT 
                c.id,
                c.company_name,
                c.company_code,
                c.email,
                c.created_at,
                cla.line_channel_id,
                cla.railway_project_id,
                cla.deployment_status
            FROM companies c
            LEFT JOIN company_line_accounts cla ON c.id = cla.company_id
            ORDER BY c.created_at DESC
        ''')
        
        companies = c.fetchall()
        conn.close()
        
        print("=== 現在の企業一覧 ===")
        for company in companies:
            (company_id, company_name, company_code, email, created_at, 
             line_channel_id, railway_project_id, deployment_status) = company
            print(f"企業ID: {company_id}")
            print(f"企業名: {company_name}")
            print(f"企業コード: {company_code}")
            print(f"メール: {email}")
            print(f"作成日: {created_at}")
            print(f"LINEチャネルID: {line_channel_id or '未設定'}")
            print(f"RailwayプロジェクトID: {railway_project_id or '未設定'}")
            print(f"デプロイ状況: {deployment_status or '未設定'}")
            print("-" * 50)
        
        return companies
        
    except Exception as e:
        print(f"❌ 企業一覧取得エラー: {e}")
        return []

def delete_company(company_id):
    """指定された企業IDの情報を削除"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業名を取得（確認用）
        c.execute('SELECT company_name FROM companies WHERE id = %s', (company_id,))
        result = c.fetchone()
        
        if not result:
            print(f"❌ 企業ID {company_id} が見つかりません")
            return False
        
        company_name = result[0]
        print(f"🗑️ 企業 '{company_name}' (ID: {company_id}) を削除します...")
        
        # 関連テーブルから削除（CASCADE制約により自動削除されるはず）
        # 1. company_line_accounts から削除
        c.execute('DELETE FROM company_line_accounts WHERE company_id = %s', (company_id,))
        line_accounts_deleted = c.rowcount
        print(f"  - company_line_accounts: {line_accounts_deleted} 件削除")
        
        # 2. company_payments から削除
        c.execute('DELETE FROM company_payments WHERE company_id = %s', (company_id,))
        payments_deleted = c.rowcount
        print(f"  - company_payments: {payments_deleted} 件削除")
        
        # 3. company_contents から削除
        c.execute('DELETE FROM company_contents WHERE company_id = %s', (company_id,))
        contents_deleted = c.rowcount
        print(f"  - company_contents: {contents_deleted} 件削除")
        
        # 4. companies から削除
        c.execute('DELETE FROM companies WHERE id = %s', (company_id,))
        companies_deleted = c.rowcount
        print(f"  - companies: {companies_deleted} 件削除")
        
        conn.commit()
        conn.close()
        
        if companies_deleted > 0:
            print(f"✅ 企業 '{company_name}' (ID: {company_id}) の削除が完了しました")
            return True
        else:
            print(f"❌ 企業ID {company_id} の削除に失敗しました")
            return False
        
    except Exception as e:
        print(f"❌ 企業削除エラー: {e}")
        return False

def delete_all_companies():
    """全企業の情報を削除"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 削除前の件数を確認
        c.execute('SELECT COUNT(*) FROM companies')
        company_count = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM company_line_accounts')
        line_accounts_count = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM company_payments')
        payments_count = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM company_contents')
        contents_count = c.fetchone()[0]
        
        print(f"🗑️ 全企業データを削除します...")
        print(f"  - companies: {company_count} 件")
        print(f"  - company_line_accounts: {line_accounts_count} 件")
        print(f"  - company_payments: {payments_count} 件")
        print(f"  - company_contents: {contents_count} 件")
        
        # 全テーブルをクリア
        c.execute('DELETE FROM company_line_accounts')
        c.execute('DELETE FROM company_payments')
        c.execute('DELETE FROM company_contents')
        c.execute('DELETE FROM companies')
        
        # シーケンスをリセット
        c.execute('ALTER SEQUENCE companies_id_seq RESTART WITH 1')
        c.execute('ALTER SEQUENCE company_line_accounts_id_seq RESTART WITH 1')
        c.execute('ALTER SEQUENCE company_payments_id_seq RESTART WITH 1')
        c.execute('ALTER SEQUENCE company_contents_id_seq RESTART WITH 1')
        
        conn.commit()
        conn.close()
        
        print("✅ 全企業データの削除が完了しました")
        print("✅ シーケンスもリセットされました")
        return True
        
    except Exception as e:
        print(f"❌ 全企業削除エラー: {e}")
        return False

def main():
    """メイン関数"""
    print("🗑️ PostgreSQL企業情報削除ツール")
    print("=" * 50)
    
    # 現在の企業一覧を表示
    companies = list_all_companies()
    
    if not companies:
        print("削除対象の企業がありません")
        return
    
    print(f"\n削除対象: {len(companies)} 企業")
    print("\n削除オプション:")
    print("1. 特定の企業を削除")
    print("2. 全企業を削除")
    print("3. キャンセル")
    
    while True:
        choice = input("\n選択してください (1-3): ").strip()
        
        if choice == "1":
            # 特定の企業を削除
            try:
                company_id = int(input("削除する企業IDを入力してください: "))
                if delete_company(company_id):
                    print("✅ 削除完了")
                else:
                    print("❌ 削除失敗")
            except ValueError:
                print("❌ 無効な企業IDです")
            break
            
        elif choice == "2":
            # 全企業を削除
            confirm = input("⚠️ 本当に全企業データを削除しますか？ (yes/no): ").strip().lower()
            if confirm == "yes":
                if delete_all_companies():
                    print("✅ 全企業削除完了")
                else:
                    print("❌ 全企業削除失敗")
            else:
                print("削除をキャンセルしました")
            break
            
        elif choice == "3":
            print("削除をキャンセルしました")
            break
            
        else:
            print("❌ 無効な選択です。1-3を入力してください")

if __name__ == "__main__":
    main() 