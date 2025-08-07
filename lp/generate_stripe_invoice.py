#!/usr/bin/env python3
"""
Stripeの請求書を手動で生成するスクリプト
"""

import os
import stripe
from dotenv import load_dotenv

def generate_stripe_invoice():
    """Stripeの請求書を手動で生成"""
    print("=== Stripe請求書生成 ===")
    
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
        print(f"ステータス: {subscription['status']}")
        print(f"現在期間開始: {subscription['current_period_start']}")
        print(f"現在期間終了: {subscription['current_period_end']}")
        
        # 新しい請求書を生成
        print(f"\n=== 新しい請求書生成 ===")
        invoice = stripe.Invoice.create(
            customer=subscription['customer'],
            subscription=subscription_id,
            auto_advance=False  # 自動送信しない
        )
        
        print(f"✅ 新しい請求書を作成しました: {invoice['id']}")
        print(f"ステータス: {invoice['status']}")
        print(f"金額: {invoice['amount_due']}円")
        print(f"期間開始: {invoice['period_start']}")
        print(f"期間終了: {invoice['period_end']}")
        
        # 請求書の明細を確認
        print(f"\n=== 請求書明細 ===")
        for line in invoice['lines']['data']:
            description = line.get('description', 'N/A')
            quantity = line.get('quantity', 0)
            unit_amount = line.get('unit_amount', 0)
            amount = line.get('amount', 0)
            print(f"  - {description}: {quantity} × {unit_amount}円 = {amount}円")
        
        # 請求書を送信
        print(f"\n=== 請求書送信 ===")
        sent_invoice = stripe.Invoice.send_invoice(invoice['id'])
        print(f"✅ 請求書を送信しました: {sent_invoice['status']}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_stripe_invoice()
