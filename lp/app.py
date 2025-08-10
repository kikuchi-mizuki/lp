import os
import sys
import logging

# Add the current directory to Python path for production deployment
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from flask import Flask, render_template, request, redirect, url_for, jsonify
import stripe
from dotenv import load_dotenv
from utils.db import get_db_connection
from services.spreadsheet_content_service import spreadsheet_content_service

load_dotenv()

# ロガーの設定
logger = logging.getLogger(__name__)

# Stripe設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
MONTHLY_PRICE_ID = os.getenv('STRIPE_MONTHLY_PRICE_ID')

# Flaskアプリケーションの作成
app = Flask(__name__)

# アプリケーション初期化
logger.info("🚀 アプリケーション起動中...")

# Blueprintの登録
try:
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
    from routes.ai_schedule_webhook import ai_schedule_webhook_bp
    from routes.ai_schedule_webhook_simple import ai_schedule_webhook_simple_bp
    from routes.debug import debug_bp

    # Blueprint登録（デバッグ系はENVで有効化）
    blueprints = [
        (line_bp, 'line'),
        (stripe_bp, 'stripe'),
        (company_bp, 'company'),
        (line_api_bp, 'line_api'),
        (stripe_payment_bp, 'stripe_payment'),
        (content_management_bp, 'content_management'),
        (cancellation_bp, 'cancellation'),
        (notification_bp, 'notification'),
        (scheduler_bp, 'scheduler'),
        (backup_bp, 'backup'),
        (dashboard_bp, 'dashboard'),
        (monitoring_bp, 'monitoring'),
        (reminder_bp, 'reminder'),
        (security_bp, 'security'),
        (dashboard_ui_bp, 'dashboard_ui'),
        (automation_bp, 'automation'),
        (company_line_accounts_bp, 'company_line_accounts'),
        (company_registration_bp, 'company_registration'),
        (ai_schedule_webhook_bp, 'ai_schedule_webhook'),
        (ai_schedule_webhook_simple_bp, 'ai_schedule_webhook_simple'),
    ]

    # デバッグ系Blueprintは明示的に有効化された場合のみ登録
    if os.getenv('ENABLE_DEBUG_ROUTES', '0') in ('1', 'true', 'TRUE', 'True'):
        blueprints.append((debug_bp, 'debug'))

    for blueprint, name in blueprints:
        try:
            app.register_blueprint(blueprint)
            logger.info(f"✅ Blueprint '{name}' を登録しました")
        except Exception as e:
            logger.error(f"❌ Blueprint '{name}' の登録に失敗: {e}")
except Exception as e:
    logger.error(f"❌ Blueprint登録エラー: {e}")

# データベース初期化
try:
    from app_database import init_db
    init_db()
    logger.info("✅ データベース初期化完了")
except Exception as e:
    logger.error(f"❌ データベース初期化エラー: {e}")

# 基本的なルート
@app.route('/')
def root_redirect_to_main():
    """LPをルートで表示（/mainに統一）"""
    return redirect('/main')

@app.route('/main')
def index():
    """メインページ（スプレッドシートのコンテンツを動的表示）"""
    try:
        result = spreadsheet_content_service.get_available_contents()
        contents = result.get('contents', {})
        return render_template('index.html', contents=contents)
    except Exception:
        # 失敗時でもテンプレートは表示
        return render_template('index.html', contents={})

@app.route('/index')
def redirect_to_main():
    """/index から /main にリダイレクト"""
    return redirect('/main')

@app.route('/ping')
def ping():
    """最もシンプルなヘルスチェックエンドポイント"""
    return "pong", 200

@app.route('/health')
def health_check():
    """ヘルスチェックエンドポイント"""
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': '2024-01-01T00:00:00Z'
        })
    except Exception as e:
        return jsonify({
            'status': 'degraded',
            'database': 'error',
            'error': str(e),
            'timestamp': '2024-01-01T00:00:00Z'
        }), 503

@app.route('/health-simple')
def simple_health_check():
    """シンプルなヘルスチェック"""
    return "OK", 200

@app.route('/static/<path:filename>')
def static_files(filename):
    """静的ファイルの配信"""
    return app.send_static_file(filename)

# 企業登録関連のルート
@app.route('/company-registration', methods=['GET', 'POST'])
def company_registration():
    """企業ユーザー専用の決済フォーム"""
    if request.method == 'GET':
        return render_template('company_registration.html')
    
    # POST処理（決済フォーム送信）
    if request.is_json:
        # LPからの直接送信（JSON形式）
        data = request.get_json()
        company_name = data.get('company_name')
        email = data.get('email')
        content_type = data.get('content_type', 'AI予定秘書')
    else:
        # フォームからの送信
        company_name = request.form.get('company_name')
        email = request.form.get('email')
        content_type = request.form.get('content_type', 'AI予定秘書')
    
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
    
    # Stripeチェックアウトセッションを作成（2週間無料トライアル）
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': MONTHLY_PRICE_ID,
                'quantity': 1,
            }],
            mode='subscription',
            subscription_data={
                'trial_period_days': 14,  # 2週間無料トライアル
            },
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
        logger.error(f"❌ Stripeチェックアウトセッション作成エラー: {e}")
        return jsonify({'error': '決済セッションの作成に失敗しました'}), 500

@app.route('/company-registration-success')
def company_registration_success():
    """企業登録成功時の処理"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        logger.error("❌ セッションIDがありません")
        return render_template('company_registration_cancel.html')
    
    try:
        # Stripeセッション情報を取得
        session = stripe.checkout.Session.retrieve(session_id)
        metadata = session.get('metadata', {})
        
        company_name = metadata.get('company_name')
        email = metadata.get('email')
        content_type = metadata.get('content_type', 'AI予定秘書')
        subscription_id = session.get('subscription')
        
        if company_name and email and subscription_id:
            # 企業プロファイルを作成・更新
            from app_company_registration import upsert_company_profile_with_subscription
            company_id = upsert_company_profile_with_subscription(
                company_name, email, subscription_id
            )

            logger.info(f"✅ 企業登録完了: {company_id}")

            # 決済完了→LINE遷移時の自動案内メッセージ送信
            # 元々LINE登録していた人も、決済完了時に必ず案内メッセージを送信
            try:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT line_user_id FROM companies WHERE id = %s', (company_id,))
                row = c.fetchone()
                conn.close()

                if row and row[0]:
                    # 既にLINE登録済みの場合：即座に案内メッセージを送信
                    line_user_id = row[0]
                    try:
                        # 企業向けのウェルカム案内（詳細テキスト + メニューボタン）を自動送信
                        from services.line_service import send_company_welcome_message
                        sent = send_company_welcome_message(line_user_id, company_name, email)
                        if sent:
                            logger.info(f"✅ 決済完了後の自動案内メッセージ送信成功（既存LINE）: company_id={company_id}, line_user_id={line_user_id}")
                        else:
                            logger.warning(f"⚠️ 決済完了後の自動案内メッセージ送信失敗（既存LINE）: company_id={company_id}")
                    except Exception as e:
                        logger.error(f"❌ 自動案内メッセージ送信エラー（既存LINE）: {e}")
                else:
                    # LINE未登録の場合：フォロー時の自動送信に委譲
                    logger.info(
                        f"ℹ️ LINE未登録のため、フォロー時の自動送信に委譲: company_id={company_id}, email={email}"
                    )
            except Exception as e:
                logger.error(f"❌ 自動案内メッセージ事前チェックエラー: {e}")

            # テンプレートに渡すデータを整形
            company_data = {
                'company_name': company_name,
                'email': email,
                'content_type': content_type,
            }

            # 次回請求日の取得（トライアル中はtrial_end、以降はcurrent_period_end）
            next_billing_date = None
            try:
                if subscription_id:
                    subscription = stripe.Subscription.retrieve(subscription_id)
                    import datetime as _dt
                    status = subscription.get('status')
                    epoch = None
                    if status == 'trialing':
                        epoch = subscription.get('trial_end') or subscription.get('current_period_end')
                    else:
                        epoch = subscription.get('current_period_end')
                    if epoch:
                        # JST表示（+9時間）
                        dt_utc = _dt.datetime.utcfromtimestamp(int(epoch))
                        next_billing_date = (dt_utc + _dt.timedelta(hours=9)).strftime('%Y-%m-%d')
            except Exception:
                next_billing_date = None

            return render_template(
                'company_registration_success.html',
                company_data=company_data,
                next_billing_date=next_billing_date,
                liff_id=os.getenv('LINE_LIFF_ID')
            )
        else:
            logger.error("❌ 必要な情報が不足しています")
            return render_template('company_registration_cancel.html')
    except Exception as e:
        logger.error(f"❌ 企業登録成功処理エラー: {e}")
        return render_template('company_registration_cancel.html')

@app.route('/company-registration-cancel')
def company_registration_cancel():
    """企業登録キャンセル時の処理"""
    return render_template('company_registration_cancel.html')

# Stripe Webhook処理
@app.route('/webhook/stripe/company', methods=['POST'])
def stripe_webhook_company():
    """Stripe Webhook処理"""
    try:
        payload = request.get_data()
        signature = request.headers.get('Stripe-Signature')
        
        # 署名の検証
        from app_stripe_webhook import verify_stripe_webhook_signature, process_stripe_webhook
        
        if not verify_stripe_webhook_signature(payload, signature):
            logger.error("❌ Webhook署名検証失敗")
            return jsonify({'error': 'Invalid signature'}), 400
        
        # イベントの処理
        event = stripe.Webhook.construct_event(payload, signature, os.getenv('STRIPE_WEBHOOK_SECRET'))
        
        if process_stripe_webhook(event):
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Webhook processing failed'}), 500
        
    except Exception as e:
        logger.error(f"❌ Webhook処理エラー: {e}")
        return jsonify({'error': str(e)}), 500

# デバッグ関連のルート
@app.route('/debug/db')
def debug_database():
    """データベースデバッグ"""
    from app_debug import debug_database
    result = debug_database()
    return jsonify(result)

@app.route('/debug/companies')
def debug_companies():
    """企業デバッグ"""
    from app_debug import debug_companies
    result = debug_companies()
    return jsonify(result)

@app.route('/debug/webhook_status')
def debug_webhook_status():
    """Webhook設定デバッグ"""
    from app_debug import debug_webhook_status
    result = debug_webhook_status()
    return jsonify(result)

@app.route('/debug/railway')
def debug_railway():
    """Railway環境デバッグ"""
    from app_debug import debug_railway
    result = debug_railway()
    return jsonify(result)

# スプレッドシート連携のデバッグ
@app.route('/debug/spreadsheet')
def debug_spreadsheet():
    """スプレッドシートからの取得状況を確認（環境変数未設定時はフォールバックを返す）"""
    result = spreadsheet_content_service.get_available_contents(force_refresh=True)
    return jsonify(result)

# システム総合チェック（自動）
@app.route('/debug/system-check')
def system_check():
    """主要機能の自己診断を一括実行"""
    try:
        # DB
        db_ok = False
        try:
            conn = get_db_connection()
            conn.close()
            db_ok = True
        except Exception:
            db_ok = False

        # Webhook/ENV
        from app_debug import debug_webhook_status as dbg_webhook
        from app_debug import debug_railway as dbg_railway
        
        return jsonify({
            'success': True,
            'db': 'ok' if db_ok else 'error',
            'spreadsheet': spreadsheet_content_service.get_available_contents(force_refresh=True),
            'webhooks': dbg_webhook(),
            'railway': dbg_railway(),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# スプレッドシートの認証情報（サービスアカウント）確認
@app.route('/debug/spreadsheet-identity')
def spreadsheet_identity():
    """サービスアカウントのメールなど、共有設定に必要な情報を表示"""
    try:
        import json
        import os
        client_email = None
        creds_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        if os.path.exists(creds_file):
            with open(creds_file, 'r') as f:
                data = json.load(f)
                client_email = data.get('client_email')
        else:
            creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if creds_json:
                data = json.loads(creds_json)
                client_email = data.get('client_email')

        return jsonify({
            'success': True,
            'service_account_email': client_email or 'Not found',
            'spreadsheet_id': os.getenv('CONTENT_SPREADSHEET_ID'),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/debug/company/pricing/<int:company_id>')
def debug_company_pricing(company_id):
    """企業料金デバッグ"""
    from app_debug import debug_company_pricing
    result = debug_company_pricing(company_id)
    return jsonify(result)

# スプレッドシート生データ確認（構造/権限の切り分け用）
@app.route('/debug/spreadsheet/raw')
def spreadsheet_raw():
    try:
        import json
        import os
        spreadsheet_id = os.getenv('CONTENT_SPREADSHEET_ID')
        client = spreadsheet_content_service._get_google_sheets_client()
        if not client:
            return jsonify({'success': False, 'error': 'Google Sheets client is None (auth or API disabled)'}), 500

        ss = client.open_by_key(spreadsheet_id)
        worksheets = [ws.title for ws in ss.worksheets()]
        ws = ss.get_worksheet(0)
        all_values = ws.get_all_values()
        sample = all_values[:5] if all_values else []
        return jsonify({
            'success': True,
            'worksheets': worksheets,
            'rows': len(all_values),
            'sample_first_5_rows': sample
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API関連のルート
@app.route('/api/v1/company/restriction/check', methods=['POST'])
def check_company_restriction_api():
    """企業制限チェックAPI"""
    from app_api import check_company_restriction_api
    return check_company_restriction_api()

@app.route('/api/v1/company/info/<line_channel_id>', methods=['GET'])
def get_company_info_api(line_channel_id):
    """企業情報取得API"""
    from app_api import get_company_info_api
    return get_company_info_api(line_channel_id)

@app.route('/api/v1/company/cancel/<int:company_id>/<content_type>', methods=['POST'])
def cancel_company_content_api(company_id, content_type):
    """企業コンテンツ解約API"""
    from app_api import cancel_company_content_api
    return cancel_company_content_api(company_id, content_type)

@app.route('/debug/fix_database_schema')
def fix_database_schema():
    """データベーススキーマ修正エンドポイント"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        print("データベーススキーマ修正開始...")
        
        # 現在のスキーマを確認
        print("現在のスキーマを確認中...")
        c.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'companies' 
            ORDER BY ordinal_position
        """)
        company_columns = c.fetchall()
        print(f"companiesテーブルのカラム: {company_columns}")
        
        # user_statesテーブルの修正
        print("user_statesテーブルを修正中...")
        
        # 既存のテーブルを削除
        c.execute("DROP TABLE IF EXISTS user_states")
        
        # 新しいスキーマでテーブルを作成
        c.execute('''
            CREATE TABLE user_states (
                id SERIAL PRIMARY KEY,
                line_user_id VARCHAR(255) UNIQUE,
                state VARCHAR(100) DEFAULT 'initial',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # companiesテーブルの修正
        print("companiesテーブルを修正中...")
        
        # 必要なカラムを追加
        required_columns = [
            ('line_user_id', 'VARCHAR(255)'),
            ('subscription_status', 'VARCHAR(50)'),
            ('current_period_start', 'TIMESTAMP'),
            ('current_period_end', 'TIMESTAMP'),
            ('trial_end', 'TIMESTAMP')
        ]
        
        existing_columns = [col[0] for col in company_columns]
        
        for col_name, col_type in required_columns:
            if col_name not in existing_columns:
                print(f"カラム {col_name} を追加中...")
                c.execute(f"ALTER TABLE companies ADD COLUMN {col_name} {col_type}")
        
        # テストデータを作成
        print("テストデータを作成中...")
        
        # 既存のデータを削除（外部キー制約を考慮）
        print("既存データを削除中...")
        
        # まず関連テーブルのデータを削除
        c.execute("DELETE FROM company_subscriptions WHERE company_id IN (SELECT id FROM companies WHERE line_user_id = %s)", ('U1b9d0d75b0c770dc1107dde349d572f7',))
        c.execute("DELETE FROM company_monthly_subscriptions WHERE company_id IN (SELECT id FROM companies WHERE line_user_id = %s)", ('U1b9d0d75b0c770dc1107dde349d572f7',))
        c.execute("DELETE FROM usage_logs WHERE company_id IN (SELECT id FROM companies WHERE line_user_id = %s)", ('U1b9d0d75b0c770dc1107dde349d572f7',))
        c.execute("DELETE FROM company_line_accounts WHERE company_id IN (SELECT id FROM companies WHERE line_user_id = %s)", ('U1b9d0d75b0c770dc1107dde349d572f7',))
        c.execute("DELETE FROM company_content_additions WHERE company_id IN (SELECT id FROM companies WHERE line_user_id = %s)", ('U1b9d0d75b0c770dc1107dde349d572f7',))
        c.execute("DELETE FROM company_contents WHERE company_id IN (SELECT id FROM companies WHERE line_user_id = %s)", ('U1b9d0d75b0c770dc1107dde349d572f7',))
        c.execute("DELETE FROM company_cancellations WHERE company_id IN (SELECT id FROM companies WHERE line_user_id = %s)", ('U1b9d0d75b0c770dc1107dde349d572f7',))
        c.execute("DELETE FROM company_notifications WHERE company_id IN (SELECT id FROM companies WHERE line_user_id = %s)", ('U1b9d0d75b0c770dc1107dde349d572f7',))
        c.execute("DELETE FROM company_payments WHERE company_id IN (SELECT id FROM companies WHERE line_user_id = %s)", ('U1b9d0d75b0c770dc1107dde349d572f7',))
        
        # 最後にcompaniesテーブルのデータを削除
        c.execute("DELETE FROM companies WHERE line_user_id = %s", ('U1b9d0d75b0c770dc1107dde349d572f7',))
        
        # 企業データ（UPSERTではなくINSERT）- 日本時間で設定
        c.execute('''
            INSERT INTO companies (company_name, email, line_user_id, stripe_subscription_id, subscription_status, current_period_start, current_period_end, trial_end, company_code) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            'サンプル株式会社',
            'sample@example.com',
            'U1b9d0d75b0c770dc1107dde349d572f7',
            'sub_1RuM84Ixg6C5hAVdp1EIGCrm',
            'trialing',
            '2025-08-23 00:00:00',  # 日本時間
            '2025-09-22 23:59:59',  # 日本時間
            '2025-09-22 23:59:59',  # 日本時間
            'SAMPLE001'
        ))
        
        # 企業IDを取得
        company_id = c.lastrowid if hasattr(c, 'lastrowid') else None
        if not company_id:
            c.execute("SELECT id FROM companies WHERE line_user_id = %s", ('U1b9d0d75b0c770dc1107dde349d572f7',))
            company_id = c.fetchone()[0]
        
        # company_monthly_subscriptionsテーブルのスキーマを確認
        c.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'company_monthly_subscriptions' 
            ORDER BY ordinal_position
        """)
        monthly_subscription_columns = c.fetchall()
        print(f"company_monthly_subscriptionsテーブルのカラム: {monthly_subscription_columns}")
        
        # 存在するカラムのみを使用してデータを挿入
        available_columns = [col[0] for col in monthly_subscription_columns]
        
        if 'company_id' in available_columns and 'stripe_subscription_id' in available_columns:
            # 基本的なカラムのみを使用（trial_endは除外）
            if 'current_period_start' in available_columns and 'current_period_end' in available_columns:
                c.execute('''
                    INSERT INTO company_monthly_subscriptions (company_id, stripe_subscription_id, subscription_status, monthly_base_price, current_period_start, current_period_end) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    company_id,
                    'sub_1RuM84Ixg6C5hAVdp1EIGCrm',
                    'trialing',
                    3900,
                    '2025-08-23 00:00:00',  # 日本時間
                    '2025-09-22 23:59:59'   # 日本時間
                ))
            else:
                # 期間カラムがない場合は基本的なカラムのみ
                c.execute('''
                    INSERT INTO company_monthly_subscriptions (company_id, stripe_subscription_id, subscription_status, monthly_base_price) 
                    VALUES (%s, %s, %s, %s)
                ''', (
                    company_id,
                    'sub_1RuM84Ixg6C5hAVdp1EIGCrm',
                    'trialing',
                    3900
                ))
        else:
            print("company_monthly_subscriptionsテーブルに必要なカラムが存在しません")
        
        # ユーザー状態データ
        c.execute("DELETE FROM user_states WHERE line_user_id = %s", ('U1b9d0d75b0c770dc1107dde349d572f7',))
        c.execute('''
            INSERT INTO user_states (line_user_id, state) 
            VALUES (%s, %s)
        ''', ('U1b9d0d75b0c770dc1107dde349d572f7', 'welcome_sent'))
        
        conn.commit()
        
        # 確認クエリ
        c.execute("SELECT * FROM user_states")
        user_states = c.fetchall()
        
        c.execute("SELECT * FROM companies")
        companies = c.fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'データベーススキーマ修正完了',
            'user_states_count': len(user_states),
            'companies_count': len(companies),
            'company_columns': company_columns
        })
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/debug/fix_stripe_subscription')
def fix_stripe_subscription():
    """Stripeサブスクリプション修正エンドポイント"""
    try:
        import stripe
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
        # テスト用のサブスクリプションID
        subscription_id = 'sub_1RuM84Ixg6C5hAVdp1EIGCrm'
        
        print(f"Stripeサブスクリプション修正開始: {subscription_id}")
        
        # サブスクリプションを取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        print(f"現在のサブスクリプション: {subscription.id}")
        print(f"現在の期間: {subscription.current_period_start} - {subscription.current_period_end}")
        
        # 日本時間で正確な期間を設定（2025年8月23日から9月22日）
        # 日本時間 2025-08-23 00:00:00 から 2025-09-22 23:59:59
        correct_start = 1755907200  # 日本時間 2025-08-23 00:00:00
        correct_end = 1758412799    # 日本時間 2025-09-22 23:59:59
        
        # サブスクリプションの期間を更新（billing_cycle_anchorは使用しない）
        # 既存のサブスクリプションの期間は変更せず、追加料金アイテムのみ作成
        print(f"既存のサブスクリプション期間を維持: {subscription.current_period_start} - {subscription.current_period_end}")
        
        print(f"既存のサブスクリプション: {subscription.id}")
        print(f"既存の期間: {subscription.current_period_start} - {subscription.current_period_end}")
        
        # 追加料金アイテムを作成
        try:
            # 追加料金用の価格を作成
            additional_price = stripe.Price.create(
                unit_amount=1500,
                currency='jpy',
                recurring={'interval': 'month'},
                product_data={'name': 'コンテンツ追加料金'},
                nickname='追加コンテンツ料金'
            )
            print(f"追加料金価格作成: {additional_price.id}")
            
            # サブスクリプションに追加料金アイテムを追加
            additional_item = stripe.SubscriptionItem.create(
                subscription=subscription_id,
                price=additional_price.id,
                quantity=1  # 1つのコンテンツを追加
            )
            print(f"追加料金アイテム作成: {additional_item.id}")
            
        except Exception as e:
            print(f"追加料金アイテム作成エラー: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Stripeサブスクリプション修正完了',
            'subscription_id': subscription_id,
            'period_start': subscription.current_period_start,
            'period_end': subscription.current_period_end
        })
        
    except Exception as e:
        print(f"Stripeサブスクリプション修正エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/debug/fix_trial_period')
def fix_trial_period():
    """トライアル期間を2週間（14日間）に修正"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 現在のトライアル期間設定を確認
        c.execute('SELECT id, company_name, trial_end FROM companies WHERE trial_end IS NOT NULL')
        companies = c.fetchall()
        
        from datetime import datetime, timezone, timedelta
        jst = timezone(timedelta(hours=9))
        current_time = datetime.now(jst)
        
        # 2週間後の日時を計算
        trial_end_date = current_time + timedelta(days=14)
        
        # 各企業のトライアル期間を2週間に修正
        updated_count = 0
        for company in companies:
            company_id, company_name, current_trial_end = company
            
            # トライアル期間を2週間に設定
            c.execute('UPDATE companies SET trial_end = %s WHERE id = %s', (trial_end_date, company_id))
            updated_count += 1
            print(f'[DEBUG] トライアル期間修正: company_id={company_id}, company_name={company_name}, trial_end={trial_end_date}')
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'トライアル期間を2週間（14日間）に修正しました',
            'updated_count': updated_count,
            'trial_end_date': trial_end_date.strftime('%Y-%m-%d %H:%M:%S JST'),
            'companies': [
                {
                    'id': company[0],
                    'name': company[1],
                    'trial_end': trial_end_date.strftime('%Y-%m-%d %H:%M:%S JST')
                }
                for company in companies
            ]
        })
        
    except Exception as e:
        print(f'[ERROR] トライアル期間修正エラー: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/debug/sync_stripe_periods')
def sync_stripe_periods():
    """Stripeの期間とデータベースの期間を同期"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業のStripeサブスクリプション情報を取得
        c.execute('''
            SELECT id, company_name, stripe_subscription_id 
            FROM companies 
            WHERE stripe_subscription_id IS NOT NULL
        ''')
        companies = c.fetchall()
        
        import stripe
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
        from datetime import datetime, timezone, timedelta
        jst = timezone(timedelta(hours=9))
        
        sync_results = []
        
        for company in companies:
            company_id, company_name, stripe_subscription_id = company
            
            try:
                # Stripeサブスクリプションを取得
                subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                
                # 期間情報を取得
                current_period_start = subscription.get('current_period_start')
                current_period_end = subscription.get('current_period_end')
                trial_end = subscription.get('trial_end')
                
                # UTC → JST変換
                if current_period_start:
                    period_start_utc = datetime.fromtimestamp(current_period_start, tz=timezone.utc)
                    period_start_jst = period_start_utc.astimezone(jst)
                else:
                    period_start_jst = None
                
                if current_period_end:
                    period_end_utc = datetime.fromtimestamp(current_period_end, tz=timezone.utc)
                    period_end_jst = period_end_utc.astimezone(jst)
                else:
                    period_end_jst = None
                
                if trial_end:
                    trial_end_utc = datetime.fromtimestamp(trial_end, tz=timezone.utc)
                    trial_end_jst = trial_end_utc.astimezone(jst)
                else:
                    trial_end_jst = None
                
                # データベースを更新
                c.execute('''
                    UPDATE companies 
                    SET trial_end = %s 
                    WHERE id = %s
                ''', (trial_end_jst, company_id))
                
                # company_monthly_subscriptionsも更新
                c.execute('''
                    UPDATE company_monthly_subscriptions 
                    SET current_period_start = %s, current_period_end = %s
                    WHERE company_id = %s
                ''', (period_start_jst, period_end_jst, company_id))
                
                sync_results.append({
                    'company_id': company_id,
                    'company_name': company_name,
                    'stripe_subscription_id': stripe_subscription_id,
                    'trial_end': trial_end_jst.strftime('%Y-%m-%d %H:%M:%S JST') if trial_end_jst else None,
                    'current_period_start': period_start_jst.strftime('%Y-%m-%d %H:%M:%S JST') if period_start_jst else None,
                    'current_period_end': period_end_jst.strftime('%Y-%m-%d %H:%M:%S JST') if period_end_jst else None,
                    'status': subscription.get('status')
                })
                
                print(f'[DEBUG] 期間同期完了: company_id={company_id}, trial_end={trial_end_jst}, period_end={period_end_jst}')
                
            except Exception as e:
                print(f'[ERROR] 企業{company_id}の期間同期エラー: {e}')
                sync_results.append({
                    'company_id': company_id,
                    'company_name': company_name,
                    'error': str(e)
                })
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Stripeの期間とデータベースの期間を同期しました',
            'sync_results': sync_results
        })
        
    except Exception as e:
        print(f'[ERROR] 期間同期エラー: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

# アプリケーション初期化完了の確認
logger.info("✅ アプリケーション初期化完了")

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', '0').lower() in ('1', 'true', 'yes')
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))