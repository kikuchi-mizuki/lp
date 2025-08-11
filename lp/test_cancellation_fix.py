#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
解約処理をテストしてStripeの数量を正しく修正するスクリプト
"""

import os
import sys
import logging
import stripe
from utils.db import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cancellation_fix():
    """解約処理をテストしてStripeの数量を正しく修正"""
    logger.info("🔄 解約処理テスト開始")
    
    # Stripe APIキーを設定
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    if not stripe.api_key:
        logger.error("❌ STRIPE_SECRET_KEYが設定されていません")
        return False
    
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        company_id = 14
        stripe_subscription_id = 'sub_1RulshIxg6C5hAVd7h0x3B5c'
        
        # 現在のアクティブコンテンツ数を取得
        c.execute('''
            SELECT COUNT(*) 
            FROM company_contents 
            WHERE company_id = %s AND status = 'active'
        ''', (company_id,))
        
        remaining_total_count = c.fetchone()[0]
        # 1個目は無料なので、課金対象は総数-1（ただし0未満にはならない）
        new_billing_count = max(0, remaining_total_count - 1)
        
        logger.info(f"現在のアクティブコンテンツ数: {remaining_total_count}")
        logger.info(f"正しい課金対象数: {new_billing_count}")
        
        # Stripeサブスクリプションを取得
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        
        # 既存の追加料金アイテムを確認
        additional_items = []
        for item in subscription['items']['data']:
            price_nickname = item['price'].get('nickname') or ''
            price_id = item['price']['id']
            
            if (("追加" in price_nickname) or 
                ("additional" in price_nickname.lower()) or
                ("metered" in price_nickname.lower()) or
                (price_id == 'price_1Rog1nIxg6C5hAVdnqB5MJiT')):
                
                additional_items.append(item)
                logger.info(f"追加料金アイテム発見: {item['id']}, 数量: {item.get('quantity', 'N/A')}")
        
        # 既存の追加料金アイテムを削除
        for item in additional_items:
            try:
                stripe.SubscriptionItem.delete(item['id'])
                logger.info(f"✅ 追加料金アイテムを削除: {item['id']}")
            except Exception as delete_error:
                logger.error(f"❌ アイテム削除エラー: {delete_error}")
        
        # 追加料金が必要な場合のみ新しいアイテムを作成
        if new_billing_count > 0:
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
                    quantity=new_billing_count
                )
                
                logger.info(f"✅ 新しい追加料金アイテムを作成: {new_item.id}, 数量: {new_billing_count}")
                
            except Exception as e:
                logger.error(f"❌ 新しいアイテム作成エラー: {e}")
                return False
        else:
            logger.info("✅ 追加料金対象なし（数量=0）のためアイテム作成スキップ")
        
        # 修正後の状態を確認
        subscription_after = stripe.Subscription.retrieve(stripe_subscription_id)
        logger.info(f"修正後のサブスクリプションアイテム数: {len(subscription_after['items']['data'])}")
        
        for i, item in enumerate(subscription_after['items']['data'], 1):
            price = item['price']
            logger.info(f"アイテム {i}:")
            logger.info(f"  - ID: {item['id']}")
            logger.info(f"  - 価格名: {price.get('nickname', 'N/A')}")
            logger.info(f"  - 金額: {price['unit_amount']}円")
            logger.info(f"  - 数量: {item.get('quantity', 'N/A')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ エラー: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = test_cancellation_fix()
    if success:
        logger.info("🎉 解約処理テストが正常に完了しました")
        sys.exit(0)
    else:
        logger.error("💥 解約処理テストに失敗しました")
        sys.exit(1)
