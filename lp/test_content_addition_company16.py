#!/usr/bin/env python3
"""
企業ID 16に新しいコンテンツを追加してStripe更新処理をテスト
"""

import os
import sys
import logging
import requests

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_content_addition_company16():
    """企業ID 16に新しいコンテンツを追加してテスト"""
    logger.info("🔄 企業ID 16のコンテンツ追加テスト開始")
    
    # 本番環境のURL
    base_url = "https://lp-production-9e2c.up.railway.app"
    
    try:
        # 1. 追加前の状況を確認
        logger.info("📊 追加前の状況を確認中...")
        response = requests.get(f"{base_url}/debug/companies")
        if response.status_code == 200:
            data = response.json()
            for company in data.get('companies', []):
                if company['company_id'] == 16:
                    logger.info(f"追加前: アクティブコンテンツ数={company.get('active_contents', 0)}, 課金対象数={company.get('billing_target', 0)}")
                    break
        
        # 2. 新しいコンテンツを追加（LINE Webhookをシミュレート）
        logger.info("➕ 新しいコンテンツを追加中...")
        
        # LINE Webhookのシミュレーション
        webhook_data = {
            "events": [
                {
                    "type": "message",
                    "message": {
                        "type": "text",
                        "text": "AIタスクコンシェルジュ"
                    },
                    "replyToken": "test_reply_token",
                    "source": {
                        "userId": "U1b9d0d75b0c770dc1107dde349d572f7",
                        "type": "user"
                    }
                }
            ]
        }
        
        response = requests.post(f"{base_url}/line/webhook", json=webhook_data)
        logger.info(f"LINE Webhook応答: {response.status_code}")
        
        # 3. 追加後の状況を確認
        logger.info("📊 追加後の状況を確認中...")
        response = requests.get(f"{base_url}/debug/companies")
        if response.status_code == 200:
            data = response.json()
            for company in data.get('companies', []):
                if company['company_id'] == 16:
                    logger.info(f"追加後: アクティブコンテンツ数={company.get('active_contents', 0)}, 課金対象数={company.get('billing_target', 0)}")
                    break
        
        # 4. Stripeサブスクリプションの状況を確認
        logger.info("💳 Stripeサブスクリプション状況を確認中...")
        response = requests.get(f"{base_url}/debug/check_stripe_periods")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"StripeサブスクリプションID: {data.get('stripe_subscription_id')}")
            logger.info(f"ステータス: {data.get('status')}")
        
        logger.info("✅ コンテンツ追加テスト完了")
        
    except Exception as e:
        logger.error(f"❌ エラー: {e}")

if __name__ == "__main__":
    test_content_addition_company16()
