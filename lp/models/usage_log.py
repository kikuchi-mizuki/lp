# usage_logsモデルとDBアクセス

class UsageLog:
    def __init__(self, id, user_id, usage_quantity, stripe_usage_record_id, is_free, content_type):
        self.id = id
        self.user_id = user_id
        self.usage_quantity = usage_quantity
        self.stripe_usage_record_id = stripe_usage_record_id
        self.is_free = is_free
        self.content_type = content_type

    @staticmethod
    def get_by_user_id(user_id):
        # DBからusage_logs取得（実装はapp.pyから移動予定）
        pass

    @staticmethod
    def create(user_id, usage_quantity, stripe_usage_record_id, is_free, content_type):
        # DBにusage_log登録（実装はapp.pyから移動予定）
        pass 