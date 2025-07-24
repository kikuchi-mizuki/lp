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
from PIL import Image, ImageDraw, ImageFont
import io
from utils.message_templates import get_default_message, get_menu_message, get_help_message
from services.line_service import send_line_message, create_rich_menu, set_rich_menu_image, set_default_rich_menu, delete_rich_menu
from services.stripe_service import create_subscription, cancel_subscription, add_usage_record
from services.user_service import register_user, get_user_by_line_id, set_user_state, get_user_state
from models.user import User
from models.usage_log import UsageLog

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
                is_free BOOLEAN DEFAULT FALSE,
                content_type VARCHAR(255),
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
                is_free BOOLEAN DEFAULT FALSE,
                content_type VARCHAR(255),
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

@app.route('/line/status')
def line_status():
    """LINE Bot設定状況を確認"""
    status = {
        'line_channel_secret_set': bool(LINE_CHANNEL_SECRET),
        'line_channel_access_token_set': bool(LINE_CHANNEL_ACCESS_TOKEN),
        'stripe_monthly_price_id_set': bool(MONTHLY_PRICE_ID),
        'stripe_usage_price_id_set': bool(USAGE_PRICE_ID),
        'stripe_webhook_secret_set': bool(STRIPE_WEBHOOK_SECRET),
        'database_url_set': bool(DATABASE_URL),
    }
    return jsonify(status)

@app.route('/debug/users')
def debug_users():
    """データベース内のユーザー情報を確認"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT id, email, stripe_customer_id, stripe_subscription_id, line_user_id, created_at FROM users ORDER BY created_at DESC')
        users = c.fetchall()
        conn.close()
        
        user_list = []
        for user in users:
            user_list.append({
                'id': user[0],
                'email': user[1],
                'stripe_customer_id': user[2],
                'stripe_subscription_id': user[3],
                'line_user_id': user[4],
                'created_at': user[5]
            })
        
        return jsonify({
            'total_users': len(user_list),
            'users': user_list
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/debug/subscription/<subscription_id>')
def debug_subscription(subscription_id):
    """サブスクリプションの詳細を確認"""
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        usage_items = []
        
        for item in subscription['items']['data']:
            usage_items.append({
                'id': item['id'],
                'price_id': item['price']['id'],
                'price_nickname': item['price'].get('nickname', 'No nickname'),
                'usage_type': item['price'].get('usage_type', 'Unknown'),
                'billing_scheme': item['price'].get('billing_scheme', 'Unknown')
            })
        
        return jsonify({
            'subscription_id': subscription_id,
            'status': subscription['status'],
            'usage_price_id': USAGE_PRICE_ID,
            'items': usage_items,
            'total_items': len(usage_items)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/debug/update_subscription/<new_subscription_id>')
def update_subscription_id(new_subscription_id):
    """サブスクリプションIDを更新"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 現在のサブスクリプションIDを確認
        c.execute('SELECT stripe_subscription_id FROM users WHERE line_user_id = ?', ('U1b9d0d75b0c770dc1107dde349d572f7',))
        current_subscription = c.fetchone()
        
        if current_subscription:
            old_subscription_id = current_subscription[0]
            print(f"現在のサブスクリプションID: {old_subscription_id}")
            
            # サブスクリプションIDを更新
            c.execute('UPDATE users SET stripe_subscription_id = ? WHERE line_user_id = ?', (new_subscription_id, 'U1b9d0d75b0c770dc1107dde349d572f7'))
            conn.commit()
            
            print(f"サブスクリプションIDを更新: {old_subscription_id} -> {new_subscription_id}")
            
            conn.close()
            
            return jsonify({
                'success': True,
                'old_subscription_id': old_subscription_id,
                'new_subscription_id': new_subscription_id,
                'message': f'サブスクリプションIDを更新しました: {old_subscription_id} -> {new_subscription_id}'
            })
        else:
            conn.close()
            return jsonify({'error': 'ユーザーが見つかりません'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/debug/add_user')
def add_user():
    """手動でユーザーを追加"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # ユーザーを追加
        c.execute('''
            INSERT INTO users (email, stripe_customer_id, stripe_subscription_id, line_user_id) 
            VALUES (?, ?, ?, ?)
        ''', ('mmms.dy.23@gmail.com', 'cus_SgegVyzBF7uIwK', 'sub_1RlGjqIxg6C5hAVdffLdWfUL', 'U1b9d0d75b0c770dc1107dde349d572f7'))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'ユーザーを追加しました',
            'user': {
                'email': 'mmms.dy.23@gmail.com',
                'stripe_customer_id': 'cus_SgegVyzBF7uIwK',
                'stripe_subscription_id': 'sub_1RlGjqIxg6C5hAVdffLdWfUL',
                'line_user_id': 'U1b9d0d75b0c770dc1107dde349d572f7'
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        subscription_data={
            'trial_period_days': 7
        },
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
        print(f'Stripe Webhook受信: invoice.payment_succeeded - {invoice["id"]}')
        print(f'Invoice詳細: {invoice}')
        
        # subscriptionキーが存在する場合のみ処理
        if 'subscription' in invoice:
            subscription_id = invoice['subscription']
            email = invoice['customer_email'] if 'customer_email' in invoice else None
            print(f'サブスクリプション情報: subscription_id={subscription_id}, email={email}')
            
            # DBに保存（既存ならスキップ）
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT id FROM users WHERE stripe_customer_id = ?', (customer_id,))
            existing_user = c.fetchone()
            print(f'既存ユーザー確認: {existing_user}')
            
            if not existing_user:
                c.execute('INSERT INTO users (email, stripe_customer_id, stripe_subscription_id) VALUES (?, ?, ?)',
                          (email, customer_id, subscription_id))
                conn.commit()
                print(f'ユーザー登録完了: customer_id={customer_id}, subscription_id={subscription_id}')
                
                # 従量課金アイテムを追加
                try:
                    stripe.SubscriptionItem.create(
                        subscription=subscription_id,
                        price=USAGE_PRICE_ID
                    )
                    print(f'従量課金アイテム追加完了: subscription_id={subscription_id}')
                except Exception as e:
                    print(f'従量課金アイテム追加エラー: {e}')
            else:
                print(f'既存ユーザーが存在: {existing_user[0]}')
            conn.close()
            print('支払い成功（サブスクリプション）:', invoice['id'])
        else:
            print('支払い成功（サブスクリプション以外）:', invoice['id'])
            print('subscriptionキーが存在しないため、ユーザー登録をスキップ')
        # ここでLINE通知やDB更新などを今後追加
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        print('支払い失敗:', invoice['id'])
    elif event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        customer_id = subscription['customer']
        subscription_id = subscription['id']
        print(f'サブスクリプション作成: {subscription_id}')
        print(f'Subscription詳細: {subscription}')
        
        # 顧客情報を取得
        try:
            customer = stripe.Customer.retrieve(customer_id)
            email = customer.get('email')
            print(f'顧客情報: customer_id={customer_id}, email={email}')
            
            # DBに保存（既存ならスキップ）
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT id FROM users WHERE stripe_customer_id = ?', (customer_id,))
            existing_user = c.fetchone()
            print(f'既存ユーザー確認: {existing_user}')
            
            if not existing_user:
                c.execute('INSERT INTO users (email, stripe_customer_id, stripe_subscription_id) VALUES (?, ?, ?)',
                          (email, customer_id, subscription_id))
                conn.commit()
                print(f'ユーザー登録完了: customer_id={customer_id}, subscription_id={subscription_id}')
                
                # 従量課金アイテムを追加
                try:
                    stripe.SubscriptionItem.create(
                        subscription=subscription_id,
                        price=USAGE_PRICE_ID
                    )
                    print(f'従量課金アイテム追加完了: subscription_id={subscription_id}')
                except Exception as e:
                    print(f'従量課金アイテム追加エラー: {e}')
            else:
                print(f'既存ユーザーが存在: {existing_user[0]}')
            conn.close()
        except Exception as e:
            print(f'サブスクリプション作成処理エラー: {e}')
    # 他のイベントも必要に応じて追加

    return jsonify({'status': 'success'})

# ユーザーごとの状態管理（本番はDBやRedis推奨）
user_states = {}

@app.route('/line/webhook', methods=['POST'])
def line_webhook():
    print("=== LINE Webhook受信 ===")
    print(f"Headers: {dict(request.headers)}")
    
    signature = request.headers.get('X-Line-Signature', '')
    body = request.data.decode('utf-8')
    print(f"Body: {body}")
    
    # 署名検証
    if LINE_CHANNEL_SECRET:
        try:
            hash = hmac.new(LINE_CHANNEL_SECRET.encode('utf-8'), body.encode('utf-8'), hashlib.sha256).digest()
            expected_signature = base64.b64encode(hash).decode('utf-8')
            if not hmac.compare_digest(signature, expected_signature):
                print(f"署名検証失敗: {signature} != {expected_signature}")
                abort(400, 'Invalid signature')
        except Exception as e:
            print(f"署名検証エラー: {e}")
            abort(400, 'Signature verification error')
    else:
        print("LINE_CHANNEL_SECRETが設定されていません")
    
    # イベント処理
    try:
        events = json.loads(body).get('events', [])
        print(f"イベント数: {len(events)}")
        
        for event in events:
            print(f"イベント: {event}")
            
            # テキストメッセージの処理
            if event.get('type') == 'message' and event['message'].get('type') == 'text':
                user_id = event['source']['userId']
                text = event['message']['text']
                print(f"ユーザーID: {user_id}, テキスト: {text}")
                
                # ユーザー情報を取得
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT id, stripe_subscription_id, line_user_id FROM users WHERE line_user_id = ?', (user_id,))
                user = c.fetchone()
                print(f"DB検索結果: {user}")
                
                if not user:
                    # line_user_id未登録なら最新ユーザーを取得し、紐付け
                    c.execute('SELECT id, stripe_subscription_id FROM users WHERE line_user_id IS NULL ORDER BY created_at DESC LIMIT 1')
                    user = c.fetchone()
                    print(f"未紐付けユーザー検索結果: {user}")
                    
                    # 全ユーザー数を確認
                    c.execute('SELECT COUNT(*) FROM users')
                    total_users = c.fetchone()[0]
                    print(f"データベース内の総ユーザー数: {total_users}")
                    
                    if user:
                        c.execute('UPDATE users SET line_user_id = ? WHERE id = ?', (user_id, user[0]))
                        conn.commit()
                        print(f"ユーザー紐付け完了: {user_id} -> {user[0]}")
                        # 歓迎メッセージを送信
                        send_line_message(event['replyToken'], get_welcome_message())
                    else:
                        # ユーザー未登録
                        print("ユーザー未登録")
                        send_line_message(event['replyToken'], get_not_registered_message())
                    conn.close()
                    continue
                
                # 登録済みユーザーの処理
                user_id_db = user[0]
                stripe_subscription_id = user[1]
                print(f"登録済みユーザー処理: user_id={user_id_db}, subscription_id={stripe_subscription_id}")
                
                # コマンド処理
                state = user_states.get(user_id, None)

                if text == '追加':
                    user_states[user_id] = 'add_select'
                    handle_add_content(event['replyToken'], user_id_db, stripe_subscription_id)
                elif text == 'メニュー':
                    send_line_message(event['replyToken'], get_menu_message())
                elif text == 'ヘルプ':
                    send_line_message(event['replyToken'], get_help_message())
                elif text == '状態':
                    handle_status_check(event['replyToken'], user_id_db)
                elif text == '解約':
                    user_states[user_id] = 'cancel_select'
                    handle_cancel_request(event['replyToken'], user_id_db, stripe_subscription_id)
                elif state == 'add_select' and text in ['1', '2', '3', '4']:
                    handle_content_selection(event['replyToken'], user_id_db, stripe_subscription_id, text)
                    user_states[user_id] = None
                elif state == 'cancel_select' and all(x.strip().isdigit() for x in text.split(',')):
                    handle_cancel_selection(event['replyToken'], user_id_db, stripe_subscription_id, text)
                    user_states[user_id] = None
                elif text.lower() in ['はい', 'yes', 'y']:
                    print("コンテンツ追加確認処理（はい）")
                    # 簡易的な実装：最新の選択を記憶するため、一時的に1を選択
                    handle_content_confirmation(event['replyToken'], user_id_db, stripe_subscription_id, '1', True)
                elif text.lower() in ['いいえ', 'no', 'n']:
                    print("コンテンツ追加確認処理（いいえ）")
                    # 簡易的な実装：最新の選択を記憶するため、一時的に1を選択
                    handle_content_confirmation(event['replyToken'], user_id_db, stripe_subscription_id, '1', False)
                else:
                    print(f"デフォルトメッセージ送信: {text}")
                    send_line_message(event['replyToken'], get_default_message())
                
                conn.close()
            
            # リッチメニューのpostbackイベント処理
            elif event.get('type') == 'postback':
                user_id = event['source']['userId']
                postback_data = event['postback']['data']
                print(f"Postback受信: user_id={user_id}, data={postback_data}")
                
                # ユーザー情報を取得
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT id, stripe_subscription_id, line_user_id FROM users WHERE line_user_id = ?', (user_id,))
                user = c.fetchone()
                
                if not user:
                    send_line_message(event['replyToken'], get_not_registered_message())
                    conn.close()
                    continue
                
                user_id_db = user[0]
                stripe_subscription_id = user[1]
                
                try:
                    # postbackデータに基づいて処理
                    if postback_data == 'action=add_content':
                        print("リッチメニュー「追加」ボタン処理")
                        handle_add_content(event['replyToken'], user_id_db, stripe_subscription_id)
                    elif postback_data == 'action=show_menu':
                        print("リッチメニュー「メニュー」ボタン処理")
                        send_line_message(event['replyToken'], get_menu_message())
                    elif postback_data == 'action=check_status':
                        print("リッチメニュー「状態」ボタン処理")
                        handle_status_check(event['replyToken'], user_id_db)
                    else:
                        print(f"不明なpostbackデータ: {postback_data}")
                        send_line_message(event['replyToken'], get_default_message())
                finally:
                    conn.close()
    except Exception as e:
        print(f"LINE Webhook処理エラー: {e}")
        import traceback
        traceback.print_exc()
    
    return jsonify({'status': 'ok'})

@app.route('/admin/rich-menu')
def admin_rich_menu():
    """リッチメニュー管理画面"""
    return render_template('admin_rich_menu.html')

@app.route('/add-usage-item/<subscription_id>')
def add_usage_item_to_subscription(subscription_id):
    """既存のサブスクリプションに従量課金アイテムを追加"""
    try:
        # サブスクリプションを取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # 既に従量課金アイテムがあるかチェック
        existing_usage_item = None
        for item in subscription['items']['data']:
            if item['price']['id'] == USAGE_PRICE_ID:
                existing_usage_item = item
                break
        
        if existing_usage_item:
            return jsonify({
                'success': False,
                'message': f'従量課金アイテムは既に存在します: {existing_usage_item["id"]}'
            })
        
        # 従量課金アイテムを追加
        usage_item = stripe.SubscriptionItem.create(
            subscription=subscription_id,
            price=USAGE_PRICE_ID
        )
        
        return jsonify({
            'success': True,
            'message': f'従量課金アイテムを追加しました: {usage_item["id"]}',
            'usage_item_id': usage_item['id']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'エラー: {str(e)}'
        })

@app.route('/set-default-rich-menu/<rich_menu_id>')
def set_existing_rich_menu_as_default(rich_menu_id):
    """既存のリッチメニューをデフォルトに設定"""
    try:
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f'https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}',
            headers=headers
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': f'リッチメニューをデフォルトに設定しました: {rich_menu_id}'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'設定失敗: {response.status_code} - {response.text}'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'エラー: {str(e)}'
        })

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

def get_not_registered_message():
    """未登録ユーザーメッセージ"""
    return """⚠️ ご登録情報が見つかりません

AIコレクションズをご利用いただくには、先にLPからご登録が必要です。

🌐 登録はこちらから：
https://lp-production-xxxx.up.railway.app

ご登録後、再度お声かけください！"""

def handle_add_content(reply_token, user_id_db, stripe_subscription_id):
    """コンテンツ選択メニュー表示"""
    try:
        # コンテンツ選択メニューを表示
        content_menu = """📚 コンテンツ選択メニュー

利用可能なコンテンツを選択してください：

1️⃣ **AI秘書機能**
   💰 料金：1,500円（1個目は無料）
   📝 内容：24時間対応のAI秘書

2️⃣ **会計管理ツール**
   💰 料金：1,500円（1個目は無料）
   📝 内容：自動会計・経費管理

3️⃣ **スケジュール管理**
   💰 料金：1,500円（1個目は無料）
   📝 内容：AIによる最適スケジュール

4️⃣ **タスク管理**
   💰 料金：1,500円（1個目は無料）
   📝 内容：プロジェクト管理・進捗追跡

選択するには：
• 「1」- AI秘書機能
• 「2」- 会計管理ツール
• 「3」- スケジュール管理
• 「4」- タスク管理

または、番号を直接入力してください。"""
        
        send_line_message(reply_token, content_menu)
        
    except Exception as e:
        print(f'コンテンツ選択メニューエラー: {e}')
        send_line_message(reply_token, "❌ エラーが発生しました。しばらく時間をおいて再度お試しください。")

def handle_content_selection(reply_token, user_id_db, stripe_subscription_id, content_number):
    """コンテンツ選択処理"""
    try:
        # コンテンツ情報
        content_info = {
            '1': {
                'name': 'AI秘書機能',
                'price': 1500,
                'description': '24時間対応のAI秘書',
                'usage': 'LINEで直接メッセージを送るだけで、予定管理、メール作成、リマインダー設定などができます。',
                'url': 'https://lp-production-9e2c.up.railway.app/secretary'
            },
            '2': {
                'name': '会計管理ツール',
                'price': 1500,
                'description': '自動会計・経費管理',
                'usage': 'レシートを撮影するだけで自動で経費を記録し、月次レポートを自動生成します。',
                'url': 'https://lp-production-9e2c.up.railway.app/accounting'
            },
            '3': {
                'name': 'スケジュール管理',
                'price': 1500,
                'description': 'AIによる最適スケジュール',
                'usage': '予定を入力すると、AIが最適なスケジュールを提案し、効率的な時間管理をサポートします。',
                'url': 'https://lp-production-9e2c.up.railway.app/schedule'
            },
            '4': {
                'name': 'タスク管理',
                'price': 1500,
                'description': 'プロジェクト管理・進捗追跡',
                'usage': 'プロジェクトのタスクを管理し、進捗状況を自動で追跡・報告します。',
                'url': 'https://lp-production-9e2c.up.railway.app/task'
            }
        }
        
        if content_number not in content_info:
            send_line_message(reply_token, "❌ 無効な選択です。1-4の数字で選択してください。")
            return
        
        content = content_info[content_number]
        
        # 無料枠チェック
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM usage_logs WHERE user_id = ?', (user_id_db,))
        usage_count = c.fetchone()[0]
        conn.close()
        
        is_free = usage_count == 0
        
        # 料金表示
        if is_free:
            price_message = "🎉 **1個目は無料です！**"
        else:
            price_message = f"💰 料金：{content['price']:,}円"
        
        # 確認メッセージ
        confirm_message = f"""📋 選択内容の確認

📚 コンテンツ：{content['name']}
📝 内容：{content['description']}
{price_message}

このコンテンツを追加しますか？

✅ 追加する場合は「はい」と入力
❌ キャンセルする場合は「いいえ」と入力"""
        
        # 一時的に選択内容を保存（実際の実装ではRedisやDBを使用）
        # ここでは簡易的にメッセージに含める
        send_line_message(reply_token, confirm_message)
        
    except Exception as e:
        print(f'コンテンツ選択エラー: {e}')
        send_line_message(reply_token, "❌ エラーが発生しました。しばらく時間をおいて再度お試しください。")

def handle_content_confirmation(reply_token, user_id_db, stripe_subscription_id, content_number, confirmed):
    """コンテンツ追加確認処理"""
    try:
        if not confirmed:
            send_line_message(reply_token, "❌ キャンセルしました。\n\n何か他にお手伝いできることはありますか？")
            return
        
        # コンテンツ情報
        content_info = {
            '1': {
                'name': 'AI秘書機能',
                'price': 1500,
                'description': '24時間対応のAI秘書',
                'usage': 'LINEで直接メッセージを送るだけで、予定管理、メール作成、リマインダー設定などができます。',
                'url': 'https://lp-production-9e2c.up.railway.app/secretary'
            },
            '2': {
                'name': '会計管理ツール',
                'price': 1500,
                'description': '自動会計・経費管理',
                'usage': 'レシートを撮影するだけで自動で経費を記録し、月次レポートを自動生成します。',
                'url': 'https://lp-production-9e2c.up.railway.app/accounting'
            },
            '3': {
                'name': 'スケジュール管理',
                'price': 1500,
                'description': 'AIによる最適スケジュール',
                'usage': '予定を入力すると、AIが最適なスケジュールを提案し、効率的な時間管理をサポートします。',
                'url': 'https://lp-production-9e2c.up.railway.app/schedule'
            },
            '4': {
                'name': 'タスク管理',
                'price': 1500,
                'description': 'プロジェクト管理・進捗追跡',
                'usage': 'プロジェクトのタスクを管理し、進捗状況を自動で追跡・報告します。',
                'url': 'https://lp-production-9e2c.up.railway.app/task'
            }
        }
        
        content = content_info[content_number]
        
        # 無料枠チェック
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM usage_logs WHERE user_id = ?', (user_id_db,))
        usage_count = c.fetchone()[0]
        conn.close()
        
        is_free = usage_count == 0
        
        # 有料の場合のみStripe処理
        usage_record = None
        if not is_free:
            print(f"コンテンツ追加処理開始: subscription_id={stripe_subscription_id}, usage_price_id={USAGE_PRICE_ID}")
            
            # Stripeからsubscription_item_id取得
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            print(f"サブスクリプション詳細: {subscription}")
            
            usage_item = None
            for item in subscription['items']['data']:
                print(f"アイテム確認: price_id={item['price']['id']}, usage_price_id={USAGE_PRICE_ID}")
                if item['price']['id'] == USAGE_PRICE_ID:
                    usage_item = item
                    print(f"従量課金アイテム発見: {item}")
                    break
            
            if not usage_item:
                print(f"従量課金アイテムが見つかりません: usage_price_id={USAGE_PRICE_ID}")
                print(f"利用可能なアイテム: {[item['price']['id'] for item in subscription['items']['data']]}")
                send_line_message(reply_token, f"❌ 従量課金アイテムが見つかりません。\n\n設定されている価格ID: {USAGE_PRICE_ID}\n\nサポートにお問い合わせください。")
                return
            
            subscription_item_id = usage_item['id']
            print(f"従量課金アイテムID: {subscription_item_id}")
            
            # Usage Record作成（従来API）
            try:
                usage_record = stripe.UsageRecord.create(
                    subscription_item=subscription_item_id,
                    quantity=1,
                    timestamp=int(__import__('time').time()),
                    action='increment',
                )
                print(f"Usage Record作成成功: {usage_record.id}")
            except Exception as usage_error:
                print(f"Usage Record作成エラー: {usage_error}")
                send_line_message(reply_token, f"❌ 使用量記録の作成に失敗しました。\n\nエラー: {str(usage_error)}")
                return
        
        # DBに記録
        try:
            conn = get_db_connection()
            c = conn.cursor()
            if is_free:
                c.execute('INSERT INTO usage_logs (user_id, usage_quantity, stripe_usage_record_id, is_free, content_type) VALUES (?, ?, ?, ?, ?)',
                          (user_id_db, 1, None, True, content['name']))
            else:
                c.execute('INSERT INTO usage_logs (user_id, usage_quantity, stripe_usage_record_id, is_free, content_type) VALUES (?, ?, ?, ?, ?)',
                          (user_id_db, 1, usage_record.id if usage_record else None, False, content['name']))
            conn.commit()
            conn.close()
            print(f"DB記録成功: user_id={user_id_db}, is_free={is_free}, content_type={content['name']}")
        except Exception as db_error:
            print(f"DB記録エラー: {db_error}")
            # DBエラーでも処理は継続
        
        # 成功メッセージ
        if is_free:
            success_message = f"""🎉 コンテンツ追加完了！

📚 追加内容：
• {content['name']} 1件追加

💰 料金：
• 🎉 **無料で追加されました！**

📖 使用方法：
{content['usage']}

🔗 アクセスURL：
{content['url']}

何か他にお手伝いできることはありますか？"""
        else:
            success_message = f"""✅ コンテンツ追加完了！

📚 追加内容：
• {content['name']} 1件追加

💰 料金：
• 追加料金：{content['price']:,}円（次回請求時に反映）

📖 使用方法：
{content['usage']}

🔗 アクセスURL：
{content['url']}

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
        c.execute('SELECT content_type, is_free, created_at FROM usage_logs WHERE user_id = ? ORDER BY created_at DESC', (user_id_db,))
        usage_logs = c.fetchall()
        conn.close()
        
        if not usage_logs:
            status_message = """📊 利用状況

📈 今月の追加回数：0回
💰 追加料金：0円

💡 ヒント：
• 「追加」でコンテンツを追加
• 「メニュー」で機能一覧を確認"""
        else:
            # 料金計算
            total_cost = 0
            content_list = []
            for log in usage_logs:
                content_type = log[0] or "不明"
                is_free = log[1]
                created_at = log[2]
                if not is_free:
                    total_cost += 1500
                content_list.append(f"• {content_type} ({'無料' if is_free else '1,500円'}) - {created_at}")
            
            status_message = f"""📊 利用状況

📈 今月の追加回数：{len(usage_logs)}回
💰 追加料金：{total_cost:,}円

📚 追加済みコンテンツ：
{chr(10).join(content_list[:5])}  # 最新5件まで表示

💡 ヒント：
• 「追加」でコンテンツを追加
• 「メニュー」で機能一覧を確認"""
        
        send_line_message(reply_token, status_message)
        
    except Exception as e:
        print(f'利用状況確認エラー: {e}')
        send_line_message(reply_token, "❌ 利用状況の取得に失敗しました。しばらく時間をおいて再度お試しください。")

def handle_cancel_request(reply_token, user_id_db, stripe_subscription_id):
    """契約中コンテンツ一覧をLINEで送信（日本語名＋金額、無料分は0円表示）"""
    try:
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        items = subscription['items']['data']
        # ユーザーのusage_logsから無料分を特定
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT content_type, is_free FROM usage_logs WHERE user_id = ?', (user_id_db,))
        usage_free_map = {}
        for row in c.fetchall():
            usage_free_map[row[0]] = usage_free_map.get(row[0], False) or row[1]
        conn.close()
        content_choices = []
        for idx, item in enumerate(items, 1):
            price = item['price']
            # 日本語名推測
            name = price.get('nickname') or price.get('id')
            if 'AI秘書' in name or 'secretary' in name or 'prod_SgSj7btk61lSNI' in price.get('product',''):
                jp_name = 'AI秘書機能'
            elif '会計' in name or 'accounting' in name or 'prod_SgSnVeUB5DAihu' in price.get('product',''):
                jp_name = '会計管理ツール'
            elif 'スケジュール' in name or 'schedule' in name:
                jp_name = 'スケジュール管理'
            elif 'タスク' in name or 'task' in name:
                jp_name = 'タスク管理'
            elif price.get('unit_amount',0) >= 500000:
                jp_name = '月額基本料金'
            else:
                jp_name = name
            # 金額計算
            amount = price.get('unit_amount', 0)
            amount_jpy = int(amount) // 100 if amount else 0
            # 無料分判定
            is_free = usage_free_map.get(jp_name, False)
            display_price = '0円' if is_free else f'{amount_jpy:,}円'
            content_choices.append(f"{idx}. {jp_name}（{display_price}/月）")
        if not content_choices:
            send_line_message(reply_token, "現在契約中のコンテンツはありません。")
            return
        choice_message = "\n".join(content_choices)
        send_line_message(reply_token, f"解約したいコンテンツを選んでください（カンマ区切りで複数選択可）:\n{choice_message}\n\n例: 1,2")
    except Exception as e:
        print(f'解約一覧取得エラー: {e}')
        send_line_message(reply_token, "❌ 契約中コンテンツの取得に失敗しました。しばらく時間をおいて再度お試しください。")

def handle_cancel_selection(reply_token, user_id_db, stripe_subscription_id, selection_text):
    """選択されたコンテンツをキャンセル（日本語名で案内）"""
    try:
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        items = subscription['items']['data']
        indices = [int(x.strip())-1 for x in selection_text.split(',') if x.strip().isdigit()]
        cancelled = []
        for idx in indices:
            if 0 <= idx < len(items):
                item = items[idx]
                stripe.SubscriptionItem.delete(item['id'], proration_behavior='none')
                price = item['price']
                name = price.get('nickname') or price.get('id')
                if 'AI秘書' in name or 'secretary' in name or 'prod_SgSj7btk61lSNI' in price.get('product',''):
                    jp_name = 'AI秘書機能'
                elif '会計' in name or 'accounting' in name or 'prod_SgSnVeUB5DAihu' in price.get('product',''):
                    jp_name = '会計管理ツール'
                elif 'スケジュール' in name or 'schedule' in name:
                    jp_name = 'スケジュール管理'
                elif 'タスク' in name or 'task' in name:
                    jp_name = 'タスク管理'
                elif price.get('unit_amount',0) >= 500000:
                    jp_name = '月額基本料金'
                else:
                    jp_name = name
                cancelled.append(jp_name)
        if cancelled:
            send_line_message(reply_token, f"以下のコンテンツの解約を受け付けました（請求期間終了まで利用可能です）：\n" + "\n".join(cancelled))
        else:
            send_line_message(reply_token, "有効な番号が選択されませんでした。もう一度お試しください。")
    except Exception as e:
        print(f'解約処理エラー: {e}')
        send_line_message(reply_token, "❌ 解約処理に失敗しました。しばらく時間をおいて再度お試しください。")

def create_rich_menu():
    """リッチメニューを作成"""
    try:
        rich_menu_to_create = {
            "size": {
                "width": 2500,
                "height": 843
            },
            "selected": False,
            "name": "AIコレクションズ メニュー",
            "chatBarText": "メニュー",
            "areas": [
                {
                    "bounds": {
                        "x": 0,
                        "y": 0,
                        "width": 833,
                        "height": 843
                    },
                    "action": {
                        "type": "postback",
                        "label": "追加",
                        "data": "action=add_content"
                    }
                },
                {
                    "bounds": {
                        "x": 833,
                        "y": 0,
                        "width": 833,
                        "height": 843
                    },
                    "action": {
                        "type": "postback",
                        "label": "メニュー",
                        "data": "action=show_menu"
                    }
                },
                {
                    "bounds": {
                        "x": 1666,
                        "y": 0,
                        "width": 833,
                        "height": 843
                    },
                    "action": {
                        "type": "postback",
                        "label": "状態",
                        "data": "action=check_status"
                    }
                }
            ]
        }
        
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            'https://api.line.me/v2/bot/richmenu',
            headers=headers,
            json=rich_menu_to_create
        )
        
        if response.status_code == 200:
            rich_menu_id = response.json()['richMenuId']
            print(f"リッチメニュー作成成功: {rich_menu_id}")
            return rich_menu_id
        else:
            print(f"リッチメニュー作成失敗: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"リッチメニュー作成エラー: {e}")
        return None

def create_rich_menu_image():
    """リッチメニュー用の画像を生成"""
    try:
        # 2500x843の画像を作成
        width, height = 2500, 843
        image = Image.new('RGB', (width, height), '#FFFFFF')
        draw = ImageDraw.Draw(image)
        
        # フォント設定（デフォルトフォントを使用）
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
            font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        except:
            # フォントが見つからない場合はデフォルト
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
        
        # 3つのエリアを描画
        areas = [
            {"x": 0, "width": 833, "text": "追加", "color": "#4F46E5"},
            {"x": 833, "width": 833, "text": "メニュー", "color": "#7C3AED"},
            {"x": 1666, "width": 833, "text": "状態", "color": "#10B981"}
        ]
        
        for area in areas:
            # 背景色
            draw.rectangle([area["x"], 0, area["x"] + area["width"], height], fill=area["color"])
            
            # テキスト
            text = area["text"]
            bbox = draw.textbbox((0, 0), text, font=font_large)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = area["x"] + (area["width"] - text_width) // 2
            y = (height - text_height) // 2
            
            draw.text((x, y), text, fill='white', font=font_large)
        
        # 画像をバイトデータに変換
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        return img_byte_arr
        
    except Exception as e:
        print(f"リッチメニュー画像生成エラー: {e}")
        return None

def set_rich_menu_image(rich_menu_id):
    """リッチメニューに画像を設定"""
    try:
        # リッチメニュー画像を生成
        image_data = create_rich_menu_image()
        if not image_data:
            print("リッチメニュー画像生成に失敗しました")
            return False
        
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
            'Content-Type': 'image/png'
        }
        
        response = requests.post(
            f'https://api.line.me/v2/bot/richmenu/{rich_menu_id}/content',
            headers=headers,
            data=image_data
        )
        
        if response.status_code == 200:
            print(f"リッチメニュー画像設定成功: {rich_menu_id}")
            return True
        else:
            print(f"リッチメニュー画像設定失敗: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"リッチメニュー画像設定エラー: {e}")
        return False

def set_default_rich_menu(rich_menu_id):
    """デフォルトリッチメニューを設定"""
    try:
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f'https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}',
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"デフォルトリッチメニュー設定成功: {rich_menu_id}")
            return True
        else:
            print(f"デフォルトリッチメニュー設定失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"デフォルトリッチメニュー設定エラー: {e}")
        return False

def delete_rich_menu(rich_menu_id):
    """リッチメニューを削除"""
    try:
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
        }
        
        response = requests.delete(
            f'https://api.line.me/v2/bot/richmenu/{rich_menu_id}',
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"リッチメニュー削除成功: {rich_menu_id}")
            return True
        else:
            print(f"リッチメニュー削除失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"リッチメニュー削除エラー: {e}")
        return False

@app.route('/setup-rich-menu')
def setup_rich_menu():
    """リッチメニュー設定エンドポイント"""
    try:
        # 既存のリッチメニューを削除
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
        }
        response = requests.get('https://api.line.me/v2/bot/richmenu/list', headers=headers)
        if response.status_code == 200:
            rich_menus = response.json()['richmenus']
            for menu in rich_menus:
                delete_rich_menu(menu['richMenuId'])
        
        # 新しいリッチメニューを作成
        rich_menu_id = create_rich_menu()
        if rich_menu_id:
            # リッチメニューに画像を設定
            if set_rich_menu_image(rich_menu_id):
                # デフォルトリッチメニューに設定
                if set_default_rich_menu(rich_menu_id):
                    return jsonify({
                        'success': True,
                        'message': f'リッチメニュー設定完了: {rich_menu_id}',
                        'rich_menu_id': rich_menu_id
                    })
        
        return jsonify({
            'success': False,
            'message': 'リッチメニュー設定に失敗しました'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'エラー: {str(e)}'
        })

@app.route('/debug-rich-menu')
def debug_rich_menu():
    """リッチメニュー設定のデバッグ情報を表示"""
    try:
        # LINE Bot設定状況を確認
        line_status = {
            'line_channel_access_token_set': bool(LINE_CHANNEL_ACCESS_TOKEN),
            'line_channel_secret_set': bool(LINE_CHANNEL_SECRET),
        }
        
        # 既存のリッチメニューを取得
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
        }
        
        response = requests.get('https://api.line.me/v2/bot/richmenu/list', headers=headers)
        existing_menus = []
        if response.status_code == 200:
            existing_menus = response.json()['richmenus']
        else:
            existing_menus = [f"Error: {response.status_code} - {response.text}"]
        
        return jsonify({
            'line_status': line_status,
            'existing_rich_menus': existing_menus,
            'response_status': response.status_code,
            'response_text': response.text if response.status_code != 200 else "Success"
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'line_status': {
                'line_channel_access_token_set': bool(LINE_CHANNEL_ACCESS_TOKEN),
                'line_channel_secret_set': bool(LINE_CHANNEL_SECRET),
            }
        })

if __name__ == '__main__':
    app.run(debug=True)
