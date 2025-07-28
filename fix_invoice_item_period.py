#!/usr/bin/env python3
"""
Invoice Itemの期間を修正するスクリプト
"""

import os
import stripe
from dotenv import load_dotenv
from datetime import datetime

# 環境変数を読み込み
load_dotenv('lp/.env')

def fix_invoice_item_period():
    """Invoice Itemの期間を修正"""
    
    # Stripe APIキーを設定
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    if not stripe.api_key:
        print("❌ STRIPE_SECRET_KEYが設定されていません")
        return
    
    print("=== Invoice Item期間修正 ===")
    
    # サブスクリプションID
    subscription_id = "sub_1RpdcsIxg6C5hAVdneqtbnUG"
    invoice_item_id = "ii_1RpoEtIxg6C5hAVdmfOaRuni"
    
    try:
        # サブスクリプション情報を取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        customer_id = subscription.customer
        
        print(f"サブスクリプションID: {subscription_id}")
        print(f"顧客ID: {customer_id}")
        print(f"現在の期間: {datetime.fromtimestamp(subscription.current_period_start)} - {datetime.fromtimestamp(subscription.current_period_end)}")
        
        # 現在のInvoice Itemを取得
        invoice_item = stripe.InvoiceItem.retrieve(invoice_item_id)
        description = invoice_item.description
        amount = invoice_item.amount
        
        print(f"\n現在のInvoice Item:")
        print(f"ID: {invoice_item.id}")
        print(f"説明: {description}")
        print(f"金額: ¥{amount:,}")
        print(f"現在の期間: {datetime.fromtimestamp(invoice_item.period.start)} - {datetime.fromtimestamp(invoice_item.period.end)}")
        
        # 正しい期間を設定
        correct_start = subscription.current_period_start
        correct_end = subscription.current_period_end
        
        print(f"\n正しい期間: {datetime.fromtimestamp(correct_start)} - {datetime.fromtimestamp(correct_end)}")
        
        # Invoice Itemを削除して再作成
        print(f"\nInvoice Itemを削除中...")
        invoice_item.delete()
        print(f"✅ 削除完了")
        
        # 新しいInvoice Itemを作成
        print(f"新しいInvoice Itemを作成中...")
        new_invoice_item = stripe.InvoiceItem.create(
            customer=customer_id,
            amount=amount,
            currency='jpy',
            description=description,
            subscription=subscription_id,
            period={
                'start': correct_start,
                'end': correct_end
            }
        )
        
        print(f"✅ 作成完了")
        print(f"新しいID: {new_invoice_item.id}")
        print(f"新しい期間: {datetime.fromtimestamp(new_invoice_item.period.start)} - {datetime.fromtimestamp(new_invoice_item.period.end)}")
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    fix_invoice_item_period() 