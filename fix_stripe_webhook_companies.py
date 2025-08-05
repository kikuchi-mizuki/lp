#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
決済時にcompaniesテーブルも自動的に作成されるように修正
"""

import os
import sys
sys.path.append('lp')

def fix_stripe_webhook():
    """Stripe webhook処理を修正"""
    try:
        print("=== Stripe Webhook処理修正 ===")
        
        # 現在のstripe.pyファイルを読み込み
        with open('lp/routes/stripe.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("現在のstripe.pyファイルを確認中...")
        
        # 新規ユーザー登録部分を修正
        # 既存のコードを探して修正
        old_code = """# 新規ユーザーとして登録
                c.execute('INSERT INTO users (email, stripe_customer_id, stripe_subscription_id) VALUES (%s, %s, %s)', (email, customer_id, subscription_id))
                conn.commit()
                print(f'新規ユーザー登録完了: email={email}, customer_id={customer_id}, subscription_id={subscription_id}')"""
        
        new_code = """# 新規ユーザーとして登録
                c.execute('INSERT INTO users (email, stripe_customer_id, stripe_subscription_id) VALUES (%s, %s, %s)', (email, customer_id, subscription_id))
                user_id = c.lastrowid
                
                # companiesテーブルにも企業データを作成
                company_name = f"企業_{email.split('@')[0]}"
                c.execute('''
                    INSERT INTO companies (company_name, company_code, stripe_subscription_id, status, created_at)
                    VALUES (%s, %s, %s, 'active', CURRENT_TIMESTAMP)
                ''', (company_name, f"company_{user_id}", subscription_id))
                company_id = c.lastrowid
                
                # company_paymentsテーブルにも決済データを作成
                c.execute('''
                    INSERT INTO company_payments (company_id, stripe_customer_id, stripe_subscription_id, subscription_status, created_at)
                    VALUES (%s, %s, %s, 'active', CURRENT_TIMESTAMP)
                ''', (company_id, customer_id, subscription_id))
                
                conn.commit()
                print(f'新規ユーザー登録完了: email={email}, customer_id={customer_id}, subscription_id={subscription_id}')
                print(f'企業データ作成完了: company_id={company_id}, company_name={company_name}')"""
        
        # 修正を適用
        if old_code in content:
            content = content.replace(old_code, new_code)
            print("✅ 新規ユーザー登録部分を修正しました")
        else:
            print("⚠️ 修正対象のコードが見つかりませんでした")
        
        # 既存ユーザー更新部分も修正
        old_update_code = """# 既存ユーザーの決済情報を更新
                c.execute('UPDATE users SET stripe_customer_id = %s, stripe_subscription_id = %s WHERE id = %s', (customer_id, subscription_id, user_id))
                conn.commit()
                print(f'既存ユーザーの決済情報を更新: id={user_id}, subscription_id={subscription_id}')"""
        
        new_update_code = """# 既存ユーザーの決済情報を更新
                c.execute('UPDATE users SET stripe_customer_id = %s, stripe_subscription_id = %s WHERE id = %s', (customer_id, subscription_id, user_id))
                
                # companiesテーブルに企業データが存在するかチェック
                c.execute('SELECT id FROM companies WHERE stripe_subscription_id = %s', (subscription_id,))
                existing_company = c.fetchone()
                
                if not existing_company:
                    # 企業データが存在しない場合は作成
                    company_name = f"企業_{email.split('@')[0]}"
                    c.execute('''
                        INSERT INTO companies (company_name, company_code, stripe_subscription_id, status, created_at)
                        VALUES (%s, %s, %s, 'active', CURRENT_TIMESTAMP)
                    ''', (company_name, f"company_{user_id}", subscription_id))
                    company_id = c.lastrowid
                    
                    # company_paymentsテーブルにも決済データを作成
                    c.execute('''
                        INSERT INTO company_payments (company_id, stripe_customer_id, stripe_subscription_id, subscription_status, created_at)
                        VALUES (%s, %s, %s, 'active', CURRENT_TIMESTAMP)
                    ''', (company_id, customer_id, subscription_id))
                    
                    print(f'企業データ作成完了: company_id={company_id}, company_name={company_name}')
                
                conn.commit()
                print(f'既存ユーザーの決済情報を更新: id={user_id}, subscription_id={subscription_id}')"""
        
        # 修正を適用
        if old_update_code in content:
            content = content.replace(old_update_code, new_update_code)
            print("✅ 既存ユーザー更新部分を修正しました")
        else:
            print("⚠️ 修正対象のコードが見つかりませんでした")
        
        # 修正したファイルを保存
        with open('lp/routes/stripe.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Stripe webhook処理の修正が完了しました")
        print("\n=== 修正内容 ===")
        print("1. 新規ユーザー登録時にcompaniesテーブルも自動作成")
        print("2. 既存ユーザー更新時にcompaniesテーブルも自動作成")
        print("3. company_paymentsテーブルにも決済データを自動作成")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_stripe_webhook() 