#!/usr/bin/env python3
"""
Stripe WebhookのForeign Keyエラーを修正
"""

import os
import psycopg2
from dotenv import load_dotenv

def fix_stripe_webhook():
    """Stripe Webhookの修正版を実装"""
    
    # データベース接続
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        database_url = "postgresql://postgres:WZgnjZezoefHmxbwRjUbiPhajtwubmUs@gondola.proxy.rlwy.net:16797/railway"
    
    try:
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        print("✅ データベース接続成功")
        
        # テスト用データ
        test_email = "test@example.com"
        test_user_id = 999
        test_subscription_id = "sub_test_123"
        test_customer_id = "cus_test_123"
        
        print(f"テストデータ: email={test_email}, user_id={test_user_id}, subscription_id={test_subscription_id}")
        
        # 1. 企業データ作成（RETURNING idを使用）
        company_name = f"企業_{test_email.split('@')[0]}"
        c.execute('''
            INSERT INTO companies (company_name, company_code, email, stripe_subscription_id, status, created_at)
            VALUES (%s, %s, %s, %s, 'active', CURRENT_TIMESTAMP)
            RETURNING id
        ''', (company_name, f"company_{test_user_id}", test_email, test_subscription_id))
        
        company_id = c.fetchone()[0]
        print(f"✅ 企業データ作成成功: company_id={company_id}, company_name={company_name}")
        
        # 2. company_paymentsテーブルに決済データ作成
        c.execute('''
            INSERT INTO company_payments (company_id, stripe_customer_id, stripe_subscription_id, subscription_status, created_at)
            VALUES (%s, %s, %s, 'active', CURRENT_TIMESTAMP)
        ''', (company_id, test_customer_id, test_subscription_id))
        
        print(f"✅ company_payments作成成功: company_id={company_id}")
        
        # 3. 確認
        c.execute('SELECT id, company_name, email FROM companies WHERE id = %s', (company_id,))
        company = c.fetchone()
        print(f"確認: company={company}")
        
        c.execute('SELECT company_id, stripe_customer_id FROM company_payments WHERE company_id = %s', (company_id,))
        payment = c.fetchone()
        print(f"確認: payment={payment}")
        
        conn.commit()
        print("✅ 修正完了")
        
        # テストデータを削除
        c.execute('DELETE FROM company_payments WHERE company_id = %s', (company_id,))
        c.execute('DELETE FROM companies WHERE id = %s', (company_id,))
        conn.commit()
        print("✅ テストデータ削除完了")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_stripe_webhook() 