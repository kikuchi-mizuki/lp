#!/usr/bin/env python3
import os
import stripe
from dotenv import load_dotenv
import psycopg2
import sqlite3
from urllib.parse import urlparse

load_dotenv()
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def get_db_connection():
    """データベース接続を取得（PostgreSQLまたはSQLite）"""
    database_url = os.getenv('DATABASE_URL', 'database.db')
    
    if database_url.startswith('postgresql://'):
        # PostgreSQL接続
        return psycopg2.connect(database_url)
    else:
        # SQLite接続
        return sqlite3.connect(database_url)

def check_duplicate_invoice_items():
    print("=== 重複Invoice Item確認 ===")
    
    # データベースからユーザー情報を取得
    conn = get_db_connection()
    c = conn.cursor()
    
    # データベースタイプを確認
    database_url = os.getenv('DATABASE_URL', 'database.db')
    is_postgresql = database_url.startswith('postgresql://')
    placeholder = '%s' if is_postgresql else '?'
    
    # ユーザー情報を取得
    c.execute(f'SELECT id, line_user_id, stripe_subscription_id FROM users WHERE line_user_id = {placeholder}', ('U1b9d0d75b0c770dc1107dde349d572f7',))
    user = c.fetchone()
    
    if not user:
        print("ユーザーが見つかりません")
        return
    
    user_id, line_user_id, stripe_subscription_id = user
    print(f"ユーザーID: {user_id}")
    print(f"LINE User ID: {line_user_id}")
    print(f"Stripe Subscription ID: {stripe_subscription_id}")
    
    # usage_logsを確認
    print("\n=== データベースのusage_logs ===")
    c.execute(f'SELECT id, content_type, is_free, stripe_usage_record_id, created_at FROM usage_logs WHERE user_id = {placeholder} ORDER BY created_at', (user_id,))
    usage_logs = c.fetchall()
    
    for log in usage_logs:
        print(f"ID: {log[0]}, コンテンツ: {log[1]}, 無料: {log[2]}, Stripe ID: {log[3]}, 作成日: {log[4]}")
    
    # StripeのInvoice Itemsを確認
    print("\n=== StripeのInvoice Items ===")
    try:
        invoice_items = stripe.InvoiceItem.list(
            customer=stripe.Customer.list(subscription=stripe_subscription_id).data[0].id,
            limit=100
        )
        
        for item in invoice_items.data:
            print(f"ID: {item.id}")
            print(f"  説明: {item.description}")
            print(f"  金額: {item.amount}")
            print(f"  期間: {item.period.start} - {item.period.end}")
            print(f"  作成日: {item.created}")
            print("---")
            
    except Exception as e:
        print(f"Stripe API エラー: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_duplicate_invoice_items() 