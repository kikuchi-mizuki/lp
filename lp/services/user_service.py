# ユーザー関連のサービス層
import stripe
import os
from dotenv import load_dotenv
from utils.db import get_db_connection
from services.stripe_service import check_subscription_status

load_dotenv()
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def register_user(line_user_id, stripe_customer_id, stripe_subscription_id):
    """ユーザー登録"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO users (line_user_id, stripe_customer_id, stripe_subscription_id, created_at, updated_at)
            VALUES (%s, %s, %s, NOW(), NOW())
        ''', (line_user_id, stripe_customer_id, stripe_subscription_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f'ユーザー登録エラー: {e}')
        return False

def get_user_by_line_id(line_user_id):
    """LINEユーザーIDでユーザー取得"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE line_user_id = %s', (line_user_id,))
        user = c.fetchone()
        conn.close()
        
        if user:
            # 辞書形式で返す
            columns = ['id', 'email', 'stripe_customer_id', 'stripe_subscription_id', 'line_user_id', 'created_at', 'updated_at']
            return dict(zip(columns, user))
        return None
    except Exception as e:
        print(f'ユーザー取得エラー: {e}')
        return None

# 永続的な状態管理を使用するため、メモリベースの状態管理は削除
# def set_user_state(line_user_id, state):
#     """ユーザー状態管理（本番はDBやRedis推奨、今はメモリ）"""
#     # メモリベースの状態管理（簡易版）
#     global user_states
#     if 'user_states' not in globals():
#         global user_states
#         user_states = {}
#     user_states[line_user_id] = state

# def get_user_state(line_user_id):
#     """ユーザー状態取得"""
#     global user_states
#     if 'user_states' not in globals():
#         global user_states
#         user_states = {}
#     return user_states.get(line_user_id) 

def is_paid_user(line_user_id):
    """
    ユーザーが決済済みかどうかをチェック
    
    Args:
        line_user_id (str): LINEユーザーID
        
    Returns:
        dict: {
            'is_paid': bool,
            'subscription_status': str,
            'message': str,
            'redirect_url': str
        }
    """
    print(f'[DEBUG] is_paid_user開始: line_user_id={line_user_id}')
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # ユーザー情報を取得
        c.execute('''
            SELECT id, stripe_subscription_id 
            FROM users 
            WHERE line_user_id = %s
        ''', (line_user_id,))
        
        result = c.fetchone()
        print(f'[DEBUG] データベース検索結果: line_user_id={line_user_id}, result={result}')
        conn.close()
        
        if not result:
            print(f'[DEBUG] ユーザーが見つかりません: line_user_id={line_user_id}')
            return {
                'is_paid': False,
                'subscription_status': 'not_registered',
                'message': 'AIコレクションズの公式LINEにご登録ください。',
                'redirect_url': 'https://line.me/R/ti/p/@ai_collections'
            }
        
        user_id, stripe_subscription_id = result
        print(f'[DEBUG] ユーザー情報取得: user_id={user_id}, stripe_subscription_id={stripe_subscription_id}')
        
        # Stripeサブスクリプションの状態をチェック
        subscription_status = check_subscription_status(stripe_subscription_id)
        print(f'[DEBUG] Stripeサブスクリプション状態: stripe_subscription_id={stripe_subscription_id}, status={subscription_status}')
        
        if not subscription_status.get('is_active'):
            print(f'[DEBUG] サブスクリプションが無効: stripe_subscription_id={stripe_subscription_id}, status={subscription_status.get("status")}')
            return {
                'is_paid': False,
                'subscription_status': subscription_status.get('status', 'inactive'),
                'message': 'サブスクリプションが無効です。AIコレクションズの公式LINEで再度ご登録ください。',
                'redirect_url': 'https://line.me/R/ti/p/@ai_collections'
            }
        
        # 有効なサブスクリプション
        print(f'[DEBUG] 有効なサブスクリプション: line_user_id={line_user_id}, status={subscription_status.get("status")}')
        return {
            'is_paid': True,
            'subscription_status': subscription_status.get('status', 'active'),
            'message': None,
            'redirect_url': None
        }
            
    except Exception as e:
        print(f'[ERROR] 決済状況チェックエラー: {e}')
        import traceback
        traceback.print_exc()
        return {
            'is_paid': False,
            'subscription_status': 'error',
            'message': 'システムエラーが発生しました。',
            'redirect_url': 'https://line.me/R/ti/p/@ai_collections'
        }

def is_paid_user_company_centric(line_user_id):
    """
    企業ID中心統合に対応した決済状況チェック（PostgreSQL対応）
    
    Args:
        line_user_id (str): LINEユーザーID
        
    Returns:
        dict: {
            'is_paid': bool,
            'subscription_status': str,
            'message': str,
            'redirect_url': str
        }
    """
    print(f'[DEBUG] is_paid_user_company_centric開始: line_user_id={line_user_id}')
    try:
        # PostgreSQL接続を使用
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        
        database_url = os.getenv('RAILWAY_DATABASE_URL')
        print(f'[DEBUG] データベースURL確認: {database_url[:20] if database_url else "None"}...')
        
        if not database_url:
            print(f'[ERROR] RAILWAY_DATABASE_URLが設定されていません')
            return {
                'is_paid': False,
                'subscription_status': 'error',
                'message': 'データベース接続エラーが発生しました。',
                'redirect_url': 'https://line.me/R/ti/p/@ai_collections'
            }
        
        print(f'[DEBUG] PostgreSQL接続開始')
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        print(f'[DEBUG] PostgreSQL接続成功')
        
        # 企業情報を取得（LINEユーザーIDで検索）
        c.execute('''
            SELECT id, company_name, stripe_subscription_id, status
            FROM companies 
            WHERE line_user_id = %s
        ''', (line_user_id,))
        
        result = c.fetchone()
        print(f'[DEBUG] 企業データベース検索結果: line_user_id={line_user_id}, result={result}')
        
        if not result:
            print(f'[DEBUG] 企業が見つかりません: line_user_id={line_user_id}')
            conn.close()
            return {
                'is_paid': False,
                'subscription_status': 'not_registered',
                'message': 'AIコレクションズの公式LINEにご登録ください。',
                'redirect_url': 'https://line.me/R/ti/p/@ai_collections'
            }
        
        company_id, company_name, stripe_subscription_id, status = result
        print(f'[DEBUG] 企業情報取得: company_id={company_id}, company_name={company_name}, stripe_subscription_id={stripe_subscription_id}, status={status}')
        
        # 企業の決済状況をチェック
        c.execute('''
            SELECT subscription_status 
            FROM company_payments 
            WHERE company_id = %s 
            ORDER BY created_at DESC 
            LIMIT 1
        ''', (company_id,))
        
        payment_result = c.fetchone()
        print(f'[DEBUG] 決済状況検索結果: company_id={company_id}, payment_result={payment_result}')
        
        conn.close()
        print(f'[DEBUG] データベース接続終了')
        
        # 決済状況の判定
        if payment_result and payment_result[0] == 'active':
            print(f'[DEBUG] 有効な決済: company_id={company_id}, status=active')
            return {
                'is_paid': True,
                'subscription_status': 'active',
                'message': None,
                'redirect_url': None
            }
        else:
            print(f'[DEBUG] 無効な決済または未決済: company_id={company_id}, payment_status={payment_result[0] if payment_result else "none"}')
            return {
                'is_paid': False,
                'subscription_status': payment_result[0] if payment_result else 'not_paid',
                'message': '決済済みユーザーのみご利用いただけます。',
                'redirect_url': 'https://line.me/R/ti/p/@ai_collections'
            }
            
    except Exception as e:
        print(f'[ERROR] 企業ID中心統合決済状況チェックエラー: {e}')
        import traceback
        traceback.print_exc()
        return {
            'is_paid': False,
            'subscription_status': 'error',
            'message': 'システムエラーが発生しました。',
            'redirect_url': 'https://line.me/R/ti/p/@ai_collections'
        }

def get_restricted_message():
    """
    制限メッセージを取得
    """
    return {
        "type": "template",
        "altText": "AIコレクションズの公式LINEにご登録ください",
        "template": {
            "type": "buttons",
            "title": "AIコレクションズ",
            "text": "決済済みユーザーのみご利用いただけます。\n\nご登録済みの方は、登録時のメールアドレスを送信してください。",
            "thumbnailImageUrl": "https://ai-collections.herokuapp.com/static/images/logo.png",
            "imageAspectRatio": "rectangle",
            "imageSize": "cover",
            "imageBackgroundColor": "#FFFFFF",
            "actions": [
                {
                    "type": "uri",
                    "label": "公式LINEに登録",
                    "uri": "https://line.me/R/ti/p/@ai_collections"
                },
                {
                    "type": "uri",
                    "label": "サービス詳細",
                    "uri": "https://ai-collections.herokuapp.com"
                }
            ]
        }
    } 