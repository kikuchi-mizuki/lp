#!/usr/bin/env python3
import os
import psycopg2
from datetime import datetime, timedelta

def add_test_data_to_railway():
    """RailwayのPostgreSQLにテストデータを追加"""
    try:
        print("=== Railway PostgreSQLにテストデータ追加 ===")
        
        # RailwayのデータベースURL（環境変数から取得）
        # RailwayのWebインターフェースの「Variables」タブからDATABASE_URLをコピーして設定
        railway_db_url = os.getenv('RAILWAY_DATABASE_URL')
        
        if not railway_db_url:
            print("❌ RAILWAY_DATABASE_URL環境変数が設定されていません")
            print("RailwayのWebインターフェースの「Variables」タブからDATABASE_URLを取得して設定してください")
            print("例: export RAILWAY_DATABASE_URL='postgresql://username:password@host:port/database'")
            return False
        
        print(f"📊 Railway PostgreSQLに接続中...")
        conn = psycopg2.connect(railway_db_url)
        c = conn.cursor()
        
        # 現在の日時を取得
        now = datetime.now()
        current_period_start = now
        current_period_end = now + timedelta(days=30)
        trial_start = now
        trial_end = now + timedelta(days=7)
        
        # テストユーザーを作成
        print(f"👥 テストユーザーを作成中...")
        
        test_email = "test_railway@example.com"
        test_line_user_id = "Urailway123456789"
        test_stripe_subscription_id = "sub_railway_test_123"
        test_stripe_customer_id = "cus_railway_test_123"
        
        # 既存ユーザーをチェック
        c.execute('SELECT id FROM users WHERE email = %s', (test_email,))
        existing_user = c.fetchone()
        
        if existing_user:
            print(f"ユーザー {test_email} は既に存在します。ID: {existing_user[0]}")
            user_id = existing_user[0]
        else:
            # 新しいユーザーを作成
            c.execute('''
                INSERT INTO users (email, line_user_id, stripe_subscription_id, stripe_customer_id, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            ''', (test_email, test_line_user_id, test_stripe_subscription_id, test_stripe_customer_id, now))
            
            user_id = c.fetchone()[0]
            print(f"新しいユーザーを作成しました。ID: {user_id}")
        
        # テストコンテンツを追加
        print(f"\n📋 テストコンテンツを追加中...")
        
        test_contents = [
            'AI予定秘書',
            'AI経理秘書', 
            'AIタスクコンシェルジュ'
        ]
        
        for i, content in enumerate(test_contents):
            is_free = (i == 0)  # 1個目は無料
            
            # usage_logsに追加
            c.execute('''
                INSERT INTO usage_logs (user_id, content_type, is_free, created_at)
                VALUES (%s, %s, %s, %s)
            ''', (user_id, content, is_free, now))
            
            # 各コンテンツに対して異なるサブスクリプションIDを使用
            content_subscription_id = f"{test_stripe_subscription_id}_{i+1}"
            
            # subscription_periodsに追加（content_typeカラムなし）
            c.execute('''
                INSERT INTO subscription_periods 
                (user_id, stripe_subscription_id, subscription_status, 
                 current_period_start, current_period_end, trial_start, trial_end, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                user_id, content_subscription_id, 'active',
                current_period_start, current_period_end, trial_start, trial_end, now
            ))
            
            print(f"✅ {content} を追加しました (Subscription ID: {content_subscription_id})")
        
        # 既存のデータも確認
        print(f"\n📊 既存データの確認:")
        
        # usersテーブル
        c.execute('SELECT COUNT(*) FROM users')
        user_count = c.fetchone()[0]
        print(f"  users: {user_count}件")
        
        # usage_logsテーブル
        c.execute('SELECT COUNT(*) FROM usage_logs')
        usage_count = c.fetchone()[0]
        print(f"  usage_logs: {usage_count}件")
        
        # subscription_periodsテーブル
        c.execute('SELECT COUNT(*) FROM subscription_periods')
        period_count = c.fetchone()[0]
        print(f"  subscription_periods: {period_count}件")
        
        # 最新のsubscription_periodsデータを表示
        if period_count > 0:
            c.execute('''
                SELECT id, user_id, stripe_subscription_id, subscription_status, 
                       current_period_start, current_period_end, created_at 
                FROM subscription_periods 
                ORDER BY created_at DESC 
                LIMIT 5
            ''')
            recent_periods = c.fetchall()
            print(f"  最新のsubscription_periods:")
            for period in recent_periods:
                print(f"    ID: {period[0]}, User: {period[1]}, Stripe: {period[2]}, Status: {period[3]}")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Railway PostgreSQLへのテストデータ追加完了")
        print(f"   テストユーザーID: {user_id}")
        print(f"   追加コンテンツ数: {len(test_contents)}")
        print(f"   subscription_periods総数: {period_count}件")
        
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    add_test_data_to_railway() 