#!/usr/bin/env python3
"""
AI予定秘書複製作成スクリプト
"""

import os
import sys
import time
import requests
import json
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.company_registration_service import CompanyRegistrationService

def create_ai_schedule_clone(company_name="テスト企業", line_channel_id="", line_access_token="", line_channel_secret=""):
    """AI予定秘書の複製を作成"""
    try:
        print(f"🚀 AI予定秘書複製作成開始: {company_name}")
        print("=" * 60)
        
        # サービスインスタンスを作成
        service = CompanyRegistrationService()
        
        # Railwayトークンの確認
        if not service.railway_token:
            print("❌ Railwayトークンが設定されていません")
            print("環境変数 RAILWAY_TOKEN を設定してください")
            return False
        
        print(f"✅ Railwayトークン確認: {service.railway_token[:8]}...")
        
        # 企業データを準備
        company_data = {
            'company_name': company_name,
            'line_channel_id': line_channel_id or "2007858939",  # デフォルト値
            'line_access_token': line_access_token or "dummy_token",
            'line_channel_secret': line_channel_secret or "dummy_secret",
            'content_type': 'AI予定秘書'
        }
        
        # LINE認証情報を準備
        line_credentials = {
            'line_channel_id': company_data['line_channel_id'],
            'line_channel_access_token': company_data['line_access_token'],
            'line_channel_secret': company_data['line_channel_secret'],
            'company_name': company_data['company_name']
        }
        
        # AI予定秘書プロジェクトを複製
        print(f"\n📦 AI予定秘書プロジェクト複製中...")
        railway_result = service.clone_ai_schedule_project(1, company_data['company_name'], line_credentials)
        
        if railway_result['success']:
            print(f"✅ AI予定秘書プロジェクト複製成功!")
            print(f"  - プロジェクト名: {railway_result['project_name']}")
            print(f"  - プロジェクトID: {railway_result['project_id']}")
            
            if railway_result.get('manual_setup_required'):
                print(f"\n📋 手動設定が必要です:")
                setup_instructions = railway_result['setup_instructions']
                print(f"  - プロジェクトURL: {setup_instructions['project_url']}")
                print(f"  - プロジェクトID: {setup_instructions['project_id']}")
                
                print(f"\n🔧 設定手順:")
                for step in setup_instructions['steps']:
                    print(f"  {step}")
                
                # 環境変数設定の提案
                print(f"\n⚙️ 推奨環境変数設定:")
                print(f"  LINE_CHANNEL_ID={line_credentials['line_channel_id']}")
                print(f"  LINE_CHANNEL_ACCESS_TOKEN={line_credentials['line_channel_access_token']}")
                print(f"  LINE_CHANNEL_SECRET={line_credentials['line_channel_secret']}")
                print(f"  COMPANY_ID=1")
                print(f"  COMPANY_NAME={company_data['company_name']}")
                print(f"  BASE_URL=https://{railway_result['project_name']}.up.railway.app")
            
            return railway_result
        else:
            print(f"❌ AI予定秘書プロジェクト複製失敗: {railway_result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ AI予定秘書複製作成エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン関数"""
    print("AI予定秘書複製作成ツール")
    print("=" * 40)
    
    # コマンドライン引数の処理
    if len(sys.argv) > 1:
        company_name = sys.argv[1]
    else:
        company_name = input("企業名を入力してください: ").strip()
        if not company_name:
            company_name = f"テスト企業-{int(time.time())}"
    
    # LINE認証情報の入力（オプション）
    line_channel_id = input("LINEチャネルID（Enterでスキップ）: ").strip()
    line_access_token = input("LINEチャネルアクセストークン（Enterでスキップ）: ").strip()
    line_channel_secret = input("LINEチャネルシークレット（Enterでスキップ）: ").strip()
    
    # AI予定秘書複製を作成
    result = create_ai_schedule_clone(
        company_name=company_name,
        line_channel_id=line_channel_id,
        line_access_token=line_access_token,
        line_channel_secret=line_channel_secret
    )
    
    if result:
        print(f"\n✅ AI予定秘書複製作成完了!")
        print(f"企業名: {company_name}")
        if isinstance(result, dict) and result.get('project_url'):
            print(f"プロジェクトURL: {result['project_url']}")
    else:
        print(f"\n❌ AI予定秘書複製作成失敗")

if __name__ == "__main__":
    main() 