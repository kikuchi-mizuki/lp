#!/usr/bin/env python3
"""
Stripeの請求状況を確認し、間違った請求を修正するスクリプト
"""

import os
import stripe
from datetime import datetime, timedelta

# Stripe APIキーを設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def check_stripe_billing():
    """Stripeの請求状況を確認"""
    try:
        print("=== Stripe請求状況確認 ===")
        
        # 最新の請求書を取得
        invoices = stripe.Invoice.list(limit=5)
        
        for invoice in invoices.data:
            print(f"\n請求書ID: {invoice.id}")
            print(f"請求日: {datetime.fromtimestamp(invoice.created)}")
            print(f"金額: ¥{invoice.amount_total}")
            print(f"状態: {invoice.status}")
            
            if invoice.lines:
                print("請求項目:")
                for line in invoice.lines.data:
                    print(f"  - {line.description}: ¥{line.amount}")
            
            print("-" * 50)
        
        # サブスクリプションの状況を確認
        subscriptions = stripe.Subscription.list(limit=10)
        
        print("\n=== サブスクリプション状況 ===")
        for sub in subscriptions.data:
            print(f"\nサブスクリプションID: {sub.id}")
            print(f"顧客ID: {sub.customer}")
            print(f"状態: {sub.status}")
            print(f"現在の期間終了: {datetime.fromtimestamp(sub.current_period_end)}")
            
            if sub.items:
                print("アイテム:")
                for item in sub.items.data:
                    print(f"  - 価格ID: {item.price.id}")
                    print(f"   数量: {item.quantity}")
                    print(f"   金額: ¥{item.price.unit_amount}")
            
            print("-" * 50)
            
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

def fix_incorrect_billing():
    """間違った請求を修正"""
    try:
        print("\n=== 請求修正 ===")
        
        # 特定のサブスクリプションIDを指定（実際のIDに変更してください）
        subscription_id = input("修正するサブスクリプションIDを入力してください: ")
        
        if not subscription_id:
            print("サブスクリプションIDが入力されていません")
            return
        
        # サブスクリプションを取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        print(f"サブスクリプション: {subscription.id}")
        print(f"状態: {subscription.status}")
        
        # 従量課金アイテムを確認
        usage_items = [item for item in subscription.items.data if item.price.id == os.getenv('STRIPE_USAGE_PRICE_ID')]
        
        if usage_items:
            usage_item = usage_items[0]
            print(f"従量課金アイテム: {usage_item.id}")
            
            # 使用量記録を確認
            usage_records = stripe.UsageRecord.list(
                subscription_item=usage_item.id,
                limit=10
            )
            
            print("使用量記録:")
            for record in usage_records.data:
                print(f"  - ID: {record.id}")
                print(f"    数量: {record.quantity}")
                print(f"    日時: {datetime.fromtimestamp(record.timestamp)}")
                print(f"    アクション: {record.action}")
            
            # 修正オプション
            print("\n修正オプション:")
            print("1. 使用量記録を削除")
            print("2. 使用量記録を修正")
            print("3. キャンセル")
            
            choice = input("選択してください (1-3): ")
            
            if choice == "1":
                # 使用量記録を削除（実際には削除できないので、0に設定）
                for record in usage_records.data:
                    if record.quantity > 0:
                        stripe.UsageRecord.create(
                            subscription_item=usage_item.id,
                            quantity=0,
                            timestamp=record.timestamp,
                            action='set'
                        )
                        print(f"使用量記録を0に設定: {record.id}")
            
            elif choice == "2":
                # 使用量記録を修正
                new_quantity = int(input("新しい数量を入力してください: "))
                for record in usage_records.data:
                    stripe.UsageRecord.create(
                        subscription_item=usage_item.id,
                        quantity=new_quantity,
                        timestamp=record.timestamp,
                        action='set'
                    )
                    print(f"使用量記録を{new_quantity}に設定: {record.id}")
        
        else:
            print("従量課金アイテムが見つかりません")
            
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Stripe請求状況確認・修正ツール")
    print("1. 請求状況を確認")
    print("2. 間違った請求を修正")
    print("3. 終了")
    
    choice = input("選択してください (1-3): ")
    
    if choice == "1":
        check_stripe_billing()
    elif choice == "2":
        fix_incorrect_billing()
    elif choice == "3":
        print("終了します")
    else:
        print("無効な選択です")
