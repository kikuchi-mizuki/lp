from flask import Blueprint, request, jsonify
import stripe
import os
from utils.db import get_db_connection

stripe_bp = Blueprint('stripe', __name__)

@stripe_bp.route('/stripe_webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except Exception as e:
        print(f"[Stripe Webhook] 検証エラー: {e}")
        return '', 400
    try:
        # ここにapp.pyからstripe_webhookのロジックを移動予定
        # 例: 支払い成功/失敗、サブスクリプション作成、従量課金処理など
        # invoice.payment_succeeded, customer.subscription.created など
        import unicodedata
        def normalize_email(email):
            if not email:
                return email
            email = email.strip().lower()
            email = unicodedata.normalize('NFKC', email)
            return email
        # ここから下は既存のイベント処理の中で、DB登録時に
        # email = normalize_email(email)
        # としてからDBに保存するようにしてください。
        # 例:
        # email = normalize_email(email)
        # c.execute('INSERT INTO users (email, ...) VALUES (?, ...)', (email, ...))
        event_type = event['type']
        if event_type == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            customer_id = invoice.get('customer')
            subscription_id = invoice.get('subscription')
            email = invoice.get('customer_email')
            email = normalize_email(email)
            if not subscription_id:
                print('subscription_idが存在しません。スキップします。')
                return jsonify({'status': 'skipped'})
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT id FROM users WHERE stripe_customer_id = ?', (customer_id,))
            existing_user = c.fetchone()
            if not existing_user:
                c.execute('SELECT id FROM users WHERE email = ?', (email,))
                existing_user_by_email = c.fetchone()
                if not existing_user_by_email:
                    c.execute('INSERT INTO users (email, stripe_customer_id, stripe_subscription_id) VALUES (?, ?, ?)',
                              (email, customer_id, subscription_id))
                    conn.commit()
                    print(f'ユーザー登録完了: customer_id={customer_id}, subscription_id={subscription_id}')
                    # 従量課金アイテムを追加
                    try:
                        USAGE_PRICE_ID = os.getenv('STRIPE_USAGE_PRICE_ID')
                        result = stripe.SubscriptionItem.create(
                            subscription=subscription_id,
                            price=USAGE_PRICE_ID
                        )
                        print(f'従量課金アイテム追加完了: subscription_id={subscription_id}, usage_price_id={USAGE_PRICE_ID}, result={result}')
                    except Exception as e:
                        import traceback
                        print(f'従量課金アイテム追加エラー: {e}')
                        print(traceback.format_exc())
                else:
                    print(f'既存ユーザーが存在（email重複）: {existing_user_by_email[0]}')
            else:
                print(f'既存ユーザーが存在: {existing_user[0]}')
            conn.close()
        elif event_type == 'customer.subscription.created':
            subscription = event['data']['object']
            customer_id = subscription['customer']
            subscription_id = subscription['id']
            customer = stripe.Customer.retrieve(customer_id)
            email = customer.get('email')
            email = normalize_email(email)
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT id FROM users WHERE stripe_customer_id = ?', (customer_id,))
            existing_user = c.fetchone()
            if not existing_user:
                c.execute('SELECT id FROM users WHERE email = ?', (email,))
                existing_user_by_email = c.fetchone()
                if not existing_user_by_email:
                    c.execute('INSERT INTO users (email, stripe_customer_id, stripe_subscription_id) VALUES (?, ?, ?)',
                              (email, customer_id, subscription_id))
                    conn.commit()
                    print(f'ユーザー登録完了: customer_id={customer_id}, subscription_id={subscription_id}')
                    # 従量課金アイテムを追加
                    try:
                        USAGE_PRICE_ID = os.getenv('STRIPE_USAGE_PRICE_ID')
                        result = stripe.SubscriptionItem.create(
                            subscription=subscription_id,
                            price=USAGE_PRICE_ID
                        )
                        print(f'従量課金アイテム追加完了: subscription_id={subscription_id}, usage_price_id={USAGE_PRICE_ID}, result={result}')
                    except Exception as e:
                        import traceback
                        print(f'従量課金アイテム追加エラー: {e}')
                        print(traceback.format_exc())
                else:
                    print(f'既存ユーザーが存在（email重複）: {existing_user_by_email[0]}')
            else:
                print(f'既存ユーザーが存在: {existing_user[0]}')
            conn.close()
    except Exception as e:
        import traceback
        print(f"[Stripe Webhook] イベント処理エラー: {e}")
        print(traceback.format_exc())
        return '', 500
    return '', 200 