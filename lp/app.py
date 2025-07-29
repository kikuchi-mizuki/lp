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
    
    # user_statesテーブルを確実に初期化
    from models.user_state import init_user_states_table
    init_user_states_table()
    
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
                pending_charge BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # 解約履歴テーブルを作成
        c.execute('''
            CREATE TABLE IF NOT EXISTS cancellation_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                content_type VARCHAR(255) NOT NULL,
                cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # 既存テーブルにpending_chargeカラムを追加（マイグレーション）
        try:
            c.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'usage_logs' AND column_name = 'pending_charge'
            """)
            
            if not c.fetchone():
                c.execute("""
                    ALTER TABLE usage_logs 
                    ADD COLUMN pending_charge BOOLEAN DEFAULT FALSE
                """)
                print("✅ pending_chargeカラムを追加しました")
            else:
                print("ℹ️ pending_chargeカラムは既に存在します")
        except Exception as e:
            print(f"❌ マイグレーションエラー: {e}")
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
                pending_charge BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # 解約履歴テーブルを作成（SQLite用）
        c.execute('''
            CREATE TABLE IF NOT EXISTS cancellation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content_type VARCHAR(255) NOT NULL,
                cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # SQLite用のマイグレーション
        try:
            c.execute("PRAGMA table_info(usage_logs)")
            columns = [column[1] for column in c.fetchall()]
            
            if 'pending_charge' not in columns:
                c.execute("""
                    ALTER TABLE usage_logs 
                    ADD COLUMN pending_charge BOOLEAN DEFAULT FALSE
                """)
                print("✅ pending_chargeカラムを追加しました")
            else:
                print("ℹ️ pending_chargeカラムは既に存在します")
        except Exception as e:
            print(f"❌ マイグレーションエラー: {e}")
    
    conn.commit()
    conn.close()

init_db()

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.register_blueprint(line_bp)
app.register_blueprint(stripe_bp)

@app.route('/')
def index():
    return render_template('index.html')

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
                cancelled_at TIMESTAMP NOT NULL
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 