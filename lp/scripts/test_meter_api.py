import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

def test_meter_api():
    """Meter付き従量課金のAPIをテスト"""
    stripe_secret_key = os.getenv('STRIPE_SECRET_KEY')
    print(f'Stripe Secret Key: {stripe_secret_key[:20]}...')
    
    headers = {
        'Authorization': f'Bearer {stripe_secret_key}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # テスト1: billing/meter_events API
    print("\n=== テスト1: billing/meter_events API ===")
    try:
        response = requests.post(
            'https://api.stripe.com/v1/billing/meter_events',
            headers=headers,
            data={
                'meter': 'mtr_test_61SuTp31IPUvCq22o41Ixg6C5hAVd1Gi',
                'value': 1,
                'timestamp': int(time.time())
            }
        )
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')
    except Exception as e:
        print(f'Error: {e}')
    
    # テスト2: billing/meter_events API with different parameters
    print("\n=== テスト2: billing/meter_events API (quantity) ===")
    try:
        response = requests.post(
            'https://api.stripe.com/v1/billing/meter_events',
            headers=headers,
            data={
                'meter': 'mtr_test_61SuTp31IPUvCq22o41Ixg6C5hAVd1Gi',
                'quantity': 1,
                'timestamp': int(time.time())
            }
        )
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')
    except Exception as e:
        print(f'Error: {e}')
    
    # テスト3: subscription_items usage_records API
    print("\n=== テスト3: subscription_items usage_records API ===")
    try:
        response = requests.post(
            'https://api.stripe.com/v1/subscription_items/si_SkLO2r1qtiXXRM/usage_records',
            headers=headers,
            data={
                'quantity': 1,
                'timestamp': int(time.time()),
                'action': 'increment'
            }
        )
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')
    except Exception as e:
        print(f'Error: {e}')
    
    # テスト4: Get meter details
    print("\n=== テスト4: Get meter details ===")
    try:
        response = requests.get(
            'https://api.stripe.com/v1/billing/meters/mtr_test_61SuTp31IPUvCq22o41Ixg6C5hAVd1Gi',
            headers=headers
        )
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')
    except Exception as e:
        print(f'Error: {e}')

    # テスト5: billing/meter_events API with correct parameters based on meter details
    print("\n=== テスト5: billing/meter_events API (correct parameters) ===")
    try:
        response = requests.post(
            'https://api.stripe.com/v1/billing/meter_events',
            headers=headers,
            data={
                'meter': 'mtr_test_61SuTp31IPUvCq22o41Ixg6C5hAVd1Gi',
                'stripe_customer_id': 'cus_SkLBddqBLEEg4N',  # customer_mappingから
                'value': 1,  # value_settingsから
                'timestamp': int(time.time())
            }
        )
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')
    except Exception as e:
        print(f'Error: {e}')
    
    # テスト6: billing/meter_events API with event_name
    print("\n=== テスト6: billing/meter_events API (with event_name) ===")
    try:
        response = requests.post(
            'https://api.stripe.com/v1/billing/meter_events',
            headers=headers,
            data={
                'meter': 'mtr_test_61SuTp31IPUvCq22o41Ixg6C5hAVd1Gi',
                'event_name': 'aiコレクションズ',
                'stripe_customer_id': 'cus_SkLBddqBLEEg4N',
                'value': 1,
                'timestamp': int(time.time())
            }
        )
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')
    except Exception as e:
        print(f'Error: {e}')

    # テスト7: billing/meter_events API with minimal parameters
    print("\n=== テスト7: billing/meter_events API (minimal parameters) ===")
    try:
        response = requests.post(
            'https://api.stripe.com/v1/billing/meter_events',
            headers=headers,
            data={
                'event_name': 'aiコレクションズ',
                'timestamp': int(time.time())
            }
        )
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')
    except Exception as e:
        print(f'Error: {e}')
    
    # テスト8: billing/meter_events API with customer_id
    print("\n=== テスト8: billing/meter_events API (with customer_id) ===")
    try:
        response = requests.post(
            'https://api.stripe.com/v1/billing/meter_events',
            headers=headers,
            data={
                'event_name': 'aiコレクションズ',
                'customer_id': 'cus_SkLBddqBLEEg4N',
                'timestamp': int(time.time())
            }
        )
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')
    except Exception as e:
        print(f'Error: {e}')
    
    # テスト9: billing/meter_events API with JSON payload
    print("\n=== テスト9: billing/meter_events API (JSON payload) ===")
    try:
        headers_json = {
            'Authorization': f'Bearer {stripe_secret_key}',
            'Content-Type': 'application/json'
        }
        response = requests.post(
            'https://api.stripe.com/v1/billing/meter_events',
            headers=headers_json,
            json={
                'event_name': 'aiコレクションズ',
                'customer_id': 'cus_SkLBddqBLEEg4N',
                'timestamp': int(time.time())
            }
        )
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')
    except Exception as e:
        print(f'Error: {e}')

    # テスト10: billing/meter_events API with payload
    print("\n=== テスト10: billing/meter_events API (with payload) ===")
    try:
        import json
        payload_data = {
            'stripe_customer_id': 'cus_SkLBddqBLEEg4N',
            'value': 1
        }
        response = requests.post(
            'https://api.stripe.com/v1/billing/meter_events',
            headers=headers,
            data={
                'event_name': 'aiコレクションズ',
                'payload': json.dumps(payload_data),
                'timestamp': int(time.time())
            }
        )
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')
    except Exception as e:
        print(f'Error: {e}')

    # テスト11: billing/meter_events API with correct parameters
    print("\n=== テスト11: billing/meter_events API (correct parameters) ===")
    try:
        response = requests.post(
            'https://api.stripe.com/v1/billing/meter_events',
            headers=headers,
            data={
                'event_name': 'aiコレクションズ',
                'timestamp': int(time.time())
            }
        )
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')
    except Exception as e:
        print(f'Error: {e}')
    
    # テスト12: billing/meter_events API with customer parameter
    print("\n=== テスト12: billing/meter_events API (with customer) ===")
    try:
        response = requests.post(
            'https://api.stripe.com/v1/billing/meter_events',
            headers=headers,
            data={
                'event_name': 'aiコレクションズ',
                'customer': 'cus_SkLBddqBLEEg4N',
                'timestamp': int(time.time())
            }
        )
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')
    except Exception as e:
        print(f'Error: {e}')
    
    # テスト13: billing/meter_events API with value parameter
    print("\n=== テスト13: billing/meter_events API (with value) ===")
    try:
        response = requests.post(
            'https://api.stripe.com/v1/billing/meter_events',
            headers=headers,
            data={
                'event_name': 'aiコレクションズ',
                'customer': 'cus_SkLBddqBLEEg4N',
                'value': 1,
                'timestamp': int(time.time())
            }
        )
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')
    except Exception as e:
        print(f'Error: {e}')

    # テスト14: Stripe公式ドキュメントに基づく正しいAPI
    print("\n=== テスト14: Stripe公式ドキュメントに基づく正しいAPI ===")
    try:
        # Stripe公式ドキュメント: https://stripe.com/docs/api/billing/meter_events/create
        response = requests.post(
            'https://api.stripe.com/v1/billing/meter_events',
            headers=headers,
            data={
                'event_name': 'aiコレクションズ',
                'payload': json.dumps({
                    'stripe_customer_id': 'cus_SkLBddqBLEEg4N',
                    'value': 1
                }),
                'timestamp': int(time.time())
            }
        )
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')
        
        if response.status_code == 200:
            print("✅ 成功！正しいAPIとパラメータが見つかりました")
        else:
            print("❌ まだ失敗しています")
            
    except Exception as e:
        print(f'Error: {e}')
    
    # テスト15: 代替案 - 従来のusage_records APIを使用
    print("\n=== テスト15: 代替案 - 従来のusage_records API ===")
    try:
        # 従来のAPIを使用して、Meter付き従量課金を回避
        response = requests.post(
            'https://api.stripe.com/v1/subscription_items/si_SkLO2r1qtiXXRM/usage_records',
            headers=headers,
            data={
                'quantity': 1,
                'timestamp': int(time.time()),
                'action': 'increment'
            }
        )
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')
        
        if response.status_code == 200:
            print("✅ 従来のAPIが成功しました")
        else:
            print("❌ 従来のAPIも失敗しています")
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    test_meter_api() 