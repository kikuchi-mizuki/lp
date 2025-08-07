#!/usr/bin/env python3
"""
Stripeの使用量レコードを修正するスクリプト
"""

import os
import stripe
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

def fix_stripe_usage_records():
    """Stripeの使用量レコードを修正"""
    print("=== Stripe使用量レコード修正 ===")
    
    try:
        # 環境変数を読み込み
        load_dotenv()
        
        # Stripe APIキーを設定
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not stripe.api_key:
            print("❌ STRIPE_SECRET_KEYが設定されていません")
            return
        
        print(f"[DEBUG] Stripe APIキー: {stripe.api_key[:20]}...")
        
        # サブスクリプションID
        subscription_id = "sub_1RtQTlIxg6C5hAVdgbiUs3Lh"
        
        print(f"\n=== サブスクリプション情報 ===")
        print(f"サブスクリプションID: {subscription_id}")
        
        # サブスクリプションを取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # meteredアイテムを特定
        metered_item = None
        for item in subscription['items']['data']:
            if item['price']['recurring']['usage_type'] == 'metered':
                metered_item = item
                break
        
        if not metered_item:
            print("❌ meteredアイテムが見つかりません")
            return
        
        print(f"\n=== meteredアイテム情報 ===")
        print(f"アイテムID: {metered_item['id']}")
        print(f"価格ID: {metered_item['price']['id']}")
        print(f"単価: {metered_item['price']['unit_amount']}円")
        
        # 現在の使用量を確認
        print(f"\n=== 現在の使用量確認 ===")
        
        # 新しい使用量レコードを作成
        jst = timezone(timedelta(hours=9))
        current_time = datetime.now(jst)
        
        try:
            usage_record = stripe.UsageRecord.create(
                subscription_item=metered_item['id'],
                quantity=1,
                timestamp=int(current_time.timestamp()),
                action='set'
            )
            
            print(f"✅ 使用量レコードを作成しました: {usage_record['id']}")
            print(f"数量: {usage_record['quantity']}")
            print(f"タイムスタンプ: {usage_record['timestamp']}")
            print(f"アクション: {usage_record['action']}")
            
        except Exception as e:
            print(f"使用量レコード作成エラー: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_stripe_usage_records()
