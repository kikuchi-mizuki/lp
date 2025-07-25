import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from lp.services.stripe_service import ensure_metered_price_in_subscription
from dotenv import load_dotenv

load_dotenv()

if __name__ == '__main__':
    # 現在のサブスクリプションID
    subscription_id = "sub_1RoqUqIxg6C5hAVdkwij7PyP"
    # Meter付き従量課金Price ID
    metered_price_id = "price_1RokfbIxg6C5hAVd1v0J5ATb"
    
    print(f"サブスクリプション {subscription_id} にMeter付き従量課金Priceを追加中...")
    
    result = ensure_metered_price_in_subscription(subscription_id, metered_price_id)
    
    if result:
        print("✅ Meter付き従量課金Priceの追加に成功しました")
        print(f"サブスクリプション状態: {result['status']}")
    else:
        print("❌ Meter付き従量課金Priceの追加に失敗しました") 