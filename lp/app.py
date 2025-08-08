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
    from routes.railway_setup import railway_setup_bp
    from routes.ai_schedule_webhook import ai_schedule_webhook_bp
    from routes.ai_schedule_webhook_simple import ai_schedule_webhook_simple_bp
    from routes.debug import debug_bp
    
    # Blueprint登録
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
        (railway_setup_bp, 'railway_setup'),
        (ai_schedule_webhook_bp, 'ai_schedule_webhook'),
        (ai_schedule_webhook_simple_bp, 'ai_schedule_webhook_simple'),
        (debug_bp, 'debug')
    ]
    
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
    """メインページ"""
    return render_template('index.html')

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
            
            return render_template('company_registration_success.html', 
                                company_name=company_name, 
                                email=email,
                                content_type=content_type)
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

@app.route('/debug/company/pricing/<int:company_id>')
def debug_company_pricing(company_id):
    """企業料金デバッグ"""
    from app_debug import debug_company_pricing
    result = debug_company_pricing(company_id)
    return jsonify(result)

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

# アプリケーション初期化完了の確認
logger.info("✅ アプリケーション初期化完了")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 3000))) 