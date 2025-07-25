# Stripe関連のサービス層

import stripe
import os

def create_subscription(customer_id, price_ids, trial_days=0):
    """サブスクリプション作成（実装はapp.pyから移動予定）"""
    pass

def cancel_subscription(subscription_id):
    """サブスクリプション解約（実装はapp.pyから移動予定）"""
    pass

def add_usage_record(subscription_item_id, quantity):
    """UsageRecord追加（実装はapp.pyから移動予定）"""
    pass

def grant_referral_free_content(user_id):
    """紹介特典の無料枠付与（今後拡張用）"""
    pass

def add_metered_price_to_subscription(subscription_id, metered_price_id):
    """
    指定したサブスクリプションIDに従量課金Priceを追加する。
    すでに追加済みの場合は何もしない。
    """
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    try:
        # すでに追加済みかチェック
        subscription = stripe.Subscription.retrieve(subscription_id)
        for item in subscription['items']['data']:
            if item['price']['id'] == metered_price_id:
                print(f"従量課金Priceは既に追加済み: {metered_price_id}")
                return True
        # 追加（quantityは指定しない）
        result = stripe.SubscriptionItem.create(
            subscription=subscription_id,
            price=metered_price_id
        )
        print(f"従量課金Price追加完了: {result}")
        return True
    except Exception as e:
        print(f"従量課金Price追加エラー: {e}")
        return False 