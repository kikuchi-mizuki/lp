#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
subscription_periodsテーブルにstatusカラムを追加するスクリプト
"""

import os
import sys
from utils.db import get_db_connection, get_db_type

def fix_subscription_periods_status_column():
    """subscription_periodsテーブルにstatusカラムを追加"""
    try:
        print("=== subscription_periodsテーブルのstatusカラム修正 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプを確認
        db_type = get_db_type()
        print(f"データベースタイプ: {db_type}")
        
        if db_type == 'postgresql':
            # PostgreSQL用の修正
            print("PostgreSQL用の修正を実行します...")
            
            # 1. 現在のテーブル構造を確認
            print("\n1️⃣ 現在のテーブル構造を確認")
            c.execute('''
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'subscription_periods'
                ORDER BY ordinal_position
            ''')
            
            columns = c.fetchall()
            print("現在のカラム:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]} ({'NULL可' if col[2] == 'YES' else 'NULL不可'})")
            
            # 2. statusカラムが存在するかチェック
            existing_columns = [col[0] for col in columns]
            
            if 'status' not in existing_columns:
                print("\n2️⃣ statusカラムを追加")
                c.execute('''
                    ALTER TABLE subscription_periods 
                    ADD COLUMN status VARCHAR(50) DEFAULT 'active'
                ''')
                print("✅ statusカラムを追加しました")
                
                # 3. 既存データのstatusを更新
                print("\n3️⃣ 既存データのstatusを更新")
                c.execute('''
                    UPDATE subscription_periods 
                    SET status = 'active' 
                    WHERE status IS NULL
                ''')
                updated_count = c.rowcount
                print(f"✅ {updated_count}件のレコードを更新しました")
                
            else:
                print("\n2️⃣ statusカラムは既に存在します")
            
            # 4. テーブル構造を再確認
            print("\n4️⃣ 修正後のテーブル構造を確認")
            c.execute('''
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'subscription_periods'
                ORDER BY ordinal_position
            ''')
            
            columns = c.fetchall()
            print("修正後のカラム:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]} ({'NULL可' if col[2] == 'YES' else 'NULL不可'})")
            
            # 5. サンプルデータを確認
            print("\n5️⃣ サンプルデータを確認")
            c.execute('''
                SELECT id, user_id, stripe_subscription_id, subscription_status, status, created_at
                FROM subscription_periods 
                LIMIT 5
            ''')
            
            sample_data = c.fetchall()
            if sample_data:
                print("サンプルデータ:")
                for row in sample_data:
                    print(f"  - ID: {row[0]}, User: {row[1]}, Stripe: {row[2]}, SubStatus: {row[3]}, Status: {row[4]}")
            else:
                print("データがありません")
            
        else:
            # SQLite用の修正
            print("SQLite用の修正を実行します...")
            
            # 1. 現在のテーブル構造を確認
            print("\n1️⃣ 現在のテーブル構造を確認")
            c.execute("PRAGMA table_info(subscription_periods)")
            columns = c.fetchall()
            
            print("現在のカラム:")
            for col in columns:
                print(f"  - {col[1]}: {col[2]} ({'NULL可' if col[3] == 0 else 'NULL不可'})")
            
            # 2. statusカラムが存在するかチェック
            existing_columns = [col[1] for col in columns]
            
            if 'status' not in existing_columns:
                print("\n2️⃣ statusカラムを追加")
                c.execute('''
                    ALTER TABLE subscription_periods 
                    ADD COLUMN status TEXT DEFAULT 'active'
                ''')
                print("✅ statusカラムを追加しました")
                
                # 3. 既存データのstatusを更新
                print("\n3️⃣ 既存データのstatusを更新")
                c.execute('''
                    UPDATE subscription_periods 
                    SET status = 'active' 
                    WHERE status IS NULL
                ''')
                updated_count = c.rowcount
                print(f"✅ {updated_count}件のレコードを更新しました")
                
            else:
                print("\n2️⃣ statusカラムは既に存在します")
            
            # 4. テーブル構造を再確認
            print("\n4️⃣ 修正後のテーブル構造を確認")
            c.execute("PRAGMA table_info(subscription_periods)")
            columns = c.fetchall()
            
            print("修正後のカラム:")
            for col in columns:
                print(f"  - {col[1]}: {col[2]} ({'NULL可' if col[3] == 0 else 'NULL不可'})")
            
            # 5. サンプルデータを確認
            print("\n5️⃣ サンプルデータを確認")
            c.execute('''
                SELECT id, user_id, stripe_subscription_id, subscription_status, status, created_at
                FROM subscription_periods 
                LIMIT 5
            ''')
            
            sample_data = c.fetchall()
            if sample_data:
                print("サンプルデータ:")
                for row in sample_data:
                    print(f"  - ID: {row[0]}, User: {row[1]}, Stripe: {row[2]}, SubStatus: {row[3]}, Status: {row[4]}")
            else:
                print("データがありません")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 subscription_periodsテーブルの修正が完了しました")
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def verify_fix():
    """修正の検証"""
    try:
        print("\n=== 修正の検証 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # statusカラムを使用したクエリをテスト
        print("1️⃣ statusカラムを使用したクエリをテスト")
        c.execute('''
            SELECT COUNT(*) 
            FROM subscription_periods 
            WHERE status = 'active'
        ''')
        
        count = c.fetchone()[0]
        print(f"✅ アクティブなレコード数: {count}")
        
        # サンプルクエリをテスト
        print("\n2️⃣ サンプルクエリをテスト")
        c.execute('''
            SELECT user_id, stripe_subscription_id, status
            FROM subscription_periods 
            WHERE user_id = 1 AND status = 'active'
            LIMIT 1
        ''')
        
        result = c.fetchone()
        if result:
            print(f"✅ クエリ成功: User {result[0]}, Stripe {result[1]}, Status {result[2]}")
        else:
            print("⚠️ 該当データが見つかりません")
        
        conn.close()
        print("\n✅ 修正の検証が完了しました")
        return True
        
    except Exception as e:
        print(f"❌ 検証エラー: {e}")
        return False

def main():
    """メイン関数"""
    print("🚀 subscription_periodsテーブルの修正を開始します")
    
    # 修正を実行
    if fix_subscription_periods_status_column():
        print("✅ 修正が完了しました")
        
        # 修正を検証
        if verify_fix():
            print("✅ 修正の検証が完了しました")
        else:
            print("❌ 修正の検証に失敗しました")
    else:
        print("❌ 修正に失敗しました")

if __name__ == "__main__":
    main() 