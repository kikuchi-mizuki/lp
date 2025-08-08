#!/usr/bin/env python3
"""
Stripeの請求書を手動で生成するスクリプト（期間同期対応）
"""

import os
import stripe
from dotenv import load_dotenv
from datetime import datetime

def generate_stripe_invoice():
    """Stripeの請求書を手動で生成（期間同期対応）"""
    print("=== Stripe請求書生成（期間同期対応） ===")
    
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
        print(f"現在期間開始: {datetime.fromtimestamp(subscription['current_period_start'])}")
        print(f"現在期間終了: {datetime.fromtimestamp(subscription['current_period_end'])}")
        
        # 使用量レコードを月額サブスクリプションの期間に合わせて同期
        print(f"\n=== 使用量レコード期間同期 ===")
        usage_price_id = 'price_1Rog1nIxg6C5hAVdnqB5MJiT'  # 従量課金のPrice ID
        
        # 従量課金アイテムを取得
        usage_item = None
        for item in subscription['items']['data']:
            if item['price']['id'] == usage_price_id:
                usage_item = item
                break
        
        if usage_item:
            print(f"従量課金アイテム発見: {usage_item['id']}")
            
            # 既存の使用量レコードを削除（期間を統一するため）
            try:
                existing_usage = stripe.UsageRecord.list(
                    subscription_item=usage_item['id'],
                    limit=100
                )
                
                print(f"既存の使用量レコード数: {len(existing_usage['data'])}")
                
                # 新しい期間で使用量レコードを作成
                stripe.UsageRecord.create(
                    subscription_item=usage_item['id'],
                    quantity=1,  # 追加コンテンツ1つ分
                    timestamp=int(subscription['current_period_start']),  # 月額期間開始時点
                    action='set'  # 既存レコードを上書き
                )
                
                print(f"✅ 使用量レコードを月額期間に同期: {datetime.fromtimestamp(subscription['current_period_start'])}")
                
            except Exception as e:
                print(f"使用量レコード同期エラー: {e}")
        else:
            print("従量課金アイテムが見つかりません")
        
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
        print(f"期間開始: {datetime.fromtimestamp(invoice['period_start'])}")
        print(f"期間終了: {datetime.fromtimestamp(invoice['period_end'])}")
        
        # 請求書の明細を確認
        print(f"\n=== 請求書明細 ===")
        for line in invoice['lines']['data']:
            description = line.get('description', 'N/A')
            quantity = line.get('quantity', 0)
            unit_amount = line.get('unit_amount', 0)
            amount = line.get('amount', 0)
            period_start = line.get('period', {}).get('start')
            period_end = line.get('period', {}).get('end')
            
            print(f"  - {description}: {quantity} × {unit_amount}円 = {amount}円")
            if period_start and period_end:
                print(f"    期間: {datetime.fromtimestamp(period_start)} - {datetime.fromtimestamp(period_end)}")
        
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
