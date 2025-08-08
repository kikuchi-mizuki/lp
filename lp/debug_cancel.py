#!/usr/bin/env python3
"""
解約処理のデバッグスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.db import get_db_connection, get_db_type
from services.line_service import smart_number_extraction, validate_selection_numbers

def debug_company_cancellation(company_id):
    """企業の解約処理をデバッグ"""
    print(f"[DEBUG] 企業ID {company_id} の解約処理デバッグ開始")
    
    try:
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 1. 企業情報を確認
        c.execute(f'SELECT id, company_name, line_user_id FROM companies WHERE id = {placeholder}', (company_id,))
        company = c.fetchone()
        print(f"[DEBUG] 企業情報: {company}")
        
        # 2. company_line_accountsの内容を確認
        c.execute(f'''
            SELECT id, content_type, created_at, status
            FROM company_line_accounts
            WHERE company_id = {placeholder}
            ORDER BY created_at DESC
        ''', (company_id,))
        
        all_accounts = c.fetchall()
        print(f"[DEBUG] 全LINEアカウント数: {len(all_accounts)}")
        for account in all_accounts:
            print(f"[DEBUG] アカウント: {account}")
        
        # 3. アクティブなアカウントのみ確認
        c.execute(f'''
            SELECT id, content_type, created_at
            FROM company_line_accounts
            WHERE company_id = {placeholder} AND status = 'active'
            ORDER BY created_at DESC
        ''', (company_id,))
        
        active_accounts = c.fetchall()
        print(f"[DEBUG] アクティブアカウント数: {len(active_accounts)}")
        for account in active_accounts:
            print(f"[DEBUG] アクティブアカウント: {account}")
        
        # 4. 数字抽出のテスト
        selection_text = "1"
        numbers = smart_number_extraction(selection_text)
        valid_numbers, invalid_reasons, duplicates = validate_selection_numbers(numbers, len(active_accounts))
        
        print(f"[DEBUG] 選択テキスト: '{selection_text}'")
        print(f"[DEBUG] 抽出された数字: {numbers}")
        print(f"[DEBUG] 有効な選択インデックス: {valid_numbers}")
        print(f"[DEBUG] 最大選択可能数: {len(active_accounts)}")
        
        if invalid_reasons:
            print(f"[DEBUG] 無効な入力: {invalid_reasons}")
        if duplicates:
            print(f"[DEBUG] 重複除去: {duplicates}")
        
        # 5. 選択されたコンテンツを特定
        selected_contents = []
        for i, (account_id, content_type, created_at) in enumerate(active_accounts, 1):
            if i in valid_numbers:
                display_name = 'AI予定秘書' if content_type == 'ai_schedule' else content_type
                selected_contents.append({
                    'account_id': account_id,
                    'content_type': content_type,
                    'display_name': display_name,
                    'additional_price': 1500 if content_type in ["AIタスクコンシェルジュ", "AI経理秘書"] else 0
                })
                print(f"[DEBUG] 選択されたコンテンツ: {selected_contents[-1]}")
        
        print(f"[DEBUG] 最終的な選択コンテンツ数: {len(selected_contents)}")
        
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] デバッグエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # テスト対象の企業IDを指定（通常は1）
    company_id = 1
    debug_company_cancellation(company_id)