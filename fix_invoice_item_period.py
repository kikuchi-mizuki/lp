#!/usr/bin/env python3
"""
Invoice Itemの期間を修正するスクリプト
"""

import os
import stripe
from dotenv import load_dotenv
from datetime import datetime, timedelta

# 環境変数を読み込み
load_dotenv('lp/.env')

def fix_invoice_item_period():
    """Invoice Itemの期間を修正"""
    
    # Stripe APIキーを設定
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    if not stripe.api_key:
        print("❌ STRIPE_SECRET_KEYが設定されていません")
        return
    
    # サブスクリプションID
    subscription_id = "sub_1RpdcsIxg6C5hAVdneqtbnUG"
    invoice_item_id = "ii_1RpinXIxg6C5hAVduOkSbWDE"
    
    try:
        # サブスクリプションを取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        print(f"✅ サブスクリプション取得: {subscription.id}")
        print(f"   ステータス: {subscription.status}")
        print(f"   期間: {datetime.fromtimestamp(subscription.current_period_start)} - {datetime.fromtimestamp(subscription.current_period_end)}")
        if subscription.status == 'trialing':
            print(f"   トライアル終了: {datetime.fromtimestamp(subscription.trial_end)}")
        
        # 現在のInvoice Itemを取得
        invoice_item = stripe.InvoiceItem.retrieve(invoice_item_id)
        description = invoice_item.description
        amount = invoice_item.amount
        
        print(f"\n=== 現在のInvoice Item ===")
        print(f"ID: {invoice_item.id}")
        print(f"説明: {description}")
        print(f"金額: {amount}")
        if hasattr(invoice_item, 'period') and invoice_item.period:
            print(f"現在の期間: {datetime.fromtimestamp(invoice_item.period.start)} - {datetime.fromtimestamp(invoice_item.period.end)}")
        
        # 正しい期間を計算
        if subscription.status == 'trialing':
            trial_end = subscription.trial_end
            if isinstance(trial_end, int):
                trial_end_dt = datetime.fromtimestamp(trial_end)
            else:
                trial_end_dt = trial_end
            
            # 次の月額期間の開始日（トライアル終了日の翌日）
            correct_period_start = int((trial_end_dt + timedelta(days=1)).timestamp())
            
            # 次の月額期間の終了日（開始日から1ヶ月後）
            next_period_end = trial_end_dt + timedelta(days=1) + timedelta(days=30)
            correct_period_end = int(next_period_end.timestamp())
            
            print(f"\n=== 正しい期間 ===")
            print(f"トライアル終了: {trial_end_dt}")
            print(f"正しい開始日: {datetime.fromtimestamp(correct_period_start)}")
            print(f"正しい終了日: {datetime.fromtimestamp(correct_period_end)}")
        
        # 現在のInvoice Itemを削除
        print(f"\n=== Invoice Item削除 ===")
        invoice_item.delete()
        print(f"✅ 削除成功: {invoice_item_id}")
        
        # 正しい期間で新しいInvoice Itemを作成
        print(f"\n=== 新しいInvoice Item作成 ===")
        new_invoice_item = stripe.InvoiceItem.create(
            customer=subscription.customer,
            amount=amount,
            currency='jpy',
            description=description,
            subscription=subscription_id,
            period={
                'start': correct_period_start,
                'end': correct_period_end
            }
        )
        print(f"✅ 作成成功: {new_invoice_item.id}")
        print(f"期間: {datetime.fromtimestamp(new_invoice_item.period.start)} - {datetime.fromtimestamp(new_invoice_item.period.end)}")
        
        print(f"\n=== 修正完了 ===")
        print("Invoice Itemの期間を正しく修正しました。")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    fix_invoice_item_period() 