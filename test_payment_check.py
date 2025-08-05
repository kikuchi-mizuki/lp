#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
決済チェック機能をテストするスクリプト
"""

import os
import sys
sys.path.append('lp')

from services.user_service import is_paid_user_company_centric

def test_payment_check():
    """決済チェック機能をテスト"""
    try:
        print("=== 決済チェック機能テスト ===")
        
        # 実際のLINEユーザーID（企業情報から取得）
        line_user_id = "Ua0cf1a45a9126eebdff952202704385e"
        
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
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_payment_check() 