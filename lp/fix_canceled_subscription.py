#!/usr/bin/env python3
"""
キャンセルされたサブスクリプションを修正するスクリプト
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

def fix_canceled_subscription():
    """キャンセルされたサブスクリプションを修正"""
    logger.info("🔄 キャンセルされたサブスクリプション修正開始")
    
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 対象企業の情報を取得
        company_id = 2  # テスト企業
        
        c.execute("""
            SELECT stripe_subscription_id, subscription_status
            FROM company_monthly_subscriptions
            WHERE company_id = %s
        """, (company_id,))
        result = c.fetchone()
        
        if not result:
            logger.error(f"❌ 企業ID {company_id} のサブスクリプション情報が見つかりません")
            return
        
        stripe_subscription_id, subscription_status = result
        logger.info(f"現在のサブスクリプション: ID={stripe_subscription_id}, Status={subscription_status}")
        
        # Stripeの状態を確認
        try:
            import stripe
            stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
            
            if not stripe.api_key:
                logger.error("❌ STRIPE_SECRET_KEYが設定されていません")
                return
            
            # 現在のサブスクリプションを取得
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            logger.info(f"Stripeサブスクリプション状態: {subscription.status}")
            
            if subscription.status == 'canceled':
                logger.info("⚠️ サブスクリプションがキャンセルされています。新しいサブスクリプションを作成します。")
                
                # 基本料金のPrice IDを取得（既存のサブスクリプションから）
                base_price_id = None
                for item in subscription['items']['data']:
                    if item['price'].get('unit_amount') == 3900:  # 基本料金
                        base_price_id = item['price']['id']
                        break
                
                if not base_price_id:
                    logger.error("❌ 基本料金のPrice IDが見つかりません")
                    return
                
                logger.info(f"基本料金Price ID: {base_price_id}")
                
                # 新しいサブスクリプションを作成
                new_subscription = stripe.Subscription.create(
                    customer=subscription.customer,
                    items=[{'price': base_price_id}],
                    payment_behavior='default_incomplete',
                    payment_settings={'save_default_payment_method': 'on_subscription'},
                    expand=['latest_invoice.payment_intent'],
                    trial_period_days=14  # 14日間のトライアル
                )
                
                logger.info(f"✅ 新しいサブスクリプションを作成: {new_subscription.id}")
                
                # データベースを更新
                c.execute("""
                    UPDATE company_monthly_subscriptions
                    SET stripe_subscription_id = %s, subscription_status = %s, updated_at = NOW()
                    WHERE company_id = %s
                """, (new_subscription.id, new_subscription.status, company_id))
                
                conn.commit()
                logger.info(f"✅ データベースを更新: stripe_subscription_id={new_subscription.id}")
                
                # 新しいサブスクリプションに追加料金アイテムを追加
                # アクティブコンテンツ数を確認
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
                        subscription=new_subscription.id,
                        price=additional_price.id,
                        quantity=billing_count
                    )
                    
                    logger.info(f"✅ 追加料金アイテムを作成: {additional_item.id}, 数量={billing_count}")
                
                # 最終確認
                final_subscription = stripe.Subscription.retrieve(new_subscription.id)
                logger.info(f"✅ 最終確認: サブスクリプション状態={final_subscription.status}")
                
                items = final_subscription['items']['data']
                logger.info(f"サブスクリプションアイテム数: {len(items)}")
                for i, item in enumerate(items):
                    price_nickname = item['price'].get('nickname', '')
                    quantity = item.get('quantity', 0)
                    unit_amount = item['price'].get('unit_amount', 0)
                    logger.info(f"アイテム{i+1}: Nickname={price_nickname}, Quantity={quantity}, Unit Amount={unit_amount}")
                
            else:
                logger.info("✅ サブスクリプションは正常な状態です")
                
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
    fix_canceled_subscription()
