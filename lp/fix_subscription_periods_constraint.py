#!/usr/bin/env python3
"""
subscription_periodsテーブルの重複キー制約を修正するスクリプト
"""

import os
from utils.db import get_db_connection

def fix_subscription_periods_constraint():
    """subscription_periodsテーブルの制約を修正"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        print("🔧 subscription_periodsテーブルの制約を修正中...")
        
        # 現在の制約を確認
        c.execute('''
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_name = 'subscription_periods'
            AND constraint_type = 'UNIQUE'
        ''')
        
        constraints = c.fetchall()
        print(f"📋 現在のUNIQUE制約: {constraints}")
        
        # stripe_subscription_idのUNIQUE制約を削除
        try:
            c.execute('''
                ALTER TABLE subscription_periods
                DROP CONSTRAINT IF EXISTS subscription_periods_stripe_subscription_id_key
            ''')
            print("✅ stripe_subscription_idのUNIQUE制約を削除しました")
        except Exception as e:
            print(f"⚠️ 制約削除エラー（既に存在しない可能性）: {e}")
        
        # 新しい制約を追加（user_idとstripe_subscription_idの組み合わせでUNIQUE）
        try:
            c.execute('''
                ALTER TABLE subscription_periods
                ADD CONSTRAINT subscription_periods_user_subscription_unique
                UNIQUE (user_id, stripe_subscription_id)
            ''')
            print("✅ 新しいUNIQUE制約を追加しました（user_id + stripe_subscription_id）")
        except Exception as e:
            print(f"⚠️ 新しい制約追加エラー: {e}")
        
        # 重複データを確認
        c.execute('''
            SELECT user_id, stripe_subscription_id, COUNT(*)
            FROM subscription_periods
            WHERE stripe_subscription_id IS NOT NULL
            GROUP BY user_id, stripe_subscription_id
            HAVING COUNT(*) > 1
        ''')
        
        duplicates = c.fetchall()
        if duplicates:
            print(f"⚠️ 重複データが見つかりました: {len(duplicates)}件")
            for dup in duplicates:
                print(f"   - user_id: {dup[0]}, subscription_id: {dup[1]}, count: {dup[2]}")
            
            # 重複データを削除（最新のものを残す）
            c.execute('''
                DELETE FROM subscription_periods
                WHERE id NOT IN (
                    SELECT MAX(id)
                    FROM subscription_periods
                    WHERE stripe_subscription_id IS NOT NULL
                    GROUP BY user_id, stripe_subscription_id
                )
                AND stripe_subscription_id IS NOT NULL
            ''')
            print("✅ 重複データを削除しました")
        else:
            print("✅ 重複データはありません")
        
        conn.commit()
        conn.close()
        
        print("🎉 subscription_periodsテーブルの制約修正が完了しました")
        return True
        
    except Exception as e:
        print(f"❌ 制約修正エラー: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def check_subscription_periods_structure():
    """subscription_periodsテーブルの構造を確認"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        print("📋 subscription_periodsテーブルの構造を確認中...")
        
        # テーブル構造を確認
        c.execute('''
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'subscription_periods'
            ORDER BY ordinal_position
        ''')
        
        columns = c.fetchall()
        print("📊 テーブル構造:")
        for col in columns:
            print(f"   - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        
        # 制約を確認
        c.execute('''
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_name = 'subscription_periods'
        ''')
        
        constraints = c.fetchall()
        print("🔒 制約:")
        for constraint in constraints:
            print(f"   - {constraint[0]}: {constraint[1]}")
        
        # データ件数を確認
        c.execute('SELECT COUNT(*) FROM subscription_periods')
        count = c.fetchone()[0]
        print(f"📈 データ件数: {count}件")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 構造確認エラー: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 subscription_periodsテーブルの制約修正を開始します...")
    
    # 現在の構造を確認
    check_subscription_periods_structure()
    
    # 制約を修正
    success = fix_subscription_periods_constraint()
    
    if success:
        # 修正後の構造を確認
        check_subscription_periods_structure()
        print("✅ 修正が完了しました")
    else:
        print("❌ 修正に失敗しました") 