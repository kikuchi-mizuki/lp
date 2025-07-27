# ユーザー関連のサービス層
from utils.db import get_db_connection

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

def set_user_state(line_user_id, state):
    """ユーザー状態管理（本番はDBやRedis推奨、今はメモリ）"""
    # メモリベースの状態管理（簡易版）
    global user_states
    if 'user_states' not in globals():
        global user_states
        user_states = {}
    user_states[line_user_id] = state

def get_user_state(line_user_id):
    """ユーザー状態取得"""
    global user_states
    if 'user_states' not in globals():
        global user_states
        user_states = {}
    return user_states.get(line_user_id) 