# Stripe関連のサービス層

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