#!/usr/bin/env python3
"""
データベース接続詳細確認スクリプト
"""

import os
import psycopg2
import sqlite3

def check_database_connection_details():
    """データベース接続の詳細情報を確認"""
    print("=== データベース接続詳細確認 ===")
    
    # 環境変数の確認
    print(f"\n📋 環境変数確認:")
    database_url = os.getenv('DATABASE_URL')
    print(f"  DATABASE_URL: {database_url or '未設定'}")
    
    # データベース接続情報の解析
    if database_url and database_url.startswith('postgresql://'):
        print(f"  ✅ PostgreSQL接続URLが設定されています")
        try:
            # URLから接続情報を解析
            from urllib.parse import urlparse
            parsed = urlparse(database_url)
            print(f"  ホスト: {parsed.hostname}")
            print(f"  ポート: {parsed.port}")
            print(f"  データベース: {parsed.path[1:]}")
            print(f"  ユーザー: {parsed.username}")
        except Exception as e:
            print(f"  ❌ URL解析エラー: {e}")
    else:
        print(f"  ℹ️ ローカルPostgreSQL接続を使用")
    
    # 実際の接続テスト
    print(f"\n🔗 接続テスト:")
    try:
        if database_url and database_url.startswith('postgresql://'):
            # 環境変数のPostgreSQLに接続
            conn = psycopg2.connect(database_url)
            print(f"  ✅ 環境変数のPostgreSQL接続成功")
        else:
            # ローカルPostgreSQLに接続
            conn = psycopg2.connect(
                host="localhost",
                database="ai_collections",
                user="postgres",
                password="password"
            )
            print(f"  ✅ ローカルPostgreSQL接続成功")
        
        c = conn.cursor()
        
        # データベース情報の取得
        c.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port()")
        db_info = c.fetchone()
        print(f"  接続先データベース: {db_info[0]}")
        print(f"  接続ユーザー: {db_info[1]}")
        print(f"  サーバーアドレス: {db_info[2]}")
        print(f"  サーバーポート: {db_info[3]}")
        
        # テーブル一覧の取得
        c.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = c.fetchall()
        
        print(f"\n📋 テーブル一覧 ({len(tables)}件):")
        for table in tables:
            print(f"  - {table[0]}")
        
        # 企業管理テーブルの確認
        company_tables = [table[0] for table in tables if table[0].startswith('company')]
        print(f"\n🏢 企業管理テーブル ({len(company_tables)}件):")
        for table in company_tables:
            print(f"  - {table}")
        
        # 企業データの確認
        if 'companies' in [table[0] for table in tables]:
            c.execute("SELECT COUNT(*) FROM companies")
            company_count = c.fetchone()[0]
            print(f"\n📊 企業データ:")
            print(f"  企業数: {company_count}")
            
            if company_count > 0:
                c.execute("SELECT id, company_name, company_code, created_at FROM companies ORDER BY created_at DESC LIMIT 3")
                companies = c.fetchall()
                print(f"  最新3件:")
                for company in companies:
                    print(f"    - ID: {company[0]}, 名前: {company[1]}, コード: {company[2]}, 作成日: {company[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"  ❌ 接続エラー: {e}")
        import traceback
        traceback.print_exc()

def check_railway_connection():
    """Railway接続の確認"""
    print(f"\n=== Railway接続確認 ===")
    
    railway_token = os.getenv('RAILWAY_TOKEN')
    if not railway_token:
        print(f"❌ RAILWAY_TOKEN環境変数が設定されていません")
        return
    
    try:
        import requests
        
        headers = {
            'Authorization': f'Bearer {railway_token}',
            'Content-Type': 'application/json'
        }
        
        # Railwayプロジェクト一覧を取得
        response = requests.get('https://backboard.railway.app/graphql/v2', 
                              headers=headers,
                              json={
                                  "query": """
                                  query {
                                    projects {
                                      nodes {
                                        id
                                        name
                                        description
                                      }
                                    }
                                  }
                                  """
                              })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Railway接続成功")
            print(f"プロジェクト数: {len(data.get('data', {}).get('projects', {}).get('nodes', []))}")
        else:
            print(f"❌ Railway接続失敗: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Railway接続エラー: {e}")

def check_local_postgresql():
    """ローカルPostgreSQL接続の確認"""
    print(f"\n=== ローカルPostgreSQL確認 ===")
    
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="ai_collections",
            user="postgres",
            password="password"
        )
        
        c = conn.cursor()
        c.execute("SELECT current_database(), current_user")
        db_info = c.fetchone()
        print(f"✅ ローカルPostgreSQL接続成功")
        print(f"  データベース: {db_info[0]}")
        print(f"  ユーザー: {db_info[1]}")
        
        # テーブル一覧
        c.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = c.fetchall()
        
        print(f"  テーブル数: {len(tables)}")
        company_tables = [table[0] for table in tables if table[0].startswith('company')]
        print(f"  企業管理テーブル数: {len(company_tables)}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ ローカルPostgreSQL接続エラー: {e}")

if __name__ == "__main__":
    check_database_connection_details()
    check_railway_connection()
    check_local_postgresql()
    
    print(f"\n🎯 推奨アクション:")
    print(f"1. PostgreSQL管理画面が正しいデータベースを参照しているか確認")
    print(f"2. 環境変数DATABASE_URLが正しく設定されているか確認")
    print(f"3. RailwayのデータベースURLとローカルのデータベースURLが一致しているか確認") 