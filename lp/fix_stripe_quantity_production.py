#!/usr/bin/env python3
"""
本番環境用Stripe数量修正スクリプト
"""

import os
import sys
import logging
import requests
from datetime import datetime

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_stripe_quantity_production():
    """本番環境でStripe数量修正を実行"""
    logger.info("🔄 本番環境Stripe数量修正開始")
    
    # 本番環境のURL
    base_url = "https://lp-production-9e2c.up.railway.app"
    
    try:
        # 1. 企業ID 16のコンテンツ状況を確認
        logger.info("📊 企業ID 16のコンテンツ状況を確認中...")
        response = requests.get(f"{base_url}/debug/company_contents")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"コンテンツ数: {data.get('total_count', 0)}")
            for account in data.get('accounts', []):
                if account['company_id'] == 16:
                    logger.info(f"  - {account['content_name']} ({account['content_type']}) - {account['status']}")
        
        # 2. Stripeサブスクリプション状況を確認
        logger.info("💳 Stripeサブスクリプション状況を確認中...")
        response = requests.get(f"{base_url}/debug/check_stripe_periods")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"サブスクリプションID: {data.get('stripe_subscription_id')}")
            logger.info(f"ステータス: {data.get('status')}")
            logger.info(f"次回請求日: {data.get('current_period_end_jst')}")
        
        # 3. 企業情報を確認
        logger.info("🏢 企業情報を確認中...")
        response = requests.get(f"{base_url}/debug/companies")
        if response.status_code == 200:
            data = response.json()
            for company in data.get('companies', []):
                if company['company_id'] == 16:
                    logger.info(f"企業名: {company['company_name']}")
                    logger.info(f"アクティブコンテンツ数: {company.get('active_contents', 0)}")
                    logger.info(f"課金対象数: {company.get('billing_target', 0)}")
                    logger.info(f"期待される追加料金: {company.get('expected_additional_charge', 0)}")
        
        logger.info("✅ 本番環境確認完了")
        
    except Exception as e:
        logger.error(f"❌ エラー: {e}")

if __name__ == "__main__":
    fix_stripe_quantity_production()
