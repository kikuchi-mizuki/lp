#!/usr/bin/env python3
"""
コンテンツ管理統合テストスクリプト
企業のコンテンツ管理・自動配信機能をテスト
"""

import requests
import json
import time

def test_content_management_integration():
    """コンテンツ管理統合テスト"""
    print("=== コンテンツ管理統合テスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    # テスト企業ID（既存の企業を使用）
    test_company_id = 1
    
    print(f"🔗 テスト対象企業ID: {test_company_id}")
    print(f"🌐 ベースURL: {base_url}")
    
    # 1. コンテンツ管理API ヘルスチェック
    print(f"\n📋 1. コンテンツ管理API ヘルスチェック")
    try:
        response = requests.get(f"{base_url}/api/v1/content/health")
        if response.status_code == 200:
            print(f"  ✅ ヘルスチェック成功: {response.json()}")
        else:
            print(f"  ❌ ヘルスチェック失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ ヘルスチェックエラー: {e}")
        return False
    
    # 2. 利用可能なコンテンツ一覧取得テスト
    print(f"\n📋 2. 利用可能なコンテンツ一覧取得テスト")
    try:
        response = requests.get(f"{base_url}/api/v1/content/available")
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ コンテンツ一覧取得成功:")
            for content_type, content_info in result['contents'].items():
                print(f"     - {content_info['name']}: {content_info['description']} (¥{content_info['price']})")
        else:
            print(f"  ❌ コンテンツ一覧取得失敗: {response.status_code}")
            print(f"     エラー: {response.json()}")
    except Exception as e:
        print(f"  ❌ コンテンツ一覧取得エラー: {e}")
    
    # 3. コンテンツ追加テスト
    print(f"\n📋 3. コンテンツ追加テスト")
    content_types = ['ai_accounting', 'ai_schedule', 'ai_task']
    
    for content_type in content_types:
        try:
            payload = {
                "content_type": content_type,
                "status": "active"
            }
            
            response = requests.post(
                f"{base_url}/api/v1/content/companies/{test_company_id}/add",
                json=payload
            )
            
            if response.status_code == 201:
                result = response.json()
                print(f"  ✅ {content_type}追加成功: {result['message']}")
            else:
                print(f"  ❌ {content_type}追加失敗: {response.status_code}")
                print(f"     エラー: {response.json()}")
        except Exception as e:
            print(f"  ❌ {content_type}追加エラー: {e}")
    
    # 4. 企業のコンテンツ一覧取得テスト
    print(f"\n📋 4. 企業のコンテンツ一覧取得テスト")
    try:
        response = requests.get(f"{base_url}/api/v1/content/companies/{test_company_id}/contents")
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ 企業コンテンツ一覧取得成功:")
            print(f"     総コンテンツ数: {result['total_count']}")
            
            for content in result['contents']:
                print(f"     - {content['content_name']}: {content['status']}")
                print(f"       機能: {', '.join(content['features'])}")
        else:
            print(f"  ❌ 企業コンテンツ一覧取得失敗: {response.status_code}")
            print(f"     エラー: {response.json()}")
    except Exception as e:
        print(f"  ❌ 企業コンテンツ一覧取得エラー: {e}")
    
    # 5. コンテンツステータス更新テスト
    print(f"\n📋 5. コンテンツステータス更新テスト")
    try:
        payload = {
            "content_type": "ai_accounting",
            "status": "suspended"
        }
        
        response = requests.put(
            f"{base_url}/api/v1/content/companies/{test_company_id}/update-status",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ ステータス更新成功: {result['message']}")
            print(f"     新しいステータス: {result['status']}")
        else:
            print(f"  ❌ ステータス更新失敗: {response.status_code}")
            print(f"     エラー: {response.json()}")
    except Exception as e:
        print(f"  ❌ ステータス更新エラー: {e}")
    
    # 6. コンテンツ通知テスト
    print(f"\n📋 6. コンテンツ通知テスト")
    notification_types = [
        ("usage_reminder", "利用状況リマインダー"),
        ("feature_update", "機能更新通知"),
        ("maintenance", "メンテナンス通知"),
        ("custom", "カスタム通知")
    ]
    
    for message_type, description in notification_types:
        try:
            payload = {
                "content_type": "ai_accounting",
                "message_type": message_type,
                "custom_message": f"テスト: {description}です。" if message_type == "custom" else ""
            }
            
            response = requests.post(
                f"{base_url}/api/v1/content/companies/{test_company_id}/notify",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ {description}成功: {result['message']}")
            else:
                print(f"  ❌ {description}失敗: {response.status_code}")
        except Exception as e:
            print(f"  ❌ {description}エラー: {e}")
    
    # 7. コンテンツ統計取得テスト
    print(f"\n📋 7. コンテンツ統計取得テスト")
    try:
        # 企業別統計
        response = requests.get(f"{base_url}/api/v1/content/statistics?company_id={test_company_id}")
        if response.status_code == 200:
            result = response.json()
            stats = result['statistics']
            print(f"  ✅ 企業別統計取得成功:")
            print(f"     総コンテンツ数: {stats['total_contents']}")
            print(f"     アクティブ: {stats['active_contents']}")
            print(f"     非アクティブ: {stats['inactive_contents']}")
            print(f"     一時停止: {stats['suspended_contents']}")
        else:
            print(f"  ❌ 企業別統計取得失敗: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 企業別統計取得エラー: {e}")
    
    try:
        # 全体統計
        response = requests.get(f"{base_url}/api/v1/content/statistics")
        if response.status_code == 200:
            result = response.json()
            stats = result['statistics']
            print(f"  ✅ 全体統計取得成功:")
            print(f"     総コンテンツ数: {stats['total_contents']}")
            print(f"     総アクティブ数: {stats['total_active']}")
            
            for breakdown in stats['content_breakdown']:
                print(f"     - {breakdown['content_type']}: {breakdown['total_count']}件 (アクティブ: {breakdown['active_count']}件)")
        else:
            print(f"  ❌ 全体統計取得失敗: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 全体統計取得エラー: {e}")
    
    # 8. 全企業コンテンツ一覧取得テスト
    print(f"\n📋 8. 全企業コンテンツ一覧取得テスト")
    try:
        response = requests.get(f"{base_url}/api/v1/content/all-contents")
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ 全企業コンテンツ一覧取得成功:")
            print(f"     総コンテンツ数: {result['total_count']}")
            
            for content in result['contents'][:3]:  # 最初の3件を表示
                print(f"     - {content['company_name']}: {content['content_name']} ({content['status']})")
        else:
            print(f"  ❌ 全企業コンテンツ一覧取得失敗: {response.status_code}")
            print(f"     エラー: {response.json()}")
    except Exception as e:
        print(f"  ❌ 全企業コンテンツ一覧取得エラー: {e}")
    
    # 9. コンテンツ削除テスト
    print(f"\n📋 9. コンテンツ削除テスト")
    try:
        payload = {
            "content_type": "ai_task"
        }
        
        response = requests.post(
            f"{base_url}/api/v1/content/companies/{test_company_id}/remove",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ コンテンツ削除成功: {result['message']}")
        else:
            print(f"  ❌ コンテンツ削除失敗: {response.status_code}")
            print(f"     エラー: {response.json()}")
    except Exception as e:
        print(f"  ❌ コンテンツ削除エラー: {e}")
    
    print(f"\n🎉 コンテンツ管理統合テスト完了！")
    print(f"💡 次のステップ:")
    print(f"   1. 実際のコンテンツ配信機能の実装")
    print(f"   2. スケジュール通知機能の実装")
    print(f"   3. コンテンツ利用状況追跡機能の実装")
    print(f"   4. 自動コンテンツ配信機能の実装")
    
    return True

def test_content_management_with_real_data():
    """実際のデータを使用したコンテンツ管理テスト"""
    print(f"\n=== 実際のデータを使用したコンテンツ管理テスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    # 企業一覧を取得
    try:
        response = requests.get(f"{base_url}/api/v1/companies")
        if response.status_code == 200:
            companies = response.json()
            print(f"📋 利用可能な企業数: {len(companies)}")
            
            for company in companies[:3]:  # 最初の3社でテスト
                company_id = company['id']
                company_name = company['company_name']
                
                print(f"\n🏢 企業: {company_name} (ID: {company_id})")
                
                # コンテンツ追加
                payload = {
                    "content_type": "ai_accounting",
                    "status": "active"
                }
                
                response = requests.post(
                    f"{base_url}/api/v1/content/companies/{company_id}/add",
                    json=payload
                )
                
                if response.status_code == 201:
                    print(f"  ✅ AI経理秘書追加成功")
                    
                    # 通知送信
                    notify_payload = {
                        "content_type": "ai_accounting",
                        "message_type": "custom",
                        "custom_message": f"{company_name}様、AI経理秘書の設定が完了しました。"
                    }
                    
                    response = requests.post(
                        f"{base_url}/api/v1/content/companies/{company_id}/notify",
                        json=notify_payload
                    )
                    
                    if response.status_code == 200:
                        print(f"  ✅ 通知送信成功")
                    else:
                        print(f"  ❌ 通知送信失敗")
                else:
                    print(f"  ❌ AI経理秘書追加失敗")
        else:
            print(f"❌ 企業一覧取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 実際データテストエラー: {e}")

if __name__ == "__main__":
    print("🚀 コンテンツ管理統合テストを開始します...")
    print("注意: Flaskサーバーが起動していることを確認してください")
    print("サーバー起動方法: python app.py")
    print()
    
    # 基本テスト
    success = test_content_management_integration()
    
    if success:
        # 実際のデータを使用したテスト
        test_content_management_with_real_data()
    
    print(f"\n✅ テスト完了！") 