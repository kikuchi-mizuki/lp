import os
import sys

# Add the current directory to Python path for production deployment
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
import stripe
from dotenv import load_dotenv
import hashlib
import hmac
import base64
import json
import requests
import sqlite3
import psycopg2
import time
from urllib.parse import urlparse
from utils.message_templates import get_default_message, get_menu_message, get_help_message
from utils.db import get_db_connection
from routes.line import line_bp
from routes.stripe import stripe_bp
from routes.company import company_bp
from routes.line_api import line_api_bp
from routes.stripe_payment import stripe_payment_bp
from routes.content_management import content_management_bp
from routes.cancellation import cancellation_bp
from routes.notification import notification_bp
from routes.scheduler import scheduler_bp
from routes.backup import backup_bp
from routes.dashboard import dashboard_bp
from routes.monitoring import monitoring_bp
from routes.reminder import reminder_bp
from routes.security import security_bp
from routes.dashboard_ui import dashboard_ui_bp
from routes.automation import automation_bp
from routes.company_line_accounts import company_line_accounts_bp
from routes.company_registration import company_registration_bp
from routes.railway_setup import railway_setup_bp
from routes.ai_schedule_webhook import ai_schedule_webhook_bp
from routes.ai_schedule_webhook_simple import ai_schedule_webhook_simple_bp
from routes.debug import debug_bp
from datetime import datetime

load_dotenv()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

MONTHLY_PRICE_ID = os.getenv('STRIPE_MONTHLY_PRICE_ID')
USAGE_PRICE_ID = os.getenv('STRIPE_USAGE_PRICE_ID')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

DATABASE_URL = os.getenv('DATABASE_URL', 'database.db')

def init_db():
    """データベースの初期化（企業ユーザー専用最小限設計）"""
    conn = None
    c = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプを確認
        from utils.db import get_db_type
        db_type = get_db_type()
        
        if db_type == 'postgresql':
            # 企業基本情報テーブル（最小限）
            c.execute('''
                CREATE TABLE IF NOT EXISTS companies (
                    id SERIAL PRIMARY KEY,
                    company_name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 企業LINEアカウントテーブル（最小限）
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_line_accounts (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL,
                    content_type VARCHAR(100) NOT NULL,
                    line_channel_id VARCHAR(255) NOT NULL,
                    line_channel_access_token VARCHAR(255) NOT NULL,
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id),
                    UNIQUE(company_id, content_type)
                )
            ''')
            
            # 企業サブスクリプション管理テーブル（料金管理強化）
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_subscriptions (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL,
                    content_type VARCHAR(100) NOT NULL,
                    subscription_status VARCHAR(50) DEFAULT 'active',
                    base_price INTEGER DEFAULT 3900,
                    additional_price INTEGER DEFAULT 0,
                    total_price INTEGER DEFAULT 3900,
                    stripe_subscription_id VARCHAR(255),
                    current_period_end TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id),
                    UNIQUE(company_id, content_type)
                )
            ''')
            
            # インデックスの作成（パフォーマンス向上）
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_company_line_accounts_channel_id 
                ON company_line_accounts(line_channel_id)
            ''')
            
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_company_subscriptions_status 
                ON company_subscriptions(subscription_status)
            ''')
            
        else:
            # SQLite用の最小限テーブル
            c.execute('''
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_line_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    content_type TEXT NOT NULL,
                    line_channel_id TEXT NOT NULL,
                    line_channel_access_token TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id),
                    UNIQUE(company_id, content_type)
                )
            ''')
            
            c.execute('''
                CREATE TABLE IF NOT EXISTS company_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    content_type TEXT NOT NULL,
                    subscription_status TEXT DEFAULT 'active',
                    base_price INTEGER DEFAULT 3900,
                    additional_price INTEGER DEFAULT 0,
                    total_price INTEGER DEFAULT 3900,
                    stripe_subscription_id TEXT,
                    current_period_end TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id),
                    UNIQUE(company_id, content_type)
                )
            ''')
        
        conn.commit()
        print("✅ 企業ユーザー専用最小限データベースの初期化が完了しました")
        
    except Exception as e:
        print(f"❌ データベース初期化エラー: {e}")
        if conn:
            conn.rollback()
    finally:
        if c:
            c.close()
        if conn:
            conn.close()
    
    # 追加テーブルの作成（新しい接続で実行）
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプを確認
        db_type = get_db_type()
        
        if db_type == 'postgresql':
            # PostgreSQL用の追加テーブル
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
                    stripe_subscription_id VARCHAR(255)
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
                    UNIQUE(stripe_subscription_id)
                )
            ''')
        else:
            # SQLite用の企業ユーザー専用テーブルは既に作成済み
            pass
        
        conn.commit()
        print("✅ 追加テーブル作成完了")
        
    except Exception as e:
        print(f"❌ 追加テーブル作成エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if c:
            c.close()
        if conn:
            conn.close()
    
    # 企業ユーザー専用システムのため、ユーザー状態テーブルは不要
    pass

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.register_blueprint(line_bp)
app.register_blueprint(stripe_bp)
app.register_blueprint(company_bp)
app.register_blueprint(line_api_bp)
app.register_blueprint(stripe_payment_bp)
app.register_blueprint(content_management_bp)
app.register_blueprint(cancellation_bp)
app.register_blueprint(notification_bp)
app.register_blueprint(scheduler_bp)
app.register_blueprint(backup_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(monitoring_bp)
app.register_blueprint(reminder_bp)
app.register_blueprint(security_bp)
app.register_blueprint(dashboard_ui_bp)
app.register_blueprint(automation_bp)
app.register_blueprint(company_line_accounts_bp)
app.register_blueprint(company_registration_bp)
app.register_blueprint(railway_setup_bp)
app.register_blueprint(ai_schedule_webhook_bp)
app.register_blueprint(ai_schedule_webhook_simple_bp)
app.register_blueprint(debug_bp)

@app.route('/')
def index():
    return render_template('index.html')

# 企業ユーザー専用の決済フォーム処理
@app.route('/company-registration', methods=['GET', 'POST'])
def company_registration():
    """
    企業ユーザー専用の決済フォーム
    """
    if request.method == 'GET':
        return render_template('company_registration.html')
    
    # POST処理（決済フォーム送信）
    if request.is_json:
        # LPからの直接送信（JSON形式）
        data = request.get_json()
        company_name = data.get('company_name')
        email = data.get('email')
        content_type = data.get('content_type', 'ai_schedule')  # デフォルトはAI予定秘書
    else:
        # フォームからの送信
        company_name = request.form.get('company_name')
        email = request.form.get('email')
        content_type = request.form.get('content_type', 'ai_schedule')
    
    if not company_name or not email:
        return jsonify({'error': '企業名とメールアドレスは必須です'}), 400
    
    # 既存企業の確認
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id FROM companies WHERE email = %s', (email,))
    existing_company = c.fetchone()
    conn.close()
    
    if existing_company:
        return jsonify({'error': 'このメールアドレスは既に登録されています'}), 400
    
    # Stripeチェックアウトセッションを作成
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': MONTHLY_PRICE_ID,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('company_registration_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('company_registration_cancel', _external=True),
            metadata={
                'company_name': company_name,
                'email': email,
                'content_type': content_type
            },
            customer_email=email,
            billing_address_collection='required',
            allow_promotion_codes=True
        )
        
        return jsonify({'url': checkout_session.url})
        
    except Exception as e:
        print(f"❌ Stripeチェックアウトセッション作成エラー: {e}")
        return jsonify({'error': '決済セッションの作成に失敗しました'}), 500

# 企業登録成功時の処理
@app.route('/company-registration-success')
def company_registration_success():
    """
    企業登録成功時の処理
    """
    session_id = request.args.get('session_id')
    
    if not session_id:
        print("❌ セッションIDがありません")
        return redirect('/company-registration')
    
    try:
        print(f"🔍 セッションID: {session_id}")
        
        # Stripeからセッション情報を取得
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        print(f"✅ Stripeセッション取得成功: {checkout_session.id}")
        print(f"💰 決済ステータス: {checkout_session.payment_status}")
        print(f"📧 メタデータ: {checkout_session.metadata}")
        
        if checkout_session.payment_status != 'paid':
            print("❌ 決済が完了していません")
            return redirect('/company-registration-cancel')
        
        # 企業情報をデータベースに保存
        print("🏢 企業情報を保存中...")
        company_id = create_company_profile(checkout_session.metadata)
        print(f"✅ 企業情報保存完了: {company_id}")
        
        # LINEアカウントを自動作成
        print("📱 LINEアカウントを作成中...")
        line_account = create_company_line_account(company_id, checkout_session.metadata)
        print(f"✅ LINEアカウント作成完了: {line_account}")
        
        # サブスクリプション情報を保存
        print("💳 サブスクリプション情報を保存中...")
        save_company_subscription(company_id, checkout_session.subscription)
        print(f"✅ サブスクリプション保存完了: {checkout_session.subscription}")
        
        # 次回請求日を計算
        subscription = stripe.Subscription.retrieve(checkout_session.subscription)
        next_billing_date = datetime.fromtimestamp(subscription.current_period_end).strftime('%Y年%m月%d日')
        print(f"📅 次回請求日: {next_billing_date}")
        
        return render_template('company_registration_success.html',
                             company_data=checkout_session.metadata,
                             company_id=company_id,
                             line_account=line_account,
                             next_billing_date=next_billing_date)
        
    except Exception as e:
        print(f"❌ 企業登録成功処理エラー: {e}")
        import traceback
        traceback.print_exc()
        return redirect('/company-registration-cancel')

# 企業登録キャンセル時の処理
@app.route('/company-registration-cancel')
def company_registration_cancel():
    """
    企業登録キャンセル時の処理
    """
    return render_template('company_registration_cancel.html')

# 企業基本情報をデータベースに保存
def create_company_profile(company_data):
    """
    企業基本情報をデータベースに保存
    """
    conn = None
    c = None
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO companies (company_name, email, status)
            VALUES (%s, %s, 'active')
            RETURNING id
        ''', (company_data['company_name'], company_data['email']))
        
        company_id = c.fetchone()[0]
        conn.commit()
        
        print(f"✅ 企業基本情報を保存しました: {company_id}")
        return company_id
        
    except Exception as e:
        print(f"❌ 企業基本情報保存エラー: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if c:
            c.close()
        if conn:
            conn.close()

# 企業専用LINEアカウントを自動作成
def create_company_line_account(company_id, company_data):
    """
    企業専用LINEアカウントを自動作成
    """
    try:
        # LINE Developers Console APIでチャンネル作成（モック）
        # 実際の実装ではLINE APIを使用
        line_channel_id = f"U{company_id}_{int(time.time())}"
        line_channel_access_token = f"token_{company_id}_{int(time.time())}"
        
        # データベースにLINEアカウント情報を保存
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO company_line_accounts 
            (company_id, content_type, line_channel_id, line_channel_access_token, status)
            VALUES (%s, %s, %s, %s, 'active')
        ''', (
            company_id,
            company_data['content_type'],
            line_channel_id,
            line_channel_access_token
        ))
        
        conn.commit()
        conn.close()
        
        line_account = {
            'line_channel_id': line_channel_id,
            'line_channel_access_token': line_channel_access_token,
            'qr_code_url': None,  # 実際の実装ではQRコードURLを生成
            'status': 'active'
        }
        
        print(f"✅ 企業LINEアカウントを作成しました: {line_channel_id}")
        return line_account
        
    except Exception as e:
        print(f"❌ 企業LINEアカウント作成エラー: {e}")
        raise

# 企業サブスクリプション情報をデータベースに保存
def save_company_subscription(company_id, stripe_subscription_id, content_type='ai_schedule'):
    """
    企業サブスクリプション情報をデータベースに保存（料金管理強化）
    """
    conn = None
    c = None
    
    try:
        # Stripeからサブスクリプション情報を取得
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        
        # 料金計算
        base_price = 3900  # 基本料金（月額3,900円）
        additional_price = 0  # 追加コンテンツ料金（初期は0）
        total_price = base_price + additional_price
        
        # サブスクリプションの期間を計算
        current_period_end = datetime.fromtimestamp(subscription.current_period_end)
        
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO company_subscriptions 
            (company_id, content_type, subscription_status, base_price, additional_price, 
             total_price, stripe_subscription_id, current_period_end)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            company_id,
            content_type,
            subscription.status,
            base_price,
            additional_price,
            total_price,
            stripe_subscription_id,
            current_period_end
        ))
        
        conn.commit()
        
        print(f"✅ 企業サブスクリプションを保存しました: {company_id}, 料金: {total_price}円")
        
    except Exception as e:
        print(f"❌ 企業サブスクリプション保存エラー: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if c:
            c.close()
        if conn:
            conn.close()

def calculate_company_pricing(company_id, content_types):
    """
    企業の料金計算
    """
    base_price = 3900  # 基本料金
    additional_price_per_content = 1500  # 追加コンテンツ料金
    
    # 基本料金（1つ目のコンテンツは基本料金に含まれる）
    if len(content_types) == 1:
        total_price = base_price
        additional_price = 0
    else:
        # 追加コンテンツ料金
        additional_contents = len(content_types) - 1
        additional_price = additional_contents * additional_price_per_content
        total_price = base_price + additional_price
    
    return {
        'base_price': base_price,
        'additional_price': additional_price,
        'total_price': total_price,
        'content_count': len(content_types),
        'additional_content_count': max(0, len(content_types) - 1)
    }

# Stripe Webhook処理（企業ユーザー専用）
@app.route('/webhook/stripe/company', methods=['POST'])
def stripe_webhook_company():
    """
    Stripe Webhook処理（企業ユーザー専用）
    """
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError as e:
        print(f"❌ Webhookペイロードエラー: {e}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        print(f"❌ Webhook署名検証エラー: {e}")
        return jsonify({'error': 'Invalid signature'}), 400
    
    # イベントタイプに応じた処理
    if event['type'] == 'customer.subscription.deleted':
        handle_company_subscription_cancelled(event)
    elif event['type'] == 'invoice.payment_failed':
        handle_company_payment_failed(event)
    elif event['type'] == 'invoice.payment_succeeded':
        handle_company_payment_succeeded(event)
    
    return jsonify({'status': 'success'})

# 企業サブスクリプション解約処理
def handle_company_subscription_cancelled(event):
    """
    企業サブスクリプション解約処理
    """
    subscription_id = event['data']['object']['id']
    
    try:
        from services.company_service import cancel_company_content
        
        # サブスクリプションIDから企業IDとコンテンツタイプを取得
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT company_id, content_type 
            FROM company_subscriptions 
            WHERE stripe_subscription_id = %s
        ''', (subscription_id,))
        
        subscription = c.fetchone()
        if not subscription:
            print(f"❌ サブスクリプションが見つかりません: {subscription_id}")
            return
        
        company_id, content_type = subscription
        
        # 解約処理を実行
        result = cancel_company_content(company_id, content_type)
        
        if result:
            print(f"✅ 企業解約処理が完了しました: {company_id}, {content_type}")
        else:
            print(f"❌ 企業解約処理に失敗しました: {company_id}, {content_type}")
        
    except Exception as e:
        print(f"❌ 企業解約処理エラー: {e}")
    finally:
        if c:
            c.close()
        if conn:
            conn.close()

# 企業決済失敗処理
def handle_company_payment_failed(event):
    """
    企業決済失敗処理
    """
    invoice = event['data']['object']
    subscription_id = invoice['subscription']
    
    print(f"⚠️ 企業決済失敗: {subscription_id}")
    
    # 決済失敗通知を送信（実装予定）
    # send_payment_failed_notification(subscription_id)

# 企業決済成功処理
def handle_company_payment_succeeded(event):
    """
    企業決済成功処理
    """
    invoice = event['data']['object']
    subscription_id = invoice['subscription']
    
    print(f"✅ 企業決済成功: {subscription_id}")
    
    # 決済成功通知を送信（実装予定）
    # send_payment_succeeded_notification(subscription_id)

@app.route('/company-registration-debug')
def company_registration_debug():
    """企業情報登録フォーム（デバッグ用）"""
    subscription_id = request.args.get('subscription_id', '')
    content_type = request.args.get('content_type', '')
    return render_template('company_registration_debug.html', 
                         subscription_id=subscription_id, 
                         content_type=content_type)

@app.route('/company-dashboard')
def company_dashboard():
    """企業管理ダッシュボード"""
    return render_template('company_dashboard.html')

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

@app.route('/monitor/line_errors')
def monitor_line_errors():
    """LINE APIエラーの監視エンドポイント"""
    try:
        from services.monitoring_service import monitoring_service
        result = monitoring_service.check_line_api_errors()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'LINE APIエラー監視エラー: {str(e)}'
        })

@app.route('/monitor/stripe_errors')
def monitor_stripe_errors():
    """Stripeエラーの監視エンドポイント"""
    try:
        from services.monitoring_service import monitoring_service
        result = monitoring_service.check_stripe_errors()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Stripeエラー監視エラー: {str(e)}'
        })

@app.route('/monitor/errors')
def monitor_all_errors():
    """全エラーの監視エンドポイント"""
    try:
        from services.monitoring_service import monitoring_service
        
        line_result = monitoring_service.check_line_api_errors()
        stripe_result = monitoring_service.check_stripe_errors()
        
        return jsonify({
            'success': True,
            'line_errors': line_result,
            'stripe_errors': stripe_result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'エラー監視エラー: {str(e)}'
        })

@app.route('/debug/user/<line_user_id>')
def debug_user(line_user_id):
    """ユーザーの決済状況をデバッグするエンドポイント"""
    try:
        from services.user_service import is_paid_user_company_centric
        from services.stripe_service import check_subscription_status
        from utils.db import get_db_connection
        
        result = {
            'line_user_id': line_user_id,
            'database_check': {},
            'payment_check': {},
            'stripe_check': {}
        }
        
        # データベースから企業情報を直接取得（企業ID中心統合対応）
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            SELECT id, company_name, stripe_subscription_id, status, created_at, updated_at
            FROM companies 
            WHERE line_user_id = %s
        ''', (line_user_id,))
        
        db_result = c.fetchone()
        if db_result:
            company_id, company_name, stripe_subscription_id, status, created_at, updated_at = db_result
            result['database_check'] = {
                'found': True,
                'company_id': company_id,
                'company_name': company_name,
                'stripe_subscription_id': stripe_subscription_id,
                'status': status,
                'created_at': str(created_at),
                'updated_at': str(updated_at)
            }
        else:
            result['database_check'] = {'found': False}
        
        conn.close()
        
        # is_paid_user_company_centric関数の結果
        from services.user_service import is_paid_user_company_centric
        payment_check = is_paid_user_company_centric(line_user_id)
        result['payment_check'] = payment_check
        
        # Stripeサブスクリプションの状態を直接確認
        if result['database_check'].get('found') and result['database_check'].get('stripe_subscription_id'):
            stripe_subscription_id = result['database_check']['stripe_subscription_id']
            subscription_status = check_subscription_status(stripe_subscription_id)
            result['stripe_check'] = subscription_status
        
        return result
        
    except Exception as e:
        return {'error': str(e)}

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

# @app.route('/debug/test_cancellation')
# def test_cancellation():
#     """解約処理のテスト用エンドポイント（企業ユーザー専用に統一するため削除）"""
#     pass

@app.route('/debug/add_company_data')
def add_company_data():
    """企業データを追加するエンドポイント"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 新しい企業データを追加
        new_company_data = {
            'company_name': 'テスト企業株式会社',
            'email': 'test_company@example.com',
            'content_type': 'ai_schedule',
            'line_channel_id': 'U231cdb3fc0687f3abc7bcaba5214dfff',
            'line_channel_access_token': 'test_token_' + str(int(time.time()))
        }
        
        # 企業基本情報を追加
        c.execute('''
            INSERT INTO companies (company_name, email, status)
            VALUES (%s, %s, 'active')
            ON CONFLICT (email) DO NOTHING
            RETURNING id
        ''', (new_company_data['company_name'], new_company_data['email']))
        
        company_result = c.fetchone()
        if company_result:
            company_id = company_result[0]
            
            # 企業LINEアカウントを追加
            c.execute('''
                INSERT INTO company_line_accounts (company_id, content_type, line_channel_id, line_channel_access_token, status)
                VALUES (%s, %s, %s, %s, 'active')
                ON CONFLICT (company_id, content_type) DO NOTHING
            ''', (company_id, new_company_data['content_type'], 
                  new_company_data['line_channel_id'], new_company_data['line_channel_access_token']))
            
            # 企業サブスクリプションを追加
            c.execute('''
                INSERT INTO company_subscriptions (company_id, content_type, subscription_status)
                VALUES (%s, %s, 'active')
                ON CONFLICT (company_id, content_type) DO NOTHING
            ''', (company_id, new_company_data['content_type']))
            
            conn.commit()
            
            # 全企業を取得
            c.execute('SELECT id, company_name, email, status FROM companies ORDER BY id')
            all_companies = []
            for row in c.fetchall():
                all_companies.append({
                    'id': row[0],
                    'company_name': row[1],
                    'email': row[2],
                    'status': row[3]
                })
            
            conn.close()
            
            return jsonify({
                'status': 'ok',
                'message': '企業データを追加しました',
                'added_company': {
                    'id': company_id,
                    'company_name': new_company_data['company_name'],
                    'email': new_company_data['email'],
                    'line_channel_id': new_company_data['line_channel_id']
                },
                'all_companies': all_companies
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
    c.execute('SELECT id FROM companies WHERE email = %s', (email,))
    user = c.fetchone()
    conn.close()
    
    if user:
        return jsonify({'registered': True, 'company_id': user[0]})
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
            c.execute('SELECT id FROM companies WHERE email = %s ORDER BY created_at DESC LIMIT 1', (email,))
            user = c.fetchone()
            conn.close()
            if user:
                company_id = user[0]
        except Exception as e:
            print(f'[DEBUG] ユーザーID取得エラー: {e}')
    
    return render_template('thanks.html', email=email, company_id=company_id)

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

@app.route('/debug/companies')
def debug_companies():
    """デバッグ用：企業一覧表示"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT id, company_name, email, status, created_at FROM companies ORDER BY created_at DESC LIMIT 10')
        companies = c.fetchall()
        conn.close()
        
        company_list = []
        for company in companies:
            company_list.append({
                'id': company[0],
                'company_name': company[1],
                'email': company[2],
                'status': company[3],
                'created_at': company[4]
            })
        
        return jsonify({'companies': company_list})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/debug/webhook_status')
def debug_webhook_status():
    """LINE Webhookの設定状況を確認"""
    try:
        import os
        import requests
        
        channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
        channel_secret = os.getenv('LINE_CHANNEL_SECRET')
        
        if not channel_access_token or not channel_secret:
            return jsonify({
                'error': 'LINE環境変数が設定されていません',
                'channel_access_token': bool(channel_access_token),
                'channel_secret': bool(channel_secret)
            })
        
        # LINE Messaging APIの情報を取得
        headers = {
            'Authorization': f'Bearer {channel_access_token}'
        }
        
        try:
            # プロフィール情報を取得してトークンの有効性を確認
            response = requests.get('https://api.line.me/v2/bot/profile/U231cdb3fc0687f3abc7bcaba5214dfff', headers=headers)
            
            return jsonify({
                'webhook_url': 'https://lp-production-9e2c.up.railway.app/line/webhook',
                'channel_access_token_set': bool(channel_access_token),
                'channel_secret_set': bool(channel_secret),
                'line_api_test': {
                    'status_code': response.status_code,
                    'success': response.status_code == 200,
                    'response': response.json() if response.status_code == 200 else response.text
                },
                'environment': {
                    'railway_url': 'https://lp-production-9e2c.up.railway.app',
                    'webhook_endpoint': '/line/webhook'
                }
            })
        except Exception as e:
            return jsonify({
                'error': f'LINE API接続エラー: {str(e)}',
                'webhook_url': 'https://lp-production-9e2c.up.railway.app/line/webhook',
                'channel_access_token_set': bool(channel_access_token),
                'channel_secret_set': bool(channel_secret)
            })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/debug/update_company_line_user_id/<email>/<new_line_user_id>')
def debug_update_company_line_user_id(email, new_line_user_id):
    """デバッグ用：企業LINEユーザーIDを手動で更新"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業IDを取得
        c.execute('SELECT id FROM companies WHERE email = %s', (email,))
        company = c.fetchone()
        
        if not company:
            return jsonify({'error': '企業が見つかりません'}), 404
        
        company_id = company[0]
        
        # 企業LINEアカウントを更新
        c.execute('UPDATE company_line_accounts SET line_channel_id = %s WHERE company_id = %s', (new_line_user_id, company_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'企業LINEユーザーIDを更新しました: company_id={company_id}, new_line_user_id={new_line_user_id}'
        })
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

# @app.route('/debug/update_subscription/<new_subscription_id>')
# def update_subscription_id(new_subscription_id):
#     """デバッグ用：サブスクリプションID更新（企業ユーザー専用に統一するため削除）"""
#     pass

# @app.route('/debug/add_user')
# def add_user():
#     """デバッグ用：テストユーザー追加（企業ユーザー専用に統一するため削除）"""
#     pass

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

# @app.route('/subscribe', methods=['POST'])
# def subscribe():
#     """Stripeサブスクリプション作成（個人ユーザー用 - 企業ユーザー専用に統一するため削除）"""
#     pass

@app.route('/debug/subscription_periods')
def debug_subscription_periods():
    """契約期間管理テーブルの内容を確認（料金情報含む）"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # company_subscriptionsテーブルの内容を取得（料金情報含む）
        c.execute('''
            SELECT 
                cs.id,
                cs.company_id,
                c.company_name,
                c.email,
                cs.content_type,
                cs.subscription_status,
                cs.base_price,
                cs.additional_price,
                cs.total_price,
                cs.stripe_subscription_id,
                cs.current_period_end,
                cs.created_at
            FROM company_subscriptions cs
            JOIN companies c ON cs.company_id = c.id
            ORDER BY cs.created_at DESC
        ''')
        
        subscriptions = []
        for row in c.fetchall():
            subscriptions.append({
                'id': row[0],
                'company_id': row[1],
                'company_name': row[2],
                'email': row[3],
                'content_type': row[4],
                'subscription_status': row[5],
                'base_price': row[6],
                'additional_price': row[7],
                'total_price': row[8],
                'stripe_subscription_id': row[9],
                'current_period_end': row[10],
                'created_at': row[11]
            })
        
        # 企業ごとの料金サマリー
        c.execute('''
            SELECT 
                c.company_name,
                c.email,
                COUNT(cs.content_type) as content_count,
                SUM(cs.total_price) as total_monthly_cost,
                STRING_AGG(cs.content_type, ', ') as content_types
            FROM companies c
            LEFT JOIN company_subscriptions cs ON c.id = cs.company_id
            WHERE cs.subscription_status = 'active'
            GROUP BY c.id, c.company_name, c.email
            ORDER BY total_monthly_cost DESC
        ''')
        
        company_summary = []
        for row in c.fetchall():
            company_summary.append({
                'company_name': row[0],
                'email': row[1],
                'content_count': row[2],
                'total_monthly_cost': row[3],
                'content_types': row[4]
            })
        
        conn.close()
        
        return jsonify({
            'subscriptions': subscriptions,
            'company_summary': company_summary,
            'total_count': len(subscriptions)
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# @app.route('/debug/sync_subscription/<int:user_id>')
# def debug_sync_subscription(user_id):
#     """指定ユーザーの契約期間情報をStripeから同期（企業ユーザー専用に統一するため削除）"""
#     pass

# @app.route('/debug/cancellation_periods')
# def debug_cancellation_periods():
#     """cancellation_historyテーブルの契約期間情報を確認（企業ユーザー専用に統一するため削除）"""
#     pass
        
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

# @app.route('/debug/update_cancellation_period/<int:user_id>/<content_type>')
# def debug_update_cancellation_period(user_id, content_type):
#     """指定ユーザーの契約期間情報をcancellation_historyに更新（企業ユーザー専用に統一するため削除）"""
#     pass

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

# @app.route('/debug/update_existing_cancellation/<int:user_id>/<content_type>')
# def update_existing_cancellation(user_id, content_type):
#     """既存のcancellation_historyレコードに契約期間情報を更新（企業ユーザー専用に統一するため削除）"""
#     pass

# @app.route('/debug/create_content_period/<int:user_id>/<content_type>')
# def debug_create_content_period(user_id, content_type):
#     """指定ユーザーのコンテンツ追加時に契約期間情報を保存（企業ユーザー専用に統一するため削除）"""
#     pass
        
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

@app.route('/debug/railway')
def debug_railway():
    """Railway環境変数のデバッグ情報"""
    try:
        railway_db_url = os.getenv('RAILWAY_DATABASE_URL')
        railway_token = os.getenv('RAILWAY_TOKEN')
        railway_project_id = os.getenv('RAILWAY_PROJECT_ID')
        
        # データベース接続テスト
        db_connection_success = False
        db_error = None
        if railway_db_url:
            try:
                import psycopg2
                conn = psycopg2.connect(railway_db_url)
                c = conn.cursor()
                c.execute('SELECT COUNT(*) FROM companies')
                count = c.fetchone()[0]
                conn.close()
                db_connection_success = True
            except Exception as e:
                db_error = str(e)
        
        return jsonify({
            'railway_database_url_set': bool(railway_db_url),
            'railway_token_set': bool(railway_token),
            'railway_project_id_set': bool(railway_project_id),
            'database_connection_success': db_connection_success,
            'database_error': db_error,
            'companies_count': count if db_connection_success else None
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        })

@app.route('/debug/update_company_line_user_id_direct/<int:company_id>/<line_user_id>')
def debug_update_company_line_user_id_direct(company_id, line_user_id):
    """デバッグ用：企業データのLINEユーザーIDを直接更新"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 現在の企業データを確認
        c.execute('SELECT id, company_name, line_user_id, stripe_subscription_id FROM companies WHERE id = %s', (company_id,))
        company_result = c.fetchone()
        
        if not company_result:
            return jsonify({'error': f'企業ID {company_id} が見つかりません'})
        
        company_id_db, company_name, current_line_user_id, stripe_subscription_id = company_result
        
        # LINEユーザーIDを更新
        c.execute('UPDATE companies SET line_user_id = %s WHERE id = %s', (line_user_id, company_id))
        conn.commit()
        
        # 更新後の確認
        c.execute('SELECT id, company_name, line_user_id, stripe_subscription_id FROM companies WHERE id = %s', (company_id,))
        updated_company = c.fetchone()
        
        conn.close()
        
        if updated_company:
            return jsonify({
                'success': True,
                'message': f'企業データのLINEユーザーIDを更新しました',
                'company_id': company_id,
                'company_name': updated_company[1],
                'line_user_id': updated_company[2],
                'stripe_subscription_id': updated_company[3]
            })
        else:
            return jsonify({'error': '更新後の確認に失敗しました'})
            
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/debug/company/pricing/<int:company_id>')
def debug_company_pricing(company_id):
    """企業の料金情報を表示"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業基本情報を取得
        c.execute('''
            SELECT company_name, email, status
            FROM companies 
            WHERE id = %s
        ''', (company_id,))
        
        company = c.fetchone()
        if not company:
            return jsonify({'error': '企業が見つかりません'}), 404
        
        # 企業のサブスクリプション情報を取得
        c.execute('''
            SELECT 
                content_type,
                subscription_status,
                base_price,
                additional_price,
                total_price,
                stripe_subscription_id,
                current_period_end
            FROM company_subscriptions 
            WHERE company_id = %s
            ORDER BY created_at DESC
        ''', (company_id,))
        
        subscriptions = []
        total_monthly_cost = 0
        content_types = []
        
        for row in c.fetchall():
            subscriptions.append({
                'content_type': row[0],
                'subscription_status': row[1],
                'base_price': row[2],
                'additional_price': row[3],
                'total_price': row[4],
                'stripe_subscription_id': row[5],
                'current_period_end': row[6]
            })
            total_monthly_cost += row[4]
            content_types.append(row[0])
        
        conn.close()
        
        # 料金計算
        pricing_info = calculate_company_pricing(company_id, content_types)
        
        return jsonify({
            'company': {
                'id': company_id,
                'name': company[0],
                'email': company[1],
                'status': company[2]
            },
            'subscriptions': subscriptions,
            'pricing_summary': {
                'total_monthly_cost': total_monthly_cost,
                'content_count': len(content_types),
                'content_types': content_types,
                'calculated_pricing': pricing_info
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

# 企業ユーザー専用の解約制限チェックAPI
@app.route('/api/v1/company/restriction/check', methods=['POST'])
def check_company_restriction_api():
    """
    企業ユーザーの解約制限チェックAPI
    """
    try:
        data = request.get_json()
        line_channel_id = data.get('line_channel_id')
        content_type = data.get('content_type')
        
        if not line_channel_id or not content_type:
            return jsonify({
                'error': 'line_channel_id と content_type は必須です'
            }), 400
        
        # 企業制限チェックを実行
        from services.company_service import check_company_restriction
        result = check_company_restriction(line_channel_id, content_type)
        
        return jsonify({
            'is_restricted': result['is_restricted'],
            'reason': result['reason'],
            'message': result['message'],
            'content_type': content_type,
            'line_channel_id': line_channel_id
        })
        
    except Exception as e:
        print(f"❌ 企業制限チェックAPIエラー: {e}")
        return jsonify({
            'error': 'システムエラーが発生しました',
            'is_restricted': False  # エラー時は制限しない
        }), 500

# 企業情報取得API
@app.route('/api/v1/company/info/<line_channel_id>', methods=['GET'])
def get_company_info_api(line_channel_id):
    """
    企業情報取得API
    """
    try:
        from services.company_service import get_company_by_line_channel_id, get_company_line_accounts, get_company_subscriptions
        
        # 企業基本情報を取得
        company = get_company_by_line_channel_id(line_channel_id)
        if not company:
            return jsonify({
                'error': '企業情報が見つかりません'
            }), 404
        
        # LINEアカウント情報を取得
        line_accounts = get_company_line_accounts(company['id'])
        
        # サブスクリプション情報を取得
        subscriptions = get_company_subscriptions(company['id'])
        
        return jsonify({
            'company': company,
            'line_accounts': line_accounts,
            'subscriptions': subscriptions
        })
        
    except Exception as e:
        print(f"❌ 企業情報取得APIエラー: {e}")
        return jsonify({
            'error': 'システムエラーが発生しました'
        }), 500

# 企業コンテンツ解約API
@app.route('/api/v1/company/cancel/<int:company_id>/<content_type>', methods=['POST'])
def cancel_company_content_api(company_id, content_type):
    """
    企業コンテンツ解約API
    """
    try:
        from services.company_service import cancel_company_content
        
        result = cancel_company_content(company_id, content_type)
        if not result:
            return jsonify({
                'error': '解約処理に失敗しました'
            }), 500
        
        return jsonify({
            'message': '解約処理が完了しました',
            'result': result
        })
        
    except Exception as e:
        print(f"❌ 企業コンテンツ解約APIエラー: {e}")
        return jsonify({
            'error': 'システムエラーが発生しました'
        }), 500

# 企業制限チェックテスト用API
@app.route('/debug/company/restriction/<line_channel_id>/<content_type>')
def debug_company_restriction(line_channel_id, content_type):
    """
    企業制限チェックのデバッグ用API
    """
    try:
        from services.company_service import check_company_restriction
        
        result = check_company_restriction(line_channel_id, content_type)
        
        return jsonify({
            'line_channel_id': line_channel_id,
            'content_type': content_type,
            'result': result
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    try:
        # データベース初期化をスキップしてアプリケーションを起動
        print("🚀 アプリケーション起動中...")
        
        # デフォルトポートを5001に設定（5000は使用中）
        port = int(os.environ.get('PORT', 5001))
        print(f"📡 ポート {port} で起動します")
        
        # アプリケーションの設定を確認
        print(f"📊 登録されたBlueprint数: {len(app.blueprints)}")
        print(f"📊 テンプレートフォルダ: {app.template_folder}")
        print(f"📊 静的ファイルフォルダ: {app.static_folder}")
        
        app.run(debug=False, host='0.0.0.0', port=port)
    except Exception as e:
        print(f"❌ アプリケーション起動エラー: {e}")
        import traceback
        traceback.print_exc() 