#!/usr/bin/env python3
"""
新しいサブスクリプションのInvoice Itemを確認するスクリプト
"""

import os
import stripe
from dotenv import load_dotenv
from datetime import datetime

# 環境変数を読み込み
load_dotenv('lp/.env')

def check_invoice_items():
    """Invoice Itemを確認"""
    
    # Stripe APIキーを設定
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    if not stripe.api_key:
        print("❌ STRIPE_SECRET_KEYが設定されていません")
        return
    
    # 新しいサブスクリプションID
    subscription_id = "sub_1RpdcsIxg6C5hAVdneqtbnUG"
    
    try:
        # サブスクリプションを取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        print(f"✅ サブスクリプション取得: {subscription.id}")
        print(f"   ステータス: {subscription.status}")
        print(f"   期間: {datetime.fromtimestamp(subscription.current_period_start)} - {datetime.fromtimestamp(subscription.current_period_end)}")
        if subscription.status == 'trialing':
            print(f"   トライアル終了: {datetime.fromtimestamp(subscription.trial_end)}")
        
        # Invoice Itemを取得
        invoice_items = stripe.InvoiceItem.list(
            customer=subscription.customer,
            limit=100
        )
        
        print(f"\n=== Invoice Item一覧 ===")
        content_items = []
        for item in invoice_items.data:
            print(f"ID: {item.id}")
            print(f"説明: {item.description}")
            print(f"金額: {item.amount}")
            if hasattr(item, 'period') and item.period:
                print(f"期間: {datetime.fromtimestamp(item.period.start)} - {datetime.fromtimestamp(item.period.end)}")
            print("---")
            
            if "コンテンツ追加" in item.description:
                content_items.append(item)
        
        if content_items:
            print(f"\n=== コンテンツ追加のInvoice Item ===")
            for item in content_items:
                print(f"ID: {item.id}")
                print(f"説明: {item.description}")
                print(f"期間: {datetime.fromtimestamp(item.period.start)} - {datetime.fromtimestamp(item.period.end)}")
                print("---")
        else:
            print("✅ コンテンツ追加のInvoice Itemは見つかりません")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    check_invoice_items() 