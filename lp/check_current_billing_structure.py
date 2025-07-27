#!/usr/bin/env python3
"""
現在の課金構造確認
"""

import os
from dotenv import load_dotenv
from services.user_service import get_user_by_line_id
from utils.db import get_db_connection

# 環境変数を読み込み
load_dotenv()

def check_current_billing_structure():
    """現在の課金構造を確認"""
    print("=== 現在の課金構造確認 ===")
    
    # テスト用のLINEユーザーID
    test_line_user_id = "U1234567890abcdef"
    
    # ユーザー情報を取得
    user = get_user_by_line_id(test_line_user_id)
    if not user:
        print("❌ テストユーザーが見つかりません")
        return
    
    print(f"✅ ユーザー取得成功: {user['id']}")
    print(f"Stripe Subscription ID: {user['stripe_subscription_id']}")
    
    # サブスクリプション状態を確認
    print("\n=== サブスクリプション状態 ===")
    from services.line_service import check_subscription_status
    subscription_status = check_subscription_status(user['stripe_subscription_id'])
    
    print(f"ステータス: {subscription_status.get('status', 'unknown')}")
    print(f"有効: {subscription_status.get('is_active', False)}")
    print(f"期間終了時解約予定: {subscription_status.get('cancel_at_period_end', False)}")
    
    if subscription_status.get('current_period_end'):
        import datetime
        period_end = datetime.datetime.fromtimestamp(subscription_status['current_period_end'])
        print(f"現在の期間終了: {period_end}")
    
    # 使用量ログを確認
    print("\n=== 使用量ログ確認 ===")
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            SELECT id, content_type, is_free, pending_charge, created_at
            FROM usage_logs
            WHERE user_id = %s
            ORDER BY created_at ASC
        ''', (user['id'],))
        logs = c.fetchall()
        conn.close()
        
        print(f"使用量ログ総数: {len(logs)}件")
        
        for i, log in enumerate(logs, 1):
            log_id, content_type, is_free, pending_charge, created_at = log
            print(f"ログ{i}: {content_type}")
            print(f"  無料: {is_free}")
            print(f"  課金予定: {pending_charge}")
            print(f"  作成日時: {created_at}")
            print("---")
            
        # 課金構造の分析
        print("\n=== 課金構造分析 ===")
        
        if subscription_status.get('status') == 'trialing':
            print("📋 現在の課金構造:")
            print("・AIコレクションズ → 月額3,900円（トライアル期間中は無料）")
            print("・AIコレクションズ（追加） → コンテンツ追加は無料（トライアル期間中）")
            
            # トライアル期間終了後の予定
            free_count = sum(1 for log in logs if log[2])  # is_free
            paid_count = len(logs) - free_count
            
            print(f"\n📊 トライアル期間終了後の予定:")
            print(f"・無料コンテンツ: {free_count}件")
            print(f"・有料コンテンツ: {paid_count}件")
            
            if free_count > 0:
                print(f"・2個目以降のコンテンツ: ¥1,500/個 × {free_count - 1}個 = ¥{(free_count - 1) * 1500:,}円")
                print(f"・月額合計予定: ¥3,900 + ¥{(free_count - 1) * 1500:,} = ¥{3900 + (free_count - 1) * 1500:,}円")
        else:
            print("📋 現在の課金構造:")
            print("・AIコレクションズ → 月額3,900円")
            
            paid_count = sum(1 for log in logs if not log[2])  # not is_free
            if paid_count > 0:
                print(f"・AIコレクションズ（追加） → ¥1,500/個 × {paid_count}個 = ¥{paid_count * 1500:,}円")
                print(f"・月額合計: ¥3,900 + ¥{paid_count * 1500:,} = ¥{3900 + paid_count * 1500:,}円")
            else:
                print("・AIコレクションズ（追加） → なし")
                print("・月額合計: ¥3,900円")
                
    except Exception as e:
        print(f"❌ データベース確認エラー: {e}")

if __name__ == "__main__":
    check_current_billing_structure() 