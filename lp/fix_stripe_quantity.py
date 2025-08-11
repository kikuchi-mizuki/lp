#!/usr/bin/env python3
"""
Stripeの数量を正しく更新するスクリプト
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

def fix_stripe_quantity():
    """Stripeの数量を正しく更新"""
    logger.info("🔄 Stripe数量修正開始")
    
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 対象企業の情報を取得
        company_id = 16  # サンプル株式会社
        
        # アクティブコンテンツ数を確認
        c.execute("""
            SELECT COUNT(*) as active_count
            FROM company_contents
            WHERE company_id = %s AND status = 'active'
        """, (company_id,))
        active_count = c.fetchone()[0]
        billing_count = max(0, active_count - 1)  # 1個目は無料
        logger.info(f"アクティブコンテンツ数: {active_count}, 課金対象: {billing_count}")
        
        # StripeサブスクリプションIDを直接指定（画像から確認）
        stripe_subscription_id = "sub_1RuoU4Ixg6C5hAVdCEpgoqQD"
        logger.info(f"StripeサブスクリプションID: {stripe_subscription_id}")
        logger.info(f"StripeサブスクリプションID: {stripe_subscription_id}")
        
        # Stripeの状態を確認
        try:
            import stripe
            stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
            
            if not stripe.api_key:
                logger.error("❌ STRIPE_SECRET_KEYが設定されていません")
                return
            
            # Stripeサブスクリプションを取得
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            logger.info(f"Stripeサブスクリプション状態: {subscription.status}")
            
            # 現在のアイテムを確認
            items = subscription['items']['data']
            logger.info(f"現在のサブスクリプションアイテム数: {len(items)}")
            
            for i, item in enumerate(items):
                price_nickname = item['price'].get('nickname', '')
                price_id = item['price']['id']
                quantity = item.get('quantity', 0)
                unit_amount = item['price'].get('unit_amount', 0)
                logger.info(f"アイテム{i+1}: ID={item['id']}, Price={price_id}, Nickname={price_nickname}, Quantity={quantity}, Unit Amount={unit_amount}")
            
            # 追加料金アイテムを特定
            additional_items = []
            for item in items:
                price_nickname = item['price'].get('nickname', '')
                price_id = item['price']['id']
                
                # 追加料金アイテムを特定
                is_additional = (
                    (price_nickname and "追加" in price_nickname) or
                    (price_nickname and "additional" in price_nickname.lower()) or
                    (price_nickname and "metered" in price_nickname.lower()) or
                    price_id == 'price_1Rog1nIxg6C5hAVdnqB5MJiT'
                )
                
                if is_additional:
                    additional_items.append(item)
                    logger.info(f"追加料金アイテム発見: {item['id']}, 現在の数量={item.get('quantity', 0)}")
            
            # 既存の追加料金アイテムを削除
            for item in additional_items:
                try:
                    # meteredタイプの場合はclear_usage=trueを設定
                    if item['price']['recurring']['usage_type'] == 'metered':
                        stripe.SubscriptionItem.delete(item['id'], clear_usage=True)
                    else:
                        stripe.SubscriptionItem.delete(item['id'])
                    logger.info(f"✅ 追加料金アイテムを削除: {item['id']}")
                except Exception as e:
                    logger.error(f"❌ アイテム削除エラー: {e}")
            
            # 追加料金が必要な場合のみ新しいアイテムを作成
            if billing_count > 0:
                try:
                    # 新しいlicensedタイプのPriceを作成
                    new_price = stripe.Price.create(
                        unit_amount=1500,
                        currency='jpy',
                        recurring={'interval': 'month', 'usage_type': 'licensed'},
                        product_data={'name': 'コンテンツ追加料金'},
                        nickname='追加コンテンツ料金(licensed)'
                    )
                    
                    # 新しいアイテムを作成
                    new_item = stripe.SubscriptionItem.create(
                        subscription=stripe_subscription_id,
                        price=new_price.id,
                        quantity=billing_count
                    )
                    
                    logger.info(f"✅ 追加料金アイテムを作成: {new_item.id}, 数量={billing_count}")
                    
                except Exception as e:
                    logger.error(f"❌ アイテム作成エラー: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                logger.info("✅ 追加料金対象なし（数量=0）のためアイテム作成スキップ")
            
            # 最終確認
            final_subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            items = final_subscription['items']['data']
            logger.info(f"修正後のサブスクリプションアイテム数: {len(items)}")
            
            for i, item in enumerate(items):
                price_nickname = item['price'].get('nickname', '')
                quantity = item.get('quantity', 0)
                unit_amount = item['price'].get('unit_amount', 0)
                logger.info(f"アイテム{i+1}: Nickname={price_nickname}, Quantity={quantity}, Unit Amount={unit_amount}")
                
                # 追加料金アイテムかどうかを判定
                is_additional = (
                    (price_nickname and "追加" in price_nickname) or
                    (price_nickname and "additional" in price_nickname.lower()) or
                    (price_nickname and "metered" in price_nickname.lower()) or
                    item['price']['id'] == 'price_1Rog1nIxg6C5hAVdnqB5MJiT'
                )
                
                if is_additional:
                    logger.info(f"  → 追加料金アイテム: 数量={quantity}, 単価={unit_amount}, 総額={quantity * unit_amount}")
                else:
                    logger.info(f"  → 基本料金アイテム: 数量={quantity}, 単価={unit_amount}, 総額={quantity * unit_amount}")
            
            # 期待される状態との比較
            stripe_additional_count = 0
            for item in items:
                price_nickname = item['price'].get('nickname', '')
                price_id = item['price']['id']
                is_additional = (
                    (price_nickname and "追加" in price_nickname) or
                    (price_nickname and "additional" in price_nickname.lower()) or
                    (price_nickname and "metered" in price_nickname.lower()) or
                    price_id == 'price_1Rog1nIxg6C5hAVdnqB5MJiT'
                )
                if is_additional:
                    stripe_additional_count += item.get('quantity', 0)
            
            logger.info(f"期待される状態との比較:")
            logger.info(f"  データベース: アクティブ={active_count}, 課金対象={billing_count}")
            logger.info(f"  Stripe: 追加料金数量={stripe_additional_count}")
            
            if billing_count == stripe_additional_count:
                logger.info("✅ データベースとStripeの数量が一致しています")
            else:
                logger.error(f"❌ 数量が一致しません: DB={billing_count}, Stripe={stripe_additional_count}")
                
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
    fix_stripe_quantity()
