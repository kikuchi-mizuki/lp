#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安全なPostgreSQLデータベース全データクリアスクリプト
"""

from utils.db import get_db_connection
import os

def safe_clear_all_data():
    """全データを安全にクリア"""
    try:
        print("=== 安全なPostgreSQLデータベース全データクリア ===")
        
        # 確認メッセージ
        print("⚠️ 警告: この操作により、すべてのデータが削除されます！")
        print("削除されるデータ:")
        print("- 企業情報 (companies)")
        print("- LINEアカウント情報 (company_line_accounts)")
        print("- 企業決済情報 (company_payments)")
        print("- 企業デプロイ情報 (company_deployments)")
        print("- ユーザー情報 (users)")
        print("- 利用ログ (usage_logs)")
        print("- サブスクリプション期間 (subscription_periods)")
        print("- 解約履歴 (cancellation_history)")
        print("- ユーザー状態 (user_states)")
        
        # ユーザー確認
        confirm = input("\n本当にすべてのデータを削除しますか？ (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ データ削除をキャンセルしました")
            return False
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 削除順序（外部キー制約を考慮）
        tables_to_clear = [
            'company_deployments',
            'company_payments', 
            'company_line_accounts',
            'company_subscriptions',  # 追加
            'companies',
            'cancellation_history',
            'usage_logs',
            'subscription_periods',
            'user_states',
            'users'
        ]
        
        deleted_counts = {}
        
        for table in tables_to_clear:
            try:
                # テーブルが存在するかチェック
                c.execute(f'''
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                ''')
                table_exists = c.fetchone()[0]
                
                if not table_exists:
                    print(f"⏭️ {table}: テーブルが存在しません")
                    continue
                
                # テーブル内のレコード数を確認
                c.execute(f'SELECT COUNT(*) FROM {table}')
                count = c.fetchone()[0]
                
                if count > 0:
                    # データを削除
                    c.execute(f'DELETE FROM {table}')
                    deleted_counts[table] = count
                    print(f"✅ {table}: {count}件削除")
                    
                    # 各テーブルごとにコミット
                    conn.commit()
                else:
                    print(f"⏭️ {table}: データなし")
                    
            except Exception as e:
                print(f"❌ {table}削除エラー: {e}")
                # エラーが発生しても続行
                try:
                    conn.rollback()
                except:
                    pass
        
        conn.close()
        
        print(f"\n🎉 データクリア完了！")
        print("削除されたデータ:")
        for table, count in deleted_counts.items():
            print(f"  - {table}: {count}件")
        
        return True
        
    except Exception as e:
        print(f"❌ データクリアエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン関数"""
    safe_clear_all_data()

if __name__ == "__main__":
    main()
