import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import stripe
from lp.services.stripe_service import add_metered_price_to_subscription

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def add_metered_price_to_all_subscriptions(metered_price_id):
    subscriptions = stripe.Subscription.list(limit=100)
    count = 0
    for sub in subscriptions.auto_paging_iter():
        print(f'処理中: {sub.id}')
        result = add_metered_price_to_subscription(sub.id, metered_price_id)
        if result:
            print(f'  → 追加または既に追加済み')
            count += 1
        else:
            print(f'  → 追加失敗')
    print(f'完了: {count}件処理しました')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('使い方: python scripts/add_metered_price_to_all.py <metered_price_id>')
        exit(1)
    metered_price_id = sys.argv[1]
    add_metered_price_to_all_subscriptions(metered_price_id) 