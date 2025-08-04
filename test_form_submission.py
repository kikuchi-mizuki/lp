#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
フォーム送信のテストスクリプト
"""

import sys
sys.path.append('lp')
from services.automated_ai_schedule_clone import AutomatedAIScheduleClone

def test_form_submission():
    """フォーム送信のテスト"""
    print("🧪 フォーム送信テスト開始")
    print("=" * 50)
    
    # テストデータ
    test_data = {
        'company_name': 'テスト企業株式会社',
        'line_channel_id': '2007858939',
        'line_access_token': '7DrmRKzZYZRT7uHBgKB7i8OMfaCDtSOBFWMTfW6v6pdB4ZyhqT',
        'line_channel_secret': '915352d9dd5bbd718a3127e4c89ff528'
    }
    
    try:
        # AutomatedAIScheduleCloneをテスト
        print("📝 ステップ1: AutomatedAIScheduleCloneのテスト")
        cloner = AutomatedAIScheduleClone()
        
        result = cloner.create_ai_schedule_clone(
            company_name=test_data['company_name'],
            line_channel_id=test_data['line_channel_id'],
            line_access_token=test_data['line_access_token'],
            line_channel_secret=test_data['line_channel_secret']
        )
        
        print(f"結果: {result}")
        
        if result['success']:
            print("✅ フォーム送信テスト成功")
            print(f"企業ID: {result.get('company_id')}")
            print(f"プロジェクトID: {result.get('project_id')}")
            print(f"プロジェクトURL: {result.get('project_url')}")
            print(f"メッセージ: {result.get('message')}")
        else:
            print("❌ フォーム送信テスト失敗")
            print(f"エラー: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🧪 テスト完了")

if __name__ == "__main__":
    test_form_submission() 