import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import stripe
from lp.services.stripe_service import ensure_metered_price_in_subscription
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def check_and_fix_all_subscriptions(metered_price_id):
    """
    全てのサブスクリプションを確認し、Meter付き従量課金Priceが不足しているものを自動で修正
    """
    print(f"全てのサブスクリプションを確認中...")
    print(f"対象Meter付き従量課金Price ID: {metered_price_id}")
    print("-" * 50)
    
    subscriptions = stripe.Subscription.list(limit=100)
    total_count = 0
    fixed_count = 0
    error_count = 0
    
    for sub in subscriptions.auto_paging_iter():
        total_count += 1
        print(f"確認中: {sub.id} (状態: {sub.status})")
        
        # アクティブなサブスクリプションのみ対象
        if sub.status in ['active', 'trialing']:
            # Meter付き従量課金Priceが含まれているかチェック
            has_metered_price = False
            for item in sub['items']['data']:
                if item['price']['id'] == metered_price_id:
                    has_metered_price = True
                    break
            
            if has_metered_price:
                print(f"  ✅ Meter付き従量課金Priceは既に追加済み")
            else:
                print(f"  ❌ Meter付き従量課金Priceが不足 - 自動追加中...")
                result = ensure_metered_price_in_subscription(sub.id, metered_price_id)
                if result:
                    print(f"  ✅ 自動追加成功")
                    fixed_count += 1
                else:
                    print(f"  ❌ 自動追加失敗")
                    error_count += 1
        else:
            print(f"  ⚠️ 非アクティブなサブスクリプション (スキップ)")
        
        print()
    
    print("=" * 50)
    print(f"確認完了:")
    print(f"  総サブスクリプション数: {total_count}")
    print(f"  修正したサブスクリプション数: {fixed_count}")
    print(f"  エラー数: {error_count}")
    print(f"  既に正常なサブスクリプション数: {total_count - fixed_count - error_count}")

if __name__ == '__main__':
    # Meter付き従量課金Price ID
    metered_price_id = "price_1RokfbIxg6C5hAVd1v0J5ATb"
    
    check_and_fix_all_subscriptions(metered_price_id) 