#!/usr/bin/env python3
import os
import stripe
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv('lp/.env')
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def fix_incorrect_invoice_item():
    print("=== 期間がずれているInvoice Item修正 ===")
    
    # サブスクリプションID
    subscription_id = "sub_1RpdcsIxg6C5hAVdneqtbnUG"
    invoice_item_id = "ii_1Rpv0TIxg6C5hAVdvgppxUmE"
    
    try:
        # サブスクリプション情報を取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        customer_id = subscription.customer
        
        print(f"サブスクリプションID: {subscription_id}")
        print(f"顧客ID: {customer_id}")
        
        # 現在のInvoice Itemを取得
        invoice_item = stripe.InvoiceItem.retrieve(invoice_item_id)
        description = invoice_item.description
        amount = invoice_item.amount
        
        print(f"\n現在のInvoice Item:")
        print(f"ID: {invoice_item.id}")
        print(f"説明: {description}")
        print(f"金額: ¥{amount:,}")
        print(f"現在の期間: {datetime.fromtimestamp(invoice_item.period.start)} - {datetime.fromtimestamp(invoice_item.period.end)}")
        
        # 正しい期間を計算
        if subscription.status == 'trialing':
            # トライアル期間中の場合、月額料金の開始期間を使用
            trial_end = subscription.trial_end
            correct_start = trial_end
            
            # 正しい終了日を計算（翌月の同じ日付の2日前）
            start_date = datetime.fromtimestamp(trial_end)
            # 次の月の同じ日付を計算
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1)
            else:
                end_date = start_date.replace(month=start_date.month + 1)
            # 2日前に調整（30日間の期間にする）
            end_date = end_date - timedelta(days=2)
            correct_end = int(end_date.timestamp())
            
            print(f"\n正しい期間（トライアル期間中）: {datetime.fromtimestamp(correct_start)} - {datetime.fromtimestamp(correct_end)}")
        else:
            # 通常の月額期間の場合
            correct_start = subscription.current_period_start
            correct_end = subscription.current_period_end
            print(f"\n正しい期間（通常期間）: {datetime.fromtimestamp(correct_start)} - {datetime.fromtimestamp(correct_end)}")
        
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
    fix_incorrect_invoice_item() 