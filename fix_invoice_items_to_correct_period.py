#!/usr/bin/env python3
import os
import stripe
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv('lp/.env')
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def fix_invoice_items_to_correct_period():
    print("=== 全てのInvoice Itemを正しい期間に修正 ===")
    
    # サブスクリプションID
    subscription_id = "sub_1RpdcsIxg6C5hAVdneqtbnUG"
    
    try:
        # サブスクリプション情報を取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        customer_id = subscription.customer
        
        print(f"サブスクリプションID: {subscription_id}")
        print(f"顧客ID: {customer_id}")
        print(f"ステータス: {subscription.status}")
        
        if subscription.status == 'trialing':
            print(f"トライアル終了: {datetime.fromtimestamp(subscription.trial_end)}")
        
        # 正しい期間を計算
        if subscription.status == 'trialing':
            trial_end = subscription.trial_end
            correct_start = trial_end
            
            start_date = datetime.fromtimestamp(trial_end)
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1)
            else:
                end_date = start_date.replace(month=start_date.month + 1)
            end_date = end_date - timedelta(days=1)
            correct_end = int(end_date.timestamp())
            
            print(f"\n正しい期間: {datetime.fromtimestamp(correct_start)} - {datetime.fromtimestamp(correct_end)}")
        
        # 全てのInvoice Itemsを取得
        invoice_items = stripe.InvoiceItem.list(
            customer=customer_id,
            limit=100
        )
        
        fixed_count = 0
        
        for item in invoice_items.data:
            current_start = datetime.fromtimestamp(item.period.start)
            current_end = datetime.fromtimestamp(item.period.end)
            expected_start = datetime.fromtimestamp(correct_start)
            expected_end = datetime.fromtimestamp(correct_end)
            
            print(f"\nInvoice Item: {item.id}")
            print(f"  説明: {item.description}")
            print(f"  現在の期間: {current_start} - {current_end}")
            print(f"  正しい期間: {expected_start} - {expected_end}")
            
            if current_start != expected_start or current_end != expected_end:
                print(f"  ❌ 期間がずれています。修正中...")
                
                # Invoice Itemを削除して再作成
                description = item.description
                amount = item.amount
                
                item.delete()
                print(f"  ✅ 削除完了")
                
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
                
                print(f"  ✅ 作成完了: {new_invoice_item.id}")
                print(f"  ✅ 新しい期間: {datetime.fromtimestamp(new_invoice_item.period.start)} - {datetime.fromtimestamp(new_invoice_item.period.end)}")
                fixed_count += 1
            else:
                print(f"  ✅ 期間は正しい")
        
        print(f"\n修正完了: {fixed_count}件のInvoice Itemを修正しました。")
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    fix_invoice_items_to_correct_period() 