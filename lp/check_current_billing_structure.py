#!/usr/bin/env python3
"""
現在の課金構造確認
"""

import os
import sys
sys.path.append('.')

import stripe
from dotenv import load_dotenv
from utils.db import get_db_connection
from services.stripe_service import check_subscription_status

load_dotenv()
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

print('=== 現在の請求構造チェック ===')

try:
    # サブスクリプションIDを取得（実際のIDを使用）
    stripe_subscription_id = 'sub_1RpNPVIxg6C5hAVdQET1f85P'
    
    # サブスクリプションの状態をチェック
    subscription_status = check_subscription_status(stripe_subscription_id)
    
    print(f'サブスクリプションID: {stripe_subscription_id}')
    print(f'ステータス: {subscription_status["status"]}')
    print(f'有効かどうか: {subscription_status["is_active"]}')
    
    # Stripeサブスクリプションの詳細を取得
    subscription = stripe.Subscription.retrieve(stripe_subscription_id)
    
    print(f'\n=== Stripeサブスクリプション構造 ===')
    print(f'サブスクリプションID: {subscription.id}')
    print(f'ステータス: {subscription.status}')
    print(f'現在の期間開始: {subscription.current_period_start}')
    print(f'現在の期間終了: {subscription.current_period_end}')
    print(f'トライアル終了: {subscription.trial_end}')
    
    print(f'\n=== サブスクリプションアイテム ===')
    for i, item in enumerate(subscription.items.data):
        print(f'アイテム {i+1}:')
        print(f'  ID: {item.id}')
        print(f'  Price ID: {item.price.id}')
        print(f'  Price 説明: {item.price.nickname}')
        print(f'  Price 金額: {item.price.unit_amount} {item.price.currency}')
        print(f'  Quantity: {item.quantity}')
        print(f'  Usage Type: {item.price.usage_type}')
        print(f'  Billing Scheme: {item.price.billing_scheme}')
    
    # データベースの状況を確認
    conn = get_db_connection()
    c = conn.cursor()
    
    # ユーザー情報を取得
    c.execute('SELECT id, email, stripe_subscription_id FROM users WHERE stripe_subscription_id = %s', (stripe_subscription_id,))
    user = c.fetchone()
    
    if user:
        user_id, email, db_subscription_id = user
        print(f'\n=== データベースユーザー情報 ===')
        print(f'ユーザーID: {user_id}')
        print(f'メール: {email}')
        print(f'サブスクリプションID: {db_subscription_id}')
        
        # 使用ログを取得
        c.execute('SELECT * FROM usage_logs WHERE user_id = %s ORDER BY created_at', (user_id,))
        usage_logs = c.fetchall()
        
        print(f'\n=== 使用ログ ===')
        print(f'総ログ数: {len(usage_logs)}')
        
        for i, log in enumerate(usage_logs):
            print(f'ログ {i+1}:')
            print(f'  ID: {log[0]}')
            print(f'  ユーザーID: {log[1]}')
            print(f'  使用量: {log[2]}')
            print(f'  Stripe Usage Record ID: {log[3]}')
            print(f'  無料かどうか: {log[4]}')
            print(f'  コンテンツタイプ: {log[5]}')
            print(f'  課金予定: {log[6]}')
            print(f'  作成日: {log[7]}')
    else:
        print(f'\n❌ データベースにユーザーが見つかりません')
    
    conn.close()
    
    print(f'\n=== 請求構造の分析 ===')
    
    # 月額料金の確認
    monthly_items = [item for item in subscription.items.data if item.price.usage_type == 'licensed']
    if monthly_items:
        print(f'✅ 月額料金アイテム: {len(monthly_items)}個')
        for item in monthly_items:
            print(f'  - {item.price.nickname}: {item.price.unit_amount} {item.price.currency}')
    else:
        print(f'❌ 月額料金アイテムが見つかりません')
    
    # 従量課金の確認
    metered_items = [item for item in subscription.items.data if item.price.usage_type == 'metered']
    if metered_items:
        print(f'✅ 従量課金アイテム: {len(metered_items)}個')
        for item in metered_items:
            print(f'  - {item.price.nickname}: {item.price.unit_amount} {item.price.currency}')
    else:
        print(f'❌ 従量課金アイテムが見つかりません')
    
    print(f'\n=== 推奨事項 ===')
    if not metered_items:
        print('1. 従量課金Priceをサブスクリプションに追加してください')
    if not monthly_items:
        print('2. 月額料金Priceをサブスクリプションに追加してください')
    
except Exception as e:
    print(f'エラー: {e}')
    import traceback
    traceback.print_exc() 