#!/usr/bin/env python3
import os
import stripe
from dotenv import load_dotenv
from datetime import datetime

load_dotenv('lp/.env')
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def check_all_invoice_items():
    print("=== 全てのInvoice Item確認 ===")
    
    # サブスクリプションID
    subscription_id = "sub_1RpdcsIxg6C5hAVdneqtbnUG"
    
    try:
        # サブスクリプション情報を取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        customer_id = subscription.customer
        
        print(f"サブスクリプションID: {subscription_id}")
        print(f"顧客ID: {customer_id}")
        print(f"ステータス: {subscription.status}")
        print(f"現在の期間: {datetime.fromtimestamp(subscription.current_period_start)} - {datetime.fromtimestamp(subscription.current_period_end)}")
        
        if subscription.status == 'trialing':
            print(f"トライアル終了: {datetime.fromtimestamp(subscription.trial_end)}")
        
        # 全てのInvoice Itemsを取得
        print("\n=== 全てのInvoice Items ===")
        invoice_items = stripe.InvoiceItem.list(
            customer=customer_id,
            limit=100
        )
        
        incorrect_items = []
        
        for item in invoice_items.data:
            start_date = datetime.fromtimestamp(item.period.start)
            end_date = datetime.fromtimestamp(item.period.end)
            
            print(f"ID: {item.id}")
            print(f"  説明: {item.description}")
            print(f"  金額: ¥{item.amount:,}")
            print(f"  期間: {start_date} - {end_date}")
            
            # 正しい期間かチェック
            expected_start = datetime(2025, 8, 4, 8, 5, 6)  # 2025-08-04 08:05:06
            expected_end = datetime(2025, 9, 3, 8, 5, 6)    # 2025-09-03 08:05:06
            
            if start_date != expected_start or end_date != expected_end:
                print(f"  ❌ 期間がずれています！")
                incorrect_items.append(item)
            else:
                print(f"  ✅ 期間は正しい")
            print("---")
        
        if incorrect_items:
            print(f"\n期間がずれているInvoice Item: {len(incorrect_items)}件")
            return incorrect_items
        else:
            print("\n全てのInvoice Itemの期間は正しいです。")
            return []
            
    except Exception as e:
        print(f"エラー: {e}")
        return []

if __name__ == "__main__":
    check_all_invoice_items() 