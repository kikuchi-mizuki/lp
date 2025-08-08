#!/usr/bin/env python3
import os
import stripe
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def debug_subscription_structure():
    """Stripeサブスクリプションの構造を詳細に確認"""
    
    # すべてのサブスクリプションを取得
    print("=== Stripeサブスクリプション調査 ===")
    
    try:
        subscriptions = stripe.Subscription.list(limit=10)
        print(f"サブスクリプション数: {len(subscriptions.data)}")
        
        for sub in subscriptions.data:
            print(f"\n--- サブスクリプション: {sub.id} ---")
            print(f"顧客: {sub.customer}")
            print(f"ステータス: {sub.status}")
            print(f"現在期間開始: {sub.current_period_start}")
            print(f"現在期間終了: {sub.current_period_end}")
            
            print(f"\nサブスクリプションアイテム数: {len(sub.items.data)}")
            for i, item in enumerate(sub.items.data):
                print(f"  アイテム{i+1}:")
                print(f"    ID: {item.id}")
                print(f"    Price ID: {item.price.id}")
                print(f"    Price Nickname: {item.price.nickname}")
                print(f"    数量: {item.quantity}")
                print(f"    単価: {item.price.unit_amount}")
                print(f"    通貨: {item.price.currency}")
                print(f"    請求間隔: {item.price.recurring}")
                
                # 追加条件チェック
                nickname = item.price.nickname or ""
                price_id = item.price.id
                
                conditions = []
                if "追加" in nickname:
                    conditions.append("日本語'追加'")
                if "additional" in nickname.lower():
                    conditions.append("英語'additional'")
                if "metered" in nickname.lower():
                    conditions.append("英語'metered'")
                if price_id == 'price_1Rog1nIxg6C5hAVdnqB5MJiT':
                    conditions.append("既知Price ID")
                
                if conditions:
                    print(f"    ✅ 追加料金アイテム候補: {', '.join(conditions)}")
                else:
                    print(f"    ❌ 追加料金アイテムではない")
            
            # このサブスクリプションで追加料金アイテムを検索
            print(f"\n🔍 追加料金アイテム検索結果:")
            found_additional = False
            for item in sub.items.data:
                price_nickname = item.price.nickname or ""
                price_id = item.price.id
                
                # 現在のコードと同じ検索条件
                if (("追加" in price_nickname) or 
                    ("additional" in price_nickname.lower()) or
                    ("metered" in price_nickname.lower()) or
                    (price_id == 'price_1Rog1nIxg6C5hAVdnqB5MJiT')):
                    print(f"  ✅ 発見: {item.id} (Price: {price_id}, Nickname: {price_nickname})")
                    found_additional = True
            
            if not found_additional:
                print(f"  ❌ 追加料金アイテムが見つかりません")
            
            print("-" * 60)
            
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_subscription_structure()