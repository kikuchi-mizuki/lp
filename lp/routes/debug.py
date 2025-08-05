from flask import Blueprint, jsonify
import os
import psycopg2
from dotenv import load_dotenv

debug_bp = Blueprint('debug', __name__)

@debug_bp.route('/debug/database-state')
def debug_database_state():
    """Railway本番環境のデータベース状態を確認"""
    
    result = {
        'success': False,
        'data': {},
        'error': None
    }
    
    try:
        # Railway本番環境のデータベース接続情報
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            database_url = "postgresql://postgres:WZgnjZezoefHmxbwRjUbiPhajtwubmUs@gondola.proxy.rlwy.net:16797/railway"
        
        print(f'[DEBUG] Railway接続URL: {database_url}')
        
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        
        print(f'[DEBUG] Railwayデータベース接続成功')
        print(f'[DEBUG] 接続先ホスト: {conn.info.host}')
        print(f'[DEBUG] 接続先データベース: {conn.info.dbname}')
        print(f'[DEBUG] 接続先ユーザー: {conn.info.user}')
        
        # 1. companiesテーブルの内容確認
        c.execute("SELECT id, company_name, email, line_user_id, stripe_subscription_id, status, created_at FROM companies ORDER BY id")
        companies = c.fetchall()
        
        companies_data = []
        for company in companies:
            companies_data.append({
                'id': company[0],
                'company_name': company[1],
                'email': company[2],
                'line_user_id': company[3],
                'stripe_subscription_id': company[4],
                'status': company[5],
                'created_at': str(company[6]) if company[6] else None
            })
        
        result['data']['companies'] = companies_data
        
        # 2. company_paymentsテーブルの内容確認
        c.execute("SELECT id, company_id, subscription_status, current_period_end, created_at FROM company_payments ORDER BY id")
        payments = c.fetchall()
        
        payments_data = []
        for payment in payments:
            payments_data.append({
                'id': payment[0],
                'company_id': payment[1],
                'subscription_status': payment[2],
                'current_period_end': str(payment[3]) if payment[3] else None,
                'created_at': str(payment[4]) if payment[4] else None
            })
        
        result['data']['company_payments'] = payments_data
        
        # 3. usersテーブルの内容確認
        c.execute("SELECT id, email, line_user_id, stripe_subscription_id FROM users ORDER BY id")
        users = c.fetchall()
        
        users_data = []
        for user in users:
            users_data.append({
                'id': user[0],
                'email': user[1],
                'line_user_id': user[2],
                'stripe_subscription_id': user[3]
            })
        
        result['data']['users'] = users_data
        
        # 4. 特定のLINEユーザーIDでの検索テスト
        target_line_user_id = "U1b9d0d75b0c770dc1107dde349d572f7"
        
        # companiesテーブルでの検索
        c.execute("SELECT id, company_name, line_user_id FROM companies WHERE line_user_id = %s", (target_line_user_id,))
        company_result = c.fetchone()
        
        if company_result:
            result['data']['target_company'] = {
                'id': company_result[0],
                'company_name': company_result[1],
                'line_user_id': company_result[2]
            }
        else:
            result['data']['target_company'] = None
        
        # usersテーブルでの検索
        c.execute("SELECT id, email, line_user_id FROM users WHERE line_user_id = %s", (target_line_user_id,))
        user_result = c.fetchone()
        
        if user_result:
            result['data']['target_user'] = {
                'id': user_result[0],
                'email': user_result[1],
                'line_user_id': user_result[2]
            }
        else:
            result['data']['target_user'] = None
        
        # 5. 企業IDが1の場合の詳細確認
        c.execute("SELECT id, company_name, line_user_id, stripe_subscription_id FROM companies WHERE id = 1")
        company_1 = c.fetchone()
        
        if company_1:
            result['data']['company_1'] = {
                'id': company_1[0],
                'company_name': company_1[1],
                'line_user_id': company_1[2],
                'stripe_subscription_id': company_1[3]
            }
            
            # 企業ID=1の最新決済情報
            c.execute("SELECT id, subscription_status, current_period_end FROM company_payments WHERE company_id = %s ORDER BY created_at DESC LIMIT 1", (company_1[0],))
            payment_1 = c.fetchone()
            
            if payment_1:
                result['data']['company_1_payment'] = {
                    'id': payment_1[0],
                    'subscription_status': payment_1[1],
                    'current_period_end': str(payment_1[2]) if payment_1[2] else None
                }
            else:
                result['data']['company_1_payment'] = None
        else:
            result['data']['company_1'] = None
            result['data']['company_1_payment'] = None
        
        conn.close()
        result['success'] = True
        
    except Exception as e:
        print(f'[ERROR] Railwayデータベース確認エラー: {e}')
        import traceback
        traceback.print_exc()
        result['error'] = str(e)
    
    return jsonify(result) 