#!/usr/bin/env python3
"""
企業ID 16のStripe更新処理を手動で実行
"""

import os
import sys
import logging
import stripe

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def manual_stripe_update_company16():
    """企業ID 16のStripe更新処理を手動で実行"""
    logger.info("🔄 企業ID 16のStripe更新処理開始")
    
    # Stripe APIキーを設定
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    
    company_id = 16
    stripe_subscription_id = "sub_1RuoU4Ixg6C5hAVdCEpgoqQD"
    
    try:
        # 現在のStripeサブスクリプションを取得
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        logger.info(f"現在のサブスクリプション状態: {subscription.status}")
        logger.info(f"現在のアイテム数: {len(subscription['items']['data'])}")
        
        # 既存の追加料金アイテムを削除
        items_to_delete = []
        for item in subscription['items']['data']:
            price_nickname = item['price'].get('nickname') or ""
            price_id = item['price']['id']
            
            # 追加料金アイテムを特定
            if (("追加" in price_nickname) or 
                ("additional" in price_nickname.lower()) or
                ("metered" in price_nickname.lower()) or
                (price_id == 'price_1Rog1nIxg6C5hAVdnqB5MJiT')):
                
                logger.info(f"削除対象アイテム発見: {item['id']}, Price={price_id}, Nickname={price_nickname}")
                items_to_delete.append(item['id'])
        
        # 既存の追加料金アイテムを削除
        for item_id in items_to_delete:
            try:
                stripe.SubscriptionItem.delete(item_id)
                logger.info(f"追加料金アイテム削除完了: {item_id}")
            except Exception as delete_error:
                logger.error(f"アイテム削除エラー: {delete_error}")
        
        # 追加料金アイテムを作成（2個のコンテンツが追加されているため）
        additional_content_count = 2  # 3個のコンテンツ - 1個（無料）= 2個
        
        if additional_content_count > 0:
            try:
                # 追加料金用の価格を作成
                additional_price_obj = stripe.Price.create(
                    unit_amount=1500,
                    currency='jpy',
                    recurring={'interval': 'month'},
                    product_data={
                        'name': 'コンテンツ追加料金',
                    },
                    nickname='追加コンテンツ料金(1500円)'
                )
                logger.info(f"追加料金用価格を作成: {additional_price_obj.id}, 単価=1500円")
                
                # サブスクリプションに追加料金アイテムを追加
                additional_item = stripe.SubscriptionItem.create(
                    subscription=stripe_subscription_id,
                    price=additional_price_obj.id,
                    quantity=additional_content_count
                )
                logger.info(f"追加料金アイテムを作成: {additional_item.id}, 数量={additional_content_count}, 総額={1500 * additional_content_count}円")
                
            except Exception as create_error:
                logger.error(f"追加料金アイテム作成エラー: {create_error}")
                import traceback
                traceback.print_exc()
        else:
            logger.info("追加料金対象なし（数量=0）のためアイテム作成スキップ")
        
        # 最終確認
        final_subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        items = final_subscription['items']['data']
        logger.info(f"修正後のサブスクリプションアイテム数: {len(items)}")
        
        for i, item in enumerate(items):
            price_nickname = item['price'].get('nickname', '')
            quantity = item.get('quantity', 0)
            unit_amount = item['price'].get('unit_amount', 0)
            logger.info(f"アイテム{i+1}: Nickname={price_nickname}, Quantity={quantity}, Unit Amount={unit_amount}")
        
        logger.info("✅ 手動Stripe更新処理完了")
        
    except Exception as e:
        logger.error(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    manual_stripe_update_company16()
