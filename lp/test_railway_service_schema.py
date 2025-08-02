#!/usr/bin/env python3
"""
Railway API serviceCreate スキーマ確認
"""

import requests
import json

def test_service_schema():
    """Railway APIのserviceCreateスキーマを確認"""
    
    railway_token = "727e6c11-507b-4b5f-9f8c-1e90c266d730"
    
    print("=== Railway API serviceCreate スキーマ確認 ===")
    print(f"Railway Token: {railway_token[:8]}...")
    
    # GraphQLエンドポイント
    url = "https://backboard.railway.app/graphql/v2"
    
    # ヘッダー
    headers = {
        "Authorization": f"Bearer {railway_token}",
        "Content-Type": "application/json"
    }
    
    # serviceCreateミューテーションのスキーマを確認
    schema_query = """
    query ServiceCreateSchema {
        __type(name: "ServiceCreateInput") {
            name
            inputFields {
                name
                type {
                    name
                    kind
                    ofType {
                        name
                        kind
                    }
                }
                description
            }
        }
    }
    """
    
    payload = {
        "query": schema_query
    }
    
    print("\n1. ServiceCreateInput スキーマ確認...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['__type']:
                input_type = data['data']['__type']
                print(f"✅ 入力タイプ: {input_type['name']}")
                print("入力フィールド:")
                for field in input_type['inputFields']:
                    field_type = field['type']
                    type_name = field_type['name'] or field_type['ofType']['name'] if field_type['ofType'] else 'Unknown'
                    print(f"  - {field['name']}: {type_name} ({field['description'] or 'No description'})")
            else:
                print(f"❌ スキーマ取得失敗: {data}")
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            
    except Exception as e:
        print(f"❌ スキーマ確認エラー: {e}")
    
    # serviceCreateミューテーションの詳細を確認
    mutation_query = """
    query ServiceCreateMutation {
        __type(name: "Mutation") {
            fields {
                name
                description
                args {
                    name
                    type {
                        name
                        kind
                        ofType {
                            name
                            kind
                        }
                    }
                }
            }
        }
    }
    """
    
    payload = {
        "query": mutation_query
    }
    
    print("\n2. serviceCreate ミューテーション詳細確認...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['__type']:
                mutations = data['data']['__type']['fields']
                service_create = [m for m in mutations if m['name'] == 'serviceCreate']
                if service_create:
                    mutation = service_create[0]
                    print(f"✅ serviceCreate ミューテーション: {mutation['description']}")
                    print("引数:")
                    for arg in mutation['args']:
                        arg_type = arg['type']
                        type_name = arg_type['name'] or arg_type['ofType']['name'] if arg_type['ofType'] else 'Unknown'
                        print(f"  - {arg['name']}: {type_name}")
                else:
                    print("❌ serviceCreate ミューテーションが見つかりません")
            else:
                print(f"❌ ミューテーション詳細取得失敗: {data}")
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            
    except Exception as e:
        print(f"❌ ミューテーション詳細確認エラー: {e}")

if __name__ == "__main__":
    test_service_schema() 