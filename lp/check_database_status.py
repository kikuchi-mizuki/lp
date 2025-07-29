#!/usr/bin/env python3
import os
import sys
from utils.db import get_db_connection, get_db_type

def check_database_status():
    """データベースの状況を確認"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        print("=== データベース状況確認 ===")
        
        # テーブル一覧を確認
        db_type = get_db_type()
        if db_type == 'postgresql':
            c.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
        else:
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        
        tables = c.fetchall()
        print(f"\n📋 テーブル一覧:")
        for table in tables:
            table_name = table[0]
            print(f"  - {table_name}")
        
        # usersテーブルの確認
        print(f"\n👥 usersテーブル:")
        c.execute('SELECT COUNT(*) FROM users')
        user_count = c.fetchone()[0]
        print(f"  総ユーザー数: {user_count}")
        
        if user_count > 0:
            c.execute('SELECT id, email, line_user_id, stripe_subscription_id, created_at FROM users ORDER BY created_at DESC LIMIT 5')
            recent_users = c.fetchall()
            print(f"  最新5ユーザー:")
            for user in recent_users:
                print(f"    ID: {user[0]}, Email: {user[1]}, LINE: {user[2]}, Stripe: {user[3]}, Created: {user[4]}")
        
        # usage_logsテーブルの確認
        print(f"\n📊 usage_logsテーブル:")
        c.execute('SELECT COUNT(*) FROM usage_logs')
        usage_count = c.fetchone()[0]
        print(f"  総利用記録数: {usage_count}")
        
        if usage_count > 0:
            c.execute('SELECT id, user_id, content_type, is_free, pending_charge, created_at FROM usage_logs ORDER BY created_at DESC LIMIT 10')
            recent_usage = c.fetchall()
            print(f"  最新10件の利用記録:")
            for usage in recent_usage:
                print(f"    ID: {usage[0]}, User: {usage[1]}, Content: {usage[2]}, Free: {usage[3]}, Pending: {usage[4]}, Created: {usage[5]}")
        
        # subscription_periodsテーブルの確認
        print(f"\n⏰ subscription_periodsテーブル:")
        c.execute('SELECT COUNT(*) FROM subscription_periods')
        period_count = c.fetchone()[0]
        print(f"  総期間記録数: {period_count}")
        
        if period_count > 0:
            c.execute('SELECT id, user_id, content_type, stripe_subscription_id, subscription_status, current_period_start, current_period_end FROM subscription_periods ORDER BY created_at DESC LIMIT 5')
            recent_periods = c.fetchall()
            print(f"  最新5件の期間記録:")
            for period in recent_periods:
                print(f"    ID: {period[0]}, User: {period[1]}, Content: {period[2]}, Stripe: {period[3]}, Status: {period[4]}, Start: {period[5]}, End: {period[6]}")
        
        # cancellation_historyテーブルの確認
        print(f"\n🚫 cancellation_historyテーブル:")
        c.execute('SELECT COUNT(*) FROM cancellation_history')
        cancel_count = c.fetchone()[0]
        print(f"  総解約記録数: {cancel_count}")
        
        if cancel_count > 0:
            c.execute('SELECT id, user_id, content_type, cancelled_at, restriction_start, restriction_end FROM cancellation_history ORDER BY cancelled_at DESC LIMIT 5')
            recent_cancels = c.fetchall()
            print(f"  最新5件の解約記録:")
            for cancel in recent_cancels:
                print(f"    ID: {cancel[0]}, User: {cancel[1]}, Content: {cancel[2]}, Cancelled: {cancel[3]}, Restriction: {cancel[4]} - {cancel[5]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_status() 