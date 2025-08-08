#!/usr/bin/env python3
"""
シンプルな企業ユーザー専用アプリケーション
- 2週間無料 → 3,900円
- コンテンツ追加は翌月課金
- 無料期間中の解約は料金発生なし
"""

import os
import sys
from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv
import psycopg2
from datetime import datetime, timedelta
import stripe
import json

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

load_dotenv()

app = Flask(__name__)

# Stripe設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
BASE_PRICE_ID = os.getenv('STRIPE_BASE_PRICE_ID', 'price_base_3900')
CONTENT_ADDITION_PRICE_ID = os.getenv('STRIPE_CONTENT_ADDITION_PRICE_ID', 'price_content_1500')
TRIAL_PERIOD_DAYS = 14  # 2週間無料

def get_db_connection():
    """データベース接続を取得"""
    try:
        import os
        database_url = os.getenv('RAILWAY_DATABASE_URL') or os.getenv('DATABASE_URL')
        if not database_url:
            raise RuntimeError('DATABASE_URL/RAILWAY_DATABASE_URL is not set')
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        print(f"データベース接続エラー: {e}")
        return None

def init_db():
    """データベースの初期化（シンプル版）"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        c = conn.cursor()
        
        # 企業テーブル
        c.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id SERIAL PRIMARY KEY,
                company_name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                stripe_customer_id VARCHAR(255),
                stripe_subscription_id VARCHAR(255),
                trial_end TIMESTAMP,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # コンテンツサブスクリプションテーブル
        c.execute('''
            CREATE TABLE IF NOT EXISTS company_content_subscriptions (
                id SERIAL PRIMARY KEY,
                company_id INTEGER NOT NULL,
                content_type VARCHAR(100) NOT NULL,
                stripe_subscription_item_id VARCHAR(255),
                stripe_price_id VARCHAR(255),
                status VARCHAR(50) DEFAULT 'active',
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                next_billing_date TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id),
                UNIQUE(company_id, content_type)
            )
        ''')
        
        # 状態管理テーブル
        c.execute('''
            CREATE TABLE IF NOT EXISTS company_status_logs (
                id SERIAL PRIMARY KEY,
                company_id INTEGER NOT NULL,
                action_type VARCHAR(50) NOT NULL,
                content_type VARCHAR(100),
                details JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        ''')
        
        # インデックスの作成
        c.execute('CREATE INDEX IF NOT EXISTS idx_companies_email ON companies(email)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_companies_trial_end ON companies(trial_end)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_content_subscriptions_company_id ON company_content_subscriptions(company_id)')
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"データベース初期化エラー: {e}")
        return False
    finally:
        conn.close()

def log_company_action(company_id, action_type, content_type=None, details=None):
    """企業アクションをログに記録"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        c = conn.cursor()
        c.execute('''
            INSERT INTO company_status_logs (company_id, action_type, content_type, details)
            VALUES (%s, %s, %s, %s)
        ''', (company_id, action_type, content_type, json.dumps(details) if details else None))
        conn.commit()
    except Exception as e:
        print(f"ログ記録エラー: {e}")
    finally:
        conn.close()

def create_stripe_customer_and_subscription(company_name, email):
    """StripeでCustomerとSubscriptionを作成"""
    try:
        # Customer作成
        customer = stripe.Customer.create(
            name=company_name,
            email=email
        )
        
        # 無料期間終了日を計算
        trial_end = datetime.now() + timedelta(days=TRIAL_PERIOD_DAYS)
        trial_end_timestamp = int(trial_end.timestamp())
        
        # Subscription作成（2週間無料）
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': BASE_PRICE_ID}],
            trial_end=trial_end_timestamp,
            payment_behavior='default_incomplete',
            expand=['latest_invoice.payment_intent']
        )
        
        return {
            'customer_id': customer.id,
            'subscription_id': subscription.id,
            'trial_end': trial_end
        }
    except Exception as e:
        print(f"Stripe作成エラー: {e}")
        return None

def register_company(company_name, email):
    """企業登録処理"""
    conn = get_db_connection()
    if not conn:
        return {'error': 'database_connection_error'}
    
    try:
        c = conn.cursor()
        
        # 既存企業チェック
        c.execute('SELECT id FROM companies WHERE email = %s', (email,))
        existing = c.fetchone()
        if existing:
            return {'error': 'company_already_exists'}
        
        # StripeでCustomerとSubscription作成
        stripe_result = create_stripe_customer_and_subscription(company_name, email)
        if not stripe_result:
            return {'error': 'stripe_creation_failed'}
        
        # 企業情報をDBに保存
        c.execute('''
            INSERT INTO companies (company_name, email, stripe_customer_id, stripe_subscription_id, trial_end)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        ''', (company_name, email, stripe_result['customer_id'], stripe_result['subscription_id'], stripe_result['trial_end']))
        
        company_id = c.fetchone()[0]
        
        # デフォルトコンテンツ（AI予定秘書）を追加
        c.execute('''
            INSERT INTO company_content_subscriptions (company_id, content_type, stripe_price_id)
            VALUES (%s, %s, %s)
        ''', (company_id, 'AI予定秘書', BASE_PRICE_ID))
        
        conn.commit()
        
        # ログ記録
        log_company_action(company_id, 'register', details={
            'company_name': company_name,
            'email': email,
            'stripe_customer_id': stripe_result['customer_id'],
            'stripe_subscription_id': stripe_result['subscription_id']
        })
        
        return {
            'company_id': company_id,
            'stripe_customer_id': stripe_result['customer_id'],
            'stripe_subscription_id': stripe_result['subscription_id'],
            'trial_end': stripe_result['trial_end'].isoformat(),
            'status': 'active',
            'message': '2週間無料でご利用いただけます'
        }
        
    except Exception as e:
        print(f"企業登録エラー: {e}")
        conn.rollback()
        return {'error': str(e)}
    finally:
        conn.close()

def add_content_to_company(company_id, content_type):
    """企業にコンテンツを追加（翌月課金）"""
    conn = get_db_connection()
    if not conn:
        return {'error': 'database_connection_error'}
    
    try:
        c = conn.cursor()
        
        # 企業情報を取得
        c.execute('SELECT stripe_subscription_id, trial_end FROM companies WHERE id = %s', (company_id,))
        company = c.fetchone()
        if not company:
            return {'error': 'company_not_found'}
        
        stripe_subscription_id, trial_end = company
        
        # 既存コンテンツチェック
        c.execute('SELECT id FROM company_content_subscriptions WHERE company_id = %s AND content_type = %s', (company_id, content_type))
        existing = c.fetchone()
        if existing:
            return {'error': 'content_already_exists'}
        
        # 次回課金日を計算（翌月の1日）
        next_billing_date = datetime.now().replace(day=1) + timedelta(days=32)
        next_billing_date = next_billing_date.replace(day=1)
        
        # StripeでSubscription Itemを追加（翌月から課金）
        try:
            subscription_item = stripe.SubscriptionItem.create(
                subscription=stripe_subscription_id,
                price=CONTENT_ADDITION_PRICE_ID,
                proration_behavior='none'  # 即座に課金しない
            )
            
            # DBに保存
            c.execute('''
                INSERT INTO company_content_subscriptions 
                (company_id, content_type, stripe_subscription_item_id, stripe_price_id, next_billing_date)
                VALUES (%s, %s, %s, %s, %s)
            ''', (company_id, content_type, subscription_item.id, CONTENT_ADDITION_PRICE_ID, next_billing_date))
            
            conn.commit()
            
            # ログ記録
            log_company_action(company_id, 'add_content', content_type, {
                'stripe_subscription_item_id': subscription_item.id,
                'next_billing_date': next_billing_date.isoformat()
            })
            
            return {
                'company_id': company_id,
                'content_type': content_type,
                'stripe_subscription_item_id': subscription_item.id,
                'next_billing_date': next_billing_date.isoformat(),
                'status': 'active',
                'message': '翌月の請求サイクルから1,500円が追加されます'
            }
            
        except Exception as e:
            print(f"Stripe Subscription Item作成エラー: {e}")
            return {'error': 'stripe_subscription_item_creation_failed'}
        
    except Exception as e:
        print(f"コンテンツ追加エラー: {e}")
        conn.rollback()
        return {'error': str(e)}
    finally:
        conn.close()

def get_company_status(company_id):
    """企業の状態を取得"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        c = conn.cursor()
        
        # 企業基本情報を取得
        c.execute('''
            SELECT id, company_name, email, stripe_customer_id, stripe_subscription_id, 
                   trial_end, status, created_at
            FROM companies WHERE id = %s
        ''', (company_id,))
        
        company = c.fetchone()
        if not company:
            return None
        
        company_id, company_name, email, stripe_customer_id, stripe_subscription_id, trial_end, status, created_at = company
        
        # 無料期間の確認
        is_trial_active = False
        trial_days_remaining = 0
        if trial_end:
            now = datetime.now()
            if trial_end > now:
                is_trial_active = True
                trial_days_remaining = (trial_end - now).days
        
        # コンテンツサブスクリプションを取得
        c.execute('''
            SELECT content_type, status, added_at, next_billing_date
            FROM company_content_subscriptions 
            WHERE company_id = %s
            ORDER BY added_at
        ''', (company_id,))
        
        subscriptions = []
        for row in c.fetchall():
            content_type, sub_status, added_at, next_billing_date = row
            subscriptions.append({
                'content_type': content_type,
                'status': sub_status,
                'added_at': added_at.isoformat() if added_at else None,
                'next_billing_date': next_billing_date.isoformat() if next_billing_date else None
            })
        
        # 請求情報を計算
        current_monthly_fee = 0
        next_monthly_fee = 3900  # 基本料金
        
        if not is_trial_active:
            current_monthly_fee = 3900
        
        # 追加コンテンツの料金を計算
        additional_contents = [s for s in subscriptions if s['content_type'] != 'AI予定秘書']
        next_monthly_fee += len(additional_contents) * 1500
        
        return {
            'company': {
                'id': company_id,
                'company_name': company_name,
                'email': email,
                'stripe_customer_id': stripe_customer_id,
                'stripe_subscription_id': stripe_subscription_id,
                'status': status,
                'trial_end': trial_end.isoformat() if trial_end else None,
                'is_trial_active': is_trial_active,
                'created_at': created_at.isoformat() if created_at else None
            },
            'subscriptions': subscriptions,
            'billing_info': {
                'current_monthly_fee': current_monthly_fee,
                'next_monthly_fee': next_monthly_fee,
                'trial_days_remaining': trial_days_remaining
            }
        }
        
    except Exception as e:
        print(f"企業状態取得エラー: {e}")
        return None
    finally:
        conn.close()

def check_company_restriction(company_id, content_type):
    """企業の解約制限チェック"""
    conn = get_db_connection()
    if not conn:
        return {'is_restricted': True, 'reason': 'database_connection_error'}
    
    try:
        c = conn.cursor()
        
        # 企業情報を取得
        c.execute('''
            SELECT status, trial_end FROM companies WHERE id = %s
        ''', (company_id,))
        
        company = c.fetchone()
        if not company:
            return {'is_restricted': True, 'reason': 'company_not_found'}
        
        status, trial_end = company
        
        # 企業ステータスチェック
        if status != 'active':
            return {'is_restricted': True, 'reason': 'company_inactive'}
        
        # コンテンツ契約チェック
        c.execute('''
            SELECT status FROM company_content_subscriptions 
            WHERE company_id = %s AND content_type = %s
        ''', (company_id, content_type))
        
        subscription = c.fetchone()
        if not subscription:
            return {'is_restricted': True, 'reason': 'content_not_subscribed'}
        
        if subscription[0] != 'active':
            return {'is_restricted': True, 'reason': 'content_inactive'}
        
        # 無料期間チェック
        is_trial_active = False
        trial_days_remaining = 0
        if trial_end:
            now = datetime.now()
            if trial_end > now:
                is_trial_active = True
                trial_days_remaining = (trial_end - now).days
        
        return {
            'is_restricted': False,
            'reason': 'access_granted',
            'company_id': company_id,
            'content_type': content_type,
            'is_trial_active': is_trial_active,
            'trial_days_remaining': trial_days_remaining
        }
        
    except Exception as e:
        print(f"解約制限チェックエラー: {e}")
        return {'is_restricted': True, 'reason': 'check_error'}
    finally:
        conn.close()

# ルート定義

@app.route('/')
def index():
    """メインページ"""
    return render_template('index_simple.html')

@app.route('/health')
def health_check():
    """ヘルスチェック"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/v1/company/register', methods=['POST'])
def register_company_api():
    """企業登録API"""
    try:
        data = request.get_json()
        company_name = data.get('company_name')
        email = data.get('email')
        
        if not company_name or not email:
            return jsonify({'error': 'company_name and email are required'}), 400
        
        result = register_company(company_name, email)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/company/<int:company_id>/content/add', methods=['POST'])
def add_content_api(company_id):
    """コンテンツ追加API"""
    try:
        data = request.get_json()
        content_type = data.get('content_type')
        
        if not content_type:
            return jsonify({'error': 'content_type is required'}), 400
        
        result = add_content_to_company(company_id, content_type)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/company/<int:company_id>/status', methods=['GET'])
def get_company_status_api(company_id):
    """企業状態取得API"""
    try:
        result = get_company_status(company_id)
        
        if not result:
            return jsonify({'error': 'company_not_found'}), 404
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/company/restriction/check', methods=['POST'])
def check_company_restriction_api():
    """企業解約制限チェックAPI"""
    try:
        data = request.get_json()
        company_id = data.get('company_id')
        content_type = data.get('content_type')
        
        if not company_id or not content_type:
            return jsonify({'error': 'company_id and content_type are required'}), 400
        
        result = check_company_restriction(company_id, content_type)
        
        # 日本語メッセージの設定
        messages = {
            'access_granted': '利用可能です',
            'company_not_found': '企業情報が見つかりません',
            'company_inactive': '企業が無効です',
            'content_not_subscribed': 'このコンテンツは契約されていません',
            'content_inactive': 'このコンテンツは無効です',
            'database_connection_error': 'データベース接続エラー',
            'check_error': 'チェック処理でエラーが発生しました'
        }
        
        response = {
            'is_restricted': result['is_restricted'],
            'reason': result['reason'],
            'message': messages.get(result['reason'], '不明なエラー'),
            'company_id': result.get('company_id'),
            'content_type': result.get('content_type')
        }
        
        if result.get('is_trial_active'):
            response['message'] += f"（無料期間中、残り{result.get('trial_days_remaining', 0)}日）"
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/debug/company/<int:company_id>')
def debug_company(company_id):
    """企業デバッグページ"""
    company_status = get_company_status(company_id)
    return render_template('debug_company.html', company_status=company_status)

if __name__ == '__main__':
    # データベース初期化
    if init_db():
        print("データベース初期化完了")
    else:
        print("データベース初期化エラー")
    
    # アプリケーション起動
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 