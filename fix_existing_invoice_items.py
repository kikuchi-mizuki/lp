#!/usr/bin/env python3
"""
既存のInvoice Itemを削除して期間を修正するスクリプト
"""

import os
import stripe
from dotenv import load_dotenv
from datetime import datetime, timedelta

# 環境変数を読み込み
load_dotenv('lp/.env')

def fix_invoice_items():
    """既存のInvoice Itemを修正"""
    
    # Stripe APIキーを設定
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    if not stripe.api_key:
        print("❌ STRIPE_SECRET_KEYが設定されていません")
        return
    
    # サブスクリプションID
    subscription_id = "sub_1RpVU2Ixg6C5hAVdeyAz8Tjk"
    
    try:
        # サブスクリプションを取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        print(f"✅ サブスクリプション取得: {subscription.id}")
        print(f"   ステータス: {subscription.status}")
        
        # 既存のInvoice Itemを取得
        invoice_items = stripe.InvoiceItem.list(
            customer=subscription.customer,
            limit=100
        )
        
        print(f"\n=== 既存のInvoice Item ===")
        for item in invoice_items.data:
            print(f"ID: {item.id}")
            print(f"説明: {item.description}")
            print(f"金額: {item.amount}")
            if hasattr(item, 'period') and item.period:
                print(f"期間: {datetime.fromtimestamp(item.period.start)} - {datetime.fromtimestamp(item.period.end)}")
            print("---")
        
        # コンテンツ追加のInvoice Itemを削除
        content_items = [item for item in invoice_items.data if "コンテンツ追加" in item.description]
        
        if content_items:
            print(f"\n=== コンテンツ追加のInvoice Itemを削除 ===")
            for item in content_items:
                try:
                    item.delete()
                    print(f"✅ 削除成功: {item.id} - {item.description}")
                except Exception as e:
                    print(f"❌ 削除失敗: {item.id} - {e}")
        else:
            print("✅ 削除対象のInvoice Itemが見つかりません")
        
        print(f"\n=== 修正完了 ===")
        print("既存のInvoice Itemを削除しました。")
        print("次回コンテンツ追加時に正しい期間で作成されます。")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    fix_invoice_items() 