# ユーザーモデルとDBアクセス

class User:
    def __init__(self, id, line_user_id, stripe_customer_id, stripe_subscription_id):
        self.id = id
        self.line_user_id = line_user_id
        self.stripe_customer_id = stripe_customer_id
        self.stripe_subscription_id = stripe_subscription_id

    @staticmethod
    def get_by_line_user_id(line_user_id):
        # DBからユーザー取得（実装はapp.pyから移動予定）
        pass

    @staticmethod
    def create(line_user_id, stripe_customer_id, stripe_subscription_id):
        # DBにユーザー登録（実装はapp.pyから移動予定）
        pass 