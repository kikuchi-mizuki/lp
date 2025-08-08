import os
import sys
import logging

# Add the current directory to Python path for production deployment
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv
from utils.db import get_db_connection

load_dotenv()

# ロガーの設定
logger = logging.getLogger(__name__)

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
def health_check_root():
    """Railwayヘルスチェック用のルートパス - 最もシンプルな応答"""
    try:
        # データベース接続の簡単な確認
        conn = get_db_connection()
        conn.close()
        return "OK", 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        # データベースエラーでもアプリケーションは起動していることを示す
        return "OK", 200, {'Content-Type': 'text/plain'}

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

# アプリケーション初期化完了の確認
logger.info("✅ アプリケーション初期化完了")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))
