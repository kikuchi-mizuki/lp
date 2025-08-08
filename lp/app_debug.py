import os
import logging
from flask import jsonify, request
from utils.db import get_db_connection

logger = logging.getLogger(__name__)

def debug_database():
    """データベース接続とテーブル構造の確認"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプの確認
        from utils.db import get_db_type
        db_type = get_db_type()
        
        # テーブル一覧の取得
        if db_type == 'postgresql':
            c.execute('''
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            ''')
        else:
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        
        tables = [row[0] for row in c.fetchall()]
        
        # 各テーブルのレコード数を取得
        table_counts = {}
        for table in tables:
            try:
                c.execute(f'SELECT COUNT(*) FROM {table}')
                count = c.fetchone()[0]
                table_counts[table] = count
            except Exception as e:
                table_counts[table] = f"Error: {str(e)}"
        
        conn.close()
        
        return {
            'success': True,
            'database_type': db_type,
            'tables': tables,
            'table_counts': table_counts
        }
        
    except Exception as e:
        logger.error(f"❌ データベースデバッグエラー: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def debug_companies():
    """企業情報の確認"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業一覧を取得
        c.execute('''
            SELECT c.id, c.company_name, c.email, c.status, c.created_at,
                   cms.stripe_subscription_id, cms.subscription_status
            FROM companies c
            LEFT JOIN company_monthly_subscriptions cms ON c.id = cms.company_id
            ORDER BY c.created_at DESC
        ''')
        
        companies = []
        for row in c.fetchall():
            companies.append({
                'id': row[0],
                'company_name': row[1],
                'email': row[2],
                'status': row[3],
                'created_at': row[4].isoformat() if row[4] else None,
                'stripe_subscription_id': row[5],
                'subscription_status': row[6]
            })
        
        conn.close()
        
        return {
            'success': True,
            'companies': companies,
            'total_count': len(companies)
        }
        
    except Exception as e:
        logger.error(f"❌ 企業デバッグエラー: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def debug_webhook_status():
    """Webhook設定の確認"""
    try:
        # 環境変数の確認
        stripe_secret_key = os.getenv('STRIPE_SECRET_KEY')
        stripe_webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        line_channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
        line_channel_secret = os.getenv('LINE_CHANNEL_SECRET')
        
        return {
            'success': True,
            'stripe_secret_key': '***' if stripe_secret_key else 'Not set',
            'stripe_webhook_secret': '***' if stripe_webhook_secret else 'Not set',
            'line_channel_access_token': '***' if line_channel_access_token else 'Not set',
            'line_channel_secret': '***' if line_channel_secret else 'Not set'
        }
        
    except Exception as e:
        logger.error(f"❌ Webhook設定デバッグエラー: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def debug_railway():
    """Railway環境の確認"""
    try:
        # Railway環境変数の確認
        railway_env = {
            'PORT': os.getenv('PORT'),
            'DATABASE_URL': os.getenv('DATABASE_URL'),
            'RAILWAY_PROJECT_ID': os.getenv('RAILWAY_PROJECT_ID'),
            'RAILWAY_SERVICE_ID': os.getenv('RAILWAY_SERVICE_ID')
        }
        
        return {
            'success': True,
            'railway_environment': railway_env
        }
        
    except Exception as e:
        logger.error(f"❌ Railwayデバッグエラー: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def debug_company_pricing(company_id):
    """企業の料金計算デバッグ"""
    try:
        from app_company_registration import calculate_company_pricing
        
        # 企業のコンテンツを取得
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT content_type 
            FROM company_contents 
            WHERE company_id = %s AND content_status = 'active'
        ''', (company_id,))
        
        content_types = [row[0] for row in c.fetchall()]
        conn.close()
        
        # 料金計算
        pricing = calculate_company_pricing(company_id, content_types)
        
        return {
            'success': True,
            'company_id': company_id,
            'content_types': content_types,
            'pricing': pricing
        }
        
    except Exception as e:
        logger.error(f"❌ 企業料金デバッグエラー: {e}")
        return {
            'success': False,
            'error': str(e)
        }
