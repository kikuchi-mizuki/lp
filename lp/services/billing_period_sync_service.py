import os
import stripe
from datetime import datetime
from utils.db import get_db_connection, get_db_type

class BillingPeriodSyncService:
    """請求期間同期サービス"""
    
    def __init__(self):
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.db_type = get_db_type()
        self.usage_price_id = 'price_1Rog1nIxg6C5hAVdnqB5MJiT'  # 従量課金のPrice ID
    
    def sync_usage_records_to_subscription_period(self, stripe_subscription_id):
        """
        使用量レコードを月額サブスクリプションの期間に合わせて同期
        """
        try:
            print(f"[DEBUG] 使用量レコード期間同期開始: subscription_id={stripe_subscription_id}")
            
            # Stripeサブスクリプションを取得
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            
            # 従量課金アイテムを取得
            usage_item = None
            for item in subscription['items']['data']:
                if item['price']['id'] == self.usage_price_id:
                    usage_item = item
                    break
            
            if not usage_item:
                print(f"[WARN] 従量課金アイテムが見つかりません: subscription_id={stripe_subscription_id}")
                return False
            
            print(f"[DEBUG] 従量課金アイテム発見: {usage_item['id']}")
            
            # 既存の使用量レコードを確認
            existing_usage = stripe.UsageRecord.list(
                subscription_item=usage_item['id'],
                limit=100
            )
            
            print(f"[DEBUG] 既存の使用量レコード数: {len(existing_usage['data'])}")
            
            # 月額サブスクリプションの期間に合わせて使用量レコードを作成
            stripe.UsageRecord.create(
                subscription_item=usage_item['id'],
                quantity=1,  # 追加コンテンツ1つ分
                timestamp=int(subscription['current_period_start']),  # 月額期間開始時点
                action='set'  # 既存レコードを上書き
            )
            
            print(f"[DEBUG] 使用量レコードを月額期間に同期完了: {datetime.fromtimestamp(subscription['current_period_start'])}")
            return True
            
        except Exception as e:
            print(f"[ERROR] 使用量レコード期間同期エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_subscription_billing_period(self, stripe_subscription_id):
        """
        サブスクリプションの請求期間を取得
        """
        try:
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            
            return {
                'period_start': datetime.fromtimestamp(subscription['current_period_start']),
                'period_end': datetime.fromtimestamp(subscription['current_period_end']),
                'status': subscription['status']
            }
        except Exception as e:
            print(f"[ERROR] 請求期間取得エラー: {e}")
            return None
    
    def create_invoice_with_synced_period(self, stripe_subscription_id):
        """
        期間同期された請求書を作成
        """
        try:
            print(f"[DEBUG] 期間同期請求書作成開始: subscription_id={stripe_subscription_id}")
            
            # 使用量レコードを同期
            if not self.sync_usage_records_to_subscription_period(stripe_subscription_id):
                print(f"[ERROR] 使用量レコード同期に失敗: subscription_id={stripe_subscription_id}")
                return None
            
            # 請求書を作成
            invoice = stripe.Invoice.create(
                subscription=stripe_subscription_id,
                auto_advance=False
            )
            
            print(f"[DEBUG] 期間同期請求書作成完了: invoice_id={invoice['id']}")
            return invoice
            
        except Exception as e:
            print(f"[ERROR] 期間同期請求書作成エラー: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def sync_company_content_billing_period(self, company_id):
        """
        企業のコンテンツ追加時の請求期間同期
        """
        try:
            print(f"[DEBUG] 企業コンテンツ請求期間同期開始: company_id={company_id}")
            
            conn = get_db_connection()
            c = conn.cursor()
            
            # 企業の月額サブスクリプション情報を取得
            c.execute('''
                SELECT stripe_subscription_id 
                FROM company_monthly_subscriptions 
                WHERE company_id = %s
            ''', (company_id,))
            
            monthly_sub = c.fetchone()
            if not monthly_sub:
                print(f"[WARN] 企業の月額サブスクリプションが見つかりません: company_id={company_id}")
                conn.close()
                return False
            
            stripe_subscription_id = monthly_sub[0]
            print(f"[DEBUG] 企業のStripeサブスクリプション: {stripe_subscription_id}")
            
            # 使用量レコードを同期
            success = self.sync_usage_records_to_subscription_period(stripe_subscription_id)
            
            conn.close()
            return success
            
        except Exception as e:
            print(f"[ERROR] 企業コンテンツ請求期間同期エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
