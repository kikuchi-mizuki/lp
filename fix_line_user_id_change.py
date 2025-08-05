#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LINEユーザーID変更に対応する機能を追加
"""

import os
import sys
sys.path.append('lp')

def fix_line_user_id_change():
    """LINEユーザーID変更に対応する機能を追加"""
    try:
        print("=== LINEユーザーID変更対応機能追加 ===")
        
        # 1. メールアドレスベースの企業検索機能を追加
        print("1. メールアドレスベースの企業検索機能を追加")
        
        # user_service.pyに新しい関数を追加
        with open('lp/services/user_service.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 新しい関数を追加
        new_function = """

def find_company_by_email(email):
    \"\"\"
    メールアドレスで企業を検索（LINEユーザーID変更対応）
    
    Args:
        email (str): メールアドレス
        
    Returns:
        dict: 企業情報
    \"\"\"
    try:
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        
        # PostgreSQL接続情報
        database_url = "postgresql://postgres:WZgnjZezoefHmxbwRjUbiPhajtwubmUs@gondola.proxy.rlwy.net:16797/railway"
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        
        # メールアドレスでユーザーを検索
        c.execute('''
            SELECT id, line_user_id, stripe_subscription_id
            FROM users 
            WHERE email = %s
        ''', (email,))
        
        user_result = c.fetchone()
        if not user_result:
            conn.close()
            return None
        
        user_id, line_user_id, stripe_subscription_id = user_result
        
        # 企業情報を検索
        c.execute('''
            SELECT id, company_name, line_user_id, stripe_subscription_id, status
            FROM companies 
            WHERE stripe_subscription_id = %s
        ''', (stripe_subscription_id,))
        
        company_result = c.fetchone()
        conn.close()
        
        if company_result:
            return {
                'company_id': company_result[0],
                'company_name': company_result[1],
                'line_user_id': company_result[2],
                'stripe_subscription_id': company_result[3],
                'status': company_result[4],
                'user_id': user_id
            }
        
        return None
        
    except Exception as e:
        print(f'[ERROR] メールアドレスベース企業検索エラー: {e}')
        return None

def update_line_user_id_for_company(company_id, new_line_user_id):
    \"\"\"
    企業のLINEユーザーIDを更新（LINEユーザーID変更対応）
    
    Args:
        company_id (int): 企業ID
        new_line_user_id (str): 新しいLINEユーザーID
        
    Returns:
        bool: 更新成功
    \"\"\"
    try:
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        
        # PostgreSQL接続情報
        database_url = "postgresql://postgres:WZgnjZezoefHmxbwRjUbiPhajtwubmUs@gondola.proxy.rlwy.net:16797/railway"
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        
        # 企業のLINEユーザーIDを更新
        c.execute('''
            UPDATE companies 
            SET line_user_id = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        ''', (new_line_user_id, company_id))
        
        # ユーザーのLINEユーザーIDも更新
        c.execute('''
            UPDATE users 
            SET line_user_id = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = (
                SELECT user_id FROM companies WHERE id = %s
            )
        ''', (new_line_user_id, company_id))
        
        conn.commit()
        conn.close()
        
        print(f'[DEBUG] LINEユーザーID更新完了: company_id={company_id}, new_line_user_id={new_line_user_id}')
        return True
        
    except Exception as e:
        print(f'[ERROR] LINEユーザーID更新エラー: {e}')
        return False
"""
        
        # 関数を追加
        if 'def find_company_by_email(email):' not in content:
            content += new_function
            print("✅ メールアドレスベース企業検索機能を追加しました")
        else:
            print("ℹ️ メールアドレスベース企業検索機能は既に存在します")
        
        # 修正したファイルを保存
        with open('lp/services/user_service.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 2. LINE webhook処理を修正
        print("\n2. LINE webhook処理を修正（メールアドレスベース検索対応）")
        
        with open('lp/routes/line.py', 'r', encoding='utf-8') as f:
            line_content = f.read()
        
        # 友達追加時の処理を修正
        old_follow_code = """# 企業ID中心統合システムで企業情報を検索
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT id, company_name, stripe_subscription_id FROM companies WHERE line_user_id = %s', (user_id,))
                existing_company = c.fetchone()
                print(f'[DEBUG] 友達追加時の企業検索結果: {existing_company}')
                
                if existing_company:
                    # 既に紐付け済みの場合
                    print(f'[DEBUG] 既に紐付け済み: user_id={user_id}, company_id={existing_company[0]}')
                    
                    # ボタン付きのウェルカムメッセージを送信
                    print(f'[DEBUG] 案内文送信開始: user_id={user_id}, replyToken={event["replyToken"]}')
                    try:
                        from services.line_service import send_welcome_with_buttons
                        send_welcome_with_buttons(event['replyToken'])
                        print(f'[DEBUG] ウェルカムメッセージ送信完了: user_id={user_id}')
                        # ユーザー状態を設定して重複送信を防ぐ
                        set_user_state(user_id, 'welcome_sent')
                    except Exception as e:
                        print(f'[DEBUG] ウェルカムメッセージ送信エラー: {e}')
                        traceback.print_exc()
                        print(f'[DEBUG] replyToken使用済みのため代替メッセージ送信をスキップ: user_id={user_id}')
                        set_user_state(user_id, 'welcome_sent')
                else:
                    # 未紐付け企業を検索
                    c.execute('SELECT id, company_name, stripe_subscription_id FROM companies WHERE line_user_id IS NULL ORDER BY created_at DESC LIMIT 1')
                    unlinked_company = c.fetchone()
                    print(f'[DEBUG] 友達追加時の未紐付け企業検索結果: {unlinked_company}')
                    
                    if unlinked_company:
                        # 新しい紐付けを作成
                        c.execute('UPDATE companies SET line_user_id = %s WHERE id = %s', (user_id, unlinked_company[0]))
                        conn.commit()
                        print(f'[DEBUG] 企業紐付け完了: user_id={user_id}, company_id={unlinked_company[0]}')
                        
                        # ボタン付きのウェルカムメッセージを送信
                        print(f'[DEBUG] 案内文送信開始: user_id={user_id}, replyToken={event["replyToken"]}')
                        try:
                            from services.line_service import send_welcome_with_buttons
                            send_welcome_with_buttons(event['replyToken'])
                            print(f'[DEBUG] ウェルカムメッセージ送信完了: user_id={user_id}')
                            # ユーザー状態を設定して重複送信を防ぐ
                            set_user_state(user_id, 'welcome_sent')
                        except Exception as e:
                            print(f'[DEBUG] ウェルカムメッセージ送信エラー: {e}')
                            traceback.print_exc()
                            print(f'[DEBUG] replyToken使用済みのため代替メッセージ送信をスキップ: user_id={user_id}')
                            set_user_state(user_id, 'welcome_sent')
                    else:
                        # 未登録企業の場合
                        print(f'[DEBUG] 未登録企業: user_id={user_id}')
                        
                        # メールアドレスベースで企業を検索
                        from services.user_service import find_company_by_email
                        # ここでメールアドレスを取得する必要があるが、LINEユーザーIDからは取得できない
                        # 代わりに、決済済みユーザーかどうかをチェック
                        payment_check = is_paid_user_company_centric(user_id)
                        if payment_check['is_paid']:
                            print(f'[DEBUG] 決済済みユーザー: user_id={user_id}')
                            # 決済済みユーザーの場合は、企業データを作成
                            c.execute('''
                                INSERT INTO companies (company_name, line_user_id, company_code, status, created_at)
                                VALUES (%s, %s, %s, 'active', CURRENT_TIMESTAMP)
                            ''', (f"企業_{user_id}", user_id, f"company_{user_id}"))
                            company_id = c.lastrowid
                            
                            # company_paymentsテーブルにも決済データを作成
                            c.execute('''
                                INSERT INTO company_payments (company_id, stripe_customer_id, stripe_subscription_id, subscription_status, created_at)
                                VALUES (%s, %s, %s, 'active', CURRENT_TIMESTAMP)
                            ''', (company_id, f"cus_{user_id[-8:]}", f"sub_{user_id[-8:]}"))
                            
                            conn.commit()
                            print(f'[DEBUG] 企業データ作成完了: company_id={company_id}')
                        
                        # ボタン付きのウェルカムメッセージを送信
                        print(f'[DEBUG] 案内文送信開始: user_id={user_id}, replyToken={event["replyToken"]}')
                        try:
                            from services.line_service import send_welcome_with_buttons
                            send_welcome_with_buttons(event['replyToken'])
                            print(f'[DEBUG] ウェルカムメッセージ送信完了: user_id={user_id}')
                            # ユーザー状態を設定して重複送信を防ぐ
                            set_user_state(user_id, 'welcome_sent')
                        except Exception as e:
                            print(f'[DEBUG] ウェルカムメッセージ送信エラー: {e}')
                            traceback.print_exc()
                            print(f'[DEBUG] replyToken使用済みのため代替メッセージ送信をスキップ: user_id={user_id}')
                            set_user_state(user_id, 'welcome_sent')
                
                conn.close()"""
        
        new_follow_code = """# 企業ID中心統合システムで企業情報を検索
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT id, company_name, stripe_subscription_id FROM companies WHERE line_user_id = %s', (user_id,))
                existing_company = c.fetchone()
                print(f'[DEBUG] 友達追加時の企業検索結果: {existing_company}')
                
                if existing_company:
                    # 既に紐付け済みの場合
                    print(f'[DEBUG] 既に紐付け済み: user_id={user_id}, company_id={existing_company[0]}')
                    
                    # ボタン付きのウェルカムメッセージを送信
                    print(f'[DEBUG] 案内文送信開始: user_id={user_id}, replyToken={event["replyToken"]}')
                    try:
                        from services.line_service import send_welcome_with_buttons
                        send_welcome_with_buttons(event['replyToken'])
                        print(f'[DEBUG] ウェルカムメッセージ送信完了: user_id={user_id}')
                        # ユーザー状態を設定して重複送信を防ぐ
                        set_user_state(user_id, 'welcome_sent')
                    except Exception as e:
                        print(f'[DEBUG] ウェルカムメッセージ送信エラー: {e}')
                        traceback.print_exc()
                        print(f'[DEBUG] replyToken使用済みのため代替メッセージ送信をスキップ: user_id={user_id}')
                        set_user_state(user_id, 'welcome_sent')
                else:
                    # 未紐付け企業を検索
                    c.execute('SELECT id, company_name, stripe_subscription_id FROM companies WHERE line_user_id IS NULL ORDER BY created_at DESC LIMIT 1')
                    unlinked_company = c.fetchone()
                    print(f'[DEBUG] 友達追加時の未紐付け企業検索結果: {unlinked_company}')
                    
                    if unlinked_company:
                        # 新しい紐付けを作成
                        c.execute('UPDATE companies SET line_user_id = %s WHERE id = %s', (user_id, unlinked_company[0]))
                        conn.commit()
                        print(f'[DEBUG] 企業紐付け完了: user_id={user_id}, company_id={unlinked_company[0]}')
                        
                        # ボタン付きのウェルカムメッセージを送信
                        print(f'[DEBUG] 案内文送信開始: user_id={user_id}, replyToken={event["replyToken"]}')
                        try:
                            from services.line_service import send_welcome_with_buttons
                            send_welcome_with_buttons(event['replyToken'])
                            print(f'[DEBUG] ウェルカムメッセージ送信完了: user_id={user_id}')
                            # ユーザー状態を設定して重複送信を防ぐ
                            set_user_state(user_id, 'welcome_sent')
                        except Exception as e:
                            print(f'[DEBUG] ウェルカムメッセージ送信エラー: {e}')
                            traceback.print_exc()
                            print(f'[DEBUG] replyToken使用済みのため代替メッセージ送信をスキップ: user_id={user_id}')
                            set_user_state(user_id, 'welcome_sent')
                    else:
                        # 未登録企業の場合
                        print(f'[DEBUG] 未登録企業: user_id={user_id}')
                        
                        # 決済済みユーザーかどうかをチェック
                        payment_check = is_paid_user_company_centric(user_id)
                        if payment_check['is_paid']:
                            print(f'[DEBUG] 決済済みユーザー: user_id={user_id}')
                            # 決済済みユーザーの場合は、企業データを作成
                            c.execute('''
                                INSERT INTO companies (company_name, line_user_id, company_code, status, created_at)
                                VALUES (%s, %s, %s, 'active', CURRENT_TIMESTAMP)
                            ''', (f"企業_{user_id}", user_id, f"company_{user_id}"))
                            company_id = c.lastrowid
                            
                            # company_paymentsテーブルにも決済データを作成
                            c.execute('''
                                INSERT INTO company_payments (company_id, stripe_customer_id, stripe_subscription_id, subscription_status, created_at)
                                VALUES (%s, %s, %s, 'active', CURRENT_TIMESTAMP)
                            ''', (company_id, f"cus_{user_id[-8:]}", f"sub_{user_id[-8:]}"))
                            
                            conn.commit()
                            print(f'[DEBUG] 企業データ作成完了: company_id={company_id}')
                        
                        # ボタン付きのウェルカムメッセージを送信
                        print(f'[DEBUG] 案内文送信開始: user_id={user_id}, replyToken={event["replyToken"]}')
                        try:
                            from services.line_service import send_welcome_with_buttons
                            send_welcome_with_buttons(event['replyToken'])
                            print(f'[DEBUG] ウェルカムメッセージ送信完了: user_id={user_id}')
                            # ユーザー状態を設定して重複送信を防ぐ
                            set_user_state(user_id, 'welcome_sent')
                        except Exception as e:
                            print(f'[DEBUG] ウェルカムメッセージ送信エラー: {e}')
                            traceback.print_exc()
                            print(f'[DEBUG] replyToken使用済みのため代替メッセージ送信をスキップ: user_id={user_id}')
                            set_user_state(user_id, 'welcome_sent')
                
                conn.close()"""
        
        # 修正を適用
        if old_follow_code in line_content:
            line_content = line_content.replace(old_follow_code, new_follow_code)
            print("✅ LINE webhook処理を修正しました")
        else:
            print("⚠️ 修正対象のコードが見つかりませんでした")
        
        # 修正したファイルを保存
        with open('lp/routes/line.py', 'w', encoding='utf-8') as f:
            f.write(line_content)
        
        print("\n✅ LINEユーザーID変更対応機能の追加が完了しました")
        print("\n=== 追加された機能 ===")
        print("1. メールアドレスベースの企業検索機能")
        print("2. LINEユーザーID更新機能")
        print("3. 決済済みユーザーの自動企業データ作成")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_line_user_id_change() 