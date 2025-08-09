import os
import logging
import stripe
import hashlib
import hmac
import base64
from flask import request, jsonify
from utils.db import get_db_connection
from app_company_registration import upsert_company_profile_with_subscription

logger = logging.getLogger(__name__)

# Stripe設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

def handle_company_subscription_cancelled(event):
    """企業サブスクリプション解約処理"""
    try:
        subscription_id = event['data']['object']['id']
        customer_email = event['data']['object']['customer_email']
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業のサブスクリプション状態を更新
        c.execute('''
            UPDATE company_monthly_subscriptions 
            SET subscription_status = 'cancelled', updated_at = CURRENT_TIMESTAMP
            WHERE stripe_subscription_id = %s
        ''', (subscription_id,))
        
        # 企業の状態も更新
        c.execute('''
            UPDATE companies 
            SET status = 'cancelled'
            WHERE email = %s
        ''', (customer_email,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ 企業サブスクリプション解約処理完了: {subscription_id}")
        
    except Exception as e:
        logger.error(f"❌ 企業サブスクリプション解約処理エラー: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise e

def handle_company_payment_failed(event):
    """企業支払い失敗処理"""
    try:
        subscription_id = event['data']['object']['id']
        customer_email = event['data']['object']['customer_email']
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業のサブスクリプション状態を更新
        c.execute('''
            UPDATE company_monthly_subscriptions 
            SET subscription_status = 'past_due', updated_at = CURRENT_TIMESTAMP
            WHERE stripe_subscription_id = %s
        ''', (subscription_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ 企業支払い失敗処理完了: {subscription_id}")
        
    except Exception as e:
        logger.error(f"❌ 企業支払い失敗処理エラー: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise e

def handle_company_payment_succeeded(event):
    """企業支払い成功処理"""
    try:
        subscription_id = event['data']['object']['id']
        customer_email = event['data']['object']['customer_email']
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Stripeから現行期間を取得して反映
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            status = subscription.get('status') or 'active'
            start_epoch = subscription.get('current_period_start')
            end_epoch = subscription.get('current_period_end')
            import datetime as _dt
            start_dt = _dt.datetime.utcfromtimestamp(int(start_epoch)) if start_epoch else None
            end_dt = _dt.datetime.utcfromtimestamp(int(end_epoch)) if end_epoch else None
        except Exception:
            status = 'active'
            start_dt = None
            end_dt = None

        # 企業のサブスクリプション状態と期間を更新
        c.execute('''
            UPDATE company_monthly_subscriptions 
            SET subscription_status = %s, current_period_start = %s, current_period_end = %s, updated_at = CURRENT_TIMESTAMP
            WHERE stripe_subscription_id = %s
        ''', (status, start_dt, end_dt, subscription_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ 企業支払い成功処理完了: {subscription_id}")
        
    except Exception as e:
        logger.error(f"❌ 企業支払い成功処理エラー: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise e

def verify_stripe_webhook_signature(payload, signature):
    """Stripe Webhook署名の検証"""
    try:
        # 署名の検証
        expected_signature = hmac.new(
            STRIPE_WEBHOOK_SECRET.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
        
    except Exception as e:
        logger.error(f"❌ Webhook署名検証エラー: {e}")
        return False

def process_stripe_webhook(event):
    """Stripe Webhookイベントの処理"""
    try:
        event_type = event['type']
        
        if event_type == 'checkout.session.completed':
            # チェックアウトセッション完了
            session = event['data']['object']
            metadata = session.get('metadata', {})
            
            company_name = metadata.get('company_name')
            email = metadata.get('email')
            content_type = metadata.get('content_type', 'AI予定秘書')
            subscription_id = session.get('subscription')
            
            if company_name and email and subscription_id:
                # 企業プロファイルを作成・更新
                company_id = upsert_company_profile_with_subscription(
                    company_name, email, subscription_id
                )
                
                logger.info(f"✅ 企業登録完了: {company_id}")
            
        elif event_type == 'customer.subscription.deleted':
            # サブスクリプション解約
            handle_company_subscription_cancelled(event)
            
        elif event_type == 'invoice.payment_failed':
            # 支払い失敗
            handle_company_payment_failed(event)
            
        elif event_type == 'invoice.payment_succeeded':
            # 支払い成功
            handle_company_payment_succeeded(event)
            
        else:
            logger.info(f"ℹ️ 未処理のイベントタイプ: {event_type}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Webhook処理エラー: {e}")
        return False
