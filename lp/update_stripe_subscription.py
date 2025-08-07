#!/usr/bin/env python3
"""
Stripeの請求項目を実際の利用状況に合わせて更新するスクリプト
"""
import os, sys
from dotenv import load_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
from utils.db import get_db_connection, get_db_type
import stripe

def update_stripe_subscription():
    print("🚀 Stripe請求項目の更新を開始します")
    try:
        # Stripe API設定
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        if not stripe.api_key:
            print("❌ STRIPE_SECRET_KEYが設定されていません")
            print("本番環境で実行してください")
            return
        
        print(f"Stripe API Key: {stripe.api_key[:20]}...")
        
        # データベース接続
        conn = get_db_connection()
        c = conn.cursor()
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        # 月額サブスクリプション情報を取得
        c.execute(f'SELECT stripe_subscription_id FROM company_monthly_subscriptions WHERE company_id = {placeholder}', (5,))
        monthly_sub = c.fetchone()
        if not monthly_sub:
            print("❌ 月額サブスクリプションが見つかりません")
            return
        
        stripe_subscription_id = monthly_sub[0]
        print(f"StripeサブスクリプションID: {stripe_subscription_id}")
        
        # アクティブなLINEアカウントを取得
        c.execute(f'SELECT content_type FROM company_line_accounts WHERE company_id = {placeholder} AND status = {placeholder}', (5, 'active'))
        active_accounts = c.fetchall()
        active_content_types = [account[0] for account in active_accounts]
        
        print(f"アクティブなコンテンツ: {active_content_types}")
        conn.close()
        
        # Stripeサブスクリプションを取得
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        print(f"現在のStripeサブスクリプション: {subscription.id}")
        
        # 現在の請求項目を確認
        print("\n=== 現在のStripe請求項目 ===")
        for item in subscription.items.data:
            print(f"請求項目ID: {item.id}")
            print(f"価格ID: {item.price.id}")
            print(f"数量: {item.quantity}")
            print(f"説明: {item.price.nickname if item.price.nickname else '説明なし'}")
            print("---")
        
        # 追加料金が必要なコンテンツをカウント
        additional_content_count = 0
        for content_type in active_content_types:
            if content_type in ["AIタスクコンシェルジュ", "AI経理秘書"]:
                additional_content_count += 1
        
        print(f"\n追加料金が必要なコンテンツ数: {additional_content_count}")
        
        # Stripeの請求項目を更新
        print("\n=== Stripe請求項目の更新 ===")
        
        # 追加料金の請求項目を更新
        for item in subscription.items.data:
            if "追加" in (item.price.nickname or ""):
                print(f"追加料金の請求項目を更新: {item.id}")
                stripe.SubscriptionItem.modify(
                    item.id,
                    quantity=additional_content_count
                )
                print(f"数量を {additional_content_count} に更新しました")
        
        print("\n✅ Stripe請求項目の更新完了")
        print(f"次回請求から正しい数量（{additional_content_count}）で計算されます")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_stripe_subscription()
