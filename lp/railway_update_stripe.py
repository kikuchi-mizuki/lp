#!/usr/bin/env python3
"""
Railway本番環境でStripe請求項目を更新するスクリプト
"""
import os
import sys
import stripe
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

def update_stripe_billing():
    print("🚀 Railway本番環境でStripe請求項目を更新します")
    
    try:
        # Stripe API設定
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        if not stripe.api_key:
            print("❌ STRIPE_SECRET_KEYが設定されていません")
            return
        
        print(f"Stripe API Key: {stripe.api_key[:20]}...")
        
        # 企業ID=5のサブスクリプションID
        stripe_subscription_id = "sub_1RtQTlIxg6C5hAVdgbiUs3Lh"
        print(f"対象サブスクリプション: {stripe_subscription_id}")
        
        # Stripeサブスクリプションを取得
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        print(f"サブスクリプションステータス: {subscription.status}")
        
        # 現在の請求項目を確認
        print("\n=== 現在のStripe請求項目 ===")
        for item in subscription.items.data:
            print(f"請求項目ID: {item.id}")
            print(f"価格ID: {item.price.id}")
            print(f"数量: {item.quantity}")
            print(f"説明: {item.price.nickname if item.price.nickname else '説明なし'}")
            print("---")
        
        # 実際の利用状況に基づいて数量を0に設定
        print("\n=== Stripe請求項目を更新 ===")
        
        for item in subscription.items.data:
            if "追加" in (item.price.nickname or ""):
                print(f"追加料金の請求項目を更新: {item.id}")
                stripe.SubscriptionItem.modify(
                    item.id,
                    quantity=0  # 実際の利用状況に基づいて0に設定
                )
                print(f"数量を0に更新しました")
                break
        
        print("\n✅ Stripe請求項目の更新完了")
        print("次回請求から正しい数量で計算されます")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_stripe_billing()
