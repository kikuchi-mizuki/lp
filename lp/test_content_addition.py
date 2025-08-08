#!/usr/bin/env python3
"""
コンテンツ追加処理のテストスクリプト
"""

import os
import sys
from dotenv import load_dotenv

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.line_service import handle_content_confirmation_company

def test_content_addition():
    """コンテンツ追加処理をテスト"""
    print("=== コンテンツ追加処理テスト ===")
    
    try:
        # 環境変数を読み込み
        load_dotenv()
        
        # テスト用パラメータ
        company_id = 5  # テスト用企業ID
        content_type = "AI経理秘書"  # 追加料金が必要なコンテンツ
        
        print(f"テスト企業ID: {company_id}")
        print(f"追加コンテンツ: {content_type}")
        
        # コンテンツ追加処理を実行
        print(f"\n=== コンテンツ追加処理開始 ===")
        result = handle_content_confirmation_company(company_id, content_type)
        
        print(f"\n=== 処理結果 ===")
        print(f"成功: {result.get('success', False)}")
        
        if result.get('success'):
            print(f"企業ID: {result.get('company_id')}")
            print(f"コンテンツタイプ: {result.get('content_type')}")
            print(f"説明: {result.get('description')}")
            print(f"追加料金: {result.get('additional_price')}円")
            print(f"請求終了日: {result.get('billing_end_date')}")
        else:
            print(f"エラー: {result.get('error')}")
        
        print(f"\n=== テスト完了 ===")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_content_addition() 