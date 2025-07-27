#!/usr/bin/env python3
"""
トライアル期間終了後の処理テスト
"""

import os
from dotenv import load_dotenv
from services.line_service import check_and_charge_trial_expired_content
from services.user_service import get_user_by_line_id

# 環境変数を読み込み
load_dotenv()

def test_trial_expired_processing():
    """トライアル期間終了後の処理をテスト"""
    print("=== トライアル期間終了後の処理テスト ===")
    
    # テスト用のLINEユーザーID
    test_line_user_id = "U1234567890abcdef"
    
    # ユーザー情報を取得
    user = get_user_by_line_id(test_line_user_id)
    if not user:
        print("❌ テストユーザーが見つかりません")
        return
    
    print(f"✅ ユーザー取得成功: {user['id']}")
    print(f"Stripe Subscription ID: {user['stripe_subscription_id']}")
    
    # トライアル期間終了後の処理を実行
    print("\n=== トライアル期間終了後の処理実行 ===")
    
    result = check_and_charge_trial_expired_content(
        user['id'],  # user_id_db
        user['stripe_subscription_id']  # stripe_subscription_id
    )
    
    print(f"\n=== 実行結果 ===")
    print(f"ステータス: {result.get('status')}")
    print(f"メッセージ: {result.get('message')}")
    
    if result.get('marked_count'):
        print(f"課金予定設定数: {result.get('marked_count')}")
        print(f"課金予定詳細: {result.get('marked_details')}")

if __name__ == "__main__":
    test_trial_expired_processing() 