#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
実際のLINE webhook処理をシミュレートして、実際のデータベース接続情報を確認
"""

import os
import sys
sys.path.append('lp')

from services.user_service import is_paid_user_company_centric

def debug_actual_line_webhook():
    """実際のLINE webhook処理をシミュレート"""
    try:
        print("=== 実際のLINE webhook処理シミュレート（本番環境） ===")
        
        # あなたのLINEユーザーID
        line_user_id = "U1b9d0d75b0c770dc1107dde349d572f7"
        
        print(f"テスト対象LINEユーザーID: {line_user_id}")
        
        # 環境変数の確認
        print(f"\n=== 環境変数確認 ===")
        print(f"DATABASE_URL: {os.getenv('DATABASE_URL', '未設定')}")
        print(f"RAILWAY_DATABASE_URL: {os.getenv('RAILWAY_DATABASE_URL', '未設定')}")
        
        # 実際のLINE webhook処理と同じ関数を呼び出し
        print(f'\n[DEBUG] 決済チェック開始: user_id={line_user_id}')
        print(f'[DEBUG] 使用する関数: is_paid_user_company_centric')
        print(f'[DEBUG] 関数呼び出し前: user_id={line_user_id}')
        
        payment_check = is_paid_user_company_centric(line_user_id)
        
        print(f'[DEBUG] 関数呼び出し後: user_id={line_user_id}, result={payment_check}')
        print(f'[DEBUG] 決済チェック結果: user_id={line_user_id}, is_paid={payment_check["is_paid"]}, status={payment_check["subscription_status"]}, message={payment_check.get("message", "N/A")}')
        print(f'[DEBUG] 決済チェック詳細: {payment_check}')
        
        if not payment_check['is_paid']:
            print(f'[DEBUG] 未決済ユーザー: user_id={line_user_id}, status={payment_check["subscription_status"]}')
            print(f'[DEBUG] 制限メッセージを送信: user_id={line_user_id}')
            print("❌ 未決済ユーザーとして認識されました")
            print(f"理由: {payment_check.get('message', '不明')}")
        else:
            print(f'[DEBUG] 決済済みユーザー: user_id={line_user_id}, status={payment_check["subscription_status"]}')
            print("✅ 決済済みユーザーとして認識されました")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_actual_line_webhook() 