#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
特定の企業を削除するスクリプト
"""

from utils.db import get_db_connection

def remove_specific_company():
    """企業 "株式会社サンプル" を削除"""
    try:
        print("=== 特定企業削除 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 削除前の確認
        c.execute('''
            SELECT id, company_name, company_code, email, created_at
            FROM companies
            WHERE company_name = '株式会社サンプル'
        ''')
        
        target_company = c.fetchone()
        
        if target_company:
            company_id = target_company[0]
            print(f"削除対象企業:")
            print(f"  - ID: {target_company[0]}")
            print(f"  - 企業名: {target_company[1]}")
            print(f"  - 企業コード: {target_company[2]}")
            print(f"  - メール: {target_company[3]}")
            print(f"  - 作成日時: {target_company[4]}")
            
            # 関連データの確認
            c.execute('SELECT COUNT(*) FROM company_line_accounts WHERE company_id = %s', (company_id,))
            line_accounts_count = c.fetchone()[0]
            
            c.execute('SELECT COUNT(*) FROM company_payments WHERE company_id = %s', (company_id,))
            payments_count = c.fetchone()[0]
            
            c.execute('SELECT COUNT(*) FROM company_deployments WHERE company_id = %s', (company_id,))
            deployments_count = c.fetchone()[0]
            
            print(f"\n関連データ:")
            print(f"  - LINEアカウント: {line_accounts_count}件")
            print(f"  - 決済情報: {payments_count}件")
            print(f"  - デプロイ情報: {deployments_count}件")
            
            # 外部キー制約の順序で削除
            print(f"\n🚀 データ削除を開始します...")
            
            c.execute('DELETE FROM company_deployments WHERE company_id = %s', (company_id,))
            print(f"✅ company_deployments: {deployments_count}件削除")
            
            c.execute('DELETE FROM company_payments WHERE company_id = %s', (company_id,))
            print(f"✅ company_payments: {payments_count}件削除")
            
            c.execute('DELETE FROM company_line_accounts WHERE company_id = %s', (company_id,))
            print(f"✅ company_line_accounts: {line_accounts_count}件削除")
            
            # 最後に企業を削除
            c.execute('DELETE FROM companies WHERE id = %s', (company_id,))
            company_deleted = c.rowcount
            
            conn.commit()
            conn.close()
            
            print(f"✅ companies: {company_deleted}件削除")
            print(f"\n🎉 企業 '株式会社サンプル' の削除が完了しました！")
            
        else:
            print("❌ 削除対象の企業が見つかりませんでした")
            conn.close()
            
    except Exception as e:
        print(f"❌ 削除エラー: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    remove_specific_company() 