#!/usr/bin/env python3
import os
import sys
sys.path.append('.')

from utils.db import get_db_connection

def check_database_status():
    """データベースの状況のみを確認"""
    
    print("=== データベース状況の確認 ===\n")
    
    try:
        # データベース接続
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業情報を取得
        c.execute('''
            SELECT id, company_name, stripe_subscription_id 
            FROM companies 
            WHERE stripe_subscription_id IS NOT NULL 
            ORDER BY id DESC 
            LIMIT 5
        ''')
        
        companies = c.fetchall()
        print(f"📊 アクティブな企業数: {len(companies)}")
        
        for company_id, company_name, stripe_subscription_id in companies:
            print(f"\n" + "="*60)
            print(f"🏢 企業: {company_name} (ID: {company_id})")
            print(f"💳 Stripeサブスクリプション: {stripe_subscription_id}")
            
            # コンテンツ状況をチェック
            c.execute('''
                SELECT content_type, status, created_at
                FROM company_line_accounts 
                WHERE company_id = %s
                ORDER BY created_at
            ''', (company_id,))
            
            contents = c.fetchall()
            active_contents = [c for c in contents if c[1] == 'active']
            
            print(f"\n📱 コンテンツ状況:")
            print(f"   - 総コンテンツ数: {len(contents)}")
            print(f"   - アクティブ数: {len(active_contents)}")
            print(f"   - 課金対象数: {max(0, len(active_contents) - 1)} (1個目は無料)")
            
            for i, (content_type, status, created_at) in enumerate(contents, 1):
                status_icon = "✅" if status == 'active' else "❌"
                free_flag = " (無料)" if i == 1 and status == 'active' else ""
                print(f"   {i}. {content_type}: {status_icon} {status}{free_flag} - {created_at}")
            
            # 分析
            if len(active_contents) == 0:
                print(f"   📊 分析: コンテンツなし → Stripe追加料金 = 0")
            elif len(active_contents) == 1:
                print(f"   📊 分析: 1個目のみ → Stripe追加料金 = 0 (無料)")
            else:
                expected_billing = len(active_contents) - 1
                expected_amount = expected_billing * 1500
                print(f"   📊 分析: {len(active_contents)}個 → Stripe追加料金数量 = {expected_billing}")
                print(f"   💰 期待される追加料金: ¥{expected_amount:,}/月")
            
            print("-" * 60)
        
        # 最新のユーザー状態も確認
        print(f"\n👤 最新のユーザー状態:")
        c.execute('''
            SELECT user_id, state 
            FROM user_states 
            ORDER BY updated_at DESC 
            LIMIT 5
        ''')
        
        user_states = c.fetchall()
        for user_id, state in user_states:
            print(f"   - {user_id[:20]}...: {state}")
        
        conn.close()
        
        print(f"\n🔍 次のステップ:")
        print(f"   1. LINEでコンテンツを追加して、ログを確認")
        print(f"   2. Stripe請求書で追加料金アイテムの数量を確認")
        print(f"   3. 数量が期待値と一致しない場合は、追加処理のログを詳細確認")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_status()