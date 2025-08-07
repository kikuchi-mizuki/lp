#!/usr/bin/env python3
"""
Stripeの請求書を確定して使用量レコードを反映させるスクリプト
"""

import os
import stripe
from dotenv import load_dotenv

def finalize_stripe_invoice():
    """Stripeの請求書を確定"""
    print("=== Stripe請求書確定 ===")
    
    try:
        # 環境変数を読み込み
        load_dotenv()
        
        # Stripe APIキーを設定
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not stripe.api_key:
            print("❌ STRIPE_SECRET_KEYが設定されていません")
            return
        
        print(f"[DEBUG] Stripe APIキー: {stripe.api_key[:20]}...")
        
        # 請求書ID
        invoice_id = "in_1RtUyCIxg6C5hAVd8tNsrRsE"
        
        print(f"\n=== 請求書情報 ===")
        print(f"請求書ID: {invoice_id}")
        
        # 請求書を取得
        invoice = stripe.Invoice.retrieve(invoice_id)
        print(f"ステータス: {invoice['status']}")
        print(f"金額: {invoice['amount_due']}円")
        
        # 請求書を確定
        print(f"\n=== 請求書確定 ===")
        finalized_invoice = stripe.Invoice.finalize_invoice(invoice_id)
        print(f"✅ 請求書を確定しました: {finalized_invoice['status']}")
        print(f"確定後金額: {finalized_invoice['amount_due']}円")
        
        # 確定後の明細を確認
        print(f"\n=== 確定後の明細 ===")
        for line in finalized_invoice['lines']['data']:
            description = line.get('description', 'N/A')
            quantity = line.get('quantity', 0)
            unit_amount = line.get('unit_amount', 0)
            amount = line.get('amount', 0)
            print(f"  - {description}: {quantity} × {unit_amount}円 = {amount}円")
        
        # 請求書を支払い
        print(f"\n=== 請求書支払い ===")
        paid_invoice = stripe.Invoice.pay(invoice_id)
        print(f"✅ 請求書を支払いしました: {paid_invoice['status']}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    finalize_stripe_invoice()
