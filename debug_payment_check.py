#!/usr/bin/env python3
"""
決済チェックの詳細なデバッグスクリプト
"""

import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()

def debug_payment_check():
    """決済チェックの詳細なデバッグ"""
    
    # Railway本番環境のデータベース接続情報
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        database_url = "postgresql://postgres:WZgnjZezoefHmxbwRjUbiPhajtwubmUs@gondola.proxy.rlwy.net:16797/railway"
    
    print(f'[DEBUG] Railway接続URL: {database_url}')
    
    try:
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        
        print(f'[DEBUG] Railwayデータベース接続成功')
        
        target_line_user_id = "U1b9d0d75b0c770dc1107dde349d572f7"
        print(f'[DEBUG] 対象LINEユーザーID: {target_line_user_id}')
        
        # 1. 企業情報の取得
        print(f'\n=== 企業情報の取得 ===')
        c.execute('''
            SELECT id, company_name, stripe_subscription_id, status
            FROM companies 
            WHERE line_user_id = %s::text
        ''', (target_line_user_id,))
        
        company_result = c.fetchone()
        print(f'[DEBUG] 企業検索結果: {company_result}')
        
        if not company_result:
            print(f'[DEBUG] 企業が見つかりません')
            return
        
        company_id, company_name, stripe_subscription_id, status = company_result
        print(f'[DEBUG] 企業情報: ID={company_id}, 名前={company_name}, Stripe_ID={stripe_subscription_id}, ステータス={status}')
        
        # 2. 決済情報の取得
        print(f'\n=== 決済情報の取得 ===')
        c.execute('''
            SELECT subscription_status, current_period_end
            FROM company_payments 
            WHERE company_id = %s 
            ORDER BY created_at DESC 
            LIMIT 1
        ''', (company_id,))
        
        payment_result = c.fetchone()
        print(f'[DEBUG] 決済検索結果: {payment_result}')
        
        if not payment_result:
            print(f'[DEBUG] 決済情報が見つかりません')
            return
        
        subscription_status, current_period_end = payment_result
        print(f'[DEBUG] 決済情報: ステータス={subscription_status}, 期限={current_period_end}')
        
        # 3. 期限チェック
        print(f'\n=== 期限チェック ===')
        if current_period_end:
            jst = timezone(timedelta(hours=9))
            current_time = datetime.now(jst)
            print(f'[DEBUG] 現在時刻: {current_time}')
            print(f'[DEBUG] 期限: {current_period_end}')
            print(f'[DEBUG] 期限切れ: {current_period_end <= current_time}')
            
            if current_period_end > current_time:
                print(f'[DEBUG] 有効期限内')
                is_paid = True
                final_status = 'active'
            else:
                print(f'[DEBUG] 期限切れ')
                is_paid = False
                final_status = 'expired'
        else:
            print(f'[DEBUG] 期限未設定')
            is_paid = True
            final_status = 'active'
        
        # 4. 最終判定
        print(f'\n=== 最終判定 ===')
        if subscription_status == 'active' and is_paid:
            print(f'[DEBUG] 有効な決済: is_paid=True, status={final_status}')
            result = {
                'is_paid': True,
                'subscription_status': final_status,
                'message': None,
                'redirect_url': None
            }
        else:
            print(f'[DEBUG] 無効な決済: is_paid=False, status={subscription_status}')
            result = {
                'is_paid': False,
                'subscription_status': subscription_status,
                'message': '決済済みユーザーのみご利用いただけます。',
                'redirect_url': 'https://line.me/R/ti/p/@ai_collections'
            }
        
        print(f'[DEBUG] 最終結果: {result}')
        
        # 5. 全決済レコードの確認
        print(f'\n=== 全決済レコードの確認 ===')
        c.execute('''
            SELECT id, company_id, subscription_status, current_period_end, created_at
            FROM company_payments 
            WHERE company_id = %s 
            ORDER BY created_at DESC
        ''', (company_id,))
        
        all_payments = c.fetchall()
        for payment in all_payments:
            print(f"ID: {payment[0]}, 企業ID: {payment[1]}, ステータス: {payment[2]}, 期限: {payment[3]}, 作成日: {payment[4]}")
        
        conn.close()
        
    except Exception as e:
        print(f'[ERROR] 決済チェックデバッグエラー: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_payment_check() 