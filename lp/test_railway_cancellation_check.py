#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import psycopg2
from datetime import datetime

def is_content_cancelled_railway(user_id, content_type):
    """Railwayデータベースで解約チェック"""
    railway_db_url = os.getenv('RAILWAY_DATABASE_URL')
    if not railway_db_url:
        print("❌ RAILWAY_DATABASE_URLが設定されていません")
        return True
    
    try:
        conn = psycopg2.connect(railway_db_url)
        c = conn.cursor()
        
        # subscription_periodsテーブルでサブスクリプション状態を確認
        c.execute('''
            SELECT subscription_status FROM subscription_periods 
            WHERE user_id = %s AND stripe_subscription_id IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id,))
        
        result = c.fetchone()
        conn.close()
        
        if result:
            subscription_status = result[0]
            # 解約済みとみなすステータス
            is_cancelled = subscription_status in ['canceled', 'incomplete', 'incomplete_expired', 'unpaid', 'past_due']
            print(f"[DEBUG] Railway解約チェック: user_id={user_id}, content_type={content_type}, status={subscription_status}, is_cancelled={is_cancelled}")
            return is_cancelled
        else:
            print(f"[DEBUG] Railway解約チェック: user_id={user_id}, content_type={content_type}, no_subscription_record, is_cancelled=True")
            return True  # レコードがない場合は解約済みとみなす
            
    except Exception as e:
        print(f"❌ Railway解約チェックエラー: {e}")
        return True

def get_cancelled_contents_railway(user_id):
    """Railwayデータベースで解約済みコンテンツを取得"""
    railway_db_url = os.getenv('RAILWAY_DATABASE_URL')
    if not railway_db_url:
        print("❌ RAILWAY_DATABASE_URLが設定されていません")
        return []
    
    try:
        conn = psycopg2.connect(railway_db_url)
        c = conn.cursor()
        
        # 解約済みステータスのレコードを取得
        c.execute('''
            SELECT subscription_status FROM subscription_periods 
            WHERE user_id = %s AND subscription_status IN ('canceled', 'incomplete', 'incomplete_expired', 'unpaid', 'past_due')
            ORDER BY created_at DESC
        ''', (user_id,))
        
        results = c.fetchall()
        conn.close()
        
        # 解約済みステータスがある場合は、すべてのコンテンツが解約済みとみなす
        if results:
            cancelled_contents = ['AI経理秘書', 'AI予定秘書', 'AIタスクコンシェルジュ']
        else:
            cancelled_contents = []
            
        print(f"[DEBUG] Railway解約コンテンツ取得: user_id={user_id}, cancelled_contents={cancelled_contents}")
        return cancelled_contents
        
    except Exception as e:
        print(f"❌ Railway解約コンテンツ取得エラー: {e}")
        return []

def test_railway_cancellation_check():
    """Railwayデータベースで解約制限チェック機能をテスト"""
    print("=== Railwayデータベース解約制限チェック機能テスト ===\n")
    
    # テスト対象のユーザーID（Railwayデータベースに存在するユーザー）
    test_users = [1, 7]  # Railwayデータベースに存在するユーザーID
    
    for user_id in test_users:
        print(f"--- ユーザーID: {user_id} ---")
        
        # 各コンテンツタイプでの解約チェック
        content_types = ['AI経理秘書', 'AI予定秘書', 'AIタスクコンシェルジュ']
        
        for content_type in content_types:
            is_cancelled = is_content_cancelled_railway(user_id, content_type)
            status = "❌ 解約済み（利用不可）" if is_cancelled else "✅ 利用可能"
            print(f"  {content_type}: {status}")
        
        # 解約済みコンテンツの一覧取得
        cancelled_contents = get_cancelled_contents_railway(user_id)
        if cancelled_contents:
            print(f"  解約済みコンテンツ: {', '.join(cancelled_contents)}")
        else:
            print("  解約済みコンテンツ: なし")
        
        print()

def test_railway_subscription_data():
    """Railwayデータベースのsubscription_periodsデータを確認"""
    print("=== Railway subscription_periodsデータ確認 ===\n")
    
    railway_db_url = os.getenv('RAILWAY_DATABASE_URL')
    if not railway_db_url:
        print("❌ RAILWAY_DATABASE_URLが設定されていません")
        return
    
    try:
        conn = psycopg2.connect(railway_db_url)
        c = conn.cursor()
        
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
        print(f"❌ エラー: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_railway_subscription_data()
    print("\n" + "="*50 + "\n")
    test_railway_cancellation_check() 