#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LINE webhook処理をシミュレートするテストスクリプト
"""

import os
import sys
sys.path.append('lp')

from services.user_service import is_paid_user_company_centric, get_restricted_message

def simulate_line_webhook():
    """LINE webhook処理をシミュレート"""
    try:
        print("=== LINE Webhook処理シミュレーション ===")
        
        # 実際のLINEユーザーID
        line_user_id = "Ua0cf1a45a9126eebdff952202704385e"
        
        print(f"テスト対象LINEユーザーID: {line_user_id}")
        
        # 決済状況をチェック（企業ID中心統合対応）
        print(f'[DEBUG] 決済チェック開始: user_id={line_user_id}')
        print(f'[DEBUG] 使用する関数: is_paid_user_company_centric')
        
        payment_check = is_paid_user_company_centric(line_user_id)
        print(f'[DEBUG] 決済チェック結果: user_id={line_user_id}, is_paid={payment_check["is_paid"]}, status={payment_check["subscription_status"]}, message={payment_check.get("message", "N/A")}')
        
        if not payment_check['is_paid']:
            print(f'[DEBUG] 未決済ユーザー: user_id={line_user_id}, status={payment_check["subscription_status"]}')
            print(f'[DEBUG] 制限メッセージを送信: user_id={line_user_id}')
            
            # 制限メッセージを取得
            restricted_message = get_restricted_message()
            print(f'[DEBUG] 制限メッセージ内容: {restricted_message}')
            
            print("❌ 制限メッセージが送信されます")
            print(f"原因: {payment_check['subscription_status']}")
        else:
            print(f'[DEBUG] 決済済みユーザー: user_id={line_user_id}, status={payment_check["subscription_status"]}')
            print("✅ 正常にサービスを利用できます")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simulate_line_webhook() 