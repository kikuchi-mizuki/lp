#!/usr/bin/env python3
"""
データベースのサブスクリプションIDを更新するスクリプト
"""

import sys
import os
sys.path.append('lp')

from utils.db import get_db_connection

def update_database_subscription():
    """データベースのサブスクリプションIDを更新"""
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 古いサブスクリプションID
        old_subscription_id = "sub_1RpVU2Ixg6C5hAVdeyAz8Tjk"
        # 新しいサブスクリプションID
        new_subscription_id = "sub_1RpdcsIxg6C5hAVdneqtbnUG"
        
        # ユーザーテーブルのサブスクリプションIDを更新
        c.execute('''
            UPDATE users 
            SET stripe_subscription_id = %s 
            WHERE stripe_subscription_id = %s
        ''', (new_subscription_id, old_subscription_id))
        
        updated_users = c.rowcount
        print(f"✅ ユーザーテーブル更新: {updated_users}件")
        
        # usage_logsのstripe_usage_record_idをクリア（削除されたInvoice Itemのため）
        c.execute('''
            UPDATE usage_logs 
            SET stripe_usage_record_id = NULL 
            WHERE stripe_usage_record_id IS NOT NULL
        ''')
        
        cleared_logs = c.rowcount
        print(f"✅ Usage Logs更新: {cleared_logs}件")
        
        # 変更をコミット
        conn.commit()
        conn.close()
        
        print(f"\n=== 更新完了 ===")
        print(f"サブスクリプションID: {old_subscription_id} → {new_subscription_id}")
        print("stripe_usage_record_idをクリアしました")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    update_database_subscription() 