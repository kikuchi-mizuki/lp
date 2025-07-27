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

def add_metered_price_to_subscription(subscription_id, price_id):
    """サブスクリプションに従量課金Priceを追加"""
    try:
        # サブスクリプションを取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # 既に同じPriceが追加されているかチェック
        for item in subscription['items']['data']:
            if item['price']['id'] == price_id:
                print(f"Price {price_id} は既にサブスクリプション {subscription_id} に追加されています")
                return subscription
        
        # 従量課金Priceを追加
        subscription_item = stripe.SubscriptionItem.create(
            subscription=subscription_id,
            price=price_id
        )
        
        print(f"従量課金Price {price_id} をサブスクリプション {subscription_id} に追加しました")
        return subscription
        
    except Exception as e:
        print(f"従量課金Price追加エラー: {e}")
        raise e

def ensure_metered_price_in_subscription(subscription_id, price_id):
    """サブスクリプションに従量課金Priceが含まれていることを確認し、なければ追加する"""
    try:
        # サブスクリプションを取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # 既に同じPriceが追加されているかチェック
        for item in subscription['items']['data']:
            if item['price']['id'] == price_id:
                print(f"Price {price_id} は既にサブスクリプション {subscription_id} に含まれています")
                return subscription
        
        # 従量課金Priceを追加
        subscription_item = stripe.SubscriptionItem.create(
            subscription=subscription_id,
            price=price_id
        )
        
        print(f"従量課金Price {price_id} をサブスクリプション {subscription_id} に追加しました")
        
        # 更新されたサブスクリプションを返す
        return stripe.Subscription.retrieve(subscription_id)
        
    except Exception as e:
        print(f"従量課金Price確認・追加エラー: {e}")
        raise e 