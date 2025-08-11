#!/usr/bin/env python3
"""
コンテンツ追加時のStripe反映状況をデバッグするスクリプト
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

def debug_stripe_reflection():
    """コンテンツ追加時のStripe反映状況をデバッグ"""
    logger.info("🔄 Stripe反映状況デバッグ開始")
    
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 1. データベースの状態を確認
        logger.info("📊 データベース状態確認")
        
        # 企業の基本情報を取得
        c.execute("""
            SELECT id, company_name, email, status
            FROM companies
            ORDER BY id DESC
            LIMIT 5
        """)
        companies = c.fetchall()
        logger.info(f"企業数: {len(companies)}")
        for company in companies:
            logger.info(f"企業: ID={company[0]}, 名前={company[1]}, メール={company[2]}, ステータス={company[3]}")
        
        # 月額サブスクリプション情報を取得
        c.execute("""
            SELECT company_id, stripe_subscription_id, subscription_status, monthly_base_price
            FROM company_monthly_subscriptions
            ORDER BY company_id DESC
            LIMIT 5
        """)
        subscriptions = c.fetchall()
        logger.info(f"サブスクリプション数: {len(subscriptions)}")
        for sub in subscriptions:
            logger.info(f"サブスクリプション: company_id={sub[0]}, stripe_id={sub[1]}, status={sub[2]}, base_price={sub[3]}")
        
        # コンテンツ情報を取得
        c.execute("""
            SELECT company_id, content_name, content_type, status, created_at
            FROM company_contents
            ORDER BY company_id DESC, created_at DESC
            LIMIT 10
        """)
        contents = c.fetchall()
        logger.info(f"コンテンツ数: {len(contents)}")
        for content in contents:
            logger.info(f"コンテンツ: company_id={content[0]}, name={content[1]}, type={content[2]}, status={content[3]}, created={content[4]}")
        
        # 2. 特定の企業の詳細情報を確認
        if companies:
            target_company_id = companies[0][0]  # 最新の企業
            logger.info(f"🎯 対象企業ID: {target_company_id}")
            
            # 対象企業のアクティブコンテンツ数を確認
            c.execute("""
                SELECT COUNT(*) as active_count
                FROM company_contents
                WHERE company_id = %s AND status = 'active'
            """, (target_company_id,))
            active_count = c.fetchone()[0]
            logger.info(f"アクティブコンテンツ数: {active_count}")
            
            # 課金対象数を計算（1個目は無料）
            billing_count = max(0, active_count - 1)
            logger.info(f"課金対象コンテンツ数: {billing_count}")
            
            # 対象企業のStripeサブスクリプションIDを取得
            c.execute("""
                SELECT stripe_subscription_id
                FROM company_monthly_subscriptions
                WHERE company_id = %s
            """, (target_company_id,))
            stripe_result = c.fetchone()
            
            if stripe_result and stripe_result[0]:
                stripe_subscription_id = stripe_result[0]
                logger.info(f"StripeサブスクリプションID: {stripe_subscription_id}")
                
                # 3. Stripeの状態を確認
                try:
                    import stripe
                    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
                    
                    if not stripe.api_key:
                        logger.error("❌ STRIPE_SECRET_KEYが設定されていません")
                        return
                    
                    # Stripeサブスクリプションを取得
                    subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                    logger.info(f"Stripeサブスクリプション状態: {subscription.status}")
                    
                    # サブスクリプションアイテムを確認
                    items = subscription['items']['data']
                    logger.info(f"Stripeサブスクリプションアイテム数: {len(items)}")
                    
                    for i, item in enumerate(items):
                        price_nickname = item['price'].get('nickname', '')
                        price_id = item['price']['id']
                        quantity = item.get('quantity', 0)
                        unit_amount = item['price'].get('unit_amount', 0)
                        
                        logger.info(f"アイテム{i+1}: ID={item['id']}, Price={price_id}, Nickname={price_nickname}, Quantity={quantity}, Unit Amount={unit_amount}")
                        
                        # 追加料金アイテムかどうかを判定
                        is_additional = (
                            (price_nickname and "追加" in price_nickname) or
                            (price_nickname and "additional" in price_nickname.lower()) or
                            (price_nickname and "metered" in price_nickname.lower()) or
                            price_id == 'price_1Rog1nIxg6C5hAVdnqB5MJiT'
                        )
                        
                        if is_additional:
                            logger.info(f"  → 追加料金アイテム: 数量={quantity}, 単価={unit_amount}, 総額={quantity * unit_amount}")
                        else:
                            logger.info(f"  → 基本料金アイテム: 数量={quantity}, 単価={unit_amount}, 総額={quantity * unit_amount}")
                    
                    # 期待される状態との比較
                    logger.info("🔍 期待される状態との比較:")
                    logger.info(f"  データベース: アクティブ={active_count}, 課金対象={billing_count}")
                    
                    # Stripeの追加料金アイテムの総数量を計算
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
                    
                    logger.info(f"  Stripe: 追加料金数量={stripe_additional_count}")
                    
                    if billing_count == stripe_additional_count:
                        logger.info("✅ データベースとStripeの数量が一致しています")
                    else:
                        logger.error(f"❌ 数量が一致しません: DB={billing_count}, Stripe={stripe_additional_count}")
                        
                except Exception as e:
                    logger.error(f"❌ Stripe確認エラー: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                logger.warning(f"⚠️ 企業ID {target_company_id} のStripeサブスクリプションIDが見つかりません")
        
    except Exception as e:
        logger.error(f"❌ デバッグエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
        logger.info("✅ デバッグ完了")

if __name__ == "__main__":
    debug_stripe_reflection()
