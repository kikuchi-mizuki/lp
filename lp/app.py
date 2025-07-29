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
import time

load_dotenv()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

MONTHLY_PRICE_ID = os.getenv('STRIPE_MONTHLY_PRICE_ID')
USAGE_PRICE_ID = os.getenv('STRIPE_USAGE_PRICE_ID')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

DATABASE_URL = os.getenv('DATABASE_URL', 'database.db')

def init_db():
    """データベースの初期化"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # データベースタイプを確認
    from utils.db import get_db_type
    db_type = get_db_type()
    
    if db_type == 'postgresql':
        # PostgreSQL用のテーブル作成
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                stripe_customer_id VARCHAR(255),
                stripe_subscription_id VARCHAR(255),
                line_user_id VARCHAR(255) UNIQUE
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS usage_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                content_type VARCHAR(100) NOT NULL,
                is_free BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                subscription_status VARCHAR(50),
                current_period_start TIMESTAMP,
                current_period_end TIMESTAMP,
                trial_start TIMESTAMP,
                trial_end TIMESTAMP,
                stripe_subscription_id VARCHAR(255),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS cancellation_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                content_type VARCHAR(100) NOT NULL,
                cancelled_at TIMESTAMP NOT NULL,
                subscription_status VARCHAR(50),
                current_period_start TIMESTAMP,
                current_period_end TIMESTAMP,
                trial_start TIMESTAMP,
                trial_end TIMESTAMP,
                stripe_subscription_id VARCHAR(255),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 契約期間管理テーブルを追加
        c.execute('''
            CREATE TABLE IF NOT EXISTS subscription_periods (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                stripe_subscription_id VARCHAR(255) NOT NULL,
                subscription_status VARCHAR(50) NOT NULL,
                current_period_start TIMESTAMP,
                current_period_end TIMESTAMP,
                trial_start TIMESTAMP,
                trial_end TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(stripe_subscription_id)
            )
        ''')
        
    else:
        # SQLite用のテーブル作成
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                line_user_id TEXT UNIQUE
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content_type TEXT NOT NULL,
                is_free BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                subscription_status TEXT,
                current_period_start TIMESTAMP,
                current_period_end TIMESTAMP,
                trial_start TIMESTAMP,
                trial_end TIMESTAMP,
                stripe_subscription_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS cancellation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content_type TEXT NOT NULL,
                cancelled_at TIMESTAMP NOT NULL,
                subscription_status TEXT,
                current_period_start TIMESTAMP,
                current_period_end TIMESTAMP,
                trial_start TIMESTAMP,
                trial_end TIMESTAMP,
                stripe_subscription_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 契約期間管理テーブルを追加
        c.execute('''
            CREATE TABLE IF NOT EXISTS subscription_periods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                stripe_subscription_id TEXT NOT NULL,
                subscription_status TEXT NOT NULL,
                current_period_start TIMESTAMP,
                current_period_end TIMESTAMP,
                trial_start TIMESTAMP,
                trial_end TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(stripe_subscription_id)
            )
        ''')
    
    conn.commit()
    conn.close()
    
    # ユーザー状態テーブルの初期化
    from models.user_state import init_user_states_table
    init_user_states_table()

init_db()

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.register_blueprint(line_bp)
app.register_blueprint(stripe_bp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/error_log')
def error_log():
    """エラーログを表示するエンドポイント"""
    try:
        with open('error.log', 'r', encoding='utf-8') as f:
            log_content = f.read()
        return log_content
    except FileNotFoundError:
        return "エラーログファイルが見つかりません"
    except Exception as e:
        return f"エラーログ読み込みエラー: {e}"

@app.route('/health')
def health_check():
    """アプリケーションの起動確認用エンドポイント"""
    return jsonify({
        'status': 'ok',
        'message': 'Application is running',
        'timestamp': '2025-07-29 08:30:00'
    })

@app.route('/debug/db')
def debug_database():
    """データベース接続確認用エンドポイント"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプを確認
        from utils.db import get_db_type
        db_type = get_db_type()
        
        # データベース接続情報を取得
        if db_type == 'postgresql':
            c.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port()")
            db_info = c.fetchone()
            db_name, db_user, db_host, db_port = db_info
        else:
            db_name = "sqlite"
            db_user = "local"
            db_host = "localhost"
            db_port = "N/A"
        
        # テーブル一覧を取得
        if db_type == 'postgresql':
            c.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
        else:
            c.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table'
                ORDER BY name
            """)
        
        tables = [row[0] for row in c.fetchall()]
        
        # 各テーブルの行数を確認
        table_counts = {}
        for table in tables:
            try:
                c.execute(f'SELECT COUNT(*) FROM {table}')
                count = c.fetchone()[0]
                table_counts[table] = count
            except Exception as e:
                table_counts[table] = f"Error: {str(e)}"
        
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'database_type': db_type,
            'database_name': db_name,
            'database_user': db_user,
            'database_host': db_host,
            'database_port': db_port,
            'database_url': DATABASE_URL[:20] + '...' if len(DATABASE_URL) > 20 else DATABASE_URL,
            'tables': tables,
            'table_counts': table_counts
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'database_url': DATABASE_URL[:20] + '...' if len(DATABASE_URL) > 20 else DATABASE_URL
        })

@app.route('/debug/cancellation_history')
def debug_cancellation_history():
    """解約履歴の詳細確認用エンドポイント"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 解約履歴を取得
        c.execute('''
            SELECT ch.id, ch.user_id, ch.content_type, ch.cancelled_at,
                   u.email, u.line_user_id
            FROM cancellation_history ch
            LEFT JOIN users u ON ch.user_id = u.id
            ORDER BY ch.cancelled_at DESC
        ''')
        
        cancellations = []
        for row in c.fetchall():
            cancellations.append({
                'id': row[0],
                'user_id': row[1],
                'content_type': row[2],
                'cancelled_at': row[3],
                'user_email': row[4],
                'line_user_id': row[5]
            })
        
        # 現在のusage_logsも確認
        c.execute('''
            SELECT ul.id, ul.user_id, ul.content_type, ul.created_at, ul.is_free,
                   u.email, u.line_user_id
            FROM usage_logs ul
            LEFT JOIN users u ON ul.user_id = u.id
            ORDER BY ul.created_at DESC
        ''')
        
        usage_logs = []
        for row in c.fetchall():
            usage_logs.append({
                'id': row[0],
                'user_id': row[1],
                'content_type': row[2],
                'created_at': row[3],
                'is_free': row[4],
                'user_email': row[5],
                'line_user_id': row[6]
            })
        
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'cancellation_history': cancellations,
            'usage_logs': usage_logs
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/debug/add_test_data')
def add_test_data():
    """テストデータを手動で追加するエンドポイント"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # テーブル構造を詳細に確認
        c.execute("""
            SELECT column_name, data_type, ordinal_position
            FROM information_schema.columns 
            WHERE table_name = 'cancellation_history' 
            ORDER BY ordinal_position
        """)
        columns = c.fetchall()
        
        # カラム名を順序通りに取得
        column_names = [col[0] for col in columns]
        
        # テスト用のusage_logを追加
        c.execute('''
            INSERT INTO usage_logs (user_id, usage_quantity, content_type, is_free, created_at)
            VALUES (1, 1, 'AI予定秘書', true, CURRENT_TIMESTAMP)
        ''')
        
        # カラム名を明示的に指定してcancellation_historyに追加
        if 'user_id' in column_names and 'content_type' in column_names and 'cancelled_at' in column_names:
            c.execute('''
                INSERT INTO cancellation_history (user_id, content_type, cancelled_at)
                VALUES (1, 'AI予定秘書', CURRENT_TIMESTAMP)
            ''')
        else:
            # カラム名が異なる場合、最初の3つのカラムに挿入
            c.execute(f'''
                INSERT INTO cancellation_history ({', '.join(column_names[1:4])})
                VALUES (1, 'AI予定秘書', CURRENT_TIMESTAMP)
            ''')
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'message': 'テストデータを追加しました',
            'table_structure': [{'column': col[0], 'type': col[1], 'position': col[2]} for col in columns],
            'column_names': column_names
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/debug/fix_table_structure')
def fix_table_structure():
    """テーブル構造を修正するエンドポイント"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 現在のテーブル構造を確認
        c.execute("""
            SELECT column_name, data_type, ordinal_position
            FROM information_schema.columns 
            WHERE table_name = 'cancellation_history' 
            ORDER BY ordinal_position
        """)
        current_columns = c.fetchall()
        
        # テーブルを削除して再作成
        c.execute("DROP TABLE IF EXISTS cancellation_history")
        
        # 正しい構造でテーブルを作成
        c.execute('''
            CREATE TABLE cancellation_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                content_type VARCHAR(100) NOT NULL,
                cancelled_at TIMESTAMP NOT NULL,
                subscription_status VARCHAR(50),
                current_period_start TIMESTAMP,
                current_period_end TIMESTAMP,
                trial_start TIMESTAMP,
                trial_end TIMESTAMP,
                stripe_subscription_id VARCHAR(255),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 新しいテーブル構造を確認
        c.execute("""
            SELECT column_name, data_type, ordinal_position
            FROM information_schema.columns 
            WHERE table_name = 'cancellation_history' 
            ORDER BY ordinal_position
        """)
        new_columns = c.fetchall()
        
        # テストデータを追加
        c.execute('''
            INSERT INTO cancellation_history (user_id, content_type, cancelled_at)
            VALUES (1, 'AI予定秘書', CURRENT_TIMESTAMP)
        ''')
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'message': 'テーブル構造を修正しました',
            'old_structure': [{'column': col[0], 'type': col[1], 'position': col[2]} for col in current_columns],
            'new_structure': [{'column': col[0], 'type': col[1], 'position': col[2]} for col in new_columns]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/debug/test_cancellation')
def test_cancellation():
    """解約処理のテスト用エンドポイント"""
    try:
        from services.cancellation_service import record_cancellation
        
        # 現在のユーザーデータを確認
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT id, email, line_user_id FROM users ORDER BY id')
        users = []
        for row in c.fetchall():
            users.append({
                'id': row[0],
                'email': row[1],
                'line_user_id': row[2]
            })
        
        # 最初のユーザーIDを使用してテスト
        if users:
            test_user_id = users[0]['id']
            print(f'[DEBUG] テスト用ユーザーID: {test_user_id}')
            
            # テスト用の解約記録
            record_cancellation(test_user_id, 'AI経理秘書')
            
            # 解約履歴を確認
            c.execute('''
                SELECT ch.id, ch.user_id, ch.content_type, ch.cancelled_at,
                       u.email, u.line_user_id
                FROM cancellation_history ch
                LEFT JOIN users u ON ch.user_id = u.id
                WHERE ch.content_type = 'AI経理秘書'
                ORDER BY ch.cancelled_at DESC
            ''')
            
            cancellations = []
            for row in c.fetchall():
                cancellations.append({
                    'id': row[0],
                    'user_id': row[1],
                    'content_type': row[2],
                    'cancelled_at': row[3],
                    'user_email': row[4],
                    'line_user_id': row[5]
                })
            
            conn.close()
            
            return jsonify({
                'status': 'ok',
                'message': '解約処理テスト完了',
                'users': users,
                'test_user_id': test_user_id,
                'cancellations': cancellations,
                'count': len(cancellations)
            })
        else:
            conn.close()
            return jsonify({
                'status': 'error',
                'message': 'ユーザーデータが見つかりません'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/debug/add_user_data')
def add_user_data():
    """ユーザーデータを追加するエンドポイント"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 新しいユーザーデータを追加
        new_user_data = {
            'email': 'test_user@example.com',
            'stripe_customer_id': 'cus_test_' + str(int(time.time())),
            'stripe_subscription_id': 'sub_test_' + str(int(time.time())),
            'line_user_id': 'U231cdb3fc0687f3abc7bcaba5214dfff'
        }
        
        c.execute('''
            INSERT INTO users (email, stripe_customer_id, stripe_subscription_id, line_user_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (line_user_id) DO NOTHING
        ''', (new_user_data['email'], new_user_data['stripe_customer_id'], 
              new_user_data['stripe_subscription_id'], new_user_data['line_user_id']))
        
        conn.commit()
        
        # 追加されたユーザーを確認
        c.execute('SELECT id, email, line_user_id FROM users WHERE line_user_id = %s', (new_user_data['line_user_id'],))
        user_result = c.fetchone()
        
        if user_result:
            user_id = user_result[0]
            # このユーザーにAI予定秘書の解約履歴を追加
            c.execute('''
                INSERT INTO cancellation_history (user_id, content_type, cancelled_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT DO NOTHING
            ''', (user_id, 'AI予定秘書'))
            
            conn.commit()
            
            # 全ユーザーを取得
            c.execute('SELECT id, email, line_user_id FROM users ORDER BY id')
            all_users = []
            for row in c.fetchall():
                all_users.append({
                    'id': row[0],
                    'email': row[1],
                    'line_user_id': row[2]
                })
            
            conn.close()
            
            return jsonify({
                'status': 'ok',
                'message': 'ユーザーデータを追加しました',
                'added_user': {
                    'id': user_id,
                    'email': new_user_data['email'],
                    'line_user_id': new_user_data['line_user_id']
                },
                'all_users': all_users
            })
        else:
            conn.close()
            return jsonify({
                'status': 'error',
                'message': 'ユーザーの追加に失敗しました'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

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
    c.execute('SELECT id, line_user_id FROM users WHERE email = %s', (email,))
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
        c.execute('UPDATE users SET stripe_subscription_id = %s WHERE id = 1', (new_subscription_id,))
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
        c.execute('INSERT INTO users (email, stripe_customer_id, stripe_subscription_id) VALUES (%s, %s, %s)',
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

@app.route('/debug/subscription_periods')
def debug_subscription_periods():
    """契約期間管理テーブルの内容を確認"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # subscription_periodsテーブルの内容を取得
        c.execute('''
            SELECT 
                sp.id,
                sp.user_id,
                u.email,
                sp.stripe_subscription_id,
                sp.subscription_status,
                sp.current_period_start,
                sp.current_period_end,
                sp.trial_start,
                sp.trial_end,
                sp.updated_at
            FROM subscription_periods sp
            JOIN users u ON sp.user_id = u.id
            ORDER BY sp.updated_at DESC
        ''')
        
        periods = []
        for row in c.fetchall():
            periods.append({
                'id': row[0],
                'user_id': row[1],
                'email': row[2],
                'stripe_subscription_id': row[3],
                'subscription_status': row[4],
                'current_period_start': row[5],
                'current_period_end': row[6],
                'trial_start': row[7],
                'trial_end': row[8],
                'updated_at': row[9]
            })
        
        # テーブル構造も確認
        c.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'subscription_periods' 
            ORDER BY ordinal_position
        """)
        
        columns = []
        for row in c.fetchall():
            columns.append({
                'column': row[0],
                'type': row[1],
                'nullable': row[2]
            })
        
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'subscription_periods': periods,
            'table_structure': columns,
            'count': len(periods)
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/debug/sync_subscription/<int:user_id>')
def debug_sync_subscription(user_id):
    """指定ユーザーの契約期間情報をStripeから同期"""
    try:
        from services.subscription_period_service import SubscriptionPeriodService
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT stripe_subscription_id FROM users WHERE id = %s', (user_id,))
        result = c.fetchone()
        conn.close()
        
        if not result or not result[0]:
            return jsonify({'status': 'error', 'message': 'サブスクリプションIDが見つかりません'})
        
        stripe_subscription_id = result[0]
        period_service = SubscriptionPeriodService()
        success = period_service.sync_subscription_period(user_id, stripe_subscription_id)
        
        if success:
            # 同期後の情報を取得
            subscription_info = period_service.get_subscription_info(user_id)
            return jsonify({
                'status': 'ok',
                'message': '契約期間情報を同期しました',
                'subscription_info': subscription_info
            })
        else:
            return jsonify({'status': 'error', 'message': '同期に失敗しました'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/debug/cancellation_periods')
def debug_cancellation_periods():
    """cancellation_historyテーブルの契約期間情報を確認"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # cancellation_historyテーブルの内容を取得
        c.execute('''
            SELECT 
                ch.id,
                ch.user_id,
                u.email,
                ch.content_type,
                ch.subscription_status,
                ch.current_period_start,
                ch.current_period_end,
                ch.trial_start,
                ch.trial_end,
                ch.stripe_subscription_id,
                ch.cancelled_at
            FROM cancellation_history ch
            JOIN users u ON ch.user_id = u.id
            ORDER BY ch.cancelled_at DESC
        ''')
        
        periods = []
        for row in c.fetchall():
            periods.append({
                'id': row[0],
                'user_id': row[1],
                'email': row[2],
                'content_type': row[3],
                'subscription_status': row[4],
                'current_period_start': row[5],
                'current_period_end': row[6],
                'trial_start': row[7],
                'trial_end': row[8],
                'stripe_subscription_id': row[9],
                'cancelled_at': row[10]
            })
        
        # テーブル構造も確認
        c.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'cancellation_history' 
            ORDER BY ordinal_position
        """)
        
        columns = []
        for row in c.fetchall():
            columns.append({
                'column': row[0],
                'type': row[1],
                'nullable': row[2]
            })
        
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'cancellation_periods': periods,
            'table_structure': columns,
            'count': len(periods)
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/debug/update_cancellation_period/<int:user_id>/<content_type>')
def debug_update_cancellation_period(user_id, content_type):
    """指定ユーザーの契約期間情報をcancellation_historyに更新"""
    try:
        from services.cancellation_period_service import CancellationPeriodService
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT stripe_subscription_id FROM users WHERE id = %s', (user_id,))
        result = c.fetchone()
        conn.close()
        
        if not result or not result[0]:
            return jsonify({'status': 'error', 'message': 'サブスクリプションIDが見つかりません'})
        
        stripe_subscription_id = result[0]
        period_service = CancellationPeriodService()
        success = period_service.update_subscription_period(user_id, content_type, stripe_subscription_id)
        
        if success:
            # 更新後の情報を取得
            subscription_info = period_service.get_subscription_info(user_id, content_type)
            return jsonify({
                'status': 'ok',
                'message': '契約期間情報を更新しました',
                'subscription_info': subscription_info
            })
        else:
            return jsonify({'status': 'error', 'message': '更新に失敗しました'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/debug/migrate_cancellation_history')
def migrate_cancellation_history():
    """cancellation_historyテーブルに契約期間管理用カラムを追加"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 現在のテーブル構造を確認
        c.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'cancellation_history' 
            ORDER BY ordinal_position
        """)
        
        current_columns = []
        for row in c.fetchall():
            current_columns.append({
                'column': row[0],
                'type': row[1],
                'nullable': row[2]
            })
        
        # 必要なカラムを確認
        required_columns = [
            'subscription_status',
            'current_period_start', 
            'current_period_end',
            'trial_start',
            'trial_end',
            'stripe_subscription_id'
        ]
        
        existing_columns = [col['column'] for col in current_columns]
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        if not missing_columns:
            return jsonify({
                'status': 'ok',
                'message': 'すべてのカラムが既に存在します',
                'current_columns': current_columns
            })
        
        # 不足しているカラムを追加
        for column in missing_columns:
            if column == 'subscription_status':
                c.execute("ALTER TABLE cancellation_history ADD COLUMN subscription_status VARCHAR(50)")
            elif column == 'current_period_start':
                c.execute("ALTER TABLE cancellation_history ADD COLUMN current_period_start TIMESTAMP")
            elif column == 'current_period_end':
                c.execute("ALTER TABLE cancellation_history ADD COLUMN current_period_end TIMESTAMP")
            elif column == 'trial_start':
                c.execute("ALTER TABLE cancellation_history ADD COLUMN trial_start TIMESTAMP")
            elif column == 'trial_end':
                c.execute("ALTER TABLE cancellation_history ADD COLUMN trial_end TIMESTAMP")
            elif column == 'stripe_subscription_id':
                c.execute("ALTER TABLE cancellation_history ADD COLUMN stripe_subscription_id VARCHAR(255)")
        
        conn.commit()
        
        # 更新後のテーブル構造を確認
        c.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'cancellation_history' 
            ORDER BY ordinal_position
        """)
        
        new_columns = []
        for row in c.fetchall():
            new_columns.append({
                'column': row[0],
                'type': row[1],
                'nullable': row[2]
            })
        
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'message': f'カラムを追加しました: {missing_columns}',
            'old_structure': current_columns,
            'new_structure': new_columns,
            'added_columns': missing_columns
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/debug/update_existing_cancellation/<int:user_id>/<content_type>')
def update_existing_cancellation(user_id, content_type):
    """既存のcancellation_historyレコードに契約期間情報を更新"""
    try:
        from services.cancellation_period_service import CancellationPeriodService
        
        # ユーザーのサブスクリプションIDを取得
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT stripe_subscription_id FROM users WHERE id = %s', (user_id,))
        result = c.fetchone()
        conn.close()
        
        if not result or not result[0]:
            return jsonify({'status': 'error', 'message': 'サブスクリプションIDが見つかりません'})
        
        stripe_subscription_id = result[0]
        
        # 契約期間情報を更新
        period_service = CancellationPeriodService()
        success = period_service.update_subscription_period(user_id, content_type, stripe_subscription_id)
        
        if success:
            # 更新後の情報を取得
            subscription_info = period_service.get_subscription_info(user_id, content_type)
            
            # 更新後のテーブル内容も確認
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('''
                SELECT 
                    id, user_id, content_type, cancelled_at,
                    subscription_status, current_period_start, current_period_end,
                    trial_start, trial_end, stripe_subscription_id
                FROM cancellation_history 
                WHERE user_id = %s AND content_type = %s
            ''', (user_id, content_type))
            
            updated_record = c.fetchone()
            conn.close()
            
            if updated_record:
                record_info = {
                    'id': updated_record[0],
                    'user_id': updated_record[1],
                    'content_type': updated_record[2],
                    'cancelled_at': updated_record[3],
                    'subscription_status': updated_record[4],
                    'current_period_start': updated_record[5],
                    'current_period_end': updated_record[6],
                    'trial_start': updated_record[7],
                    'trial_end': updated_record[8],
                    'stripe_subscription_id': updated_record[9]
                }
            else:
                record_info = None
            
            return jsonify({
                'status': 'ok',
                'message': '既存レコードを更新しました',
                'subscription_info': subscription_info,
                'updated_record': record_info
            })
        else:
            return jsonify({'status': 'error', 'message': '更新に失敗しました'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/debug/create_content_period/<int:user_id>/<content_type>')
def debug_create_content_period(user_id, content_type):
    """指定ユーザーのコンテンツ追加時に契約期間情報を保存"""
    try:
        from services.cancellation_period_service import CancellationPeriodService
        
        # ユーザーのサブスクリプションIDを取得
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT stripe_subscription_id FROM users WHERE id = %s', (user_id,))
        result = c.fetchone()
        conn.close()
        
        if not result or not result[0]:
            return jsonify({'status': 'error', 'message': 'サブスクリプションIDが見つかりません'})
        
        stripe_subscription_id = result[0]
        
        # 契約期間情報を保存
        period_service = CancellationPeriodService()
        success = period_service.create_content_period_record(user_id, content_type, stripe_subscription_id)
        
        if success:
            # 保存後の情報を取得
            subscription_info = period_service.get_subscription_info(user_id, content_type)
            
            # 保存後のテーブル内容も確認
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('''
                SELECT 
                    id, user_id, content_type, cancelled_at,
                    subscription_status, current_period_start, current_period_end,
                    trial_start, trial_end, stripe_subscription_id
                FROM cancellation_history 
                WHERE user_id = %s AND content_type = %s
            ''', (user_id, content_type))
            
            saved_record = c.fetchone()
            conn.close()
            
            if saved_record:
                record_info = {
                    'id': saved_record[0],
                    'user_id': saved_record[1],
                    'content_type': saved_record[2],
                    'cancelled_at': saved_record[3],
                    'subscription_status': saved_record[4],
                    'current_period_start': saved_record[5],
                    'current_period_end': saved_record[6],
                    'trial_start': saved_record[7],
                    'trial_end': saved_record[8],
                    'stripe_subscription_id': saved_record[9]
                }
            else:
                record_info = None
            
            return jsonify({
                'status': 'ok',
                'message': 'コンテンツ期間情報を保存しました',
                'subscription_info': subscription_info,
                'saved_record': record_info
            })
        else:
            return jsonify({'status': 'error', 'message': '保存に失敗しました'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 