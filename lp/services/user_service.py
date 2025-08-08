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
    企業ID中心統合に対応した決済状況チェック（新しい請求システム対応）
    
    Args:
        line_user_id (str): LINEユーザーID
        
    Returns:
        dict: {
            'is_paid': bool,
            'subscription_status': str,
            'message': str,
            'redirect_url': str,
            'trial_days_remaining': int
        }
    """
    print(f'[DEBUG] is_paid_user_company_centric開始: line_user_id={line_user_id}')
    try:
        # PostgreSQL接続を使用
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        
        # Railway本番環境のデータベース接続情報
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            # フォールバック用の接続情報
            database_url = "postgresql://postgres:WZgnjZezoefHmxbwRjUbiPhajtwubmUs@gondola.proxy.rlwy.net:16797/railway"
        
        print(f'[DEBUG] PostgreSQL接続開始: {database_url[:50]}...')
        
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        print(f'[DEBUG] PostgreSQL接続成功')
        
        # 企業情報を取得（LINEユーザーIDで検索）
        print(f'[DEBUG] 検索用LINEユーザーID: line_user_id={line_user_id}')
        
        c.execute('''
            SELECT id, company_name, email, status
            FROM companies 
            WHERE line_user_id = %s::text
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
                'redirect_url': 'https://line.me/R/ti/p/@ai_collections',
                'trial_days_remaining': 0
            }
        
        company_id, company_name, email, status = result
        print(f'[DEBUG] 企業情報取得: company_id={company_id}, company_name={company_name}, email={email}, status={status}')
        
        # トライアル期間の確認
        c.execute('''
            SELECT trial_end
            FROM companies 
            WHERE id = %s
        ''', (company_id,))
        
        trial_result = c.fetchone()
        trial_end = trial_result[0] if trial_result else None
        print(f'[DEBUG] トライアル期間確認: company_id={company_id}, trial_end={trial_end}')
        
        # 新しい請求システム：月額基本サブスクリプションの決済状況をチェック
        c.execute('''
            SELECT subscription_status, current_period_end, monthly_base_price, stripe_subscription_id
            FROM company_monthly_subscriptions 
            WHERE company_id = %s
        ''', (company_id,))
        
        payment_result = c.fetchone()
        print(f'[DEBUG] 月額基本サブスクリプション検索結果: company_id={company_id}, payment_result={payment_result}')
        
        conn.close()
        print(f'[DEBUG] データベース接続終了')
        
        # トライアル期間の判定
        trial_days_remaining = 0
        is_trial_active = False
        
        if trial_end:
            from datetime import datetime, timezone, timedelta
            jst = timezone(timedelta(hours=9))
            current_time = datetime.now(jst)
            
            # タイムゾーン情報を統一（trial_endをawareに変換）
            if trial_end.tzinfo is None:
                trial_end = trial_end.replace(tzinfo=jst)
            
            if current_time < trial_end:
                is_trial_active = True
                trial_days_remaining = (trial_end - current_time).days
                print(f'[DEBUG] トライアル期間中: company_id={company_id}, days_remaining={trial_days_remaining}')
            else:
                print(f'[DEBUG] トライアル期間終了: company_id={company_id}, trial_end={trial_end}')
        
        # 決済状況の判定
        if is_trial_active:
            print(f'[DEBUG] トライアル期間中: company_id={company_id}, days_remaining={trial_days_remaining}')
            return {
                'is_paid': True,
                'subscription_status': 'trialing',
                'message': f'トライアル期間中です。残り{trial_days_remaining}日間ご利用いただけます。',
                'redirect_url': None,
                'trial_days_remaining': trial_days_remaining
            }
        # company_monthly_subscriptions が trialing の場合も有効扱い
        elif payment_result and payment_result[0] == 'trialing':
            print(f"[DEBUG] company_monthly_subscriptions が 'trialing' を示しています: company_id={company_id}")
            trial_days_remaining = 0
            try:
                # companies.trial_end が無い場合はStripeから取得（可能なら）
                stripe_subscription_id = payment_result[3]
                if stripe_subscription_id:
                    import stripe, os
                    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
                    sub = stripe.Subscription.retrieve(stripe_subscription_id)
                    from datetime import datetime, timezone, timedelta
                    jst = timezone(timedelta(hours=9))
                    if getattr(sub, 'trial_end', None):
                        trial_end_utc = datetime.fromtimestamp(sub.trial_end, tz=timezone.utc)
                        trial_end_jst = trial_end_utc.astimezone(jst)
                        now = datetime.now(jst)
                        if now < trial_end_jst:
                            trial_days_remaining = max(0, (trial_end_jst - now).days)
            except Exception as e:
                print(f"[WARN] Stripeからtrial_end取得に失敗: {e}")
            return {
                'is_paid': True,
                'subscription_status': 'trialing',
                'message': 'トライアル期間中です。',
                'redirect_url': None,
                'trial_days_remaining': trial_days_remaining
            }
        elif payment_result and payment_result[0] == 'active':
            current_period_end = payment_result[1]
            monthly_base_price = payment_result[2]
            print(f'[DEBUG] 有効な月額基本サブスクリプション: company_id={company_id}, status=active, period_end={current_period_end}, base_price={monthly_base_price}')
            
            # 期限切れチェック
            if current_period_end:
                from datetime import datetime, timezone, timedelta
                jst = timezone(timedelta(hours=9))
                current_time = datetime.now(jst)
                
                # タイムゾーン情報を統一（current_period_endをawareに変換）
                if current_period_end.tzinfo is None:
                    current_period_end = current_period_end.replace(tzinfo=jst)
                
                if current_time > current_period_end:
                    print(f'[DEBUG] 期限切れ: current_time={current_time}, period_end={current_period_end}')
                    return {
                        'is_paid': False,
                        'subscription_status': 'expired',
                        'message': '月額基本料金の支払い期限が切れています。',
                        'redirect_url': 'https://line.me/R/ti/p/@ai_collections',
                        'trial_days_remaining': 0
                    }
            
            print(f'[DEBUG] 有効な決済確認: company_id={company_id}')
            return {
                'is_paid': True,
                'subscription_status': 'active',
                'message': None,
                'redirect_url': None,
                'trial_days_remaining': 0
            }
        else:
            print(f'[DEBUG] 無効な決済: company_id={company_id}, payment_result={payment_result}')
            return {
                'is_paid': False,
                'subscription_status': 'not_paid',
                'message': '決済済みユーザーのみご利用いただけます。',
                'redirect_url': 'https://line.me/R/ti/p/@ai_collections',
                'trial_days_remaining': 0
            }
            
    except Exception as e:
        print(f'[ERROR] is_paid_user_company_centricエラー: {e}')
        import traceback
        traceback.print_exc()
        return {
            'is_paid': False,
            'subscription_status': 'error',
            'message': 'システムエラーが発生しました。',
            'redirect_url': 'https://line.me/R/ti/p/@ai_collections',
            'trial_days_remaining': 0
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

def find_company_by_email(email):
    """
    メールアドレスで企業を検索（LINEユーザーID変更対応）
    
    Args:
        email (str): メールアドレス
        
    Returns:
        dict: 企業情報
    """
    try:
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        
        # PostgreSQL接続情報
        database_url = "postgresql://postgres:WZgnjZezoefHmxbwRjUbiPhajtwubmUs@gondola.proxy.rlwy.net:16797/railway"
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        
        # メールアドレスでユーザーを検索
        c.execute('''
            SELECT id, line_user_id, stripe_subscription_id
            FROM users 
            WHERE email = %s
        ''', (email,))
        
        user_result = c.fetchone()
        if not user_result:
            conn.close()
            return None
        
        user_id, line_user_id, stripe_subscription_id = user_result
        
        # 企業情報を検索
        c.execute('''
            SELECT id, company_name, line_user_id, stripe_subscription_id, status
            FROM companies 
            WHERE stripe_subscription_id = %s
        ''', (stripe_subscription_id,))
        
        company_result = c.fetchone()
        conn.close()
        
        if company_result:
            return {
                'company_id': company_result[0],
                'company_name': company_result[1],
                'line_user_id': company_result[2],
                'stripe_subscription_id': company_result[3],
                'status': company_result[4],
                'user_id': user_id
            }
        
        return None
        
    except Exception as e:
        print(f'[ERROR] メールアドレスベース企業検索エラー: {e}')
        return None

def update_line_user_id_for_company(company_id, new_line_user_id):
    """
    企業のLINEユーザーIDを更新（LINEユーザーID変更対応）
    
    Args:
        company_id (int): 企業ID
        new_line_user_id (str): 新しいLINEユーザーID
        
    Returns:
        bool: 更新成功
    """
    try:
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        
        # PostgreSQL接続情報
        database_url = "postgresql://postgres:WZgnjZezoefHmxbwRjUbiPhajtwubmUs@gondola.proxy.rlwy.net:16797/railway"
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        
        # 企業のLINEユーザーIDを更新
        c.execute('''
            UPDATE companies 
            SET line_user_id = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        ''', (new_line_user_id, company_id))
        
        # ユーザーのLINEユーザーIDも更新
        c.execute('''
            UPDATE users 
            SET line_user_id = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = (
                SELECT user_id FROM companies WHERE id = %s
            )
        ''', (new_line_user_id, company_id))
        
        conn.commit()
        conn.close()
        
        print(f'[DEBUG] LINEユーザーID更新完了: company_id={company_id}, new_line_user_id={new_line_user_id}')
        return True
        
    except Exception as e:
        print(f'[ERROR] LINEユーザーID更新エラー: {e}')
        return False

def update_line_user_id_for_email(email, new_line_user_id):
    """
    メールアドレスに対応する企業データのLINEユーザーIDを更新
    
    Args:
        email (str): メールアドレス
        new_line_user_id (str): 新しいLINEユーザーID
        
    Returns:
        bool: 更新成功時True
    """
    try:
        print(f'[DEBUG] LINEユーザーID更新開始: email={email}, new_line_user_id={new_line_user_id}')
        
        # PostgreSQL接続
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            database_url = "postgresql://postgres:WZgnjZezoefHmxbwRjUbiPhajtwubmUs@gondola.proxy.rlwy.net:16797/railway"
        
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        
        # 企業データのLINEユーザーIDを更新
        c.execute('''
            UPDATE companies 
            SET line_user_id = %s, updated_at = CURRENT_TIMESTAMP
            WHERE email = %s
        ''', (new_line_user_id, email))
        
        updated_count = c.rowcount
        conn.commit()
        conn.close()
        
        if updated_count > 0:
            print(f'[DEBUG] LINEユーザーID更新成功: email={email}, new_line_user_id={new_line_user_id}')
            return True
        else:
            print(f'[DEBUG] 更新対象が見つかりません: email={email}')
            return False
            
    except Exception as e:
        print(f'[ERROR] LINEユーザーID更新エラー: {e}')
        return False

def is_paid_user_by_email(email):
    """
    メールアドレス中心の決済状況チェック（LINEユーザーID変更対応）
    
    Args:
        email (str): メールアドレス
        
    Returns:
        dict: {
            'is_paid': bool,
            'subscription_status': str,
            'message': str,
            'redirect_url': str
        }
    """
    print(f'[DEBUG] is_paid_user_by_email開始: email={email}')
    try:
        # PostgreSQL接続を使用
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        
        # Railway本番環境のデータベース接続情報
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            database_url = "postgresql://postgres:WZgnjZezoefHmxbwRjUbiPhajtwubmUs@gondola.proxy.rlwy.net:16797/railway"
        
        print(f'[DEBUG] PostgreSQL接続開始: {database_url[:50]}...')
        
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        print(f'[DEBUG] PostgreSQL接続成功')
        
        # メールアドレスで企業データを検索
        c.execute('''
            SELECT id, company_name, stripe_subscription_id, status
            FROM companies 
            WHERE email = %s
        ''', (email,))
        
        result = c.fetchone()
        print(f'[DEBUG] 企業データベース検索結果: email={email}, result={result}')
        
        if not result:
            print(f'[DEBUG] 企業が見つかりません: email={email}')
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
            SELECT subscription_status, current_period_end
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
            current_period_end = payment_result[1]
            print(f'[DEBUG] 有効な決済: company_id={company_id}, status=active, period_end={current_period_end}')
            
            # 期限切れチェック
            if current_period_end:
                from datetime import datetime, timezone, timedelta
                jst = timezone(timedelta(hours=9))
                current_time = datetime.now(jst)
                
                # タイムゾーン情報を統一（current_period_endをawareに変換）
                if current_period_end.tzinfo is None:
                    current_period_end = current_period_end.replace(tzinfo=jst)
                
                if current_period_end > current_time:
                    print(f'[DEBUG] 有効期限内: company_id={company_id}')
                    return {
                        'is_paid': True,
                        'subscription_status': 'active',
                        'message': None,
                        'redirect_url': None
                    }
                else:
                    print(f'[DEBUG] 期限切れ: company_id={company_id}, period_end={current_period_end}, current_time={current_time}')
                    return {
                        'is_paid': False,
                        'subscription_status': 'expired',
                        'message': 'サブスクリプションの有効期限が切れています。',
                        'redirect_url': 'https://line.me/R/ti/p/@ai_collections'
                    }
            else:
                print(f'[DEBUG] 期限未設定: company_id={company_id}')
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
        print(f'[ERROR] メールアドレス中心決済状況チェックエラー: {e}')
        import traceback
        traceback.print_exc()
        return {
            'is_paid': False,
            'subscription_status': 'error',
            'message': 'システムエラーが発生しました。',
            'redirect_url': 'https://line.me/R/ti/p/@ai_collections'
        }
