import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.stripe_service import add_metered_price_to_subscription

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('使い方: python scripts/add_metered_price.py <subscription_id> <metered_price_id>')
        sys.exit(1)
    subscription_id = sys.argv[1]
    metered_price_id = sys.argv[2]
    result = add_metered_price_to_subscription(subscription_id, metered_price_id)
    if result:
        print('従量課金Priceの追加に成功しました')
    else:
        print('従量課金Priceの追加に失敗しました') 