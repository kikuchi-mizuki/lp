#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修正されたline_serviceのhandle_content_confirmation関数をテストするスクリプト
"""

import os
import sys
from utils.db import get_db_connection, get_db_type

def test_handle_content_confirmation():
    """handle_content_confirmation関数をテスト"""
    try:
        print("=== handle_content_confirmation関数テスト ===")
        
        # 1. アクティブなサブスクリプションを持つユーザーを確認
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT DISTINCT u.id, u.line_user_id, u.email, sp.stripe_subscription_id, sp.subscription_status
            FROM users u
            JOIN subscription_periods sp ON u.id = sp.user_id
            WHERE sp.status = 'active'
            ORDER BY u.id
            LIMIT 1
        ''')
        
        test_user = c.fetchone()
        if not test_user:
            print("❌ テスト用のアクティブユーザーが見つかりません")
            return False
        
        user_id = test_user[0]
        line_user_id = test_user[1]
        email = test_user[2]
        stripe_subscription_id = test_user[3]
        subscription_status = test_user[4]
        
        print(f"テスト用ユーザー:")
        print(f"  - ID: {user_id}")
        print(f"  - LINE: {line_user_id}")
        print(f"  - Email: {email}")
        print(f"  - Stripe: {stripe_subscription_id}")
        print(f"  - Status: {subscription_status}")
        
        conn.close()
        
        # 2. handle_content_confirmation関数をテスト
        print(f"\n2️⃣ handle_content_confirmation関数テスト")
        
        from services.line_service import handle_content_confirmation
        
        test_content = "AI予定秘書"
        print(f"テスト用コンテンツ: {test_content}")
        
        try:
            result = handle_content_confirmation(user_id, test_content)
            print(f"結果: {result}")
            
            if result.get('success'):
                print("✅ handle_content_confirmationが成功しました！")
                
                # 3. データベースの状態を確認
                print(f"\n3️⃣ データベース状態確認")
                
                conn = get_db_connection()
                c = conn.cursor()
                
                # subscription_periodsの確認
                c.execute('''
                    SELECT id, user_id, stripe_subscription_id, subscription_status, status, updated_at
                    FROM subscription_periods 
                    WHERE user_id = %s AND stripe_subscription_id = %s
                ''', (user_id, stripe_subscription_id))
                
                updated_period = c.fetchone()
                if updated_period:
                    print(f"✅ subscription_periods更新確認: ID={updated_period[0]}, Status={updated_period[4]}")
                
                # usage_logsの確認
                c.execute('''
                    SELECT id, user_id, content_type, usage_quantity, is_free, pending_charge, created_at
                    FROM usage_logs 
                    WHERE user_id = %s AND content_type = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', (user_id, test_content))
                
                usage_log = c.fetchone()
                if usage_log:
                    print(f"✅ usage_logs追加確認: ID={usage_log[0]}, Content={usage_log[2]}, Pending={usage_log[5]}")
                
                conn.close()
                
                return True
            else:
                error = result.get('error', '不明なエラー')
                print(f"❌ handle_content_confirmationが失敗: {error}")
                
                # エラーの詳細分析
                if "ON CONFLICT" in error:
                    print("🔍 ON CONFLICTエラーの可能性:")
                    print("  - データベース制約の問題")
                    print("  - 重複データの挿入試行")
                elif "Stripe" in error:
                    print("🔍 Stripe APIエラーの可能性:")
                    print("  - APIキーの設定問題")
                    print("  - ネットワーク接続問題")
                
                return False
                
        except Exception as e:
            print(f"❌ handle_content_confirmation例外: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_constraints():
    """データベース制約の確認"""
    print(f"\n=== データベース制約確認 ===")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        db_type = get_db_type()
        if db_type == 'postgresql':
            # subscription_periodsテーブルの制約を確認
            c.execute('''
                SELECT conname, contype, pg_get_constraintdef(oid) as definition
                FROM pg_constraint 
                WHERE conrelid = 'subscription_periods'::regclass
            ''')
            
            constraints = c.fetchall()
            print("subscription_periodsテーブルの制約:")
            for constraint in constraints:
                print(f"  - {constraint[0]}: {constraint[1]} - {constraint[2]}")
                
                # ユニーク制約の確認
                if constraint[1] == 'u' and 'user_id' in constraint[2] and 'stripe_subscription_id' in constraint[2]:
                    print(f"    ✅ 必要なユニーク制約が存在します: {constraint[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 制約確認エラー: {e}")

def test_on_conflict_query():
    """ON CONFLICTクエリの直接テスト"""
    print(f"\n=== ON CONFLICTクエリ直接テスト ===")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # テスト用のユーザーIDを取得
        c.execute('SELECT id FROM users LIMIT 1')
        test_user_id = c.fetchone()[0]
        
        # 既存のサブスクリプションIDを取得
        c.execute('''
            SELECT stripe_subscription_id FROM subscription_periods 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 1
        ''', (test_user_id,))
        
        existing_stripe_id = c.fetchone()[0]
        
        print(f"テスト用ユーザーID: {test_user_id}")
        print(f"既存のStripe ID: {existing_stripe_id}")
        
        # ON CONFLICTクエリをテスト
        try:
            c.execute('''
                INSERT INTO subscription_periods (
                    user_id, stripe_subscription_id, subscription_status, status,
                    current_period_start, current_period_end,
                    trial_start, trial_end, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, stripe_subscription_id) DO UPDATE SET
                    subscription_status = EXCLUDED.subscription_status,
                    status = EXCLUDED.status,
                    current_period_start = EXCLUDED.current_period_start,
                    current_period_end = EXCLUDED.current_period_end,
                    trial_start = EXCLUDED.trial_start,
                    trial_end = EXCLUDED.trial_end,
                    updated_at = EXCLUDED.updated_at
            ''', (
                test_user_id,
                existing_stripe_id,
                'active',
                'active',
                None,  # current_period_start
                None,  # current_period_end
                None,  # trial_start
                None,  # trial_end
                None,  # created_at
                None   # updated_at
            ))
            
            print("✅ ON CONFLICTクエリが成功しました")
            
        except Exception as e:
            print(f"❌ ON CONFLICTクエリが失敗: {e}")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ ON CONFLICTクエリテストエラー: {e}")
        return False

def main():
    """メイン関数"""
    print("🚀 line_service修正テストを開始します")
    
    # データベース制約の確認
    test_database_constraints()
    
    # ON CONFLICTクエリの直接テスト
    if test_on_conflict_query():
        print("✅ ON CONFLICTクエリテストが完了しました")
        
        # handle_content_confirmation関数のテスト
        if test_handle_content_confirmation():
            print("✅ handle_content_confirmationテストが完了しました")
            print("\n🎉 すべてのテストが成功しました！")
        else:
            print("❌ handle_content_confirmationテストに失敗しました")
    else:
        print("❌ ON CONFLICTクエリテストに失敗しました")

if __name__ == "__main__":
    main() 