#!/usr/bin/env python3
"""
テスト用企業データ作成スクリプト
"""

from services.company_service import CompanyService
from services.company_line_service import CompanyLineService
import json

def create_test_companies():
    """テスト用の企業データを作成"""
    print("=== テスト用企業データ作成 ===")
    
    company_service = CompanyService()
    line_service = CompanyLineService()
    
    # テスト用企業データ
    test_companies = [
        {
            "company_name": "株式会社テックソリューション",
            "email": "info@techsolution.co.jp",
            "phone": "03-1234-5678",
            "address": "東京都渋谷区渋谷1-1-1",
            "industry": "IT",
            "employee_count": 150
        },
        {
            "company_name": "グローバル商事株式会社",
            "email": "contact@global-trading.co.jp",
            "phone": "03-2345-6789",
            "address": "東京都新宿区新宿2-2-2",
            "industry": "貿易",
            "employee_count": 80
        },
        {
            "company_name": "未来建設株式会社",
            "email": "info@mirai-construction.co.jp",
            "phone": "03-3456-7890",
            "address": "東京都港区港3-3-3",
            "industry": "建設業",
            "employee_count": 200
        },
        {
            "company_name": "サステナブルフーズ株式会社",
            "email": "info@sustainable-foods.co.jp",
            "phone": "03-4567-8901",
            "address": "東京都品川区品川4-4-4",
            "industry": "食品",
            "employee_count": 120
        },
        {
            "company_name": "デジタルマーケティング株式会社",
            "email": "hello@digital-marketing.co.jp",
            "phone": "03-5678-9012",
            "address": "東京都目黒区目黒5-5-5",
            "industry": "マーケティング",
            "employee_count": 60
        }
    ]
    
    created_companies = []
    
    for i, company_data in enumerate(test_companies, 1):
        print(f"\n📋 企業 {i} を作成中: {company_data['company_name']}")
        
        # 企業作成
        result = company_service.create_company(company_data)
        
        if result['success']:
            company_id = result['company_id']
            company_code = result['company_code']
            
            print(f"  ✅ 企業作成成功 - ID: {company_id}, コード: {company_code}")
            
            # LINEアカウント作成
            line_result = line_service.create_line_account(company_id, company_data)
            
            if line_result['success']:
                print(f"  ✅ LINEアカウント作成成功")
                created_companies.append({
                    'company_id': company_id,
                    'company_code': company_code,
                    'company_name': company_data['company_name'],
                    'line_account': line_result['line_account']
                })
            else:
                print(f"  ⚠️ LINEアカウント作成失敗: {line_result['error']}")
                created_companies.append({
                    'company_id': company_id,
                    'company_code': company_code,
                    'company_name': company_data['company_name'],
                    'line_account': None
                })
        else:
            print(f"  ❌ 企業作成失敗: {result['error']}")
    
    # 作成結果の表示
    print(f"\n🎉 テスト企業データ作成完了")
    print(f"📊 作成された企業数: {len(created_companies)}")
    
    print(f"\n📋 作成された企業一覧:")
    for company in created_companies:
        print(f"  - {company['company_name']} (ID: {company['company_id']}, コード: {company['company_code']})")
        if company['line_account']:
            print(f"    LINE Basic ID: {company['line_account']['basicId']}")
    
    # 企業一覧の取得テスト
    print(f"\n🔍 企業一覧取得テスト:")
    list_result = company_service.list_companies(page=1, limit=10)
    
    if list_result['success']:
        print(f"  総企業数: {list_result['pagination']['total_count']}")
        print(f"  ページ数: {list_result['pagination']['total_pages']}")
        print(f"  現在のページ: {list_result['pagination']['page']}")
        
        print(f"\n  企業一覧:")
        for company in list_result['companies']:
            print(f"    - {company['company_name']} ({company['company_code']}) - {company['status']}")
    else:
        print(f"  ❌ 企業一覧取得失敗: {list_result['error']}")
    
    # 統計情報の取得テスト
    if created_companies:
        print(f"\n📊 統計情報取得テスト:")
        stats_result = company_service.get_company_statistics(created_companies[0]['company_id'])
        
        if stats_result['success']:
            stats = stats_result['statistics']
            print(f"  コンテンツ統計:")
            print(f"    - 総コンテンツ数: {stats['contents']['total']}")
            print(f"    - アクティブコンテンツ数: {stats['contents']['active']}")
            print(f"    - 総利用回数: {stats['contents']['total_usage']}")
            
            print(f"  決済統計:")
            print(f"    - ステータス: {stats['payment']['status'] or '未設定'}")
        else:
            print(f"  ❌ 統計情報取得失敗: {stats_result['error']}")
    
    return created_companies

def test_company_api():
    """企業APIのテスト"""
    print(f"\n=== 企業APIテスト ===")
    
    import requests
    
    base_url = "http://localhost:5000"
    
    # 企業一覧取得テスト
    print(f"📋 企業一覧取得テスト")
    try:
        response = requests.get(f"{base_url}/api/v1/companies")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 成功 - 企業数: {data['pagination']['total_count']}")
        else:
            print(f"  ❌ 失敗 - ステータス: {response.status_code}")
    except Exception as e:
        print(f"  ❌ エラー: {e}")
    
    # 企業作成テスト
    print(f"📝 企業作成テスト")
    test_company = {
        "company_name": "APIテスト株式会社",
        "email": "api-test@example.com",
        "phone": "03-9999-9999",
        "industry": "IT",
        "employee_count": 10
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/companies",
            json=test_company,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"  ✅ 成功 - 企業ID: {data.get('company_id')}")
            
            # 作成された企業の詳細取得テスト
            company_id = data.get('company_id')
            if company_id:
                detail_response = requests.get(f"{base_url}/api/v1/companies/{company_id}")
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    print(f"  ✅ 詳細取得成功 - {detail_data['company']['company_name']}")
                else:
                    print(f"  ❌ 詳細取得失敗 - ステータス: {detail_response.status_code}")
        else:
            print(f"  ❌ 失敗 - ステータス: {response.status_code}")
            print(f"    レスポンス: {response.text}")
    except Exception as e:
        print(f"  ❌ エラー: {e}")

if __name__ == "__main__":
    print("テスト用企業データの作成を開始します...")
    print("注意: このスクリプトを実行する前に、Flaskサーバーが起動していることを確認してください")
    print("サーバー起動方法: python app.py")
    print()
    
    # テスト企業データの作成
    created_companies = create_test_companies()
    
    # APIテスト（サーバーが起動している場合）
    print(f"\n" + "="*50)
    test_company_api()
    
    print(f"\n🎉 テスト完了！")
    print(f"\n📝 次のステップ:")
    print(f"1. http://localhost:5000/company-dashboard でダッシュボードを確認")
    print(f"2. PostgreSQL管理画面で企業管理テーブルを確認")
    print(f"3. APIエンドポイントで企業データを確認") 