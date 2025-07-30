#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
subscription_periodsテーブルの制約を修正するスクリプト
"""

import os
import sys
from utils.db import get_db_connection, get_db_type

def fix_subscription_periods_constraints():
    """subscription_periodsテーブルの制約を修正"""
    try:
        print("=== subscription_periodsテーブルの制約修正 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプを確認
        db_type = get_db_type()
        print(f"データベースタイプ: {db_type}")
        
        if db_type == 'postgresql':
            # PostgreSQL用の修正
            print("PostgreSQL用の制約修正を実行します...")
            
            # 1. 現在の制約を確認
            print("\n1️⃣ 現在の制約を確認")
            c.execute('''
                SELECT conname, contype, pg_get_constraintdef(oid) as definition
                FROM pg_constraint 
                WHERE conrelid = 'subscription_periods'::regclass
            ''')
            
            constraints = c.fetchall()
            print("現在の制約:")
            for constraint in constraints:
                print(f"  - {constraint[0]}: {constraint[1]} - {constraint[2]}")
            
            # 2. 既存のユニーク制約を削除（存在する場合）
            print("\n2️⃣ 既存のユニーク制約を削除")
            for constraint in constraints:
                if constraint[1] == 'u':  # ユニーク制約
                    try:
                        c.execute(f'ALTER TABLE subscription_periods DROP CONSTRAINT {constraint[0]}')
                        print(f"✅ 制約 {constraint[0]} を削除しました")
                    except Exception as e:
                        print(f"⚠️ 制約 {constraint[0]} の削除に失敗: {e}")
            
            # 3. 新しいユニーク制約を追加
            print("\n3️⃣ 新しいユニーク制約を追加")
            try:
                c.execute('''
                    ALTER TABLE subscription_periods 
                    ADD CONSTRAINT subscription_periods_user_subscription_unique 
                    UNIQUE (user_id, stripe_subscription_id)
                ''')
                print("✅ 新しいユニーク制約を追加しました")
            except Exception as e:
                print(f"❌ ユニーク制約の追加に失敗: {e}")
                
                # 重複データがある場合は削除
                print("重複データを確認・削除します...")
                c.execute('''
                    DELETE FROM subscription_periods 
                    WHERE id NOT IN (
                        SELECT MIN(id) 
                        FROM subscription_periods 
                        GROUP BY user_id, stripe_subscription_id
                    )
                ''')
                deleted_count = c.rowcount
                print(f"✅ {deleted_count}件の重複データを削除しました")
                
                # 再度制約を追加
                c.execute('''
                    ALTER TABLE subscription_periods 
                    ADD CONSTRAINT subscription_periods_user_subscription_unique 
                    UNIQUE (user_id, stripe_subscription_id)
                ''')
                print("✅ ユニーク制約を追加しました")
            
            # 4. 修正後の制約を確認
            print("\n4️⃣ 修正後の制約を確認")
            c.execute('''
                SELECT conname, contype, pg_get_constraintdef(oid) as definition
                FROM pg_constraint 
                WHERE conrelid = 'subscription_periods'::regclass
            ''')
            
            constraints = c.fetchall()
            print("修正後の制約:")
            for constraint in constraints:
                print(f"  - {constraint[0]}: {constraint[1]} - {constraint[2]}")
            
            # 5. サンプルデータを確認
            print("\n5️⃣ サンプルデータを確認")
            c.execute('''
                SELECT id, user_id, stripe_subscription_id, subscription_status, status, created_at
                FROM subscription_periods 
                ORDER BY user_id, created_at
                LIMIT 10
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
            print("SQLite用の制約修正を実行します...")
            
            # 1. 現在のテーブル構造を確認
            print("\n1️⃣ 現在のテーブル構造を確認")
            c.execute("PRAGMA table_info(subscription_periods)")
            columns = c.fetchall()
            
            print("現在のカラム:")
            for col in columns:
                print(f"  - {col[1]}: {col[2]} ({'NULL可' if col[3] == 0 else 'NULL不可'})")
            
            # 2. 重複データを削除
            print("\n2️⃣ 重複データを削除")
            c.execute('''
                DELETE FROM subscription_periods 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM subscription_periods 
                    GROUP BY user_id, stripe_subscription_id
                )
            ''')
            deleted_count = c.rowcount
            print(f"✅ {deleted_count}件の重複データを削除しました")
            
            # 3. 新しいテーブルを作成（制約付き）
            print("\n3️⃣ 新しいテーブルを作成")
            c.execute('''
                CREATE TABLE subscription_periods_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    stripe_subscription_id TEXT NOT NULL,
                    subscription_status TEXT NOT NULL,
                    current_period_start TIMESTAMP,
                    current_period_end TIMESTAMP,
                    trial_start TIMESTAMP,
                    trial_end TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    UNIQUE(user_id, stripe_subscription_id)
                )
            ''')
            
            # 4. データを移行
            print("\n4️⃣ データを移行")
            c.execute('''
                INSERT INTO subscription_periods_new 
                SELECT * FROM subscription_periods
            ''')
            
            # 5. 古いテーブルを削除して新しいテーブルにリネーム
            c.execute('DROP TABLE subscription_periods')
            c.execute('ALTER TABLE subscription_periods_new RENAME TO subscription_periods')
            
            print("✅ テーブルの再作成が完了しました")
            
            # 6. 修正後のテーブル構造を確認
            print("\n5️⃣ 修正後のテーブル構造を確認")
            c.execute("PRAGMA table_info(subscription_periods)")
            columns = c.fetchall()
            
            print("修正後のカラム:")
            for col in columns:
                print(f"  - {col[1]}: {col[2]} ({'NULL可' if col[3] == 0 else 'NULL不可'})")
            
            # 7. サンプルデータを確認
            print("\n6️⃣ サンプルデータを確認")
            c.execute('''
                SELECT id, user_id, stripe_subscription_id, subscription_status, status, created_at
                FROM subscription_periods 
                ORDER BY user_id, created_at
                LIMIT 10
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
        
        print("\n🎉 subscription_periodsテーブルの制約修正が完了しました")
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def verify_constraints():
    """制約の検証"""
    try:
        print("\n=== 制約の検証 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 1. ユニーク制約のテスト
        print("1️⃣ ユニーク制約のテスト")
        
        # 既存データを確認
        c.execute('''
            SELECT user_id, stripe_subscription_id, COUNT(*)
            FROM subscription_periods 
            GROUP BY user_id, stripe_subscription_id
            HAVING COUNT(*) > 1
        ''')
        
        duplicates = c.fetchall()
        if duplicates:
            print(f"❌ 重複データが存在します: {len(duplicates)}件")
            for dup in duplicates:
                print(f"  - User: {dup[0]}, Stripe: {dup[1]}, Count: {dup[2]}")
        else:
            print("✅ 重複データはありません")
        
        # 2. ON CONFLICTクエリのテスト
        print("\n2️⃣ ON CONFLICTクエリのテスト")
        try:
            # テスト用のデータを挿入（既存データがある場合は更新）
            c.execute('''
                INSERT INTO subscription_periods (user_id, stripe_subscription_id, subscription_status, status)
                VALUES (999, 'test_subscription_999', 'active', 'active')
                ON CONFLICT (user_id, stripe_subscription_id) 
                DO UPDATE SET 
                    subscription_status = EXCLUDED.subscription_status,
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP
            ''')
            
            print("✅ ON CONFLICTクエリが成功しました")
            
            # テストデータを削除
            c.execute('DELETE FROM subscription_periods WHERE user_id = 999')
            
        except Exception as e:
            print(f"❌ ON CONFLICTクエリが失敗: {e}")
        
        # 3. 実際のクエリパターンのテスト
        print("\n3️⃣ 実際のクエリパターンのテスト")
        try:
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
                
        except Exception as e:
            print(f"❌ クエリテストが失敗: {e}")
        
        conn.close()
        print("\n✅ 制約の検証が完了しました")
        return True
        
    except Exception as e:
        print(f"❌ 検証エラー: {e}")
        return False

def main():
    """メイン関数"""
    print("🚀 subscription_periodsテーブルの制約修正を開始します")
    
    # 制約修正を実行
    if fix_subscription_periods_constraints():
        print("✅ 制約修正が完了しました")
        
        # 制約を検証
        if verify_constraints():
            print("✅ 制約の検証が完了しました")
        else:
            print("❌ 制約の検証に失敗しました")
    else:
        print("❌ 制約修正に失敗しました")

if __name__ == "__main__":
    main() 