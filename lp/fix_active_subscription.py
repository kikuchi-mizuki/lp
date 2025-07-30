#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
アクティブなサブスクリプションを作成するスクリプト
"""

import os
import sys
import time
from utils.db import get_db_connection, get_db_type

def create_active_subscription():
    """アクティブなサブスクリプションを作成"""
    try:
        print("=== アクティブなサブスクリプション作成 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 1. 既存のユーザーを確認
        print("\n1️⃣ 既存のユーザーを確認")
        c.execute('SELECT id, line_user_id, email FROM users')
        users = c.fetchall()
        
        print(f"ユーザー数: {len(users)}")
        for user in users:
            print(f"  - ID: {user[0]}, LINE: {user[1]}, Email: {user[2]}")
        
        # 2. 各ユーザーのサブスクリプション状況を確認
        print("\n2️⃣ サブスクリプション状況を確認")
        for user in users:
            user_id = user[0]
            c.execute('''
                SELECT id, stripe_subscription_id, subscription_status, status
                FROM subscription_periods 
                WHERE user_id = %s
                ORDER BY created_at DESC
            ''', (user_id,))
            
            periods = c.fetchall()
            print(f"ユーザー {user_id} ({user[2]}):")
            if periods:
                for period in periods:
                    print(f"  - ID: {period[0]}, Stripe: {period[1]}, SubStatus: {period[2]}, Status: {period[3]}")
            else:
                print("  - サブスクリプションなし")
        
        # 3. アクティブなサブスクリプションを作成
        print("\n3️⃣ アクティブなサブスクリプションを作成")
        
        for user in users:
            user_id = user[0]
            line_user_id = user[1]
            
            # アクティブなサブスクリプションがあるかチェック
            c.execute('''
                SELECT COUNT(*)
                FROM subscription_periods 
                WHERE user_id = %s AND status = 'active'
            ''', (user_id,))
            
            active_count = c.fetchone()[0]
            
            if active_count == 0:
                print(f"ユーザー {user_id} にアクティブなサブスクリプションを作成します")
                
                # 既存のサブスクリプションがあるかチェック
                c.execute('''
                    SELECT id FROM subscription_periods 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT 1
                ''', (user_id,))
                
                existing_period = c.fetchone()
                
                if existing_period:
                    # 既存のサブスクリプションをアクティブに更新
                    period_id = existing_period[0]
                    c.execute('''
                        UPDATE subscription_periods 
                        SET status = 'active', updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    ''', (period_id,))
                    
                    print(f"✅ ユーザー {user_id} のサブスクリプションをアクティブに更新しました")
                else:
                    # 新しいサブスクリプションを作成
                    stripe_subscription_id = f"sub_active_{user_id}_{int(time.time())}"
                    
                    c.execute('''
                        INSERT INTO subscription_periods (
                            user_id, stripe_subscription_id, subscription_status, status
                        ) VALUES (%s, %s, 'active', 'active')
                    ''', (user_id, stripe_subscription_id))
                    
                    print(f"✅ ユーザー {user_id} に新しいアクティブサブスクリプションを作成しました: {stripe_subscription_id}")
            else:
                print(f"ユーザー {user_id} は既にアクティブなサブスクリプションがあります")
        
        # 4. 修正後の状況を確認
        print("\n4️⃣ 修正後の状況を確認")
        for user in users:
            user_id = user[0]
            c.execute('''
                SELECT id, stripe_subscription_id, subscription_status, status
                FROM subscription_periods 
                WHERE user_id = %s AND status = 'active'
                ORDER BY created_at DESC
            ''', (user_id,))
            
            active_periods = c.fetchall()
            print(f"ユーザー {user_id} のアクティブサブスクリプション:")
            if active_periods:
                for period in active_periods:
                    print(f"  - ID: {period[0]}, Stripe: {period[1]}, SubStatus: {period[2]}, Status: {period[3]}")
            else:
                print("  - アクティブなサブスクリプションなし")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 アクティブなサブスクリプションの作成が完了しました")
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def test_content_addition():
    """コンテンツ追加のテスト"""
    print("\n=== コンテンツ追加テスト ===")
    
    try:
        from services.line_service import handle_content_confirmation
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # LINEユーザーIDを持つユーザーを取得
        c.execute('SELECT id, line_user_id FROM users WHERE line_user_id IS NOT NULL')
        line_users = c.fetchall()
        
        if line_users:
            test_user = line_users[0]
            test_user_id = test_user[0]
            line_user_id = test_user[1]
            
            print(f"テスト用ユーザー: ID={test_user_id}, LINE={line_user_id}")
            
            # アクティブなサブスクリプションを確認
            c.execute('''
                SELECT COUNT(*)
                FROM subscription_periods 
                WHERE user_id = %s AND status = 'active'
            ''', (test_user_id,))
            
            active_count = c.fetchone()[0]
            print(f"アクティブなサブスクリプション数: {active_count}")
            
            if active_count > 0:
                # コンテンツ追加をテスト
                test_content = "AI予定秘書"
                print(f"コンテンツ追加テスト: {test_content}")
                
                result = handle_content_confirmation(test_user_id, test_content)
                print(f"結果: {result}")
                
                if result.get('success'):
                    print("✅ コンテンツ追加が成功しました！")
                else:
                    print(f"❌ コンテンツ追加が失敗: {result.get('error')}")
            else:
                print("❌ アクティブなサブスクリプションがありません")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()

def main():
    """メイン関数"""
    print("🚀 アクティブなサブスクリプション作成を開始します")
    
    if create_active_subscription():
        print("✅ アクティブなサブスクリプション作成が完了しました")
        
        # コンテンツ追加テスト
        test_content_addition()
    else:
        print("❌ アクティブなサブスクリプション作成に失敗しました")

if __name__ == "__main__":
    main() 