#!/usr/bin/env python3
"""
stripe_subscription_idがNoneのサブスクリプションを修正するスクリプト
"""

import os
import sys
from dotenv import load_dotenv

# 現在のディレクトリをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils.db import get_db_connection, get_db_type

def fix_stripe_subscription_id():
    """stripe_subscription_idがNoneのサブスクリプションを修正"""
    print("🚀 stripe_subscription_id修正を開始します")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプを取得
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        print("=== 修正前の状況 ===")
        c.execute(f'SELECT id, company_id, content_type, subscription_status, stripe_subscription_id FROM company_subscriptions WHERE company_id = 5')
        subscriptions = c.fetchall()
        
        for sub in subscriptions:
            print(f"ID: {sub[0]}, 企業ID: {sub[1]}, コンテンツ: {sub[2]}, ステータス: {sub[3]}, Stripe ID: {sub[4]}")
        
        # stripe_subscription_idがNoneのサブスクリプションを修正
        print("\n=== stripe_subscription_idを修正 ===")
        
        # 企業ID=5の有効なstripe_subscription_idを取得
        c.execute(f'SELECT stripe_subscription_id FROM company_subscriptions WHERE company_id = %s AND stripe_subscription_id IS NOT NULL AND subscription_status = %s LIMIT 1', (5, 'active'))
        valid_subscription = c.fetchone()
        
        if valid_subscription:
            valid_stripe_id = valid_subscription[0]
            print(f"有効なStripe ID: {valid_stripe_id}")
            
            # stripe_subscription_idがNoneのサブスクリプションを更新
            c.execute(f'UPDATE company_subscriptions SET stripe_subscription_id = {placeholder} WHERE company_id = %s AND stripe_subscription_id IS NULL AND subscription_status = %s', (valid_stripe_id, 5, 'active'))
            updated_count = c.rowcount
            print(f"✅ {updated_count}件のサブスクリプションを修正しました")
            
            conn.commit()
            
            print("\n=== 修正後の状況 ===")
            c.execute(f'SELECT id, company_id, content_type, subscription_status, stripe_subscription_id FROM company_subscriptions WHERE company_id = 5')
            subscriptions = c.fetchall()
            
            for sub in subscriptions:
                print(f"ID: {sub[0]}, 企業ID: {sub[1]}, コンテンツ: {sub[2]}, ステータス: {sub[3]}, Stripe ID: {sub[4]}")
        else:
            print("❌ 有効なStripeサブスクリプションIDが見つかりません")
        
        conn.close()
        print("\n✅ stripe_subscription_id修正完了")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_stripe_subscription_id()
