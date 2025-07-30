#!/usr/bin/env python3
"""
Stripe決済統合テストスクリプト
企業の決済管理・Webhook処理・自動通知機能をテスト
"""

import requests
import json
import time

def test_stripe_payment_integration():
    """Stripe決済統合テスト"""
    print("=== Stripe決済統合テスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    # テスト企業ID（既存の企業を使用）
    test_company_id = 1
    
    print(f"🔗 テスト対象企業ID: {test_company_id}")
    print(f"🌐 ベースURL: {base_url}")
    
    # 1. Stripe決済API ヘルスチェック
    print(f"\n📋 1. Stripe決済API ヘルスチェック")
    try:
        response = requests.get(f"{base_url}/api/v1/stripe/health")
        if response.status_code == 200:
            print(f"  ✅ ヘルスチェック成功: {response.json()}")
        else:
            print(f"  ❌ ヘルスチェック失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ ヘルスチェックエラー: {e}")
        return False
    
    # 2. Stripe顧客作成テスト
    print(f"\n📋 2. Stripe顧客作成テスト")
    try:
        payload = {
            "email": f"test-company-{test_company_id}@example.com"
        }
        
        response = requests.post(
            f"{base_url}/api/v1/stripe/companies/{test_company_id}/create-customer",
            json=payload
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"  ✅ 顧客作成成功: {result['message']}")
            print(f"     顧客ID: {result['customer_id']}")
        else:
            print(f"  ❌ 顧客作成失敗: {response.status_code}")
            print(f"     エラー: {response.json()}")
    except Exception as e:
        print(f"  ❌ 顧客作成エラー: {e}")
    
    # 3. サブスクリプション作成テスト
    print(f"\n📋 3. サブスクリプション作成テスト")
    try:
        # テスト用の価格ID（実際のStripe価格IDに置き換える必要があります）
        test_price_id = "price_test_monthly"
        
        payload = {
            "price_id": test_price_id,
            "trial_days": 14
        }
        
        response = requests.post(
            f"{base_url}/api/v1/stripe/companies/{test_company_id}/create-subscription",
            json=payload
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"  ✅ サブスクリプション作成成功: {result['message']}")
            print(f"     サブスクリプションID: {result['subscription_id']}")
            print(f"     ステータス: {result['status']}")
            print(f"     トライアル終了: {result['trial_end']}")
        else:
            print(f"  ❌ サブスクリプション作成失敗: {response.status_code}")
            print(f"     エラー: {response.json()}")
    except Exception as e:
        print(f"  ❌ サブスクリプション作成エラー: {e}")
    
    # 4. 決済状況取得テスト
    print(f"\n📋 4. 決済状況取得テスト")
    try:
        response = requests.get(f"{base_url}/api/v1/stripe/companies/{test_company_id}/payment-status")
        if response.status_code == 200:
            result = response.json()
            payment_info = result['payment_info']
            print(f"  ✅ 決済状況取得成功:")
            print(f"     顧客ID: {payment_info['customer_id']}")
            print(f"     サブスクリプションID: {payment_info['subscription_id']}")
            print(f"     支払いステータス: {payment_info['payment_status']}")
            print(f"     サブスクリプションステータス: {payment_info['subscription_status']}")
        else:
            print(f"  ❌ 決済状況取得失敗: {response.status_code}")
            print(f"     エラー: {response.json()}")
    except Exception as e:
        print(f"  ❌ 決済状況取得エラー: {e}")
    
    # 5. テスト決済通知テスト
    print(f"\n📋 5. テスト決済通知テスト")
    payment_types = [
        ("success", "支払い成功"),
        ("failed", "支払い失敗")
    ]
    
    for payment_type, description in payment_types:
        try:
            payload = {
                "type": payment_type
            }
            
            response = requests.post(
                f"{base_url}/api/v1/stripe/test-payment/{test_company_id}",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ {description}通知成功: {result['message']}")
            else:
                print(f"  ❌ {description}通知失敗: {response.status_code}")
        except Exception as e:
            print(f"  ❌ {description}通知エラー: {e}")
    
    # 6. 全決済情報取得テスト
    print(f"\n📋 6. 全決済情報取得テスト")
    try:
        response = requests.get(f"{base_url}/api/v1/stripe/payments")
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ 全決済情報取得成功:")
            print(f"     総決済数: {result['total_count']}")
            
            for payment in result['payments'][:3]:  # 最初の3件を表示
                print(f"     - {payment['company_name']}: {payment['payment_status']} ({payment['subscription_status']})")
        else:
            print(f"  ❌ 全決済情報取得失敗: {response.status_code}")
            print(f"     エラー: {response.json()}")
    except Exception as e:
        print(f"  ❌ 全決済情報取得エラー: {e}")
    
    # 7. サブスクリプション解約テスト
    print(f"\n📋 7. サブスクリプション解約テスト")
    try:
        response = requests.post(f"{base_url}/api/v1/stripe/companies/{test_company_id}/cancel-subscription")
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ 解約成功: {result['message']}")
            print(f"     サブスクリプションID: {result['subscription_id']}")
            print(f"     ステータス: {result['status']}")
        else:
            print(f"  ❌ 解約失敗: {response.status_code}")
            print(f"     エラー: {response.json()}")
    except Exception as e:
        print(f"  ❌ 解約エラー: {e}")
    
    print(f"\n🎉 Stripe決済統合テスト完了！")
    print(f"💡 次のステップ:")
    print(f"   1. 実際のStripe APIキーを設定")
    print(f"   2. 本物のStripe価格IDを使用")
    print(f"   3. Webhook URLを実際のドメインに設定")
    print(f"   4. 実際の決済処理を実装")
    
    return True

def test_stripe_payment_with_real_data():
    """実際のデータを使用したStripe決済テスト"""
    print(f"\n=== 実際のデータを使用したStripe決済テスト ===")
    
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
                
                # Stripe顧客作成
                payload = {
                    "email": f"{company_name.lower().replace(' ', '_')}@example.com"
                }
                
                response = requests.post(
                    f"{base_url}/api/v1/stripe/companies/{company_id}/create-customer",
                    json=payload
                )
                
                if response.status_code == 201:
                    print(f"  ✅ Stripe顧客作成成功")
                    
                    # テスト決済通知
                    test_payload = {
                        "type": "success"
                    }
                    
                    response = requests.post(
                        f"{base_url}/api/v1/stripe/test-payment/{company_id}",
                        json=test_payload
                    )
                    
                    if response.status_code == 200:
                        print(f"  ✅ テスト決済通知成功")
                    else:
                        print(f"  ❌ テスト決済通知失敗")
                else:
                    print(f"  ❌ Stripe顧客作成失敗")
        else:
            print(f"❌ 企業一覧取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 実際データテストエラー: {e}")

if __name__ == "__main__":
    print("🚀 Stripe決済統合テストを開始します...")
    print("注意: Flaskサーバーが起動していることを確認してください")
    print("サーバー起動方法: python app.py")
    print()
    
    # 基本テスト
    success = test_stripe_payment_integration()
    
    if success:
        # 実際のデータを使用したテスト
        test_stripe_payment_with_real_data()
    
    print(f"\n✅ テスト完了！") 