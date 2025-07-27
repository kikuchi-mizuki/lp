#!/usr/bin/env python3
"""
分岐処理修正のテスト
"""

import os
from dotenv import load_dotenv
from utils.db import get_db_connection

# 環境変数を読み込み
load_dotenv()

def test_branching_fix():
    """分岐処理修正をテスト"""
    print("=== 分岐処理修正のテスト ===")
    
    # データベースのユーザー確認
    print("\n=== データベースのユーザー確認 ===")
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            SELECT id, line_user_id, email, stripe_subscription_id, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT 5
        ''')
        users = c.fetchall()
        conn.close()
        
        print(f"登録ユーザー数: {len(users)}")
        for user in users:
            user_id, line_user_id, email, stripe_subscription_id, created_at = user
            print(f"  - ID: {user_id}, LINE ID: {line_user_id}, Email: {email}, Subscription: {stripe_subscription_id}, 作成日時: {created_at}")
            
    except Exception as e:
        print(f"データベース確認エラー: {e}")
    
    # 使用量ログ確認
    print("\n=== 使用量ログ確認 ===")
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            SELECT id, user_id, content_type, is_free, pending_charge, created_at
            FROM usage_logs
            ORDER BY created_at DESC
            LIMIT 10
        ''')
        logs = c.fetchall()
        conn.close()
        
        print(f"使用量ログ数: {len(logs)}")
        for log in logs:
            log_id, user_id, content_type, is_free, pending_charge, created_at = log
            print(f"  - ID: {log_id}, User: {user_id}, Content: {content_type}, 無料: {is_free}, 課金予定: {pending_charge}, 作成日時: {created_at}")
            
    except Exception as e:
        print(f"使用量ログ確認エラー: {e}")
    
    # 修正内容の説明
    print("\n=== 修正内容 ===")
    print("✅ 分岐処理のデバッグログ追加:")
    print("  1. add_select状態での処理ログ")
    print("  2. 各コマンド受信時のログ")
    print("  3. デフォルト処理時のログ")
    print("  4. 状態遷移の詳細ログ")
    
    print("\n✅ 期待される結果:")
    print("  - 分岐処理の問題が特定される")
    print("  - デバッグログで問題箇所が判明する")
    print("  - 正しい分岐処理が動作する")
    
    print("\n📋 次のステップ:")
    print("  1. 実際のLINE Botで「追加」→「1」をテスト")
    print("  2. デバッグログを確認して問題箇所を特定")
    print("  3. 必要に応じて追加修正を実施")

if __name__ == "__main__":
    test_branching_fix() 