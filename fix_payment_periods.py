#!/usr/bin/env python3
"""
決済情報のcurrent_period_endを設定するスクリプト
"""

import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()

def fix_payment_periods():
    """決済情報のcurrent_period_endを設定"""
    
    # Railway本番環境のデータベース接続情報
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        database_url = "postgresql://postgres:WZgnjZezoefHmxbwRjUbiPhajtwubmUs@gondola.proxy.rlwy.net:16797/railway"
    
    print(f'[DEBUG] Railway接続URL: {database_url}')
    
    try:
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        
        print(f'[DEBUG] Railwayデータベース接続成功')
        
        # 現在の日時（JST）
        jst = timezone(timedelta(hours=9))
        current_time = datetime.now(jst)
        
        # 1ヶ月後の日時
        next_month = current_time + timedelta(days=30)
        
        print(f'[DEBUG] 現在時刻: {current_time}')
        print(f'[DEBUG] 1ヶ月後: {next_month}')
        
        # company_paymentsテーブルのcurrent_period_endを更新
        c.execute("""
            UPDATE company_payments 
            SET current_period_end = %s 
            WHERE current_period_end IS NULL AND subscription_status = 'active'
        """, (next_month,))
        
        updated_count = c.rowcount
        print(f'[DEBUG] 更新されたレコード数: {updated_count}')
        
        # 更新後の確認
        c.execute("SELECT id, company_id, subscription_status, current_period_end FROM company_payments WHERE company_id = 1 ORDER BY id")
        payments = c.fetchall()
        
        print(f'\n=== 更新後の決済情報 ===')
        for payment in payments:
            print(f"ID: {payment[0]}, 企業ID: {payment[1]}, ステータス: {payment[2]}, 期限: {payment[3]}")
        
        conn.commit()
        conn.close()
        
        print(f'\n[DEBUG] 決済期間設定完了')
        
    except Exception as e:
        print(f'[ERROR] 決済期間設定エラー: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_payment_periods() 