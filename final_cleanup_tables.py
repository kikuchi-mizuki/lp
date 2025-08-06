#!/usr/bin/env python3
"""
残りの不要なテーブルを完全に削除するスクリプト
"""

import os
import sys
from dotenv import load_dotenv

# 現在のディレクトリをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# lpディレクトリをパスに追加
lp_dir = os.path.join(current_dir, 'lp')
if lp_dir not in sys.path:
    sys.path.insert(0, lp_dir)

from lp.utils.db import get_db_connection, get_db_type

load_dotenv()

def final_cleanup_tables():
    """
    残りの不要なテーブルを完全に削除
    """
    conn = None
    c = None
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        db_type = get_db_type()
        print(f"📊 データベースタイプ: {db_type}")
        
        # 削除する残りのテーブルリスト
        remaining_tables_to_drop = [
            'subscription_periods',
            'user_states', 
            'cancellation_history',
            'company_contents'  # 古い設計のテーブル
        ]
        
        print("🗑️  残りの不要なテーブルの削除を開始します...")
        
        for table_name in remaining_tables_to_drop:
            try:
                # テーブルが存在するかチェック
                if db_type == 'postgresql':
                    c.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = %s
                        )
                    """, (table_name,))
                else:
                    c.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name=?
                    """, (table_name,))
                
                table_exists = c.fetchone()
                
                if table_exists and (db_type == 'postgresql' and table_exists[0]) or (db_type == 'sqlite' and table_exists):
                    # CASCADEオプションでテーブルを削除
                    c.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                    print(f"✅ {table_name} テーブルを削除しました（CASCADE）")
                else:
                    print(f"ℹ️  {table_name} テーブルは存在しません（スキップ）")
                    
            except Exception as e:
                print(f"❌ {table_name} テーブルの削除中にエラー: {e}")
                continue
        
        # 最終的なテーブル一覧を確認
        print("\n📋 最終的なテーブル一覧:")
        
        if db_type == 'postgresql':
            c.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
        else:
            c.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table'
                ORDER BY name
            """)
        
        remaining_tables = c.fetchall()
        
        print("📊 残っているテーブル:")
        for table in remaining_tables:
            table_name = table[0] if db_type == 'postgresql' else table[0]
            print(f"  - {table_name}")
        
        # 企業ユーザー専用の最小限テーブルが存在するか最終確認
        required_tables = ['companies', 'company_line_accounts', 'company_subscriptions']
        existing_tables = [table[0] if db_type == 'postgresql' else table[0] for table in remaining_tables]
        
        print("\n✅ 企業ユーザー専用最小限テーブルの最終確認:")
        all_required_exist = True
        for required_table in required_tables:
            if required_table in existing_tables:
                print(f"  ✅ {required_table} - 存在")
            else:
                print(f"  ❌ {required_table} - 存在しない")
                all_required_exist = False
        
        if all_required_exist:
            print("\n🎉 企業ユーザー専用最小限データベースの準備が完了しました！")
        else:
            print("\n⚠️  必要なテーブルが不足しています")
        
        conn.commit()
        print("\n✨ 最終クリーンアップが完了しました")
        
    except Exception as e:
        print(f"❌ 最終クリーンアップエラー: {e}")
        if conn:
            conn.rollback()
    finally:
        if c:
            c.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🧹 残りの不要なテーブルの最終削除を開始します...")
    
    # 残りの不要なテーブルを削除
    final_cleanup_tables()
    
    print("\n📝 次のステップ:")
    print("1. LPでの決済フォーム実装")
    print("2. Stripe決済連携実装")
    print("3. LINE API連携実装") 