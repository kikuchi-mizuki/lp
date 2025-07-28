#!/usr/bin/env python3
"""
メータード課金アイテムを削除するスクリプト
"""

import os
import stripe
from dotenv import load_dotenv
from datetime import datetime

# 環境変数を読み込み
load_dotenv('lp/.env')

def remove_metered_item():
    """メータード課金アイテムを削除"""
    
    # Stripe APIキーを設定
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    if not stripe.api_key:
        print("❌ STRIPE_SECRET_KEYが設定されていません")
        return
    
    # サブスクリプションID
    subscription_id = "sub_1RpdcsIxg6C5hAVdneqtbnUG"
    # メータード課金アイテムのID
    metered_item_id = "si_Sl9wRTBiD5qO4m"
    
    try:
        print(f"=== メータード課金アイテム削除 ===")
        print(f"サブスクリプションID: {subscription_id}")
        print(f"アイテムID: {metered_item_id}")
        
        # メータード課金アイテムを削除（使用量レコードもクリア）
        deleted_item = stripe.SubscriptionItem.delete(
            metered_item_id,
            clear_usage=True
        )
        print(f"✅ 削除成功: {deleted_item.id}")
        
        # 削除後のサブスクリプションアイテムを確認
        subscription_items = stripe.SubscriptionItem.list(
            subscription=subscription_id
        )
        
        print(f"\n=== 削除後のサブスクリプションアイテム ===")
        for item in subscription_items.data:
            print(f"ID: {item.id}")
            print(f"Price ID: {item.price.id}")
            if hasattr(item, 'quantity'):
                print(f"Quantity: {item.quantity}")
            else:
                print("Quantity: メータード課金")
            print("---")
        
        print(f"\n=== 削除完了 ===")
        print("メータード課金アイテム「AIコレクションズ（追加）」を削除しました。")
        print("これで請求書から「トライアル期間: AIコレクションズ (追加)」の項目が消えます。")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    remove_metered_item() 