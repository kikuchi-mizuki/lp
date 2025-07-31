#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
企業関連データのみをクリアするスクリプト
"""

from utils.db import get_db_connection

def clear_company_data():
    """企業関連データのみクリア"""
    try:
        print("=== 企業関連データクリア ===")
        
        print("削除されるデータ:")
        print("- 企業情報 (companies): 8件")
        print("- LINEアカウント情報 (company_line_accounts): 8件")
        print("- 企業決済情報 (company_payments): 8件")
        print("- 企業デプロイ情報 (company_deployments): 0件")
        print("\n合計: 24件のレコードが削除されます")
        
        confirm = input("\n企業関連データを削除しますか？ (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ データ削除をキャンセルしました")
            return False
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業関連テーブルのみ削除
        company_tables = [
            'company_deployments',
            'company_payments',
            'company_line_accounts', 
            'companies'
        ]
        
        deleted_counts = {}
        
        for table in company_tables:
            try:
                c.execute(f'SELECT COUNT(*) FROM {table}')
                count = c.fetchone()[0]
                
                if count > 0:
                    c.execute(f'DELETE FROM {table}')
                    deleted_counts[table] = count
                    print(f"✅ {table}: {count}件削除")
                else:
                    print(f"⏭️ {table}: データなし")
                    
            except Exception as e:
                print(f"❌ {table}削除エラー: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 企業関連データクリア完了！")
        total_deleted = sum(deleted_counts.values())
        print(f"削除されたレコード数: {total_deleted}件")
        
        return True
        
    except Exception as e:
        print(f"❌ 企業データクリアエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    clear_company_data() 