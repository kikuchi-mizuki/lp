#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
セキュリティ機能統合テスト
"""

import requests
import json
import time
from datetime import datetime, timedelta

def test_security_integration():
    """セキュリティ機能統合テスト"""
    print("=== セキュリティ機能統合テスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    print(f"🌐 ベースURL: {base_url}")
    
    # 1. セキュリティAPI ヘルスチェック
    print("\n1️⃣ セキュリティAPI ヘルスチェック")
    try:
        response = requests.get(f"{base_url}/api/v1/security/health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ ヘルスチェック成功: {result['message']}")
            print(f"   - サービス状態: {result['service_status']}")
        else:
            print(f"❌ ヘルスチェック失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ヘルスチェックエラー: {e}")
        return False
    
    # 2. パスワード強度検証
    print("\n2️⃣ パスワード強度検証")
    try:
        test_passwords = [
            "weak",  # 弱いパスワード
            "Strong123!",  # 強いパスワード
            "nouppercase123!",  # 大文字なし
            "NONUMBERS!",  # 数字なし
            "NoSpecial123"  # 特殊文字なし
        ]
        
        for password in test_passwords:
            response = requests.post(
                f"{base_url}/api/v1/security/password/validate",
                json={'password': password},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                status = "✅" if result['valid'] else "❌"
                print(f"   {status} {password}: {'有効' if result['valid'] else '無効'}")
                if not result['valid']:
                    print(f"     - エラー: {', '.join(result['errors'])}")
            else:
                print(f"   ❌ {password}: 検証失敗 ({response.status_code})")
    except Exception as e:
        print(f"❌ パスワード強度検証エラー: {e}")
    
    # 3. ユーザーログイン
    print("\n3️⃣ ユーザーログイン")
    try:
        # 正しい認証情報でログイン
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        response = requests.post(
            f"{base_url}/api/v1/security/login",
            json=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ ログイン成功: {result['message']}")
            print(f"   - トークン: {result['token'][:20]}...")
            print(f"   - 有効期限: {result['expires_at']}")
            
            auth_token = result['token']
        else:
            print(f"❌ ログイン失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ログインエラー: {e}")
        return False
    
    # 4. トークン検証
    print("\n4️⃣ トークン検証")
    try:
        response = requests.post(
            f"{base_url}/api/v1/security/validate",
            json={'token': auth_token},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ トークン検証成功: {result['message']}")
            print(f"   - ユーザーID: {result['user_id']}")
            print(f"   - ユーザータイプ: {result['user_type']}")
        else:
            print(f"❌ トークン検証失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ トークン検証エラー: {e}")
    
    # 5. セキュリティ設定取得
    print("\n5️⃣ セキュリティ設定取得")
    try:
        headers = {'Authorization': f'Bearer {auth_token}'}
        response = requests.get(
            f"{base_url}/api/v1/security/config",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            config = result['config']
            print(f"✅ セキュリティ設定取得成功:")
            print(f"   - 最大ログイン試行回数: {config['max_login_attempts']}")
            print(f"   - ロックアウト期間: {config['lockout_duration']}分")
            print(f"   - セッションタイムアウト: {config['session_timeout']}分")
            print(f"   - パスワード最小長: {config['password_min_length']}文字")
        else:
            print(f"❌ セキュリティ設定取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ セキュリティ設定取得エラー: {e}")
    
    # 6. 監査ログ作成
    print("\n6️⃣ 監査ログ作成")
    try:
        audit_data = {
            'action': 'test_action',
            'details': {
                'test': True,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        response = requests.post(
            f"{base_url}/api/v1/security/audit-logs",
            json=audit_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ 監査ログ作成成功: {result['message']}")
        else:
            print(f"❌ 監査ログ作成失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 監査ログ作成エラー: {e}")
    
    # 7. 監査ログ取得
    print("\n7️⃣ 監査ログ取得")
    try:
        headers = {'Authorization': f'Bearer {auth_token}'}
        response = requests.get(
            f"{base_url}/api/v1/security/audit-logs",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            logs = result['logs']
            print(f"✅ 監査ログ取得成功:")
            print(f"   - ログ件数: {result['total_count']}件")
            
            for i, log in enumerate(logs[:3]):
                print(f"   {i+1}. {log['action']} - {log['created_at']}")
        else:
            print(f"❌ 監査ログ取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 監査ログ取得エラー: {e}")
    
    # 8. アクティブセッション取得
    print("\n8️⃣ アクティブセッション取得")
    try:
        headers = {'Authorization': f'Bearer {auth_token}'}
        response = requests.get(
            f"{base_url}/api/v1/security/sessions",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            sessions = result['sessions']
            print(f"✅ アクティブセッション取得成功:")
            print(f"   - セッション数: {result['total_count']}件")
            
            for i, session in enumerate(sessions[:3]):
                print(f"   {i+1}. {session['user_id']} - {session['created_at']}")
        else:
            print(f"❌ アクティブセッション取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ アクティブセッション取得エラー: {e}")
    
    # 9. セキュリティ統計取得
    print("\n9️⃣ セキュリティ統計取得")
    try:
        headers = {'Authorization': f'Bearer {auth_token}'}
        response = requests.get(
            f"{base_url}/api/v1/security/statistics",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            stats = result['statistics']
            print(f"✅ セキュリティ統計取得成功:")
            print(f"   - アクティブセッション数: {stats['active_sessions']}")
            print(f"   - 今日のログイン試行数: {stats['today_login_attempts']}")
            print(f"   - 失敗したログイン試行数: {stats['failed_login_attempts']}")
            print(f"   - 今日の監査ログ数: {stats['today_audit_logs']}")
            print(f"   - セキュリティレベル: {stats['security_level']}")
        else:
            print(f"❌ セキュリティ統計取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ セキュリティ統計取得エラー: {e}")
    
    # 10. データ暗号化・復号化
    print("\n🔟 データ暗号化・復号化")
    try:
        test_text = "機密データ123"
        
        # 暗号化
        encrypt_data = {'text': test_text}
        headers = {'Authorization': f'Bearer {auth_token}'}
        response = requests.post(
            f"{base_url}/api/v1/security/encrypt",
            json=encrypt_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            encrypted_data = result['encrypted_data']
            print(f"✅ 暗号化成功: {test_text} -> {encrypted_data[:20]}...")
            
            # 復号化
            decrypt_data = {'encrypted_data': encrypted_data}
            response = requests.post(
                f"{base_url}/api/v1/security/decrypt",
                json=decrypt_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                decrypted_text = result['decrypted_data']
                print(f"✅ 復号化成功: {encrypted_data[:20]}... -> {decrypted_text}")
                
                if test_text == decrypted_text:
                    print(f"   ✅ 暗号化・復号化の整合性確認成功")
                else:
                    print(f"   ❌ 暗号化・復号化の整合性確認失敗")
            else:
                print(f"❌ 復号化失敗: {response.status_code}")
        else:
            print(f"❌ 暗号化失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ データ暗号化・復号化エラー: {e}")
    
    # 11. APIキー検証
    print("\n1️⃣1️⃣ APIキー検証")
    try:
        # 無効なAPIキーでテスト
        invalid_api_key = "invalid_key"
        response = requests.post(
            f"{base_url}/api/v1/security/api-key/validate",
            json={'api_key': invalid_api_key},
            timeout=10
        )
        
        if response.status_code == 401:
            result = response.json()
            print(f"✅ APIキー検証成功: {result['error']}")
        else:
            print(f"❌ APIキー検証失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ APIキー検証エラー: {e}")
    
    # 12. ログアウト
    print("\n1️⃣2️⃣ ログアウト")
    try:
        headers = {'Authorization': f'Bearer {auth_token}'}
        response = requests.post(
            f"{base_url}/api/v1/security/logout",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ ログアウト成功: {result['message']}")
        else:
            print(f"❌ ログアウト失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ ログアウトエラー: {e}")
    
    print("\n🎉 セキュリティ機能統合テスト完了")
    return True

def test_security_with_real_data():
    """実際のデータを使用したセキュリティテスト"""
    print("\n=== 実際のデータを使用したセキュリティテスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    # ログインしてトークンを取得
    try:
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        response = requests.post(
            f"{base_url}/api/v1/security/login",
            json=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            auth_token = result['token']
            print(f"🔐 認証トークン取得成功")
            
            headers = {'Authorization': f'Bearer {auth_token}'}
            
            # セキュリティ統計の詳細分析
            print(f"\n📊 セキュリティ統計詳細分析:")
            
            response = requests.get(
                f"{base_url}/api/v1/security/statistics",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                stats = result['statistics']
                
                print(f"   - アクティブセッション数: {stats['active_sessions']}")
                print(f"   - 今日のログイン試行数: {stats['today_login_attempts']}")
                print(f"   - 失敗したログイン試行数: {stats['failed_login_attempts']}")
                print(f"   - 今日の監査ログ数: {stats['today_audit_logs']}")
                print(f"   - セキュリティレベル: {stats['security_level']}")
                
                # セキュリティレベルの評価
                if stats['security_level'] == 'high':
                    print(f"   ✅ セキュリティレベル: 高 (良好)")
                elif stats['security_level'] == 'medium':
                    print(f"   ⚠️ セキュリティレベル: 中 (注意が必要)")
                else:
                    print(f"   ❌ セキュリティレベル: 低 (改善が必要)")
            
            # 監査ログの詳細分析
            print(f"\n📋 監査ログ詳細分析:")
            
            response = requests.get(
                f"{base_url}/api/v1/security/audit-logs?limit=10",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logs = result['logs']
                
                print(f"   - 最新の監査ログ数: {len(logs)}件")
                
                # アクション別の集計
                action_counts = {}
                for log in logs:
                    action = log['action']
                    action_counts[action] = action_counts.get(action, 0) + 1
                
                print(f"   - アクション別集計:")
                for action, count in action_counts.items():
                    print(f"     * {action}: {count}件")
            
            # ログアウト
            response = requests.post(
                f"{base_url}/api/v1/security/logout",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"   ✅ ログアウト完了")
            
        else:
            print("❌ 認証トークン取得に失敗しました")
    except Exception as e:
        print(f"❌ 実際のデータテストエラー: {e}")

def test_security_performance():
    """セキュリティ機能パフォーマンステスト"""
    print("\n=== セキュリティ機能パフォーマンステスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    # 各エンドポイントの応答時間を測定
    endpoints = [
        ('health', '/api/v1/security/health'),
        ('password_validate', '/api/v1/security/password/validate'),
        ('login', '/api/v1/security/login'),
        ('config', '/api/v1/security/config'),
        ('statistics', '/api/v1/security/statistics')
    ]
    
    performance_results = {}
    
    # まずログインしてトークンを取得
    try:
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        response = requests.post(
            f"{base_url}/api/v1/security/login",
            json=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            auth_token = result['token']
            headers = {'Authorization': f'Bearer {auth_token}'}
            
            for name, endpoint in endpoints:
                try:
                    start_time = time.time()
                    
                    if name == 'password_validate':
                        response = requests.post(
                            f"{base_url}{endpoint}",
                            json={'password': 'TestPassword123!'},
                            timeout=30
                        )
                    elif name == 'login':
                        response = requests.post(
                            f"{base_url}{endpoint}",
                            json=login_data,
                            timeout=30
                        )
                    elif name in ['config', 'statistics']:
                        response = requests.get(
                            f"{base_url}{endpoint}",
                            headers=headers,
                            timeout=30
                        )
                    else:
                        response = requests.get(
                            f"{base_url}{endpoint}",
                            timeout=30
                        )
                    
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000  # ミリ秒
                    
                    if response.status_code in [200, 201]:
                        print(f"✅ {name}: {response_time:.2f}ms")
                        performance_results[name] = {
                            'status': 'success',
                            'response_time': response_time,
                            'status_code': response.status_code
                        }
                    else:
                        print(f"❌ {name}: {response.status_code} ({response_time:.2f}ms)")
                        performance_results[name] = {
                            'status': 'error',
                            'response_time': response_time,
                            'status_code': response.status_code
                        }
                        
                except Exception as e:
                    print(f"❌ {name}: エラー ({str(e)})")
                    performance_results[name] = {
                        'status': 'exception',
                        'error': str(e)
                    }
            
            # パフォーマンスサマリー
            successful_requests = [r for r in performance_results.values() if r['status'] == 'success']
            if successful_requests:
                avg_response_time = sum(r['response_time'] for r in successful_requests) / len(successful_requests)
                max_response_time = max(r['response_time'] for r in successful_requests)
                min_response_time = min(r['response_time'] for r in successful_requests)
                
                print(f"\n📊 パフォーマンスサマリー:")
                print(f"   - 成功リクエスト: {len(successful_requests)}/{len(endpoints)}")
                print(f"   - 平均応答時間: {avg_response_time:.2f}ms")
                print(f"   - 最大応答時間: {max_response_time:.2f}ms")
                print(f"   - 最小応答時間: {min_response_time:.2f}ms")
                
                # セキュリティ評価
                if avg_response_time < 100:
                    print(f"   ✅ セキュリティ機能の応答性: 優秀")
                elif avg_response_time < 500:
                    print(f"   ⚠️ セキュリティ機能の応答性: 良好")
                else:
                    print(f"   ❌ セキュリティ機能の応答性: 改善が必要")
            
        else:
            print("❌ ログインに失敗しました")
    except Exception as e:
        print(f"❌ パフォーマンステストエラー: {e}")

def main():
    """メイン関数"""
    print("🚀 セキュリティ機能テストを開始します")
    
    # 基本的な統合テスト
    if test_security_integration():
        print("✅ 基本的な統合テストが完了しました")
    else:
        print("❌ 基本的な統合テストに失敗しました")
        return
    
    # 実際のデータを使用したテスト
    test_security_with_real_data()
    
    # パフォーマンステスト
    test_security_performance()

if __name__ == "__main__":
    main() 