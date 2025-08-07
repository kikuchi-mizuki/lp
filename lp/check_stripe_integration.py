#!/usr/bin/env python3
"""
Stripe統合状況確認スクリプト
"""

import os
import sys
from dotenv import load_dotenv

# 現在のディレクトリをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def check_stripe_integration():
    """Stripe統合状況を確認"""
    print("🔍 Stripe統合状況確認")
    
    # 環境変数確認
    print("\n=== 環境変数確認 ===")
    env_vars = [
        'STRIPE_SECRET_KEY',
        'STRIPE_PUBLISHABLE_KEY', 
        'STRIPE_MONTHLY_PRICE_ID',
        'STRIPE_USAGE_PRICE_ID',
        'STRIPE_WEBHOOK_SECRET'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # 機密情報は一部マスク
            if 'SECRET' in var or 'WEBHOOK' in var:
                masked_value = value[:10] + '*' * (len(value) - 20) + value[-10:] if len(value) > 20 else '***'
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: 未設定")
    
    # Stripe接続テスト
    print("\n=== Stripe接続テスト ===")
    try:
        import stripe
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
        if not stripe.api_key:
            print("❌ Stripe API キーが設定されていません")
            return
        
        # アカウント情報取得
        account = stripe.Account.retrieve()
        print(f"✅ Stripe接続成功: {account.id}")
        print(f"📊 アカウント名: {account.business_profile.name}")
        
        # Price確認
        monthly_price_id = os.getenv('STRIPE_MONTHLY_PRICE_ID')
        usage_price_id = os.getenv('STRIPE_USAGE_PRICE_ID')
        
        if monthly_price_id:
            try:
                monthly_price = stripe.Price.retrieve(monthly_price_id)
                print(f"✅ 月額料金Price: {monthly_price.id} - {monthly_price.unit_amount/100}円/{monthly_price.recurring.interval}")
            except Exception as e:
                print(f"❌ 月額料金Price取得エラー: {e}")
        
        if usage_price_id:
            try:
                usage_price = stripe.Price.retrieve(usage_price_id)
                print(f"✅ 使用量料金Price: {usage_price.id} - {usage_price.unit_amount/100}円/usage")
            except Exception as e:
                print(f"❌ 使用量料金Price取得エラー: {e}")
        
        # サブスクリプション確認
        subscriptions = stripe.Subscription.list(limit=5)
        print(f"\n📊 サブスクリプション数: {len(subscriptions.data)}")
        
        for sub in subscriptions.data:
            status_emoji = "✅" if sub.status == "active" else "⚠️" if sub.status == "trialing" else "❌"
            print(f"  {status_emoji} ID: {sub.id}")
            print(f"    ステータス: {sub.status}")
            print(f"    金額: {sub.items.data[0].price.unit_amount/100}円")
            print(f"    期間: {sub.current_period_start} 〜 {sub.current_period_end}")
        
    except ImportError:
        print("❌ stripeライブラリがインストールされていません")
    except Exception as e:
        print(f"❌ Stripe接続エラー: {e}")
    
    # データベース連携確認
    print("\n=== データベース連携確認 ===")
    try:
        from utils.db import get_db_connection
        conn = get_db_connection()
        c = conn.cursor()
        
        # 月額サブスクリプション確認
        c.execute('SELECT COUNT(*) FROM company_monthly_subscriptions WHERE subscription_status = %s', ('active',))
        active_monthly_count = c.fetchone()[0]
        print(f"✅ アクティブな月額サブスクリプション: {active_monthly_count}件")
        
        # コンテンツ追加確認
        c.execute('SELECT COUNT(*) FROM company_content_additions WHERE status = %s', ('active',))
        active_content_count = c.fetchone()[0]
        print(f"✅ アクティブなコンテンツ追加: {active_content_count}件")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ データベース連携エラー: {e}")

if __name__ == "__main__":
    check_stripe_integration()
