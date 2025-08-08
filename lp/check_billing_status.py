#!/usr/bin/env python3
import os
import sys
sys.path.append('.')

# 環境変数を読み込み（.envファイルから）
def load_env_file():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

load_env_file()

import stripe
from utils.db import get_db_connection

# Stripe設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def check_billing_status():
    """現在の請求状況とコンテンツ状況を確認"""
    
    print("=== 請求状況とコンテンツ状況の自動確認 ===\n")
    
    try:
        # データベース接続
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業情報を取得（最新の企業を確認）
        c.execute('''
            SELECT id, company_name, stripe_subscription_id 
            FROM companies 
            WHERE stripe_subscription_id IS NOT NULL 
            ORDER BY id DESC 
            LIMIT 5
        ''')
        
        companies = c.fetchall()
        print(f"📊 アクティブな企業数: {len(companies)}")
        
        for company_id, company_name, stripe_subscription_id in companies:
            print(f"\n" + "="*60)
            print(f"🏢 企業: {company_name} (ID: {company_id})")
            print(f"💳 Stripeサブスクリプション: {stripe_subscription_id}")
            
            # コンテンツ状況をチェック
            c.execute('''
                SELECT content_type, status, created_at
                FROM company_line_accounts 
                WHERE company_id = %s
                ORDER BY created_at
            ''', (company_id,))
            
            contents = c.fetchall()
            active_contents = [c for c in contents if c[1] == 'active']
            
            print(f"\n📱 コンテンツ状況:")
            print(f"   - 総コンテンツ数: {len(contents)}")
            print(f"   - アクティブ数: {len(active_contents)}")
            print(f"   - 課金対象数: {max(0, len(active_contents) - 1)} (1個目は無料)")
            
            for i, (content_type, status, created_at) in enumerate(contents, 1):
                status_icon = "✅" if status == 'active' else "❌"
                free_flag = " (無料)" if i == 1 and status == 'active' else ""
                print(f"   {i}. {content_type}: {status_icon} {status}{free_flag}")
            
            # Stripeサブスクリプション詳細を確認
            if stripe_subscription_id:
                print(f"\n💰 Stripe請求詳細:")
                
                try:
                    subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                    print(f"   - ステータス: {subscription.status}")
                    print(f"   - 現在期間: {subscription.current_period_start} - {subscription.current_period_end}")
                    
                    print(f"\n💳 請求項目:")
                    total_amount = 0
                    additional_found = False
                    
                    for i, item in enumerate(subscription.items.data, 1):
                        price_nickname = item.price.nickname or "名前なし"
                        unit_amount = item.price.unit_amount or 0
                        quantity = item.quantity
                        item_total = (unit_amount * quantity) / 100  # セントから円に変換
                        
                        print(f"   {i}. {price_nickname}")
                        print(f"      - 価格ID: {item.price.id}")
                        print(f"      - 単価: ¥{unit_amount/100:,.0f}")
                        print(f"      - 数量: {quantity}")
                        print(f"      - 小計: ¥{item_total:,.0f}")
                        
                        # 追加料金アイテムかチェック
                        if (("追加" in price_nickname) or 
                            ("additional" in price_nickname.lower()) or
                            ("metered" in price_nickname.lower()) or
                            (item.price.id == 'price_1Rog1nIxg6C5hAVdnqB5MJiT')):
                            additional_found = True
                            print(f"      ⭐ 追加料金アイテム発見!")
                            
                            # 期待値と比較
                            expected_quantity = max(0, len(active_contents) - 1)
                            if quantity == expected_quantity:
                                print(f"      ✅ 数量正常: {quantity} = {expected_quantity}")
                            else:
                                print(f"      ❌ 数量異常: {quantity} ≠ {expected_quantity} (期待値)")
                        
                        total_amount += item_total
                    
                    print(f"\n💸 合計月額: ¥{total_amount:,.0f}")
                    
                    if not additional_found:
                        print(f"   ⚠️  追加料金アイテムが見つかりません!")
                        if len(active_contents) > 1:
                            print(f"   ❌ {len(active_contents)}個のコンテンツがあるのに追加料金なし")
                        else:
                            print(f"   ✅ 1個以下なので追加料金不要")
                    
                except Exception as e:
                    print(f"   ❌ Stripe情報取得エラー: {e}")
            
            print("-" * 60)
        
        conn.close()
        
        print(f"\n🔍 診断結果:")
        print(f"   - データベースとStripeの整合性を確認しました")
        print(f"   - 問題がある場合は上記に❌で表示されています")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_billing_status()