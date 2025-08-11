#!/usr/bin/env python3
"""
新しい顧客とサブスクリプションを作成するスクリプト
"""

import os
import sys
import logging
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import get_db_connection

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_new_subscription():
    """新しい顧客とサブスクリプションを作成"""
    logger.info("🔄 新しい顧客とサブスクリプション作成開始")
    
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 対象企業の情報を取得
        company_id = 2  # テスト企業
        
        c.execute("""
            SELECT company_name, email
            FROM companies
            WHERE id = %s
        """, (company_id,))
        result = c.fetchone()
        
        if not result:
            logger.error(f"❌ 企業ID {company_id} の情報が見つかりません")
            return
        
        company_name, email = result
        logger.info(f"企業情報: 名前={company_name}, メール={email}")
        
        # Stripeで新しい顧客を作成
        try:
            import stripe
            stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
            
            if not stripe.api_key:
                logger.error("❌ STRIPE_SECRET_KEYが設定されていません")
                return
            
            # 新しい顧客を作成
            customer = stripe.Customer.create(
                email=email,
                name=company_name,
                metadata={
                    'company_id': str(company_id),
                    'company_name': company_name
                }
            )
            
            logger.info(f"✅ 新しい顧客を作成: {customer.id}")
            
            # 基本料金のPriceを作成（または既存のものを使用）
            base_price = stripe.Price.create(
                unit_amount=3900,
                currency='jpy',
                recurring={'interval': 'month'},
                product_data={'name': 'AIコレクションズ 基本料金'},
                nickname='基本料金'
            )
            
            logger.info(f"✅ 基本料金Priceを作成: {base_price.id}")
            
            # 新しいサブスクリプションを作成
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{'price': base_price.id}],
                payment_behavior='default_incomplete',
                payment_settings={'save_default_payment_method': 'on_subscription'},
                expand=['latest_invoice.payment_intent'],
                trial_period_days=14  # 14日間のトライアル
            )
            
            logger.info(f"✅ 新しいサブスクリプションを作成: {subscription.id}")
            
            # データベースを更新
            c.execute("""
                UPDATE company_monthly_subscriptions
                SET stripe_subscription_id = %s, subscription_status = %s, updated_at = NOW()
                WHERE company_id = %s
            """, (subscription.id, subscription.status, company_id))
            
            conn.commit()
            logger.info(f"✅ データベースを更新: stripe_subscription_id={subscription.id}")
            
            # アクティブコンテンツ数を確認して追加料金アイテムを追加
            c.execute("""
                SELECT COUNT(*) as active_count
                FROM company_contents
                WHERE company_id = %s AND status = 'active'
            """, (company_id,))
            active_count = c.fetchone()[0]
            billing_count = max(0, active_count - 1)  # 1個目は無料
            
            logger.info(f"アクティブコンテンツ数: {active_count}, 課金対象: {billing_count}")
            
            if billing_count > 0:
                # 追加料金用のPriceを作成
                additional_price = stripe.Price.create(
                    unit_amount=1500,
                    currency='jpy',
                    recurring={'interval': 'month'},
                    product_data={'name': 'コンテンツ追加料金'},
                    nickname='追加コンテンツ料金'
                )
                
                # 追加料金アイテムを追加
                additional_item = stripe.SubscriptionItem.create(
                    subscription=subscription.id,
                    price=additional_price.id,
                    quantity=billing_count
                )
                
                logger.info(f"✅ 追加料金アイテムを作成: {additional_item.id}, 数量={billing_count}")
            
            # 最終確認
            final_subscription = stripe.Subscription.retrieve(subscription.id)
            logger.info(f"✅ 最終確認: サブスクリプション状態={final_subscription.status}")
            
            items = final_subscription['items']['data']
            logger.info(f"サブスクリプションアイテム数: {len(items)}")
            for i, item in enumerate(items):
                price_nickname = item['price'].get('nickname', '')
                quantity = item.get('quantity', 0)
                unit_amount = item['price'].get('unit_amount', 0)
                logger.info(f"アイテム{i+1}: Nickname={price_nickname}, Quantity={quantity}, Unit Amount={unit_amount}")
            
            # 請求書プレビューを確認
            try:
                invoice = stripe.Invoice.retrieve(final_subscription.latest_invoice)
                logger.info(f"✅ 請求書プレビュー: 金額={invoice.amount_due}, 状態={invoice.status}")
                
                # 請求書の明細を確認
                for line in invoice.lines.data:
                    description = line.description or "不明"
                    amount = line.amount
                    quantity = line.quantity
                    logger.info(f"請求明細: {description}, 数量={quantity}, 金額={amount}")
                    
            except Exception as e:
                logger.warning(f"⚠️ 請求書プレビュー取得エラー: {e}")
                
        except Exception as e:
            logger.error(f"❌ Stripe処理エラー: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        logger.error(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
        logger.info("✅ 処理完了")

if __name__ == "__main__":
    create_new_subscription()
