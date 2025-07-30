#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ON CONFLICT修正のテストスクリプト
"""

import os
import sys
import time
from utils.db import get_db_connection, get_db_type

def test_on_conflict_fix():
    """ON CONFLICT修正のテスト"""
    try:
        print("=== ON CONFLICT修正のテスト ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 1. 既存のユーザーIDを取得
        print("\n1️⃣ 既存のユーザーIDを取得")
        c.execute('SELECT id FROM users LIMIT 1')
        user_result = c.fetchone()
        
        if not user_result:
            print("❌ テスト用のユーザーが見つかりません")
            return False
        
        test_user_id = user_result[0]
        print(f"✅ テスト用ユーザーID: {test_user_id}")
        
        # 2. 既存のsubscription_periodsデータを確認
        print("\n2️⃣ 既存のsubscription_periodsデータを確認")
        c.execute('''
            SELECT id, user_id, stripe_subscription_id, subscription_status, status
            FROM subscription_periods 
            WHERE user_id = %s
        ''', (test_user_id,))
        
        existing_data = c.fetchall()
        print(f"既存データ数: {len(existing_data)}")
        for row in existing_data:
            print(f"  - ID: {row[0]}, User: {row[1]}, Stripe: {row[2]}, SubStatus: {row[3]}, Status: {row[4]}")
        
        # 3. ON CONFLICTクエリのテスト（既存データの更新）
        print("\n3️⃣ ON CONFLICTクエリのテスト（既存データの更新）")
        if existing_data:
            existing_stripe_id = existing_data[0][2]
            
            try:
                c.execute('''
                    INSERT INTO subscription_periods (user_id, stripe_subscription_id, subscription_status, status)
                    VALUES (%s, %s, 'updated_status', 'updated')
                    ON CONFLICT (user_id, stripe_subscription_id) 
                    DO UPDATE SET 
                        subscription_status = EXCLUDED.subscription_status,
                        status = EXCLUDED.status,
                        updated_at = CURRENT_TIMESTAMP
                ''', (test_user_id, existing_stripe_id))
                
                print("✅ ON CONFLICTクエリ（更新）が成功しました")
                
                # 更新結果を確認
                c.execute('''
                    SELECT subscription_status, status, updated_at
                    FROM subscription_periods 
                    WHERE user_id = %s AND stripe_subscription_id = %s
                ''', (test_user_id, existing_stripe_id))
                
                updated_result = c.fetchone()
                if updated_result:
                    print(f"✅ 更新確認: SubStatus={updated_result[0]}, Status={updated_result[1]}")
                
            except Exception as e:
                print(f"❌ ON CONFLICTクエリ（更新）が失敗: {e}")
                return False
        
        # 4. ON CONFLICTクエリのテスト（新規データの挿入）
        print("\n4️⃣ ON CONFLICTクエリのテスト（新規データの挿入）")
        new_stripe_id = f"test_new_subscription_{test_user_id}_{int(time.time())}"
        
        try:
            c.execute('''
                INSERT INTO subscription_periods (user_id, stripe_subscription_id, subscription_status, status)
                VALUES (%s, %s, 'new_status', 'new')
                ON CONFLICT (user_id, stripe_subscription_id) 
                DO UPDATE SET 
                    subscription_status = EXCLUDED.subscription_status,
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP
            ''', (test_user_id, new_stripe_id))
            
            print("✅ ON CONFLICTクエリ（新規挿入）が成功しました")
            
            # 挿入結果を確認
            c.execute('''
                SELECT subscription_status, status, created_at
                FROM subscription_periods 
                WHERE user_id = %s AND stripe_subscription_id = %s
            ''', (test_user_id, new_stripe_id))
            
            inserted_result = c.fetchone()
            if inserted_result:
                print(f"✅ 挿入確認: SubStatus={inserted_result[0]}, Status={inserted_result[1]}")
            
            # テストデータを削除
            c.execute('DELETE FROM subscription_periods WHERE stripe_subscription_id = %s', (new_stripe_id,))
            print("✅ テストデータを削除しました")
            
        except Exception as e:
            print(f"❌ ON CONFLICTクエリ（新規挿入）が失敗: {e}")
            return False
        
        # 5. 実際のアプリケーションで使用されるクエリパターンのテスト
        print("\n5️⃣ 実際のクエリパターンのテスト")
        try:
            # コンテンツ確認処理で使用されるクエリ
            c.execute('''
                SELECT user_id, stripe_subscription_id, status
                FROM subscription_periods 
                WHERE user_id = %s AND status = 'active'
                LIMIT 1
            ''', (test_user_id,))
            
            result = c.fetchone()
            if result:
                print(f"✅ クエリ成功: User {result[0]}, Stripe {result[1]}, Status {result[2]}")
            else:
                print("⚠️ アクティブなデータが見つかりません")
                
        except Exception as e:
            print(f"❌ クエリテストが失敗: {e}")
            return False
        
        # 6. 重複データのテスト
        print("\n6️⃣ 重複データのテスト")
        try:
            # 同じuser_idとstripe_subscription_idで複数回挿入を試行
            duplicate_stripe_id = f"test_duplicate_{test_user_id}"
            
            # 1回目の挿入
            c.execute('''
                INSERT INTO subscription_periods (user_id, stripe_subscription_id, subscription_status, status)
                VALUES (%s, %s, 'first_insert', 'active')
                ON CONFLICT (user_id, stripe_subscription_id) 
                DO UPDATE SET 
                    subscription_status = EXCLUDED.subscription_status,
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP
            ''', (test_user_id, duplicate_stripe_id))
            
            # 2回目の挿入（更新されるはず）
            c.execute('''
                INSERT INTO subscription_periods (user_id, stripe_subscription_id, subscription_status, status)
                VALUES (%s, %s, 'second_insert', 'updated')
                ON CONFLICT (user_id, stripe_subscription_id) 
                DO UPDATE SET 
                    subscription_status = EXCLUDED.subscription_status,
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP
            ''', (test_user_id, duplicate_stripe_id))
            
            # 結果を確認
            c.execute('''
                SELECT COUNT(*), subscription_status, status
                FROM subscription_periods 
                WHERE user_id = %s AND stripe_subscription_id = %s
                GROUP BY subscription_status, status
            ''', (test_user_id, duplicate_stripe_id))
            
            duplicate_result = c.fetchone()
            if duplicate_result and duplicate_result[0] == 1:
                print(f"✅ 重複制約テスト成功: Count={duplicate_result[0]}, SubStatus={duplicate_result[1]}, Status={duplicate_result[2]}")
            else:
                print("❌ 重複制約テスト失敗")
            
            # テストデータを削除
            c.execute('DELETE FROM subscription_periods WHERE stripe_subscription_id = %s', (duplicate_stripe_id,))
            print("✅ 重複テストデータを削除しました")
            
        except Exception as e:
            print(f"❌ 重複データテストが失敗: {e}")
            return False
        
        conn.commit()
        conn.close()
        
        print("\n🎉 ON CONFLICT修正のテストが完了しました")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def test_line_service_integration():
    """LINEサービスとの統合テスト"""
    try:
        print("\n=== LINEサービスとの統合テスト ===")
        
        # LINEサービスのhandle_content_confirmation関数をテスト
        from services.line_service import handle_content_confirmation
        
        # 既存のユーザーIDを取得
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT id FROM users LIMIT 1')
        user_result = c.fetchone()
        conn.close()
        
        if not user_result:
            print("❌ テスト用のユーザーが見つかりません")
            return False
        
        test_user_id = user_result[0]
        test_content = "AI予定秘書"
        
        print(f"テスト用ユーザーID: {test_user_id}")
        print(f"テスト用コンテンツ: {test_content}")
        
        # handle_content_confirmation関数をテスト
        try:
            result = handle_content_confirmation(test_user_id, test_content)
            print(f"✅ handle_content_confirmation結果: {result}")
        except Exception as e:
            print(f"❌ handle_content_confirmationエラー: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 統合テストエラー: {e}")
        return False

def main():
    """メイン関数"""
    print("🚀 ON CONFLICT修正のテストを開始します")
    
    import time
    
    # ON CONFLICT修正のテスト
    if test_on_conflict_fix():
        print("✅ ON CONFLICT修正のテストが完了しました")
        
        # LINEサービスとの統合テスト
        if test_line_service_integration():
            print("✅ LINEサービスとの統合テストが完了しました")
        else:
            print("❌ LINEサービスとの統合テストに失敗しました")
    else:
        print("❌ ON CONFLICT修正のテストに失敗しました")

if __name__ == "__main__":
    main() 