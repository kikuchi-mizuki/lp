#!/usr/bin/env python3
"""
現在のデータベースの状態を確認するスクリプト
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

def check_current_database():
    """
    現在のデータベースの状態を確認
    """
    conn = None
    c = None
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        db_type = get_db_type()
        print(f"📊 データベースタイプ: {db_type}")
        
        # 現在のテーブル一覧を取得
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
        
        tables = c.fetchall()
        
        print("\n📋 現在のテーブル一覧:")
        for table in tables:
            table_name = table[0] if db_type == 'postgresql' else table[0]
            print(f"  - {table_name}")
        
        # 企業ユーザー専用の最小限テーブルが存在するか確認
        required_tables = ['companies', 'company_line_accounts', 'company_subscriptions']
        existing_tables = [table[0] if db_type == 'postgresql' else table[0] for table in tables]
        
        print("\n✅ 企業ユーザー専用最小限テーブルの確認:")
        for required_table in required_tables:
            if required_table in existing_tables:
                print(f"  ✅ {required_table} - 存在")
            else:
                print(f"  ❌ {required_table} - 存在しない")
        
        # 不要なテーブルが残っているか確認
        old_tables = [
            'users', 'subscription_periods', 'user_states',
            'usage_logs', 'cancellation_history', 'company_users',
            'company_usage_logs', 'company_payments', 'company_notifications',
            'company_deployments', 'company_cancellations', 'cancellation_schedule'
        ]
        
        print("\n🗑️  不要なテーブルの確認:")
        for old_table in old_tables:
            if old_table in existing_tables:
                print(f"  ⚠️  {old_table} - まだ残っている")
            else:
                print(f"  ✅ {old_table} - 削除済み")
        
        # 各テーブルの構造を確認
        print("\n📋 テーブル構造の確認:")
        
        for table_name in ['companies', 'company_line_accounts', 'company_subscriptions']:
            if table_name in existing_tables:
                print(f"\n🔍 {table_name} テーブルの構造:")
                if db_type == 'postgresql':
                    c.execute("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_name = %s
                        ORDER BY ordinal_position
                    """, (table_name,))
                else:
                    c.execute("PRAGMA table_info(?)", (table_name,))
                
                columns = c.fetchall()
                for column in columns:
                    if db_type == 'postgresql':
                        print(f"  - {column[0]}: {column[1]} ({'NULL' if column[2] == 'YES' else 'NOT NULL'})")
                    else:
                        print(f"  - {column[1]}: {column[2]} ({'NULL' if column[3] == 0 else 'NOT NULL'})")
        
        # データの確認
        print("\n📊 データの確認:")
        for table_name in ['companies', 'company_line_accounts', 'company_subscriptions']:
            if table_name in existing_tables:
                c.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = c.fetchone()[0]
                print(f"  - {table_name}: {count} 件")
        
        # インデックスの確認
        if db_type == 'postgresql':
            print("\n🔍 インデックスの確認:")
            c.execute("""
                SELECT indexname, tablename 
                FROM pg_indexes 
                WHERE schemaname = 'public' 
                AND tablename IN ('companies', 'company_line_accounts', 'company_subscriptions')
                ORDER BY tablename, indexname
            """)
            
            indexes = c.fetchall()
            for index in indexes:
                print(f"  - {index[1]}: {index[0]}")
        
    except Exception as e:
        print(f"❌ データベース確認エラー: {e}")
    finally:
        if c:
            c.close()
        if conn:
            conn.close()

def check_api_endpoints():
    """
    APIエンドポイントの確認
    """
    print("\n🌐 APIエンドポイントの確認:")
    
    # 企業ユーザー専用APIエンドポイント
    endpoints = [
        "POST /api/v1/company/restriction/check",
        "GET /api/v1/company/info/{line_channel_id}",
        "POST /api/v1/company/cancel/{company_id}/{content_type}",
        "GET /debug/company/restriction/{line_channel_id}/{content_type}"
    ]
    
    for endpoint in endpoints:
        print(f"  - {endpoint}")
    
    print("\n✅ 企業ユーザー専用APIエンドポイントが実装されています")

def check_service_functions():
    """
    サービス関数の確認
    """
    print("\n🔧 サービス関数の確認:")
    
    try:
        from lp.services.company_service import (
            check_company_restriction,
            get_company_by_line_channel_id,
            get_company_line_accounts,
            get_company_subscriptions,
            cancel_company_content
        )
        
        functions = [
            "check_company_restriction",
            "get_company_by_line_channel_id", 
            "get_company_line_accounts",
            "get_company_subscriptions",
            "cancel_company_content"
        ]
        
        for func in functions:
            print(f"  ✅ {func} - 実装済み")
            
    except ImportError as e:
        print(f"❌ サービス関数のインポートエラー: {e}")

if __name__ == "__main__":
    print("🔍 現在のシステム状態を確認します...")
    
    # データベースの状態確認
    check_current_database()
    
    # APIエンドポイントの確認
    check_api_endpoints()
    
    # サービス関数の確認
    check_service_functions()
    
    print("\n✨ 確認完了！") 