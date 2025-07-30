#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Stripe APIを使わずにコンテンツ追加をテストするスクリプト
"""

import os
import sys
from utils.db import get_db_connection, get_db_type

def test_content_addition_without_stripe():
    """Stripe APIを使わずにコンテンツ追加をテスト"""
    try:
        print("=== Stripe APIを使わずにコンテンツ追加テスト ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 1. アクティブなサブスクリプションを持つユーザーを確認
        print("\n1️⃣ アクティブなサブスクリプションを持つユーザーを確認")
        c.execute('''
            SELECT DISTINCT u.id, u.line_user_id, u.email, sp.stripe_subscription_id, sp.subscription_status
            FROM users u
            JOIN subscription_periods sp ON u.id = sp.user_id
            WHERE sp.status = 'active'
            ORDER BY u.id
        ''')
        
        active_users = c.fetchall()
        print(f"アクティブなサブスクリプションを持つユーザー数: {len(active_users)}")
        for user in active_users:
            print(f"  - ID: {user[0]}, LINE: {user[1]}, Email: {user[2]}, Stripe: {user[3]}, Status: {user[4]}")
        
        # 2. コンテンツ追加処理をシミュレート
        print("\n2️⃣ コンテンツ追加処理をシミュレート")
        
        if active_users:
            test_user = active_users[0]
            test_user_id = test_user[0]
            test_content = "AI予定秘書"
            
            print(f"テスト用ユーザー: ID={test_user_id}, LINE={test_user[1]}")
            print(f"テスト用コンテンツ: {test_content}")
            
            # 3. 実際のデータベース操作をシミュレート
            print("\n3️⃣ データベース操作をシミュレート")
            
            # 3-1. アクティブなサブスクリプションを確認
            c.execute('''
                SELECT id, stripe_subscription_id, subscription_status, status
                FROM subscription_periods 
                WHERE user_id = %s AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
            ''', (test_user_id,))
            
            active_subscription = c.fetchone()
            if active_subscription:
                print(f"✅ アクティブなサブスクリプション: ID={active_subscription[0]}, Stripe={active_subscription[1]}")
                
                # 3-2. コンテンツ追加の確認メッセージをシミュレート
                print(f"\n📝 コンテンツ追加確認メッセージ:")
                print(f"選択内容の確認")
                print(f"コンテンツ: {test_content}")
                print(f"料金: 1,500円 (2個目、月額料金に追加)")
                print(f"追加しますか?")
                print(f"[はい、追加する] [いいえ、キャンセル]")
                
                # 3-3. ユーザーが「はい」と回答した場合の処理をシミュレート
                print(f"\n👤 ユーザー回答: はい")
                print(f"🔄 コンテンツ追加処理を開始...")
                
                # 3-4. subscription_periodsテーブルの更新をシミュレート
                try:
                    # 既存のレコードを更新（ON CONFLICT処理）
                    c.execute('''
                        INSERT INTO subscription_periods (
                            user_id, stripe_subscription_id, subscription_status, status
                        ) VALUES (%s, %s, %s, 'active')
                        ON CONFLICT (user_id, stripe_subscription_id) 
                        DO UPDATE SET 
                            subscription_status = EXCLUDED.subscription_status,
                            status = EXCLUDED.status,
                            updated_at = CURRENT_TIMESTAMP
                    ''', (test_user_id, active_subscription[1], active_subscription[2]))
                    
                    print(f"✅ subscription_periodsテーブルの更新が成功しました")
                    
                    # 3-5. usage_logsテーブルに使用記録を追加
                    c.execute('''
                        INSERT INTO usage_logs (
                            user_id, usage_quantity, content_type, is_free, pending_charge
                        ) VALUES (%s, 1, %s, false, true)
                    ''', (test_user_id, test_content))
                    
                    print(f"✅ usage_logsテーブルに使用記録を追加しました")
                    
                    # 3-6. 成功メッセージをシミュレート
                    print(f"\n✅ コンテンツ追加成功メッセージ:")
                    print(f"「{test_content}」を追加しました！")
                    print(f"月額料金に1,500円が追加されます。")
                    print(f"次回請求時に反映されます。")
                    
                    # 3-7. 実際のデータを確認
                    print(f"\n4️⃣ 追加後のデータ確認")
                    
                    # subscription_periodsの確認
                    c.execute('''
                        SELECT id, user_id, stripe_subscription_id, subscription_status, status, updated_at
                        FROM subscription_periods 
                        WHERE user_id = %s AND stripe_subscription_id = %s
                    ''', (test_user_id, active_subscription[1]))
                    
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
                    ''', (test_user_id, test_content))
                    
                    usage_log = c.fetchone()
                    if usage_log:
                        print(f"✅ usage_logs追加確認: ID={usage_log[0]}, Content={usage_log[2]}, Pending={usage_log[5]}")
                    
                    conn.commit()
                    print(f"\n🎉 コンテンツ追加のシミュレーションが成功しました！")
                    
                except Exception as e:
                    print(f"❌ データベース操作エラー: {e}")
                    conn.rollback()
                    return False
                
            else:
                print(f"❌ アクティブなサブスクリプションが見つかりません")
                return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_line_bot_flow():
    """LINEボットの実際のフローをテスト"""
    print("\n=== LINEボットフローテスト ===")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # LINEユーザーIDを持つユーザーを取得
        c.execute('''
            SELECT u.id, u.line_user_id, u.email
            FROM users u
            JOIN subscription_periods sp ON u.id = sp.user_id
            WHERE u.line_user_id IS NOT NULL AND sp.status = 'active'
            LIMIT 1
        ''')
        
        line_user = c.fetchone()
        if line_user:
            user_id = line_user[0]
            line_user_id = line_user[1]
            email = line_user[2]
            
            print(f"LINEボットテスト用ユーザー:")
            print(f"  - ID: {user_id}")
            print(f"  - LINE ID: {line_user_id}")
            print(f"  - Email: {email}")
            
            # LINEボットの実際の処理フローをシミュレート
            print(f"\n📱 LINEボット処理フロー:")
            print(f"1. ユーザーが「AI予定秘書」を選択")
            print(f"2. 確認メッセージを送信")
            print(f"3. ユーザーが「はい」と回答")
            print(f"4. コンテンツ追加処理を実行")
            print(f"5. 成功メッセージを送信")
            
            # 実際のデータベース状態を確認
            c.execute('''
                SELECT sp.stripe_subscription_id, sp.subscription_status, sp.status
                FROM subscription_periods sp
                WHERE sp.user_id = %s AND sp.status = 'active'
                ORDER BY sp.created_at DESC
                LIMIT 1
            ''', (user_id,))
            
            subscription = c.fetchone()
            if subscription:
                print(f"\n✅ 現在のサブスクリプション状態:")
                print(f"  - Stripe ID: {subscription[0]}")
                print(f"  - Subscription Status: {subscription[1]}")
                print(f"  - Status: {subscription[2]}")
                
                print(f"\n✅ LINEボットテスト準備完了")
                print(f"実際のLINEボットでユーザー {line_user_id} に「AI予定秘書」を追加できます")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ LINEボットフローテストエラー: {e}")

def main():
    """メイン関数"""
    print("🚀 Stripe APIを使わずにコンテンツ追加テストを開始します")
    
    if test_content_addition_without_stripe():
        print("✅ コンテンツ追加テストが完了しました")
        
        # LINEボットフローテスト
        test_line_bot_flow()
    else:
        print("❌ コンテンツ追加テストに失敗しました")

if __name__ == "__main__":
    main() 