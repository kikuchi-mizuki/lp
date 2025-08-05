#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.append('lp')

from services.user_service import is_paid_user_company_centric
from utils.db import get_db_connection

def test_payment_check_detailed():
    """決済チェック機能の詳細テスト"""
    print("=== 決済チェック機能詳細テスト ===")
    
    # テスト対象のLINEユーザーID
    test_line_user_id = "Ua0cf1a45a9126eebdff952202704385e"
    
    print(f"📋 テスト対象: {test_line_user_id}")
    
    # データベース接続テスト
    try:
        conn = get_db_connection()
        c = conn.cursor()
        print("✅ データベース接続成功")
        
        # 企業テーブルの確認
        c.execute("SELECT * FROM companies WHERE line_user_id = %s", (test_line_user_id,))
        company_result = c.fetchone()
        print(f"📊 企業データ: {company_result}")
        
        # 決済テーブルの確認
        if company_result:
            company_id = company_result[0]
            c.execute("SELECT * FROM company_payments WHERE company_id = %s", (company_id,))
            payment_result = c.fetchone()
            print(f"📊 決済データ: {payment_result}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")
        return
    
    # 決済チェック機能のテスト
    print("\n🔍 決済チェック機能テスト:")
    try:
        result = is_paid_user_company_centric(test_line_user_id)
        print(f"📊 結果: {result}")
        
        if result['is_paid']:
            print("✅ 決済済みユーザーとして認識されました")
        else:
            print("❌ 未決済ユーザーとして認識されました")
            print(f"   理由: {result.get('message', '不明')}")
            
    except Exception as e:
        print(f"❌ 決済チェック機能エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_payment_check_detailed() 