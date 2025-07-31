#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
企業デプロイ管理テーブル作成スクリプト
"""

import os
import sys
import time
from utils.db import get_db_connection, get_db_type

def create_company_deployments_table():
    """企業デプロイ管理テーブルを作成"""
    try:
        print("=== 企業デプロイ管理テーブル作成 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        db_type = get_db_type()
        print(f"データベースタイプ: {db_type}")
        
        if db_type == 'postgresql':
            # PostgreSQL用のテーブル作成
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_deployments (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL,
                    railway_project_id VARCHAR(255),
                    railway_url VARCHAR(500),
                    deployment_status VARCHAR(50) DEFAULT 'pending',
                    deployment_log TEXT,
                    environment_variables JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
                )
            ''')
            
            # インデックスを作成
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_company_deployments_company_id 
                ON company_deployments (company_id)
            ''')
            
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_company_deployments_status 
                ON company_deployments (deployment_status)
            ''')
            
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_company_deployments_railway_project_id 
                ON company_deployments (railway_project_id)
            ''')
            
        else:
            # SQLite用のテーブル作成
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_deployments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    railway_project_id TEXT,
                    railway_url TEXT,
                    deployment_status TEXT DEFAULT 'pending',
                    deployment_log TEXT,
                    environment_variables TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies (id)
                )
            ''')
            
            # インデックスを作成
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_company_deployments_company_id 
                ON company_deployments (company_id)
            ''')
            
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_company_deployments_status 
                ON company_deployments (deployment_status)
            ''')
            
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_company_deployments_railway_project_id 
                ON company_deployments (railway_project_id)
            ''')
        
        conn.commit()
        conn.close()
        
        print("✅ 企業デプロイ管理テーブルを作成しました")
        
        # テーブル構造を確認
        verify_table_structure()
        
        return True
        
    except Exception as e:
        print(f"❌ テーブル作成エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_table_structure():
    """テーブル構造を確認"""
    try:
        print("\n=== テーブル構造確認 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        db_type = get_db_type()
        
        if db_type == 'postgresql':
            # PostgreSQL用の構造確認
            c.execute('''
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'company_deployments'
                ORDER BY ordinal_position
            ''')
            
            columns = c.fetchall()
            
            print("📋 company_deployments テーブル構造:")
            for column in columns:
                print(f"  - {column[0]}: {column[1]} ({'NULL可' if column[2] == 'YES' else 'NULL不可'})")
                if column[3]:
                    print(f"    デフォルト値: {column[3]}")
            
            # 制約を確認
            c.execute('''
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints
                WHERE table_name = 'company_deployments'
            ''')
            
            constraints = c.fetchall()
            
            print("\n🔒 制約:")
            for constraint in constraints:
                print(f"  - {constraint[0]}: {constraint[1]}")
            
            # インデックスを確認
            c.execute('''
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'company_deployments'
            ''')
            
            indexes = c.fetchall()
            
            print("\n📊 インデックス:")
            for index in indexes:
                print(f"  - {index[0]}")
            
        else:
            # SQLite用の構造確認
            c.execute('PRAGMA table_info(company_deployments)')
            columns = c.fetchall()
            
            print("📋 company_deployments テーブル構造:")
            for column in columns:
                print(f"  - {column[1]}: {column[2]} ({'NULL可' if column[3] == 0 else 'NULL不可'})")
                if column[4]:
                    print(f"    デフォルト値: {column[4]}")
            
            # インデックスを確認
            c.execute('PRAGMA index_list(company_deployments)')
            indexes = c.fetchall()
            
            print("\n📊 インデックス:")
            for index in indexes:
                print(f"  - {index[1]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ テーブル構造確認エラー: {e}")

def create_sample_deployment_data():
    """サンプルデプロイデータを作成"""
    try:
        print("\n=== サンプルデプロイデータ作成 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 既存の企業を確認
        c.execute('SELECT id, company_name FROM companies LIMIT 3')
        companies = c.fetchall()
        
        if not companies:
            print("❌ 企業データが見つかりません。先に企業データを作成してください。")
            return False
        
        print(f"サンプルデプロイデータ作成対象企業数: {len(companies)}")
        
        for company in companies:
            company_id = company[0]
            company_name = company[1]
            
            # 既存のデプロイデータをチェック
            c.execute('''
                SELECT id FROM company_deployments 
                WHERE company_id = %s
            ''', (company_id,))
            
            existing = c.fetchone()
            if existing:
                print(f"⚠️  企業 {company_name} は既にデプロイデータが存在します")
                continue
            
            # サンプルデプロイデータを作成
            railway_project_id = f"proj_{company_id}_{int(time.time())}"
            railway_url = f"https://{company_name.lower().replace(' ', '-')}-line-bot.railway.app"
            
            c.execute('''
                INSERT INTO company_deployments (
                    company_id, railway_project_id, railway_url, deployment_status,
                    deployment_log, environment_variables
                ) VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                company_id,
                railway_project_id,
                railway_url,
                'pending',
                'デプロイ待機中',
                '{"LINE_CHANNEL_ACCESS_TOKEN": "sample_token", "LINE_CHANNEL_SECRET": "sample_secret"}'
            ))
            
            print(f"✅ 企業 {company_name} のサンプルデプロイデータを作成しました")
            print(f"  - プロジェクトID: {railway_project_id}")
            print(f"  - Railway URL: {railway_url}")
        
        conn.commit()
        conn.close()
        
        print("\n✅ サンプルデプロイデータの作成が完了しました")
        return True
        
    except Exception as e:
        print(f"❌ サンプルデプロイデータ作成エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン関数"""
    print("🚀 企業デプロイ管理テーブル作成を開始します")
    
    import time
    
    # 1. テーブル作成
    if create_company_deployments_table():
        print("✅ テーブル作成が完了しました")
        
        # 2. サンプルデータ作成（オプション）
        create_sample = input("\nサンプルデプロイデータを作成しますか？ (y/n): ").lower().strip()
        if create_sample == 'y':
            create_sample_deployment_data()
        
        print("\n🎉 企業デプロイ管理システムの準備が完了しました！")
        print("\n📋 次のステップ:")
        print("1. Railway API トークンを設定")
        print("2. 企業情報登録フォームをテスト")
        print("3. 自動デプロイ機能をテスト")
        print("4. 本格運用開始")
        
    else:
        print("❌ テーブル作成に失敗しました")

if __name__ == "__main__":
    main() 