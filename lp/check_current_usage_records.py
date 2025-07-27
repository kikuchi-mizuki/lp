#!/usr/bin/env python3
"""
現在のStripe Usage Records確認
"""

import os
import stripe
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

def check_current_usage_records():
    """現在のStripe Usage Recordsを確認"""
    print("=== 現在のStripe Usage Records確認 ===")
    
    # Stripe APIキーを設定
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    
    # サブスクリプションID
    subscription_id = "sub_1RpVU2Ixg6C5hAVdeyAz8Tjk"
    
    try:
        # サブスクリプションを取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        print(f"✅ サブスクリプション取得成功: {subscription_id}")
        print(f"ステータス: {subscription.status}")
        print(f"現在期間: {subscription.current_period_start} - {subscription.current_period_end}")
        
        # サブスクリプションアイテムを確認
        print(f"\n=== サブスクリプションアイテム ===")
        for item in subscription.items.data:
            print(f"アイテムID: {item.id}")
            print(f"価格ID: {item.price.id}")
            print(f"価格: {item.price.unit_amount}円")
            print(f"使用量タイプ: {item.price.usage_type}")
            
            # Usage Recordsを取得
            if item.price.usage_type == 'metered':
                print(f"\n--- Usage Records for {item.id} ---")
                usage_records = stripe.SubscriptionItem.list_usage_record_summaries(
                    item.id,
                    limit=10
                )
                
                for record in usage_records.data:
                    print(f"期間: {record.period.start} - {record.period.end}")
                    print(f"使用量: {record.total_usage}")
                    print(f"請求可能: {record.invoice}")
                    print("---")
                    
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    check_current_usage_records() 