from flask import Blueprint, jsonify
import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

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

@debug_bp.route('/debug/fix-payment-periods')
def fix_payment_periods():
    """決済期間を設定するエンドポイント"""
    
    result = {
        'success': False,
        'message': '',
        'updated_count': 0,
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
        
        # 現在の日時（JST）
        jst = timezone(timedelta(hours=9))
        current_time = datetime.now(jst)
        
        # 1ヶ月後の日時
        next_month = current_time + timedelta(days=30)
        
        print(f'[DEBUG] 現在時刻: {current_time}')
        print(f'[DEBUG] 1ヶ月後: {next_month}')
        
        # company_paymentsテーブルのcurrent_period_endを更新
        c.execute("""
            UPDATE company_payments 
            SET current_period_end = %s 
            WHERE current_period_end IS NULL AND subscription_status = 'active'
        """, (next_month,))
        
        updated_count = c.rowcount
        print(f'[DEBUG] 更新されたレコード数: {updated_count}')
        
        # 更新後の確認
        c.execute("SELECT id, company_id, subscription_status, current_period_end FROM company_payments WHERE company_id = 1 ORDER BY id")
        payments = c.fetchall()
        
        print(f'\n=== 更新後の決済情報 ===')
        for payment in payments:
            print(f"ID: {payment[0]}, 企業ID: {payment[1]}, ステータス: {payment[2]}, 期限: {payment[3]}")
        
        conn.commit()
        conn.close()
        
        result['success'] = True
        result['message'] = f'決済期間設定完了: {updated_count}件更新'
        result['updated_count'] = updated_count
        
        print(f'\n[DEBUG] 決済期間設定完了')
        
    except Exception as e:
        print(f'[ERROR] 決済期間設定エラー: {e}')
        import traceback
        traceback.print_exc()
        result['error'] = str(e)
    
    return jsonify(result)

@debug_bp.route('/debug/payment-check')
def debug_payment_check():
    """決済チェックの詳細デバッグエンドポイント"""
    
    result = {
        'success': False,
        'debug_info': {},
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
        
        target_line_user_id = "U1b9d0d75b0c770dc1107dde349d572f7"
        print(f'[DEBUG] 対象LINEユーザーID: {target_line_user_id}')
        
        # 1. 企業情報の取得
        print(f'\n=== 企業情報の取得 ===')
        c.execute('''
            SELECT id, company_name, stripe_subscription_id, status
            FROM companies 
            WHERE line_user_id = %s::text
        ''', (target_line_user_id,))
        
        company_result = c.fetchone()
        print(f'[DEBUG] 企業検索結果: {company_result}')
        
        if company_result:
            result['debug_info']['company'] = {
                'id': company_result[0],
                'name': company_result[1],
                'stripe_id': company_result[2],
                'status': company_result[3]
            }
        else:
            result['debug_info']['company'] = None
        
        # 2. 決済情報の取得
        print(f'\n=== 決済情報の取得 ===')
        if company_result:
            company_id = company_result[0]
            c.execute('''
                SELECT subscription_status, current_period_end
                FROM company_payments 
                WHERE company_id = %s 
                ORDER BY created_at DESC 
                LIMIT 1
            ''', (company_id,))
            
            payment_result = c.fetchone()
            print(f'[DEBUG] 決済検索結果: {payment_result}')
            
            if payment_result:
                subscription_status, current_period_end = payment_result
                result['debug_info']['payment'] = {
                    'status': subscription_status,
                    'period_end': str(current_period_end) if current_period_end else None
                }
                
                # 3. 期限チェック
                print(f'\n=== 期限チェック ===')
                if current_period_end:
                    jst = timezone(timedelta(hours=9))
                    current_time = datetime.now(jst)
                    print(f'[DEBUG] 現在時刻: {current_time}')
                    print(f'[DEBUG] 期限: {current_period_end}')
                    
                    # タイムゾーン情報を統一（current_period_endをawareに変換）
                    if current_period_end.tzinfo is None:
                        current_period_end = current_period_end.replace(tzinfo=jst)
                    
                    print(f'[DEBUG] 期限切れ: {current_period_end <= current_time}')
                    
                    if current_period_end > current_time:
                        print(f'[DEBUG] 有効期限内')
                        is_paid = True
                        final_status = 'active'
                    else:
                        print(f'[DEBUG] 期限切れ')
                        is_paid = False
                        final_status = 'expired'
                else:
                    print(f'[DEBUG] 期限未設定')
                    is_paid = True
                    final_status = 'active'
                
                # 4. 最終判定
                print(f'\n=== 最終判定 ===')
                if subscription_status == 'active' and is_paid:
                    print(f'[DEBUG] 有効な決済: is_paid=True, status={final_status}')
                    final_result = {
                        'is_paid': True,
                        'subscription_status': final_status,
                        'message': None,
                        'redirect_url': None
                    }
                else:
                    print(f'[DEBUG] 無効な決済: is_paid=False, status={subscription_status}')
                    final_result = {
                        'is_paid': False,
                        'subscription_status': subscription_status,
                        'message': '決済済みユーザーのみご利用いただけます。',
                        'redirect_url': 'https://line.me/R/ti/p/@ai_collections'
                    }
                
                result['debug_info']['final_result'] = final_result
                print(f'[DEBUG] 最終結果: {final_result}')
            else:
                result['debug_info']['payment'] = None
                result['debug_info']['final_result'] = {
                    'is_paid': False,
                    'subscription_status': 'no_payment',
                    'message': '決済情報が見つかりません',
                    'redirect_url': 'https://line.me/R/ti/p/@ai_collections'
                }
        
        # 5. 全決済レコードの確認
        print(f'\n=== 全決済レコードの確認 ===')
        if company_result:
            company_id = company_result[0]
            c.execute('''
                SELECT id, company_id, subscription_status, current_period_end, created_at
                FROM company_payments 
                WHERE company_id = %s 
                ORDER BY created_at DESC
            ''', (company_id,))
            
            all_payments = c.fetchall()
            payments_data = []
            for payment in all_payments:
                payments_data.append({
                    'id': payment[0],
                    'company_id': payment[1],
                    'status': payment[2],
                    'period_end': str(payment[3]) if payment[3] else None,
                    'created_at': str(payment[4]) if payment[4] else None
                })
            result['debug_info']['all_payments'] = payments_data
        
        conn.close()
        result['success'] = True
        
    except Exception as e:
        print(f'[ERROR] 決済チェックデバッグエラー: {e}')
        import traceback
        traceback.print_exc()
        result['error'] = str(e)
    
    return jsonify(result)

@debug_bp.route('/debug/simulate-line-webhook')
def simulate_line_webhook():
    """LINE Webhook処理のシミュレーション"""
    
    result = {
        'success': False,
        'steps': [],
        'error': None
    }
    
    try:
        # シミュレーション用のデータ
        user_id = "U1b9d0d75b0c770dc1107dde349d572f7"
        text = "追加"
        
        result['steps'].append(f'[STEP 1] ユーザーID: {user_id}')
        result['steps'].append(f'[STEP 2] メッセージ: {text}')
        
        # 1. 決済チェック
        result['steps'].append('[STEP 3] 決済チェック開始')
        from services.user_service import is_paid_user_company_centric
        
        try:
            payment_check = is_paid_user_company_centric(user_id)
            result['steps'].append(f'[STEP 4] 決済チェック結果: {payment_check}')
            
            if not payment_check['is_paid']:
                result['steps'].append('[STEP 5] 未決済ユーザー - 制限メッセージ送信')
                result['success'] = True
                return jsonify(result)
        except Exception as e:
            result['steps'].append(f'[STEP 4] 決済チェックエラー: {e}')
            result['error'] = str(e)
            return jsonify(result)
        
        # 2. 企業情報取得
        result['steps'].append('[STEP 5] 企業情報取得開始')
        from utils.db import get_db_connection
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT id, company_name, stripe_subscription_id FROM companies WHERE line_user_id = %s', (user_id,))
            company = c.fetchone()
            result['steps'].append(f'[STEP 6] 企業情報: {company}')
            conn.close()
            
            if not company:
                result['steps'].append('[STEP 7] 企業情報なし - エラーメッセージ送信')
                result['success'] = True
                return jsonify(result)
        except Exception as e:
            result['steps'].append(f'[STEP 6] 企業情報取得エラー: {e}')
            result['error'] = str(e)
            return jsonify(result)
        
        # 3. ユーザー状態確認
        result['steps'].append('[STEP 7] ユーザー状態確認開始')
        from models.user_state import get_user_state
        
        try:
            state = get_user_state(user_id)
            result['steps'].append(f'[STEP 8] ユーザー状態: {state}')
        except Exception as e:
            result['steps'].append(f'[STEP 8] ユーザー状態確認エラー: {e}')
            result['error'] = str(e)
            return jsonify(result)
        
        # 4. メッセージ処理分岐
        result['steps'].append('[STEP 9] メッセージ処理分岐開始')
        
        if text == '追加':
            result['steps'].append('[STEP 10] 追加コマンド処理開始')
            
            try:
                from services.line_service import handle_add_content
                company_id = company[0]
                stripe_subscription_id = company[2]
                
                result['steps'].append(f'[STEP 11] handle_add_content呼び出し: company_id={company_id}, stripe_subscription_id={stripe_subscription_id}')
                
                # 実際の関数呼び出しは行わず、ログのみ
                result['steps'].append('[STEP 12] handle_add_content実行完了')
                
            except Exception as e:
                result['steps'].append(f'[STEP 11] handle_add_contentエラー: {e}')
                result['error'] = str(e)
                return jsonify(result)
        else:
            result['steps'].append('[STEP 10] その他のメッセージ処理')
        
        result['success'] = True
        
    except Exception as e:
        result['steps'].append(f'[ERROR] シミュレーションエラー: {e}')
        result['error'] = str(e)
        import traceback
        traceback.print_exc()
    
    return jsonify(result) 