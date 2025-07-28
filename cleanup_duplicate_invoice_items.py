#!/usr/bin/env python3
import os
import stripe
from dotenv import load_dotenv
from datetime import datetime

load_dotenv('lp/.env')
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def cleanup_duplicate_invoice_items():
    print("=== 重複Invoice Item削除 ===")
    
    # サブスクリプションID
    subscription_id = "sub_1RpdcsIxg6C5hAVdneqtbnUG"
    
    try:
        # サブスクリプション情報を取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        customer_id = subscription.customer
        
        print(f"サブスクリプションID: {subscription_id}")
        print(f"顧客ID: {customer_id}")
        
        # Invoice Itemsを取得
        invoice_items = stripe.InvoiceItem.list(
            customer=customer_id,
            limit=100
        )
        
        # 同じ説明のInvoice Itemをグループ化
        items_by_description = {}
        for item in invoice_items.data:
            desc = item.description
            if desc not in items_by_description:
                items_by_description[desc] = []
            items_by_description[desc].append(item)
        
        # 重複を削除（最新のものを残す）
        deleted_count = 0
        for desc, items in items_by_description.items():
            if len(items) > 1:
                print(f"\n重複発見: {desc}")
                print(f"  件数: {len(items)}")
                
                # 作成日時でソート（最新を最後に）
                items.sort(key=lambda x: getattr(x, 'created', 0))
                
                # 最新以外を削除
                for item in items[:-1]:
                    created_time = getattr(item, 'created', 0)
                    print(f"  削除: {item.id} (作成日: {datetime.fromtimestamp(created_time) if created_time else '不明'})")
                    try:
                        item.delete()
                        deleted_count += 1
                        print(f"  ✅ 削除成功")
                    except Exception as e:
                        print(f"  ❌ 削除失敗: {e}")
                
                print(f"  残存: {items[-1].id} (最新)")
        
        if deleted_count == 0:
            print("\n重複したInvoice Itemは見つかりませんでした。")
        else:
            print(f"\n合計 {deleted_count} 件の重複Invoice Itemを削除しました。")
            
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    cleanup_duplicate_invoice_items() 