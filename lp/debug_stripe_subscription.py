#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
現在のStripeサブスクリプションの状態を確認するスクリプト
"""

import os
import sys
import logging
import stripe
from utils.db import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_stripe_subscription():
    """現在のStripeサブスクリプションの状態を確認"""
    logger.info("🔄 Stripeサブスクリプション状態確認開始")
    
    # Stripe APIキーを設定
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    if not stripe.api_key:
        logger.error("❌ STRIPE_SECRET_KEYが設定されていません")
        return False
    
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業ID 14のサブスクリプション情報を取得
        c.execute('''
            SELECT stripe_subscription_id, subscription_status, current_period_end
            FROM company_monthly_subscriptions 
            WHERE company_id = 14
        ''')
        
        subscription_info = c.fetchone()
        if not subscription_info:
            logger.error("❌ 企業ID 14のサブスクリプション情報が見つかりません")
            return False
            
        stripe_subscription_id, subscription_status, current_period_end = subscription_info
        logger.info(f"サブスクリプションID: {stripe_subscription_id}")
        logger.info(f"ステータス: {subscription_status}")
        logger.info(f"請求期間終了: {current_period_end}")
        
        # Stripeサブスクリプションの詳細を取得
        try:
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            logger.info(f"Stripeステータス: {subscription.status}")
            logger.info(f"Stripe請求期間終了: {subscription.current_period_end}")
            
            # サブスクリプションアイテムを確認
            logger.info(f"サブスクリプションアイテム数: {len(subscription['items']['data'])}")
            
            for i, item in enumerate(subscription['items']['data'], 1):
                price = item['price']
                logger.info(f"アイテム {i}:")
                logger.info(f"  - ID: {item['id']}")
                logger.info(f"  - 価格ID: {price['id']}")
                logger.info(f"  - 価格名: {price.get('nickname', 'N/A')}")
                logger.info(f"  - 金額: {price['unit_amount']}円")
                logger.info(f"  - 数量: {item.get('quantity', 'N/A')}")
                logger.info(f"  - 使用タイプ: {price['recurring']['usage_type']}")
                logger.info(f"  - 請求方式: {price['billing_scheme']}")
                
        except Exception as e:
            logger.error(f"❌ Stripe API呼び出しエラー: {e}")
            return False
        
        # データベースのコンテンツ状態も確認
        c.execute('''
            SELECT id, content_name, content_type, status, created_at
            FROM company_contents
            WHERE company_id = 14
            ORDER BY created_at ASC
        ''')
        
        contents = c.fetchall()
        logger.info(f"\nデータベースのコンテンツ状態:")
        active_count = 0
        for content in contents:
            content_id, content_name, content_type, status, created_at = content
            logger.info(f"  - ID: {content_id}, 名前: {content_name}, ステータス: {status}")
            if status == 'active':
                active_count += 1
        
        logger.info(f"アクティブコンテンツ数: {active_count}")
        
        # 課金対象数の計算
        billing_count = max(0, active_count - 1)  # 1個目は無料
        logger.info(f"課金対象数: {billing_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ エラー: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = debug_stripe_subscription()
    if success:
        logger.info("🎉 Stripeサブスクリプション状態確認が正常に完了しました")
        sys.exit(0)
    else:
        logger.error("💥 Stripeサブスクリプション状態確認に失敗しました")
        sys.exit(1)
