#!/usr/bin/env python3
"""
Railway本番環境用：サブスクリプション情報をsubscription_periodsテーブルに追加
"""

import os
import sys
from dotenv import load_dotenv
import stripe
from utils.db import get_db_connection, get_db_type

# Railway環境変数を読み込み
load_dotenv()

def fix_subscription_periods_railway():
    """Railway環境でサブスクリプション情報を修正"""
    
    print("🔧 Railway環境でサブスクリプション情報を修正中...")
    
    # データベース接続
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # サブスクリプションIDがあるがsubscription_periodsにないユーザーを取得
        c.execute('''
            SELECT u.id, u.email, u.stripe_customer_id, u.stripe_subscription_id
            FROM users u
            LEFT JOIN subscription_periods sp ON u.id = sp.user_id
            WHERE u.stripe_subscription_id IS NOT NULL 
            AND sp.id IS NULL
        ''')
        
        users_to_fix = c.fetchall()
        print(f"修正対象ユーザー数: {len(users_to_fix)}")
        
        for user in users_to_fix:
            user_id, email, customer_id, subscription_id = user
            print(f"\n📧 ユーザー: {email}")
            print(f"   Customer ID: {customer_id}")
            print(f"   Subscription ID: {subscription_id}")
            
            # 手動でサブスクリプション情報を追加（Stripe APIを使わず）
            db_type = get_db_type()
            
            if db_type == 'postgresql':
                c.execute('''
                    INSERT INTO subscription_periods 
                    (user_id, stripe_subscription_id, subscription_status, 
                     current_period_start, current_period_end, trial_start, trial_end)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (
                    user_id,
                    subscription_id,
                    'active',  # デフォルトでactive
                    None,  # current_period_start
                    None,  # current_period_end
                    None,  # trial_start
                    None   # trial_end
                ))
            else:
                c.execute('''
                    INSERT INTO subscription_periods 
                    (user_id, stripe_subscription_id, subscription_status, 
                     current_period_start, current_period_end, trial_start, trial_end)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    subscription_id,
                    'active',  # デフォルトでactive
                    None,  # current_period_start
                    None,  # current_period_end
                    None,  # trial_start
                    None   # trial_end
                ))
            
            conn.commit()
            print(f"   ✅ サブスクリプション情報を追加しました (status: active)")
        
        print(f"\n🎉 修正完了！")
        
        # 修正後の確認
        c.execute('''
            SELECT u.email, sp.stripe_subscription_id, sp.subscription_status
            FROM users u
            LEFT JOIN subscription_periods sp ON u.id = sp.user_id
            WHERE u.email = 'mmms.dy.23@gmail.com'
        ''')
        
        result = c.fetchone()
        if result:
            email, sub_id, status = result
            print(f"\n📊 修正確認:")
            print(f"   Email: {email}")
            print(f"   Subscription ID: {sub_id}")
            print(f"   Status: {status}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    fix_subscription_periods_railway() 