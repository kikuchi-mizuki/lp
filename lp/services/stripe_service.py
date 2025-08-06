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

def check_subscription_status(stripe_subscription_id):
    """サブスクリプションの状態をチェック"""
    try:
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        status = subscription['status']
        cancel_at_period_end = subscription.get('cancel_at_period_end', False)
        
        print(f'[DEBUG] サブスクリプション状態: status={status}, cancel_at_period_end={cancel_at_period_end}')
        
        # 有効な状態かチェック
        # trialing（試用期間）とactive（有効）の場合は有効とする
        # ただし、cancel_at_period_endがTrueの場合は解約予定なので無効とする
        is_active = status in ['active', 'trialing'] and not cancel_at_period_end
        
        return {
            'is_active': is_active,
            'status': status,
            'cancel_at_period_end': cancel_at_period_end,
            'current_period_end': subscription.get('current_period_end'),
            'subscription': subscription
        }
    except Exception as e:
        print(f'[ERROR] サブスクリプション状態確認エラー: {e}')
        return {
            'is_active': False,
            'status': 'error',
            'error': str(e)
        }

def add_metered_price_to_subscription(subscription_id, price_id=None):
    """サブスクリプションに従量課金Priceを追加"""
    try:
        # デフォルトのPrice IDを使用
        if price_id is None:
            price_id = 'price_1Rog1nIxg6C5hAVdnqB5MJiT'  # 実際のサブスクリプションに含まれているPrice ID
        
        # サブスクリプションを取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # 既に同じPriceが追加されているかチェック
        existing_item = None
        for item in subscription['items']['data']:
            if item['price']['id'] == price_id:
                existing_item = item
                print(f"Price {price_id} は既にサブスクリプション {subscription_id} に追加されています (SubscriptionItem: {item['id']})")
                return {
                    'success': True,
                    'message': f"Price {price_id} は既に追加されています",
                    'subscription_item_id': item['id'],
                    'subscription': subscription
                }
        
        # 従量課金Priceを追加（quantityは設定しない）
        subscription_item = stripe.SubscriptionItem.create(
            subscription=subscription_id,
            price=price_id
        )
        
        print(f"従量課金Price {price_id} をサブスクリプション {subscription_id} に追加しました (SubscriptionItem: {subscription_item['id']})")
        return {
            'success': True,
            'message': f"Price {price_id} を追加しました",
            'subscription_item_id': subscription_item['id'],
            'subscription': subscription
        }
        
    except stripe.error.InvalidRequestError as e:
        if "already using that Price" in str(e):
            print(f"Price {price_id} は既にサブスクリプション {subscription_id} で使用されています")
            return {
                'success': False,
                'error': 'PRICE_ALREADY_EXISTS',
                'message': f"Price {price_id} は既に使用されています"
            }
        else:
            print(f"従量課金Price追加エラー: {e}")
            return {
                'success': False,
                'error': 'STRIPE_ERROR',
                'message': str(e)
            }
    except Exception as e:
        print(f"従量課金Price追加エラー: {e}")
        return {
            'success': False,
            'error': 'UNKNOWN_ERROR',
            'message': str(e)
        }

def ensure_metered_price_in_subscription(subscription_id, price_id=None):
    """サブスクリプションに従量課金Priceが含まれていることを確認し、なければ追加する"""
    try:
        # デフォルトのPrice IDを使用
        if price_id is None:
            price_id = 'price_1Rog1nIxg6C5hAVdnqB5MJiT'  # 実際のサブスクリプションに含まれているPrice ID
        
        # サブスクリプションを取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # 既に同じPriceが追加されているかチェック
        existing_item = None
        for item in subscription['items']['data']:
            if item['price']['id'] == price_id:
                existing_item = item
                print(f"Price {price_id} は既にサブスクリプション {subscription_id} に含まれています (SubscriptionItem: {item['id']})")
                return {
                    'success': True,
                    'message': f"Price {price_id} は既に含まれています",
                    'subscription_item_id': item['id'],
                    'subscription': subscription
                }
        
        # 従量課金Priceを追加（quantityは設定しない）
        subscription_item = stripe.SubscriptionItem.create(
            subscription=subscription_id,
            price=price_id
        )
        
        print(f"従量課金Price {price_id} をサブスクリプション {subscription_id} に追加しました (SubscriptionItem: {subscription_item['id']})")
        
        return {
            'success': True,
            'message': f"Price {price_id} を追加しました",
            'subscription_item_id': subscription_item['id'],
            'subscription': subscription
        }
        
    except stripe.error.InvalidRequestError as e:
        if "already using that Price" in str(e):
            print(f"Price {price_id} は既にサブスクリプション {subscription_id} で使用されています")
            return {
                'success': False,
                'error': 'PRICE_ALREADY_EXISTS',
                'message': f"Price {price_id} は既に使用されています"
            }
        else:
            print(f"従量課金Price確認・追加エラー: {e}")
            return {
                'success': False,
                'error': 'STRIPE_ERROR',
                'message': str(e)
            }
    except Exception as e:
        print(f"従量課金Price確認・追加エラー: {e}")
        return {
            'success': False,
            'error': 'UNKNOWN_ERROR',
            'message': str(e)
        } 