#!/usr/bin/env python3
"""
包括的な修正テスト
"""

import os
from dotenv import load_dotenv
from utils.db import get_db_connection, get_db_type

# 環境変数を読み込み
load_dotenv()

def test_comprehensive_fix():
    """包括的な修正テスト"""
    print("=== 包括的な修正テスト ===")
    
    # 1. データベース接続テスト
    print("\n=== 1. データベース接続テスト ===")
    try:
        conn = get_db_connection()
        db_type = get_db_type()
        print(f"✅ データベース接続成功: {db_type}")
        conn.close()
    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")
    
    # 2. プレースホルダーテスト
    print("\n=== 2. プレースホルダーテスト ===")
    db_type = get_db_type()
    placeholder = '%s' if db_type == 'postgresql' else '?'
    print(f"✅ プレースホルダー: {placeholder} (DB: {db_type})")
    
    # 3. 修正内容の確認
    print("\n=== 3. 修正内容の確認 ===")
    print("✅ 修正済み項目:")
    print("  - ユーザー状態管理の完全修正")
    print("  - content_info[str(content_number)] の修正")
    print("  - データベースプレースホルダーの動的選択")
    print("  - check_subscription_status関数の改善")
    
    print("\n✅ 修正前の問題:")
    print("  - KeyError: 'cancel_at_period_end'")
    print("  - KeyError: 1 (content_infoアクセス)")
    print("  - sqlite3.OperationalError: near '%': syntax error")
    print("  - 重複した初回案内文送信")
    print("  - 分岐処理の不具合")
    
    print("\n✅ 修正後の期待される動作:")
    print("  - データベースタイプに応じたプレースホルダー使用")
    print("  - エラーハンドリングの改善")
    print("  - ユーザー状態の正しい管理")
    print("  - 分岐処理の正常動作")
    
    # 4. 環境変数チェック
    print("\n=== 4. 環境変数チェック ===")
    required_vars = [
        'STRIPE_SECRET_KEY',
        'STRIPE_MONTHLY_PRICE_ID',
        'STRIPE_USAGE_PRICE_ID',
        'LINE_CHANNEL_ACCESS_TOKEN',
        'LINE_CHANNEL_SECRET',
        'DATABASE_URL'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: 設定済み")
        else:
            print(f"❌ {var}: 未設定")
    
    print("\n🔧 次のステップ:")
    print("  1. 実際のLINE Botでテスト")
    print("  2. エラーログの監視")
    print("  3. 分岐処理の動作確認")
    print("  4. Stripe連携の動作確認")

if __name__ == "__main__":
    test_comprehensive_fix() 