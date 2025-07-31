#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PostgreSQLデータベースの全データをクリアするスクリプト
"""

from utils.db import get_db_connection
import os

def clear_all_data():
    """全データをクリア"""
    try:
        print("=== PostgreSQLデータベース全データクリア ===")
        
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
                # テーブル内のレコード数を確認
                c.execute(f'SELECT COUNT(*) FROM {table}')
                count = c.fetchone()[0]
                
                if count > 0:
                    # データを削除
                    c.execute(f'DELETE FROM {table}')
                    deleted_counts[table] = count
                    print(f"✅ {table}: {count}件削除")
                else:
                    print(f"⏭️ {table}: データなし")
                    
            except Exception as e:
                print(f"❌ {table}削除エラー: {e}")
        
        # 変更をコミット
        conn.commit()
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

def clear_company_data_only():
    """企業関連データのみクリア"""
    try:
        print("=== 企業関連データのみクリア ===")
        
        print("削除されるデータ:")
        print("- 企業情報 (companies)")
        print("- LINEアカウント情報 (company_line_accounts)")
        print("- 企業決済情報 (company_payments)")
        print("- 企業デプロイ情報 (company_deployments)")
        
        confirm = input("\n企業関連データのみを削除しますか？ (yes/no): ")
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
        for table, count in deleted_counts.items():
            print(f"  - {table}: {count}件")
        
        return True
        
    except Exception as e:
        print(f"❌ 企業データクリアエラー: {e}")
        return False

def clear_test_data_only():
    """テストデータのみクリア"""
    try:
        print("=== テストデータのみクリア ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # テストデータを特定して削除
        test_patterns = [
            ("companies", "company_name LIKE '%テスト%' OR company_name LIKE '%サンプル%'"),
            ("company_line_accounts", "line_channel_id LIKE '%test%' OR line_channel_id LIKE '%1234567890%'"),
            ("users", "email LIKE '%test%' OR email LIKE '%example%'"),
            ("usage_logs", "content_type LIKE '%テスト%'")
        ]
        
        deleted_counts = {}
        
        for table, condition in test_patterns:
            try:
                # テストデータの数を確認
                c.execute(f'SELECT COUNT(*) FROM {table} WHERE {condition}')
                count = c.fetchone()[0]
                
                if count > 0:
                    c.execute(f'DELETE FROM {table} WHERE {condition}')
                    deleted_counts[table] = count
                    print(f"✅ {table}: {count}件のテストデータ削除")
                else:
                    print(f"⏭️ {table}: テストデータなし")
                    
            except Exception as e:
                print(f"❌ {table}テストデータ削除エラー: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 テストデータクリア完了！")
        for table, count in deleted_counts.items():
            print(f"  - {table}: {count}件")
        
        return True
        
    except Exception as e:
        print(f"❌ テストデータクリアエラー: {e}")
        return False

def show_current_data_status():
    """現在のデータ状況を表示"""
    try:
        print("=== 現在のデータ状況 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        tables = [
            'companies', 'company_line_accounts', 'company_payments', 
            'company_deployments', 'users', 'usage_logs', 
            'subscription_periods', 'cancellation_history', 'user_states'
        ]
        
        for table in tables:
            try:
                c.execute(f'SELECT COUNT(*) FROM {table}')
                count = c.fetchone()[0]
                print(f"📊 {table}: {count}件")
            except Exception as e:
                print(f"❌ {table}: エラー ({e})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ データ状況確認エラー: {e}")

def main():
    """メイン関数"""
    print("🚀 PostgreSQLデータクリアツール")
    print("\n選択してください:")
    print("1. 全データをクリア")
    print("2. 企業関連データのみクリア")
    print("3. テストデータのみクリア")
    print("4. 現在のデータ状況を確認")
    print("5. 終了")
    
    while True:
        choice = input("\n選択 (1-5): ")
        
        if choice == '1':
            clear_all_data()
            break
        elif choice == '2':
            clear_company_data_only()
            break
        elif choice == '3':
            clear_test_data_only()
            break
        elif choice == '4':
            show_current_data_status()
        elif choice == '5':
            print("終了します")
            break
        else:
            print("無効な選択です。1-5を入力してください。")

if __name__ == "__main__":
    main() 