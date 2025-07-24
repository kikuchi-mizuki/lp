# ユーザー関連のサービス層

def register_user(line_user_id, stripe_customer_id, stripe_subscription_id):
    """ユーザー登録（実装はapp.pyから移動予定）"""
    pass

def get_user_by_line_id(line_user_id):
    """LINEユーザーIDでユーザー取得（実装はapp.pyから移動予定）"""
    pass

def set_user_state(line_user_id, state):
    """ユーザー状態管理（本番はDBやRedis推奨、今はメモリ）"""
    pass

def get_user_state(line_user_id):
    """ユーザー状態取得"""
    pass 