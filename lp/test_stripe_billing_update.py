#!/usr/bin/env python3
"""
Stripe請求項目更新処理のテストスクリプト
"""

import os
import stripe
from dotenv import load_dotenv
from datetime import datetime

def test_stripe_billing_update():
    """Stripe請求項目更新処理をテスト"""
    print("=== Stripe請求項目更新処理テスト ===")
    
    try:
        # 環境変数を読み込み
        load_dotenv()
        
        # Stripe APIキーを設定
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not stripe.api_key:
            print("❌ STRIPE_SECRET_KEYが設定されていません")
            return
        
        print(f"[DEBUG] Stripe APIキー: {stripe.api_key[:20]}...")
        
        # テスト用サブスクリプションID
        subscription_id = "sub_1RtQTlIxg6C5hAVdgbiUs3Lh"
        
        print(f"\n=== サブスクリプション情報確認 ===")
        print(f"サブスクリプションID: {subscription_id}")
        
        # サブスクリプションを取得
        subscription = stripe.Subscription.retrieve(subscription_id)
        print(f"ステータス: {subscription['status']}")
        print(f"現在期間開始: {datetime.fromtimestamp(subscription['current_period_start'])}")
        print(f"現在期間終了: {datetime.fromtimestamp(subscription['current_period_end'])}")
        
        # サブスクリプションアイテムを詳細にログ出力
        print(f"\n=== サブスクリプションアイテム詳細 ===")
        print(f"アイテム数: {len(subscription['items']['data'])}")
        
        for i, item in enumerate(subscription['items']['data']):
            price_id = item['price']['id']
            price_nickname = item['price'].get('nickname', '')
            quantity = item.get('quantity', 0)
            print(f"アイテム{i}: ID={item['id']}, Price={price_id}, Nickname={price_nickname}, Quantity={quantity}")
        
        # 追加料金アイテムを特定
        print(f"\n=== 追加料金アイテム特定テスト ===")
        usage_price_id = 'price_1Rog1nIxg6C5hAVdnqB5MJiT'
        
        updated = False
        for item in subscription['items']['data']:
            price_nickname = item['price'].get('nickname', '')
            price_id = item['price']['id']
            
            # 複数の条件で追加料金アイテムを特定
            if (("追加" in price_nickname) or 
                ("additional" in price_nickname.lower()) or
                ("metered" in price_nickname.lower()) or
                (price_id == usage_price_id)):
                
                print(f"✅ 追加料金アイテム発見: {item['id']}, Price={price_id}, Nickname={price_nickname}")
                updated = True
                break
        
        if not updated:
            print("❌ 追加料金アイテムが見つかりませんでした")
            print("利用可能なアイテム:")
            for item in subscription['items']['data']:
                print(f"  - ID: {item['id']}, Price: {item['price']['id']}, Nickname: {item['price'].get('nickname', '')}")
        
        # 使用量レコードの確認
        print(f"\n=== 使用量レコード確認 ===")
        for item in subscription['items']['data']:
            if item['price']['recurring']['usage_type'] == 'metered':
                try:
                    usage_records = stripe.UsageRecord.list(
                        subscription_item=item['id'],
                        limit=10
                    )
                    print(f"アイテム {item['id']} の使用量レコード:")
                    for usage in usage_records['data']:
                        print(f"  期間: {datetime.fromtimestamp(usage['timestamp'])}")
                        print(f"  使用量: {usage['quantity']}")
                        print(f"  アクション: {usage['action']}")
                        print("  ---")
                except Exception as e:
                    print(f"  使用量レコード取得エラー: {e}")
        
        print(f"\n=== テスト完了 ===")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stripe_billing_update()
