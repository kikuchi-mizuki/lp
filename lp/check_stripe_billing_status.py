#!/usr/bin/env python3
"""
Stripeの請求状況を確認するスクリプト
"""

import os
import stripe
from dotenv import load_dotenv

def check_stripe_billing_status():
    """Stripeの請求状況を確認"""
    print("=== Stripe請求状況確認 ===")
    
    try:
        # 環境変数を読み込み
        load_dotenv()
        
        # Stripe APIキーを設定
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not stripe.api_key:
            print("❌ STRIPE_SECRET_KEYが設定されていません")
            return
        
        print(f"[DEBUG] Stripe APIキー: {stripe.api_key[:20]}...")
        
        # サブスクリプションID
        subscription_id = "sub_1RtQTlIxg6C5hAVdgbiUs3Lh"
        
        print(f"\n=== サブスクリプション情報 ===")
        print(f"サブスクリプションID: {subscription_id}")
        
        # サブスクリプションを取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        print(f"ステータス: {subscription.status}")
        print(f"現在期間開始: {subscription.current_period_start}")
        print(f"現在期間終了: {subscription.current_period_end}")
        print(f"請求間隔: {subscription.billing_cycle_anchor}")
        
        # サブスクリプションアイテムを確認
        print(f"\n=== サブスクリプションアイテム ===")
        for item in subscription['items']['data']:
            print(f"アイテムID: {item['id']}")
            print(f"価格ID: {item['price']['id']}")
            if 'quantity' in item:
                print(f"数量: {item['quantity']}")
            else:
                print(f"数量: metered（使用量ベース）")
            print(f"使用量タイプ: {item['price']['recurring']['usage_type']}")
            print(f"単価: {item['price']['unit_amount']}円")
            print("-" * 50)
        
        # 使用量レコードを確認
        print(f"\n=== 使用量レコード ===")
        for item in subscription['items']['data']:
            if item['price']['recurring']['usage_type'] == 'metered':
                try:
                    usage_records = stripe.UsageRecord.list(
                        subscription_item=item['id'],
                        limit=10
                    )
                    print(f"アイテム {item['id']} の使用量:")
                    for usage in usage_records['data']:
                        print(f"  期間: {usage['timestamp']}")
                        print(f"  使用量: {usage['quantity']}")
                        print(f"  アクション: {usage['action']}")
                        print(f"  説明: {usage.get('description', 'N/A')}")
                        print("  ---")
                except Exception as e:
                    print(f"  使用量レコード取得エラー: {e}")
        
        # 最新の請求書を確認
        print(f"\n=== 最新の請求書 ===")
        invoices = stripe.Invoice.list(
            subscription=subscription_id,
            limit=5
        )
        
        for invoice in invoices.data:
            print(f"\n請求書ID: {invoice.id}")
            print(f"ステータス: {invoice.status}")
            print(f"金額: {invoice.amount_paid}円")
            print(f"期間開始: {invoice.period_start}")
            print(f"期間終了: {invoice.period_end}")
            print(f"請求日: {invoice.created}")
            print("明細:")
            for line in invoice['lines']['data']:
                description = line.get('description', 'N/A')
                quantity = line.get('quantity', 0)
                unit_amount = line.get('unit_amount', 0)
                amount = line.get('amount', 0)
                print(f"  - {description}: {quantity} × {unit_amount}円 = {amount}円")
            print("-" * 50)
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_stripe_billing_status()
