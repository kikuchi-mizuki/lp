#!/usr/bin/env python3
"""
サブスクリプション情報をsubscription_periodsテーブルに追加するスクリプト
"""

import os
import sys
from dotenv import load_dotenv
import stripe
from utils.db import get_db_connection, get_db_type

load_dotenv()

def fix_subscription_periods():
    """サブスクリプション情報をsubscription_periodsテーブルに追加"""
    
    # Stripe APIキーを設定
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    if not stripe.api_key:
        print("❌ STRIPE_SECRET_KEYが設定されていません")
        return
    
    print("🔧 サブスクリプション情報を修正中...")
    
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
            
            try:
                # Stripeからサブスクリプション情報を取得
                subscription = stripe.Subscription.retrieve(subscription_id)
                
                # subscription_periodsテーブルに追加
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
                        subscription.status,
                        subscription.current_period_start,
                        subscription.current_period_end,
                        subscription.trial_start,
                        subscription.trial_end
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
                        subscription.status,
                        subscription.current_period_start,
                        subscription.current_period_end,
                        subscription.trial_start,
                        subscription.trial_end
                    ))
                
                conn.commit()
                print(f"   ✅ サブスクリプション情報を追加しました")
                
            except Exception as e:
                print(f"   ❌ エラー: {e}")
                conn.rollback()
        
        print(f"\n🎉 修正完了！")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    fix_subscription_periods() 