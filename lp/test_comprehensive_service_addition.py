#!/usr/bin/env python3
"""
包括的サービス追加テストスクリプト
"""

import os
import sys
import time
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.company_registration_service import CompanyRegistrationService

def test_comprehensive_service_addition():
    """包括的なサービス追加テスト"""
    
    print("=== 包括的サービス追加テスト ===")
    print(f"テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # サービスインスタンスを作成
    service = CompanyRegistrationService()
    
    # Railwayトークンの確認
    if not service.railway_token:
        print("❌ Railwayトークンが設定されていません")
        print("環境変数 RAILWAY_TOKEN を設定してください")
        return False
    
    print(f"✅ Railwayトークン確認済み: {service.railway_token[:8]}...")
    
    # 1. テスト用プロジェクトを作成
    print("\n1. テスト用プロジェクトを作成中...")
    
    test_project_name = f"test-service-addition-{int(time.time())}"
    
    url = "https://backboard.railway.app/graphql/v2"
    headers = service.get_railway_headers()
    
    create_query = """
    mutation CreateProject($name: String!, $description: String) {
        projectCreate(input: { name: $name, description: $description }) {
            id
            name
            description
        }
    }
    """
    
    variables = {
        "name": test_project_name,
        "description": f"包括的サービス追加テスト用プロジェクト - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    }
    
    payload = {
        "query": create_query,
        "variables": variables
    }
    
    try:
        import requests
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['projectCreate']:
                project = data['data']['projectCreate']
                project_id = project['id']
                print(f"✅ テストプロジェクト作成成功: {project['name']} (ID: {project_id})")
            else:
                print(f"❌ プロジェクト作成失敗: {data}")
                return False
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ プロジェクト作成エラー: {e}")
        return False
    
    # 2. 包括的なサービス追加テスト
    print(f"\n2. 包括的サービス追加テスト開始...")
    print(f"プロジェクトID: {project_id}")
    
    try:
        result = service.add_service_to_project(project_id)
        
        if result:
            print(f"\n=== サービス追加結果 ===")
            print(f"成功: {result.get('success', False)}")
            print(f"方法: {result.get('method', 'unknown')}")
            
            if result.get('success'):
                print("✅ サービス追加が成功しました！")
                
                if result.get('method') == 'railway_cli':
                    print("Railway CLIを使用してサービスが追加されました")
                elif result.get('method') == 'github_actions':
                    print("GitHub Actionsワークフローが作成されました")
                    print(f"ワークフローファイル: {result.get('workflow_file')}")
                    print(f"メッセージ: {result.get('message')}")
                elif result.get('method') == 'railway_api':
                    print("Railway APIを使用してサービスが追加されました")
                    service_info = result.get('service', {})
                    print(f"サービス名: {service_info.get('name')}")
                    print(f"サービスID: {service_info.get('id')}")
                
                return True
            else:
                print("⚠️ 自動サービス追加は失敗しましたが、手動設定の指示が生成されました")
                
                if result.get('manual_setup_required'):
                    instructions = result.get('instructions', {})
                    print(f"プロジェクトURL: {instructions.get('project_url')}")
                    print("手動設定手順:")
                    for i, step in enumerate(instructions.get('steps', []), 1):
                        print(f"  {i}. {step}")
                
                return False
        else:
            print("❌ サービス追加が完全に失敗しました")
            return False
            
    except Exception as e:
        print(f"❌ サービス追加テストエラー: {e}")
        return False

def test_railway_cli_directly():
    """Railway CLIを直接テスト"""
    
    print("\n=== Railway CLI直接テスト ===")
    
    # Railway CLIの確認
    try:
        import subprocess
        result = subprocess.run(['railway', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Railway CLI確認済み: {result.stdout.strip()}")
        else:
            print("❌ Railway CLIが利用できません")
            return False
    except Exception as e:
        print(f"❌ Railway CLI確認エラー: {e}")
        return False
    
    # Railway CLIログインテスト
    railway_token = os.getenv('RAILWAY_TOKEN')
    if not railway_token:
        print("❌ Railwayトークンが設定されていません")
        return False
    
    try:
        env = os.environ.copy()
        env['RAILWAY_TOKEN'] = railway_token
        
        result = subprocess.run(['railway', 'login'], input=railway_token, text=True, capture_output=True, env=env, timeout=30)
        
        if result.returncode == 0:
            print("✅ Railway CLIログイン成功")
            return True
        else:
            print(f"⚠️ Railway CLIログイン失敗: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Railway CLIログインエラー: {e}")
        return False

def main():
    """メイン関数"""
    
    print("包括的サービス追加テストを開始します...")
    print("=" * 50)
    
    # 1. Railway CLI直接テスト
    cli_success = test_railway_cli_directly()
    
    # 2. 包括的サービス追加テスト
    service_success = test_comprehensive_service_addition()
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("=== テスト結果サマリー ===")
    print(f"Railway CLIテスト: {'✅ 成功' if cli_success else '❌ 失敗'}")
    print(f"サービス追加テスト: {'✅ 成功' if service_success else '❌ 失敗'}")
    
    if cli_success and service_success:
        print("\n🎉 すべてのテストが成功しました！")
        print("サービス追加の自動化が正常に動作しています。")
    elif cli_success and not service_success:
        print("\n⚠️ Railway CLIは動作しますが、サービス追加に問題があります。")
        print("手動設定が必要な場合があります。")
    else:
        print("\n❌ Railway CLIに問題があります。")
        print("Railway CLIの設定を確認してください。")
    
    return cli_success and service_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 