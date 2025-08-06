#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
現在の企業データを修正して、正しいLINEユーザーIDを設定するスクリプト
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def fix_current_company_data():
    """現在の企業データを修正"""
    try:
        print("=== 企業データ修正 ===")
        
        # 接続情報
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            database_url = "postgresql://postgres:WZgnjZezoefHmxbwRjUbiPhajtwubmUs@gondola.proxy.rlwy.net:16797/railway"
        
        print(f"[DEBUG] データベース接続: {database_url[:50]}...")
        
        # データベース接続
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        
        # 現在の企業データを確認
        c.execute('SELECT id, company_name, email, line_user_id, stripe_subscription_id FROM companies ORDER BY id')
        companies = c.fetchall()
        print(f"📊 現在の企業データ:")
        for company in companies:
            print(f"  ID: {company[0]}, 名前: {company[1]}, Email: {company[2]}, LINE: {company[3]}, Stripe: {company[4]}")
        
        # 企業ID8に正しいLINEユーザーIDを設定
        target_company_id = 8
        target_line_user_id = "U1b9d0d75b0c770dc1107dde349d572f7"
        target_email = "mmms.dy.23@gmail.com"
        
        print(f"\n📝 企業データ修正:")
        print(f"  企業ID: {target_company_id}")
        print(f"  LINEユーザーID: {target_line_user_id}")
        print(f"  Email: {target_email}")
        
        # 企業データを更新
        c.execute('''
            UPDATE companies 
            SET line_user_id = %s, email = %s 
            WHERE id = %s
        ''', (target_line_user_id, target_email, target_company_id))
        conn.commit()
        
        print(f"✅ 企業データ更新完了")
        
        # 更新後の確認
        c.execute('SELECT id, company_name, email, line_user_id, stripe_subscription_id FROM companies WHERE id = %s', (target_company_id,))
        updated_company = c.fetchone()
        
        if updated_company:
            print(f"📊 更新後の企業データ:")
            print(f"  ID: {updated_company[0]}")
            print(f"  名前: {updated_company[1]}")
            print(f"  Email: {updated_company[2]}")
            print(f"  LINE: {updated_company[3]}")
            print(f"  Stripe: {updated_company[4]}")
        
        conn.close()
        print("✅ 企業データ修正完了")
        
        # 決済チェックテスト
        print("\n🔍 決済チェックテスト:")
        try:
            sys.path.append('lp')
            from services.user_service import is_paid_user_company_centric
            
            result = is_paid_user_company_centric(target_line_user_id)
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
    fix_current_company_data() 