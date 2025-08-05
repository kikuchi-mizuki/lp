#!/usr/bin/env python3
"""
LINE Webhook処理の詳細なデバッグスクリプト
"""

import os
import sys
import traceback
from dotenv import load_dotenv

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def test_line_webhook_debug():
    """LINE Webhook処理の詳細デバッグ"""
    
    print("=== LINE Webhook処理デバッグ開始 ===")
    
    try:
        # シミュレーション用のデータ
        user_id = "U1b9d0d75b0c770dc1107dde349d572f7"
        text = "追加"
        
        print(f'[STEP 1] ユーザーID: {user_id}')
        print(f'[STEP 2] メッセージ: {text}')
        
        # 1. 決済チェック
        print(f'\n[STEP 3] 決済チェック開始')
        try:
            from services.user_service import is_paid_user_company_centric
            print(f'[DEBUG] is_paid_user_company_centric関数をインポート成功')
            
            payment_check = is_paid_user_company_centric(user_id)
            print(f'[STEP 4] 決済チェック結果: {payment_check}')
            
            if not payment_check['is_paid']:
                print(f'[STEP 5] 未決済ユーザー - 制限メッセージ送信')
                return
        except Exception as e:
            print(f'[STEP 4] 決済チェックエラー: {e}')
            traceback.print_exc()
            return
        
        # 2. 企業情報取得
        print(f'\n[STEP 5] 企業情報取得開始')
        try:
            from utils.db import get_db_connection
            print(f'[DEBUG] get_db_connection関数をインポート成功')
            
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT id, company_name, stripe_subscription_id FROM companies WHERE line_user_id = %s', (user_id,))
            company = c.fetchone()
            print(f'[STEP 6] 企業情報: {company}')
            conn.close()
            
            if not company:
                print(f'[STEP 7] 企業情報なし - エラーメッセージ送信')
                return
        except Exception as e:
            print(f'[STEP 6] 企業情報取得エラー: {e}')
            traceback.print_exc()
            return
        
        # 3. ユーザー状態確認
        print(f'\n[STEP 7] ユーザー状態確認開始')
        try:
            from models.user_state import get_user_state
            print(f'[DEBUG] get_user_state関数をインポート成功')
            
            state = get_user_state(user_id)
            print(f'[STEP 8] ユーザー状態: {state}')
        except Exception as e:
            print(f'[STEP 8] ユーザー状態確認エラー: {e}')
            traceback.print_exc()
            return
        
        # 4. メッセージ処理分岐
        print(f'\n[STEP 9] メッセージ処理分岐開始')
        print(f'[DEBUG] text="{text}", state="{state}"')
        
        if text == '追加':
            print(f'[STEP 10] 追加コマンド処理開始')
            
            try:
                from services.line_service import handle_add_content
                print(f'[DEBUG] handle_add_content関数をインポート成功')
                
                company_id = company[0]
                stripe_subscription_id = company[2]
                
                print(f'[STEP 11] handle_add_content呼び出し: company_id={company_id}, stripe_subscription_id={stripe_subscription_id}')
                
                # 実際の関数呼び出し
                handle_add_content("test_reply_token", company_id, stripe_subscription_id)
                print(f'[STEP 12] handle_add_content実行完了')
                
            except Exception as e:
                print(f'[STEP 11] handle_add_contentエラー: {e}')
                traceback.print_exc()
                return
        else:
            print(f'[STEP 10] その他のメッセージ処理')
        
        print(f'\n=== LINE Webhook処理デバッグ完了 ===')
        
    except Exception as e:
        print(f'[ERROR] 全体エラー: {e}')
        traceback.print_exc()

if __name__ == "__main__":
    test_line_webhook_debug() 