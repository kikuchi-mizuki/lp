#!/usr/bin/env python3
import os
import stripe
from dotenv import load_dotenv
from datetime import datetime

load_dotenv('lp/.env')
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def check_stripe_invoice_items():
    print("=== Stripe Invoice Items確認 ===")
    
    # サブスクリプションID（ログから取得）
    subscription_id = "sub_1RpdcsIxg6C5hAVdneqtbnUG"
    
    try:
        # サブスクリプション情報を取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        customer_id = subscription.customer
        
        print(f"サブスクリプションID: {subscription_id}")
        print(f"顧客ID: {customer_id}")
        print(f"ステータス: {subscription.status}")
        print(f"現在の期間: {datetime.fromtimestamp(subscription.current_period_start)} - {datetime.fromtimestamp(subscription.current_period_end)}")
        
        # Invoice Itemsを取得
        print("\n=== Invoice Items ===")
        invoice_items = stripe.InvoiceItem.list(
            customer=customer_id,
            limit=100
        )
        
        for item in invoice_items.data:
            print(f"ID: {item.id}")
            print(f"  説明: {item.description}")
            print(f"  金額: ¥{item.amount:,}")
            print(f"  期間: {datetime.fromtimestamp(item.period.start)} - {datetime.fromtimestamp(item.period.end)}")
            print(f"  作成日: {datetime.fromtimestamp(item.created)}")
            print(f"  サブスクリプション: {item.subscription}")
            print("---")
            
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    check_stripe_invoice_items() 