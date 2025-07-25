from flask import Blueprint, request, jsonify
import stripe
import os
from utils.db import get_db_connection

stripe_bp = Blueprint('stripe', __name__)

@stripe_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    print(f"[Stripe Webhook] リクエスト受信: {request.method}")
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
        print(f"[Stripe Webhook] イベント受信: {event_type}")
        if event_type == 'checkout.session.completed':
            session = event['data']['object']
            customer_id = session.get('customer')
            subscription_id = session.get('subscription')
            customer_email = session.get('customer_email')
            
            if not subscription_id:
                print('subscription_idが存在しません。スキップします。')
                return jsonify({'status': 'skipped'})
            
            email = normalize_email(customer_email)
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT id FROM users WHERE stripe_customer_id = %s', (customer_id,))
            existing_user = c.fetchone()
            if not existing_user:
                c.execute('SELECT id FROM users WHERE email = %s', (email,))
                existing_user_by_email = c.fetchone()
                if not existing_user_by_email:
                    c.execute('INSERT INTO users (email, stripe_customer_id, stripe_subscription_id) VALUES (%s, %s, %s)', (email, customer_id, subscription_id))
                    conn.commit()
                    print(f'ユーザー登録完了: customer_id={customer_id}, subscription_id={subscription_id}')
                    # 従量課金アイテムを追加
                    try:
                        USAGE_PRICE_ID = os.getenv('STRIPE_USAGE_PRICE_ID')
                        subscription = stripe.Subscription.retrieve(subscription_id)
                        # 従量課金（metered）Price IDのみ追加
                        for item in subscription['items']['data']:
                            if item['price']['id'] == USAGE_PRICE_ID:
                                print(f'従量課金アイテムは既に追加済み: subscription_id={subscription_id}, usage_price_id={USAGE_PRICE_ID}')
                                break
                        else:
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
                    # 既存ユーザーにもsubscription_idをUPDATE
                    c.execute('UPDATE users SET stripe_customer_id = %s, stripe_subscription_id = %s WHERE id = %s', (customer_id, subscription_id, existing_user_by_email[0]))
                    conn.commit()
                    print(f'既存ユーザーのsubscription_idをUPDATE: id={existing_user_by_email[0]}, subscription_id={subscription_id}')
            else:
                print(f'既存ユーザーが存在: {existing_user[0]}')
                # 既存ユーザーにもsubscription_idをUPDATE
                c.execute('UPDATE users SET stripe_customer_id = %s, stripe_subscription_id = %s WHERE id = %s', (customer_id, subscription_id, existing_user[0]))
                conn.commit()
                print(f'既存ユーザーのsubscription_idをUPDATE: id={existing_user[0]}, subscription_id={subscription_id}')
            conn.close()
        elif event_type == 'invoice.payment_succeeded':
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
            c.execute('SELECT id FROM users WHERE stripe_customer_id = %s', (customer_id,))
            existing_user = c.fetchone()
            if not existing_user:
                c.execute('SELECT id FROM users WHERE email = %s', (email,))
                existing_user_by_email = c.fetchone()
                if not existing_user_by_email:
                    c.execute('INSERT INTO users (email, stripe_customer_id, stripe_subscription_id) VALUES (%s, %s, %s)', (email, customer_id, subscription_id))
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
                    # 既存ユーザーにもsubscription_idをUPDATE
                    c.execute('UPDATE users SET stripe_customer_id = %s, stripe_subscription_id = %s WHERE id = %s', (customer_id, subscription_id, existing_user_by_email[0]))
                    conn.commit()
                    print(f'既存ユーザーのsubscription_idをUPDATE: id={existing_user_by_email[0]}, subscription_id={subscription_id}')
            else:
                print(f'既存ユーザーが存在: {existing_user[0]}')
                # 既存ユーザーにもsubscription_idをUPDATE
                c.execute('UPDATE users SET stripe_customer_id = %s, stripe_subscription_id = %s WHERE id = %s', (customer_id, subscription_id, existing_user[0]))
                conn.commit()
                print(f'既存ユーザーのsubscription_idをUPDATE: id={existing_user[0]}, subscription_id={subscription_id}')
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
            c.execute('SELECT id FROM users WHERE stripe_customer_id = %s', (customer_id,))
            existing_user = c.fetchone()
            if not existing_user:
                c.execute('SELECT id FROM users WHERE email = %s', (email,))
                existing_user_by_email = c.fetchone()
                if not existing_user_by_email:
                    c.execute('INSERT INTO users (email, stripe_customer_id, stripe_subscription_id) VALUES (%s, %s, %s)', (email, customer_id, subscription_id))
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
                    # 既存ユーザーにもsubscription_idをUPDATE
                    c.execute('UPDATE users SET stripe_customer_id = %s, stripe_subscription_id = %s WHERE id = %s', (customer_id, subscription_id, existing_user_by_email[0]))
                    conn.commit()
                    print(f'既存ユーザーのsubscription_idをUPDATE: id={existing_user_by_email[0]}, subscription_id={subscription_id}')
            else:
                print(f'既存ユーザーが存在: {existing_user[0]}')
                # 既存ユーザーにもsubscription_idをUPDATE
                c.execute('UPDATE users SET stripe_customer_id = %s, stripe_subscription_id = %s WHERE id = %s', (customer_id, subscription_id, existing_user[0]))
                conn.commit()
                print(f'既存ユーザーのsubscription_idをUPDATE: id={existing_user[0]}, subscription_id={subscription_id}')
            conn.close()
    except Exception as e:
        import traceback
        print(f"[Stripe Webhook] イベント処理エラー: {e}")
        print(traceback.format_exc())
        return '', 500
    return '', 200 