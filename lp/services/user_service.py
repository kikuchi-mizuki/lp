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