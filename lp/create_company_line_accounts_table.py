#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
企業別LINEアカウント管理テーブル作成スクリプト
"""

import os
import sys
from utils.db import get_db_connection, get_db_type

def create_company_line_accounts_table():
    """企業別LINEアカウント管理テーブルを作成"""
    try:
        print("=== 企業別LINEアカウント管理テーブル作成 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        db_type = get_db_type()
        print(f"データベースタイプ: {db_type}")
        
        if db_type == 'postgresql':
            # PostgreSQL用のテーブル作成
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_line_accounts (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL,
                    line_channel_id VARCHAR(255) NOT NULL UNIQUE,
                    line_channel_access_token VARCHAR(255) NOT NULL,
                    line_channel_secret VARCHAR(255) NOT NULL,
                    line_basic_id VARCHAR(255),
                    line_qr_code_url VARCHAR(500),
                    webhook_url VARCHAR(500),
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
                )
            ''')
            
            # インデックスを作成
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_company_line_accounts_company_id 
                ON company_line_accounts (company_id)
            ''')
            
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_company_line_accounts_status 
                ON company_line_accounts (status)
            ''')
            
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_company_line_accounts_channel_id 
                ON company_line_accounts (line_channel_id)
            ''')
            
        else:
            # SQLite用のテーブル作成
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_line_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    line_channel_id TEXT NOT NULL UNIQUE,
                    line_channel_access_token TEXT NOT NULL,
                    line_channel_secret TEXT NOT NULL,
                    line_basic_id TEXT,
                    line_qr_code_url TEXT,
                    webhook_url TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies (id)
                )
            ''')
            
            # インデックスを作成
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_company_line_accounts_company_id 
                ON company_line_accounts (company_id)
            ''')
            
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_company_line_accounts_status 
                ON company_line_accounts (status)
            ''')
            
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_company_line_accounts_channel_id 
                ON company_line_accounts (line_channel_id)
            ''')
        
        conn.commit()
        conn.close()
        
        print("✅ 企業別LINEアカウント管理テーブルを作成しました")
        
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
                WHERE table_name = 'company_line_accounts'
                ORDER BY ordinal_position
            ''')
            
            columns = c.fetchall()
            
            print("📋 company_line_accounts テーブル構造:")
            for column in columns:
                print(f"  - {column[0]}: {column[1]} ({'NULL可' if column[2] == 'YES' else 'NULL不可'})")
                if column[3]:
                    print(f"    デフォルト値: {column[3]}")
            
            # 制約を確認
            c.execute('''
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints
                WHERE table_name = 'company_line_accounts'
            ''')
            
            constraints = c.fetchall()
            
            print("\n🔒 制約:")
            for constraint in constraints:
                print(f"  - {constraint[0]}: {constraint[1]}")
            
            # インデックスを確認
            c.execute('''
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'company_line_accounts'
            ''')
            
            indexes = c.fetchall()
            
            print("\n📊 インデックス:")
            for index in indexes:
                print(f"  - {index[0]}")
            
        else:
            # SQLite用の構造確認
            c.execute('PRAGMA table_info(company_line_accounts)')
            columns = c.fetchall()
            
            print("📋 company_line_accounts テーブル構造:")
            for column in columns:
                print(f"  - {column[1]}: {column[2]} ({'NULL可' if column[3] == 0 else 'NULL不可'})")
                if column[4]:
                    print(f"    デフォルト値: {column[4]}")
            
            # インデックスを確認
            c.execute('PRAGMA index_list(company_line_accounts)')
            indexes = c.fetchall()
            
            print("\n📊 インデックス:")
            for index in indexes:
                print(f"  - {index[1]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ テーブル構造確認エラー: {e}")

def create_sample_data():
    """サンプルデータを作成"""
    try:
        print("\n=== サンプルデータ作成 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 既存の企業を確認
        c.execute('SELECT id, company_name, company_code FROM companies LIMIT 3')
        companies = c.fetchall()
        
        if not companies:
            print("❌ 企業データが見つかりません。先に企業データを作成してください。")
            return False
        
        print(f"サンプルデータ作成対象企業数: {len(companies)}")
        
        for company in companies:
            company_id = company[0]
            company_name = company[1]
            company_code = company[2]
            
            # 既存のLINEアカウントをチェック
            c.execute('''
                SELECT id FROM company_line_accounts 
                WHERE company_id = %s
            ''', (company_id,))
            
            existing = c.fetchone()
            if existing:
                print(f"⚠️  企業 {company_name} は既にLINEアカウントが存在します")
                continue
            
            # サンプルデータを作成
            channel_id = f"U{company_code.lower()}"
            access_token = f"access_token_{company_code.lower()}"
            channel_secret = f"secret_{company_code.lower()}"
            basic_id = f"@{company_code.lower()}"
            qr_code_url = f"https://qr.liqr.com/{channel_id}"
            webhook_url = f"https://your-domain.com/webhook/{company_id}"
            
            c.execute('''
                INSERT INTO company_line_accounts (
                    company_id, line_channel_id, line_channel_access_token,
                    line_channel_secret, line_basic_id, line_qr_code_url,
                    webhook_url, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                company_id, channel_id, access_token, channel_secret,
                basic_id, qr_code_url, webhook_url, 'active'
            ))
            
            print(f"✅ 企業 {company_name} のサンプルLINEアカウントを作成しました")
            print(f"  - チャネルID: {channel_id}")
            print(f"  - 基本ID: {basic_id}")
            print(f"  - QRコード: {qr_code_url}")
        
        conn.commit()
        conn.close()
        
        print("\n✅ サンプルデータの作成が完了しました")
        return True
        
    except Exception as e:
        print(f"❌ サンプルデータ作成エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン関数"""
    print("🚀 企業別LINEアカウント管理テーブル作成を開始します")
    
    # 1. テーブル作成
    if create_company_line_accounts_table():
        print("✅ テーブル作成が完了しました")
        
        # 2. サンプルデータ作成（オプション）
        create_sample = input("\nサンプルデータを作成しますか？ (y/n): ").lower().strip()
        if create_sample == 'y':
            create_sample_data()
        
        print("\n🎉 企業別LINEアカウント管理システムの準備が完了しました！")
        print("\n📋 次のステップ:")
        print("1. LINE Developers Consoleでチャネルを作成")
        print("2. チャネル情報をデータベースに保存")
        print("3. Webhook URLを設定")
        print("4. テストを実行")
        
    else:
        print("❌ テーブル作成に失敗しました")

if __name__ == "__main__":
    main() 