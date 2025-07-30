#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LINEボットのコンテンツ追加処理をデバッグするスクリプト
"""

import os
import sys
import json
from utils.db import get_db_connection, get_db_type
from services.line_service import handle_content_confirmation

def debug_content_addition():
    """コンテンツ追加処理のデバッグ"""
    try:
        print("=== LINEボット コンテンツ追加処理デバッグ ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 1. データベースの状態を確認
        print("\n1️⃣ データベースの状態確認")
        
        # ユーザーテーブル
        c.execute('SELECT id, line_user_id, email FROM users LIMIT 5')
        users = c.fetchall()
        print(f"ユーザー数: {len(users)}")
        for user in users:
            print(f"  - ID: {user[0]}, LINE: {user[1]}, Email: {user[2]}")
        
        # subscription_periodsテーブル
        c.execute('''
            SELECT id, user_id, stripe_subscription_id, subscription_status, status, created_at
            FROM subscription_periods 
            ORDER BY user_id, created_at
        ''')
        periods = c.fetchall()
        print(f"\nsubscription_periods数: {len(periods)}")
        for period in periods:
            print(f"  - ID: {period[0]}, User: {period[1]}, Stripe: {period[2]}, SubStatus: {period[3]}, Status: {period[4]}")
        
        # 2. 実際のコンテンツ追加処理をテスト
        print("\n2️⃣ コンテンツ追加処理のテスト")
        
        if users:
            test_user_id = users[0][0]
            test_content = "AI予定秘書"
            
            print(f"テスト用ユーザーID: {test_user_id}")
            print(f"テスト用コンテンツ: {test_content}")
            
            # handle_content_confirmation関数をテスト
            try:
                result = handle_content_confirmation(test_user_id, test_content)
                print(f"✅ handle_content_confirmation結果: {result}")
                
                # 結果の詳細分析
                if result.get('success'):
                    print("✅ コンテンツ追加が成功しました")
                else:
                    error = result.get('error', '不明なエラー')
                    print(f"❌ コンテンツ追加が失敗: {error}")
                    
                    # エラーの原因を分析
                    analyze_error_cause(test_user_id, error)
                
            except Exception as e:
                print(f"❌ handle_content_confirmation例外: {e}")
                import traceback
                traceback.print_exc()
        
        # 3. データベース制約の確認
        print("\n3️⃣ データベース制約の確認")
        
        db_type = get_db_type()
        if db_type == 'postgresql':
            # PostgreSQLの制約を確認
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
        
        # 4. ON CONFLICTクエリの直接テスト
        print("\n4️⃣ ON CONFLICTクエリの直接テスト")
        
        if users:
            test_user_id = users[0][0]
            test_stripe_id = f"test_debug_{test_user_id}"
            
            try:
                # テスト用のデータを挿入
                c.execute('''
                    INSERT INTO subscription_periods (user_id, stripe_subscription_id, subscription_status, status)
                    VALUES (%s, %s, 'test_status', 'active')
                    ON CONFLICT (user_id, stripe_subscription_id) 
                    DO UPDATE SET 
                        subscription_status = EXCLUDED.subscription_status,
                        status = EXCLUDED.status,
                        updated_at = CURRENT_TIMESTAMP
                ''', (test_user_id, test_stripe_id))
                
                print("✅ ON CONFLICTクエリが成功しました")
                
                # テストデータを削除
                c.execute('DELETE FROM subscription_periods WHERE stripe_subscription_id = %s', (test_stripe_id,))
                print("✅ テストデータを削除しました")
                
            except Exception as e:
                print(f"❌ ON CONFLICTクエリが失敗: {e}")
                import traceback
                traceback.print_exc()
        
        # 5. LINEボットの実際の処理フローをシミュレート
        print("\n5️⃣ LINEボット処理フローのシミュレート")
        
        if users:
            test_user_id = users[0][0]
            
            # 1. ユーザーのアクティブなサブスクリプションを確認
            c.execute('''
                SELECT sp.id, sp.user_id, sp.stripe_subscription_id, sp.subscription_status, sp.status
                FROM subscription_periods sp
                WHERE sp.user_id = %s AND sp.status = 'active'
                ORDER BY sp.created_at DESC
                LIMIT 1
            ''', (test_user_id,))
            
            active_subscription = c.fetchone()
            if active_subscription:
                print(f"✅ アクティブなサブスクリプション: ID={active_subscription[0]}, Stripe={active_subscription[2]}")
                
                # 2. コンテンツ追加処理をシミュレート
                test_content = "AI予定秘書"
                print(f"コンテンツ追加シミュレート: {test_content}")
                
                # 3. 実際の処理を実行
                result = handle_content_confirmation(test_user_id, test_content)
                print(f"シミュレート結果: {result}")
                
            else:
                print("❌ アクティブなサブスクリプションが見つかりません")
        
        conn.close()
        
        print("\n🎉 デバッグが完了しました")
        return True
        
    except Exception as e:
        print(f"❌ デバッグエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_error_cause(user_id, error_message):
    """エラーの原因を分析"""
    print(f"\n🔍 エラー原因の分析: {error_message}")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 1. ユーザーのサブスクリプション状況を確認
        c.execute('''
            SELECT id, user_id, stripe_subscription_id, subscription_status, status, created_at
            FROM subscription_periods 
            WHERE user_id = %s
            ORDER BY created_at DESC
        ''', (user_id,))
        
        user_periods = c.fetchall()
        print(f"ユーザー {user_id} のサブスクリプション期間:")
        for period in user_periods:
            print(f"  - ID: {period[0]}, Stripe: {period[2]}, SubStatus: {period[3]}, Status: {period[4]}")
        
        # 2. アクティブなサブスクリプションを確認
        c.execute('''
            SELECT COUNT(*)
            FROM subscription_periods 
            WHERE user_id = %s AND status = 'active'
        ''', (user_id,))
        
        active_count = c.fetchone()[0]
        print(f"アクティブなサブスクリプション数: {active_count}")
        
        # 3. エラーメッセージに基づく分析
        if "ON CONFLICT" in error_message:
            print("🔍 ON CONFLICTエラーの可能性:")
            print("  - データベース制約の問題")
            print("  - 重複データの挿入試行")
            
            # 制約を再確認
            db_type = get_db_type()
            if db_type == 'postgresql':
                c.execute('''
                    SELECT conname, contype, pg_get_constraintdef(oid) as definition
                    FROM pg_constraint 
                    WHERE conrelid = 'subscription_periods'::regclass AND contype = 'u'
                ''')
                
                unique_constraints = c.fetchall()
                print(f"ユニーク制約数: {len(unique_constraints)}")
                for constraint in unique_constraints:
                    print(f"  - {constraint[0]}: {constraint[2]}")
        
        elif "サブスクリプション期間更新エラー" in error_message:
            print("🔍 サブスクリプション期間更新エラーの可能性:")
            print("  - アクティブなサブスクリプションが見つからない")
            print("  - サブスクリプションステータスの問題")
            
            # 最新のサブスクリプションを確認
            if user_periods:
                latest = user_periods[0]
                print(f"最新のサブスクリプション: ID={latest[0]}, Status={latest[4]}, SubStatus={latest[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー分析中にエラー: {e}")

def test_line_webhook_simulation():
    """LINE Webhookのシミュレーション"""
    print("\n=== LINE Webhookシミュレーション ===")
    
    # 実際のLINE Webhookデータをシミュレート
    webhook_data = {
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "text": "はい"
                },
                "source": {
                    "userId": "test_user_id"
                }
            }
        ]
    }
    
    print(f"Webhookデータ: {json.dumps(webhook_data, indent=2, ensure_ascii=False)}")
    
    # 実際の処理をシミュレート
    try:
        from routes.line import line_bp
        from flask import Flask, request
        
        app = Flask(__name__)
        app.register_blueprint(line_bp)
        
        # テスト用のリクエストを作成
        with app.test_client() as client:
            response = client.post('/webhook', 
                                json=webhook_data,
                                headers={'Content-Type': 'application/json'})
            
            print(f"Webhook応答: {response.status_code}")
            print(f"応答内容: {response.get_data(as_text=True)}")
            
    except Exception as e:
        print(f"❌ Webhookシミュレーションエラー: {e}")

def main():
    """メイン関数"""
    print("🚀 LINEボット コンテンツ追加処理デバッグを開始します")
    
    # コンテンツ追加処理のデバッグ
    if debug_content_addition():
        print("✅ デバッグが完了しました")
        
        # LINE Webhookシミュレーション
        test_line_webhook_simulation()
    else:
        print("❌ デバッグに失敗しました")

if __name__ == "__main__":
    main() 