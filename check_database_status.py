#!/usr/bin/env python3
"""
データベースの状況を確認するスクリプト
"""

import sys
import os
sys.path.append('lp')

from utils.db import get_db_connection

def check_database_status():
    """データベースの状況を確認"""
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # ユーザー情報を取得
        c.execute('SELECT id, line_user_id, stripe_subscription_id FROM users ORDER BY id DESC LIMIT 5')
        users = c.fetchall()
        
        print("=== ユーザー情報 ===")
        for user in users:
            print(f"ID: {user[0]}, LINE ID: {user[1]}, Stripe Sub: {user[2]}")
        
        # usage_logsを取得
        c.execute('''
            SELECT id, user_id, content_type, is_free, pending_charge, stripe_usage_record_id, created_at 
            FROM usage_logs 
            ORDER BY created_at DESC 
            LIMIT 10
        ''')
        usage_logs = c.fetchall()
        
        print("\n=== Usage Logs ===")
        for log in usage_logs:
            print(f"ID: {log[0]}, User: {log[1]}, Content: {log[2]}, Free: {log[3]}, Pending: {log[4]}, Stripe ID: {log[5]}, Created: {log[6]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    check_database_status() 