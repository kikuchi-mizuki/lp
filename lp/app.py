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
from routes.line import line_bp
from routes.stripe import stripe_bp
from utils.db import get_db_connection

load_dotenv()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

MONTHLY_PRICE_ID = os.getenv('STRIPE_MONTHLY_PRICE_ID')
USAGE_PRICE_ID = os.getenv('STRIPE_USAGE_PRICE_ID')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

DATABASE_URL = os.getenv('DATABASE_URL', 'database.db')

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
app.register_blueprint(line_bp)
app.register_blueprint(stripe_bp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/wait_for_registration')
def wait_for_registration():
    return render_template('wait_for_registration.html')

@app.route('/check_registration')
def check_registration():
    def normalize_email(email):
        if not email:
            return email
        email = email.strip().lower()
        import unicodedata
        email = unicodedata.normalize('NFKC', email)
        return email
    
    email = request.args.get('email')
    if not email:
        return jsonify({'registered': False, 'error': 'Email parameter is required'})
    email = normalize_email(email)
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, line_user_id FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    
    if user:
        return jsonify({'registered': True, 'line_linked': user[1] is not None})
    else:
        return jsonify({'registered': False})

@app.route('/thanks')
def thanks():
    def normalize_email(email):
        if not email:
            return email
        email = email.strip().lower()
        import unicodedata
        email = unicodedata.normalize('NFKC', email)
        return email
    
    email = request.args.get('email')
    user_id = None
    
    if email:
        email = normalize_email(email)
        # ユーザーIDを取得
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT id FROM users WHERE email = %s ORDER BY created_at DESC LIMIT 1', (email,))
            user = c.fetchone()
            conn.close()
            if user:
                user_id = user[0]
        except Exception as e:
            print(f'[DEBUG] ユーザーID取得エラー: {e}')
    
    return render_template('thanks.html', email=email, user_id=user_id)

@app.route('/static/<path:filename>')
def static_files(filename):
    return app.send_static_file(filename)

@app.route('/line/status')
def line_status():
    """LINE Botの状態確認"""
    try:
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
        }
        response = requests.get('https://api.line.me/v2/bot/profile/U1234567890abcdef', headers=headers)
        if response.status_code == 200:
            return jsonify({'status': 'ok', 'message': 'LINE Bot is working'})
        else:
            return jsonify({'status': 'error', 'message': f'LINE API error: {response.status_code}'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/debug/users')
def debug_users():
    """デバッグ用：ユーザー一覧表示"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT id, email, stripe_customer_id, stripe_subscription_id, line_user_id, created_at FROM users ORDER BY created_at DESC LIMIT 10')
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
        
        return jsonify({'users': user_list})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/debug/subscription/<subscription_id>')
def debug_subscription(subscription_id):
    """デバッグ用：サブスクリプション詳細表示"""
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        return jsonify(subscription)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/debug/update_subscription/<new_subscription_id>')
def update_subscription_id(new_subscription_id):
    """デバッグ用：サブスクリプションID更新"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('UPDATE users SET stripe_subscription_id = ? WHERE id = 1', (new_subscription_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Updated subscription ID to {new_subscription_id}'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/debug/add_user')
def add_user():
    """デバッグ用：テストユーザー追加"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('INSERT INTO users (email, stripe_customer_id, stripe_subscription_id) VALUES (?, ?, ?)',
                  ('test@example.com', 'cus_test123', 'sub_test123'))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Test user added'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/debug/usage_logs')
def debug_usage_logs():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM usage_logs ORDER BY created_at DESC LIMIT 20')
        logs = c.fetchall()
        conn.close()
        return jsonify({'usage_logs': logs})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/subscribe', methods=['POST'])
def subscribe():
    """Stripeサブスクリプション作成"""
    try:
        # フォームデータとJSONの両方に対応
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
        else:
            email = request.form.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # 既存ユーザーの確認
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT id, stripe_customer_id, stripe_subscription_id FROM users WHERE email = %s', (email,))
        existing_user = c.fetchone()
        conn.close()
        
        if existing_user:
            user_id, customer_id, subscription_id = existing_user
            print(f"既存ユーザー発見: user_id={user_id}, customer_id={customer_id}, subscription_id={subscription_id}")
            
            # 既存のサブスクリプションの状態を確認
            try:
                subscription = stripe.Subscription.retrieve(subscription_id)
                if subscription['status'] in ['active', 'trialing']:
                    print(f"既存のサブスクリプションが有効: {subscription_id}")
                    # 既存のサブスクリプションが有効な場合は、そのまま成功ページにリダイレクト
                    return jsonify({
                        'existing_subscription': True,
                        'subscription_id': subscription_id,
                        'redirect_url': url_for('thanks', _external=True) + f"?email={email}"
                    })
                else:
                    print(f"既存のサブスクリプションが無効: {subscription_id}, status={subscription['status']}")
            except Exception as e:
                print(f"既存サブスクリプション確認エラー: {e}")
        
        # 新規ユーザーまたは無効なサブスクリプションの場合、新しいサブスクリプションを作成
        print(f"新しいサブスクリプションを作成: email={email}")
        
        # Stripe Checkout Sessionを作成（月額料金と従量課金Priceの両方を含む）
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
                    # 従量課金Priceにはquantityを指定しない
                }
            ],
            subscription_data={
                'trial_period_days': 7,  # 1週間の無料期間
            },
            success_url=url_for('thanks', _external=True) + f"?email={email}",
            cancel_url=url_for('index', _external=True),
        )
        
        return jsonify({
            'session_id': session.id,
            'url': session.url
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 