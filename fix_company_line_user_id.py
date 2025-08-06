#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
企業データにLINEユーザーIDを直接紐付けるスクリプト
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def fix_company_line_user_id():
    """企業データにLINEユーザーIDを直接紐付ける"""
    try:
        print("=== 企業データLINEユーザーID紐付け修正 ===")
        
        # 接続情報
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            database_url = "postgresql://postgres:WZgnjZezoefHmxbwRjUbiPhajtwubmUs@gondola.proxy.rlwy.net:16797/railway"
        
        print(f"[DEBUG] データベース接続: {database_url[:50]}...")
        
        # データベース接続
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        
        # 対象の企業IDとLINEユーザーID
        company_id = 8
        line_user_id = "U1b9d0d75b0c770dc1107dde349d572f7"
        
        print(f"📋 更新対象:")
        print(f"  企業ID: {company_id}")
        print(f"  LINEユーザーID: {line_user_id}")
        
        # 現在の企業データを確認
        c.execute('SELECT id, company_name, line_user_id, stripe_subscription_id FROM companies WHERE id = %s', (company_id,))
        company_result = c.fetchone()
        
        if not company_result:
            print(f"❌ 企業ID {company_id} が見つかりません")
            return
        
        company_id_db, company_name, current_line_user_id, stripe_subscription_id = company_result
        print(f"📊 現在の企業データ:")
        print(f"  企業名: {company_name}")
        print(f"  現在のLINEユーザーID: {current_line_user_id}")
        print(f"  StripeサブスクリプションID: {stripe_subscription_id}")
        
        # LINEユーザーIDを更新
        c.execute('UPDATE companies SET line_user_id = %s WHERE id = %s', (line_user_id, company_id))
        conn.commit()
        
        print(f"✅ 企業データ更新完了:")
        print(f"  企業ID: {company_id}")
        print(f"  LINEユーザーID: {line_user_id} に更新")
        
        # 更新後の確認
        c.execute('SELECT id, company_name, line_user_id, stripe_subscription_id FROM companies WHERE id = %s', (company_id,))
        updated_company = c.fetchone()
        
        if updated_company:
            print(f"📊 更新後の企業データ:")
            print(f"  企業名: {updated_company[1]}")
            print(f"  LINEユーザーID: {updated_company[2]}")
            print(f"  StripeサブスクリプションID: {updated_company[3]}")
        
        conn.close()
        print("✅ 企業データLINEユーザーID紐付け修正完了")
        
        # 決済チェックテスト
        print("\n🔍 決済チェックテスト:")
        try:
            sys.path.append('lp')
            from services.user_service import is_paid_user_company_centric
            
            result = is_paid_user_company_centric(line_user_id)
            print(f"📊 決済チェック結果: {result}")
            
            if result['is_paid']:
                print("✅ 決済済みユーザーとして認識されました")
            else:
                print("❌ 未決済ユーザーとして認識されました")
                print(f"   理由: {result.get('message', '不明')}")
                
        except Exception as e:
            print(f"❌ 決済チェックエラー: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_company_line_user_id() 