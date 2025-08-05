#!/usr/bin/env python3
"""
ユーザーの決済状況を詳しく調べるデバッグスクリプト
"""

import os
import sys
from dotenv import load_dotenv

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import get_db_connection
from services.stripe_service import check_subscription_status
from services.user_service import is_paid_user

load_dotenv()

def debug_user_payment_status(line_user_id):
    """ユーザーの決済状況を詳しく調べる"""
    print(f"🔍 ユーザー決済状況デバッグ: {line_user_id}")
    print("=" * 50)
    
    try:
        # 1. データベースでユーザー情報を取得
        print("📊 ステップ1: データベースでユーザー情報を確認")
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT id, company_name, stripe_subscription_id, status, created_at, updated_at
            FROM companies 
            WHERE line_user_id = %s
        ''', (line_user_id,))
        
        user_result = c.fetchone()
        
        if not user_result:
            print("❌ データベースに企業が見つかりません")
            print("   原因: LINE_IDがデータベースに登録されていない")
            return
        
        company_id, company_name, stripe_subscription_id, status, created_at, updated_at = user_result
        print(f"✅ 企業情報取得成功:")
        print(f"   - 企業ID: {company_id}")
        print(f"   - 企業名: {company_name}")
        print(f"   - StripeサブスクリプションID: {stripe_subscription_id}")
        print(f"   - ステータス: {status}")
        print(f"   - 作成日時: {created_at}")
        print(f"   - 更新日時: {updated_at}")
        
        # 2. Stripeサブスクリプションの状態をチェック
        print("\n💳 ステップ2: Stripeサブスクリプションの状態を確認")
        if not stripe_subscription_id:
            print("❌ StripeサブスクリプションIDが設定されていません")
            return
        
        subscription_status = check_subscription_status(stripe_subscription_id)
        print(f"✅ Stripeサブスクリプション情報:")
        print(f"   - 状態: {subscription_status.get('status')}")
        print(f"   - 有効: {subscription_status.get('is_active')}")
        print(f"   - 解約予定: {subscription_status.get('cancel_at_period_end')}")
        print(f"   - 期間終了: {subscription_status.get('current_period_end')}")
        
        # 3. is_paid_user_company_centric関数の結果を確認
        print("\n🎯 ステップ3: is_paid_user_company_centric関数の結果を確認")
        from services.user_service import is_paid_user_company_centric
        payment_check = is_paid_user_company_centric(line_user_id)
        print(f"✅ is_paid_user_company_centric結果:")
        print(f"   - 決済済み: {payment_check['is_paid']}")
        print(f"   - サブスクリプション状態: {payment_check['subscription_status']}")
        print(f"   - メッセージ: {payment_check['message']}")
        print(f"   - リダイレクトURL: {payment_check['redirect_url']}")
        
        # 4. 問題の原因を特定
        print("\n🔍 ステップ4: 問題の原因を特定")
        if not payment_check['is_paid']:
            print("❌ 問題発見: ユーザーが決済済みと判定されていません")
            
            if payment_check['subscription_status'] == 'not_registered':
                print("   原因: データベースにユーザーが登録されていない")
            elif not subscription_status.get('is_active'):
                print("   原因: Stripeサブスクリプションが無効")
                if subscription_status.get('cancel_at_period_end'):
                    print("   - 詳細: 解約予定のサブスクリプション")
                else:
                    print(f"   - 詳細: サブスクリプション状態が '{subscription_status.get('status')}'")
            else:
                print("   原因: その他のエラー")
        else:
            print("✅ 問題なし: ユーザーは正常に決済済みと判定されています")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

def list_recent_users():
    """最近のユーザー一覧を表示"""
    print("\n📋 最近の企業一覧")
    print("=" * 30)
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT id, company_name, line_user_id, stripe_subscription_id, created_at
            FROM companies 
            ORDER BY created_at DESC 
            LIMIT 10
        ''')
        
        users = c.fetchall()
        
        for company in users:
            company_id, company_name, line_user_id, stripe_subscription_id, created_at = company
            print(f"ID: {company_id}, 企業名: {company_name}, LINE_ID: {line_user_id}, 作成日: {created_at}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        line_user_id = sys.argv[1]
        debug_user_payment_status(line_user_id)
    else:
        print("使用方法: python debug_user_payment_status.py <LINE_USER_ID>")
        print("例: python debug_user_payment_status.py U1234567890abcdef")
        print("\n最近の企業一覧:")
        list_recent_users() 