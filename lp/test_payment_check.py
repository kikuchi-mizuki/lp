#!/usr/bin/env python3
"""
決済チェック機能をテストするスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.user_service import is_paid_user_company_centric

def test_payment_check():
    """決済チェック機能をテスト"""
    print("=== 決済チェック機能テスト ===")
    
    # テスト用のLINEユーザーID
    test_line_user_id = "Ua0cf1a45a9126eebdff952202704385e"
    
    print(f"📋 テスト対象: {test_line_user_id}")
    
    # 決済状況をチェック
    result = is_paid_user_company_centric(test_line_user_id)
    
    print(f"\n📊 結果:")
    print(f"  is_paid: {result['is_paid']}")
    print(f"  subscription_status: {result['subscription_status']}")
    print(f"  message: {result.get('message', 'N/A')}")
    print(f"  redirect_url: {result.get('redirect_url', 'N/A')}")
    
    if result['is_paid']:
        print(f"\n✅ 決済済みユーザーとして認識されました")
    else:
        print(f"\n❌ 未決済ユーザーとして認識されました")
        print(f"   理由: {result.get('message', '不明')}")
    
    return result

if __name__ == "__main__":
    test_payment_check() 