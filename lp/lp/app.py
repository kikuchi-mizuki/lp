from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
import os
import stripe
from dotenv import load_dotenv
import hashlib
import hmac
import base64
import json
import requests
import sqlite3

load_dotenv()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

MONTHLY_PRICE_ID = os.getenv('STRIPE_MONTHLY_PRICE_ID')
USAGE_PRICE_ID = os.getenv('STRIPE_USAGE_PRICE_ID')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

DB_PATH = os.getenv('DATABASE_URL', 'database.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(255) UNIQUE NOT NULL,
            stripe_customer_id VARCHAR(255) UNIQUE NOT NULL,
            stripe_subscription_id VARCHAR(255) UNIQUE NOT NULL,
            line_user_id VARCHAR(255) UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            usage_quantity INTEGER DEFAULT 1,
            stripe_usage_record_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/thanks')
def thanks():
    return render_template('thanks.html')

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    if not email:
        return redirect(url_for('index'))

    # Stripe Checkoutセッション作成
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='subscription',
        customer_email=email,
        line_items=[
            {
                'price': MONTHLY_PRICE_ID,
                'quantity': 1,
            },
            {
                'price': USAGE_PRICE_ID,
                'quantity': 0,  # 従量課金は初期数量0で追加
            },
        ],
        success_url=url_for('thanks', _external=True),
        cancel_url=url_for('index', _external=True),
    )
    return redirect(session.url, code=303)

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400

    if event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        customer_id = invoice.get('customer')
        subscription_id = invoice.get('subscription')
        email = invoice.get('customer_email')
        if not subscription_id:
            print('subscription_idが存在しません。スキップします。')
            return jsonify({'status': 'skipped'})
        # DBに保存（既存ならスキップ）
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE stripe_customer_id = ?', (customer_id,))
        if not c.fetchone():
            c.execute('INSERT INTO users (email, stripe_customer_id, stripe_subscription_id) VALUES (?, ?, ?)',
                      (email, customer_id, subscription_id))
            conn.commit()
        conn.close()
        print('支払い成功:', invoice.get('id'))
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        print('支払い失敗:', invoice.get('id'))
    return jsonify({'status': 'success'})

@app.route('/line/webhook', methods=['POST'])
def line_webhook():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.data.decode('utf-8')
    # 署名検証
    hash = hmac.new(LINE_CHANNEL_SECRET.encode('utf-8'), body.encode('utf-8'), hashlib.sha256).digest()
    expected_signature = base64.b64encode(hash).decode('utf-8')
    if not hmac.compare_digest(signature, expected_signature):
        abort(400, 'Invalid signature')
    # イベント処理
    events = json.loads(body).get('events', [])
    for event in events:
        if event.get('type') == 'message' and event['message'].get('type') == 'text':
            user_id = event['source']['userId']
            text = event['message']['text']
            if text == '追加':
                print(f'ユーザー {user_id} から「追加」メッセージ受信')
                # DBからユーザー情報取得
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('SELECT id, stripe_subscription_id, line_user_id FROM users WHERE line_user_id = ?', (user_id,))
                user = c.fetchone()
                if not user:
                    # line_user_id未登録ならstripe_customer_idで最新ユーザーを取得し、紐付け
                    c.execute('SELECT id, stripe_subscription_id FROM users WHERE line_user_id IS NULL ORDER BY created_at DESC LIMIT 1')
                    user = c.fetchone()
                    if user:
                        c.execute('UPDATE users SET line_user_id = ? WHERE id = ?', (user_id, user[0]))
                        conn.commit()
                    else:
                        conn.close()
                        # ユーザー未登録
                        reply_token = event['replyToken']
                        headers = {
                            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
                            'Content-Type': 'application/json'
                        }
                        data = {
                            'replyToken': reply_token,
                            'messages': [
                                {'type': 'text', 'text': 'ご登録情報が見つかりません。先にLPからご登録ください。'}
                            ]
                        }
                        requests.post('https://api.line.me/v2/bot/message/reply', headers=headers, json=data)
                        return jsonify({'status': 'ok'})
                user_id_db = user[0]
                stripe_subscription_id = user[1]
                # Stripeからsubscription_item_id取得
                subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                # 最初のitemを従量課金と仮定
                usage_item = None
                for item in subscription['items']['data']:
                    if item['price']['id'] == USAGE_PRICE_ID:
                        usage_item = item
                        break
                if not usage_item:
                    conn.close()
                    print('従量課金アイテムが見つかりません')
                    return jsonify({'status': 'ok'})
                subscription_item_id = usage_item['id']
                try:
                    usage_record = stripe.SubscriptionItem.create_usage_record(
                        subscription_item_id,
                        quantity=1,
                        timestamp=int(__import__('time').time()),
                        action='increment',
                    )
                    # usage_logsに記録
                    c.execute('INSERT INTO usage_logs (user_id, usage_quantity, stripe_usage_record_id) VALUES (?, ?, ?)',
                              (user_id_db, 1, usage_record.id))
                    conn.commit()
                    # LINEに返信
                    reply_token = event['replyToken']
                    headers = {
                        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
                        'Content-Type': 'application/json'
                    }
                    data = {
                        'replyToken': reply_token,
                        'messages': [
                            {'type': 'text', 'text': 'コンテンツ追加を受け付けました！'}
                        ]
                    }
                    requests.post('https://api.line.me/v2/bot/message/reply', headers=headers, json=data)
                except Exception as e:
                    print('Usage Record作成エラー:', e)
                conn.close()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True) 