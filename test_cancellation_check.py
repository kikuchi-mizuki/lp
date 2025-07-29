#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.cancellation_service import is_content_cancelled, get_cancelled_contents
from utils.db import get_db_connection

def test_cancellation_check():
    """解約制限チェック機能をテストする"""
    print("=== 解約制限チェック機能テスト ===\n")
    
    # テスト対象のユーザーID
    test_users = [1, 2, 4, 7]  # 実際のデータベースに存在するユーザーID
    
    for user_id in test_users:
        print(f"--- ユーザーID: {user_id} ---")
        
        # 各コンテンツタイプでの解約チェック
        content_types = ['AI経理秘書', 'AI予定秘書', 'AIタスクコンシェルジュ']
        
        for content_type in content_types:
            is_cancelled = is_content_cancelled(user_id, content_type)
            status = "❌ 解約済み（利用不可）" if is_cancelled else "✅ 利用可能"
            print(f"  {content_type}: {status}")
        
        # 解約済みコンテンツの一覧取得
        cancelled_contents = get_cancelled_contents(user_id)
        if cancelled_contents:
            print(f"  解約済みコンテンツ: {', '.join(cancelled_contents)}")
        else:
            print("  解約済みコンテンツ: なし")
        
        print()

def test_subscription_periods_data():
    """subscription_periodsテーブルのデータを確認"""
    print("=== subscription_periodsテーブルデータ確認 ===\n")
    
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        c.execute('''
            SELECT user_id, stripe_subscription_id, subscription_status, 
                   current_period_start, current_period_end, created_at
            FROM subscription_periods 
            ORDER BY user_id, created_at DESC
        ''')
        
        results = c.fetchall()
        
        if results:
            for row in results:
                user_id, stripe_sub_id, status, period_start, period_end, created_at = row
                print(f"ユーザーID: {user_id}")
                print(f"  Stripe ID: {stripe_sub_id}")
                print(f"  ステータス: {status}")
                print(f"  期間開始: {period_start}")
                print(f"  期間終了: {period_end}")
                print(f"  作成日時: {created_at}")
                print()
        else:
            print("データが見つかりません")
            
    except Exception as e:
        print(f"エラー: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_subscription_periods_data()
    print("\n" + "="*50 + "\n")
    test_cancellation_check() 