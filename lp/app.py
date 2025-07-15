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
import psycopg2
from urllib.parse import urlparse

load_dotenv()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

MONTHLY_PRICE_ID = os.getenv('STRIPE_MONTHLY_PRICE_ID')
USAGE_PRICE_ID = os.getenv('STRIPE_USAGE_PRICE_ID')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

DATABASE_URL = os.getenv('DATABASE_URL', 'database.db')

def get_db_connection():
    """データベース接続を取得（SQLiteまたはPostgreSQL）"""
    if DATABASE_URL.startswith('postgresql://'):
        # PostgreSQL接続
        return psycopg2.connect(DATABASE_URL)
    else:
        # SQLite接続（開発環境）
        return sqlite3.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # PostgreSQLとSQLiteの違いを吸収
    if DATABASE_URL.startswith('postgresql://'):
        # PostgreSQL用のテーブル作成
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
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
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                usage_quantity INTEGER DEFAULT 1,
                stripe_usage_record_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
    else:
        # SQLite用のテーブル作成
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

app = Flask(__name__, static_folder='static', static_url_path='/static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/thanks')
def thanks():
    return render_template('thanks.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return app.send_static_file(filename)

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
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return 'Invalid signature', 400

    # イベント種別ごとに処理
    if event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        customer_id = invoice['customer']
        
        # subscriptionキーが存在する場合のみ処理
        if 'subscription' in invoice:
            subscription_id = invoice['subscription']
            email = invoice['customer_email'] if 'customer_email' in invoice else None
            # DBに保存（既存ならスキップ）
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT id FROM users WHERE stripe_customer_id = %s', (customer_id,))
            if not c.fetchone():
                c.execute('INSERT INTO users (email, stripe_customer_id, stripe_subscription_id) VALUES (%s, %s, %s)',
                          (email, customer_id, subscription_id))
                conn.commit()
            conn.close()
            print('支払い成功（サブスクリプション）:', invoice['id'])
        else:
            print('支払い成功（サブスクリプション以外）:', invoice['id'])
        # ここでLINE通知やDB更新などを今後追加
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        print('支払い失敗:', invoice['id'])
    # 他のイベントも必要に応じて追加

    return jsonify({'status': 'success'})

@app.route('/line/webhook', methods=['POST'])
def line_webhook():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.data.decode('utf-8')
    # 署名検証
    if LINE_CHANNEL_SECRET:
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
            
            # ユーザー情報を取得
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT id, stripe_subscription_id, line_user_id FROM users WHERE line_user_id = %s', (user_id,))
            user = c.fetchone()
            
            if not user:
                # line_user_id未登録なら最新ユーザーを取得し、紐付け
                c.execute('SELECT id, stripe_subscription_id FROM users WHERE line_user_id IS NULL ORDER BY created_at DESC LIMIT 1')
                user = c.fetchone()
                if user:
                    c.execute('UPDATE users SET line_user_id = %s WHERE id = %s', (user_id, user[0]))
                    conn.commit()
                    # 歓迎メッセージを送信
                    send_line_message(event['replyToken'], get_welcome_message())
                else:
                    # ユーザー未登録
                    send_line_message(event['replyToken'], get_not_registered_message())
                conn.close()
                continue
            
            # 登録済みユーザーの処理
            user_id_db = user[0]
            stripe_subscription_id = user[1]
            
            # コマンド処理
            if text == '追加':
                handle_add_content(event['replyToken'], user_id_db, stripe_subscription_id)
            elif text == 'メニュー':
                send_line_message(event['replyToken'], get_menu_message())
            elif text == 'ヘルプ':
                send_line_message(event['replyToken'], get_help_message())
            elif text == '状態':
                handle_status_check(event['replyToken'], user_id_db)
            else:
                send_line_message(event['replyToken'], get_default_message())
            
            conn.close()
    
    return jsonify({'status': 'ok'})

def send_line_message(reply_token, message):
    """LINEメッセージを送信"""
    headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'replyToken': reply_token,
        'messages': [{'type': 'text', 'text': message}]
    }
    try:
        response = requests.post('https://api.line.me/v2/bot/message/reply', headers=headers, json=data)
        response.raise_for_status()
    except Exception as e:
        print(f'LINEメッセージ送信エラー: {e}')

def get_welcome_message():
    """歓迎メッセージ"""
    return """🎉 AIコレクションズへようこそ！

あなたのAI秘書が準備できました。

📋 利用可能なコマンド：
• 「追加」- コンテンツを追加
• 「メニュー」- メニューを表示
• 「状態」- 利用状況を確認
• 「ヘルプ」- ヘルプを表示

何かご質問がございましたら、お気軽にお声かけください！"""

def get_menu_message():
    """メニューメッセージ"""
    return """📋 AIコレクションズ メニュー

🤖 利用可能なAI秘書：
1. AI予定秘書 - スケジュール管理
2. AI経理秘書 - 見積書・請求書作成
3. AIタスクコンシェルジュ - タスク最適配置

💡 コマンド：
• 「追加」- コンテンツを追加
• 「状態」- 利用状況を確認
• 「ヘルプ」- ヘルプを表示

何かご質問がございましたら、お気軽にお声かけください！"""

def get_help_message():
    """ヘルプメッセージ"""
    return """❓ AIコレクションズ ヘルプ

📝 基本的な使い方：
1. 「追加」と送信してコンテンツを追加
2. 「状態」で利用状況を確認
3. 「メニュー」で利用可能な機能を確認

🔧 サポート：
ご不明な点がございましたら、以下のコマンドをお試しください：
• 「メニュー」- 機能一覧
• 「状態」- 現在の利用状況

お困りの際は、いつでもお声かけください！"""

def get_not_registered_message():
    """未登録ユーザーメッセージ"""
    return """⚠️ ご登録情報が見つかりません

AIコレクションズをご利用いただくには、先にLPからご登録が必要です。

🌐 登録はこちらから：
https://lp-production-xxxx.up.railway.app

ご登録後、再度お声かけください！"""

def get_default_message():
    """デフォルトメッセージ"""
    return """💬 何かお手伝いできることはありますか？

📋 利用可能なコマンド：
• 「追加」- コンテンツを追加
• 「メニュー」- メニューを表示
• 「状態」- 利用状況を確認
• 「ヘルプ」- ヘルプを表示

お気軽にお声かけください！"""

def handle_add_content(reply_token, user_id_db, stripe_subscription_id):
    """コンテンツ追加処理"""
    try:
        # Stripeからsubscription_item_id取得
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        usage_item = None
        for item in subscription['items']['data']:
            if item['price']['id'] == USAGE_PRICE_ID:
                usage_item = item
                break
        
        if not usage_item:
            send_line_message(reply_token, "❌ 従量課金アイテムが見つかりません。サポートにお問い合わせください。")
            return
        
        subscription_item_id = usage_item['id']
        
        # Usage Record作成
        usage_record = stripe.SubscriptionItem.create_usage_record(
            subscription_item_id,
            quantity=1,
            timestamp=int(__import__('time').time()),
            action='increment',
        )
        
        # DBに記録
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('INSERT INTO usage_logs (user_id, usage_quantity, stripe_usage_record_id) VALUES (%s, %s, %s)',
                  (user_id_db, 1, usage_record.id))
        conn.commit()
        conn.close()
        
        # 成功メッセージ
        success_message = """✅ コンテンツ追加を受け付けました！

📊 追加内容：
• AI秘書機能 1件追加

💰 料金：
• 追加料金：1,500円（次回請求時に反映）

何か他にお手伝いできることはありますか？"""
        
        send_line_message(reply_token, success_message)
        
    except Exception as e:
        print(f'コンテンツ追加エラー: {e}')
        send_line_message(reply_token, "❌ エラーが発生しました。しばらく時間をおいて再度お試しください。")

def handle_status_check(reply_token, user_id_db):
    """利用状況確認"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM usage_logs WHERE user_id = %s', (user_id_db,))
        usage_count = c.fetchone()[0]
        conn.close()
        
        status_message = f"""📊 利用状況

📈 今月の追加回数：{usage_count}回
💰 追加料金：{usage_count * 1500}円

💡 ヒント：
• 「追加」でコンテンツを追加
• 「メニュー」で機能一覧を確認"""
        
        send_line_message(reply_token, status_message)
        
    except Exception as e:
        print(f'利用状況確認エラー: {e}')
        send_line_message(reply_token, "❌ 利用状況の取得に失敗しました。しばらく時間をおいて再度お試しください。")

if __name__ == '__main__':
    app.run(debug=True)
