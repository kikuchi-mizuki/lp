#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
実際のLINEユーザーIDで決済チェックをテスト
"""

import os
import sys
sys.path.append('lp')

from services.user_service import is_paid_user_company_centric

def test_actual_line_user():
    """実際のLINEユーザーIDでテスト"""
    try:
        print("=== 実際のLINEユーザーIDテスト ===")
        
        # 実際のLINEユーザーID（あなたのLINEユーザーIDを入力してください）
        line_user_id = input("LINEユーザーIDを入力してください: ").strip()
        
        if not line_user_id:
            print("❌ LINEユーザーIDが入力されていません")
            return
        
        print(f"テスト対象LINEユーザーID: {line_user_id}")
        
        # 決済チェック実行
        result = is_paid_user_company_centric(line_user_id)
        
        print(f"\n=== テスト結果 ===")
        print(f"is_paid: {result['is_paid']}")
        print(f"subscription_status: {result['subscription_status']}")
        print(f"message: {result['message']}")
        print(f"redirect_url: {result['redirect_url']}")
        
        if result['is_paid']:
            print("✅ 決済済みとして正しく認識されました")
        else:
            print("❌ 決済済みとして認識されませんでした")
            print(f"原因: {result['subscription_status']}")
            
            # データベースの詳細を確認
            print(f"\n=== データベース詳細確認 ===")
            from utils.db import get_db_connection
            conn = get_db_connection()
            c = conn.cursor()
            
            # 企業情報を確認
            c.execute('SELECT id, company_name, line_user_id, stripe_subscription_id, status FROM companies WHERE line_user_id = %s', (line_user_id,))
            company = c.fetchone()
            if company:
                print(f"企業情報: ID={company[0]}, 名前={company[1]}, LINE_ID={company[2]}, Stripe={company[3]}, 状態={company[4]}")
                
                # 決済情報を確認
                c.execute('SELECT subscription_status FROM company_payments WHERE company_id = %s ORDER BY created_at DESC LIMIT 1', (company[0],))
                payment = c.fetchone()
                if payment:
                    print(f"決済情報: status={payment[0]}")
                else:
                    print("決済情報: なし")
            else:
                print("企業情報: 見つかりません")
            
            conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_actual_line_user() 