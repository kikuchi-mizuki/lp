#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
システム監視機能統合テスト
"""

import requests
import json
import time
from datetime import datetime, timedelta

def test_monitoring_integration():
    """システム監視機能統合テスト"""
    print("=== システム監視機能統合テスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    print(f"🌐 ベースURL: {base_url}")
    
    # 1. システム健全性チェック
    print("\n1️⃣ システム健全性チェック")
    try:
        response = requests.get(f"{base_url}/api/v1/monitoring/health", timeout=15)
        if response.status_code == 200:
            result = response.json()
            health_status = result['health_status']
            print(f"✅ システム健全性チェック成功:")
            print(f"   - 全体ステータス: {health_status['overall_status']}")
            print(f"   - タイムスタンプ: {health_status['timestamp']}")
            
            # 各チェック項目の詳細
            for check_name, check_result in health_status['checks'].items():
                status = check_result.get('status', 'unknown')
                status_icon = "✅" if status == 'healthy' else "⚠️" if status == 'warning' else "❌"
                print(f"   - {check_name}: {status_icon} {status}")
        else:
            print(f"❌ システム健全性チェック失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ システム健全性チェックエラー: {e}")
        return False
    
    # 2. パフォーマンスメトリクス取得
    print("\n2️⃣ パフォーマンスメトリクス取得")
    try:
        response = requests.get(f"{base_url}/api/v1/monitoring/performance", timeout=15)
        if response.status_code == 200:
            result = response.json()
            metrics = result['metrics']
            print(f"✅ パフォーマンスメトリクス取得成功:")
            
            # システムメトリクス
            system_metrics = metrics['system_metrics']
            print(f"   - CPU使用率: {system_metrics['cpu_percent']}%")
            print(f"   - メモリ使用率: {system_metrics['memory_percent']}%")
            print(f"   - ディスク使用率: {system_metrics['disk_percent']}%")
            
            # アプリケーションメトリクス
            app_metrics = metrics['application_metrics']
            print(f"   - Flaskプロセス数: {app_metrics['process_count']}")
            print(f"   - 総メモリ使用率: {app_metrics['total_memory_percent']:.2f}%")
            print(f"   - 総CPU使用率: {app_metrics['total_cpu_percent']:.2f}%")
            
            # データベースメトリクス
            db_metrics = metrics['database_metrics']
            if 'error' not in db_metrics:
                print(f"   - データベースサイズ: {db_metrics['database_size']}")
                print(f"   - アクティブ接続数: {db_metrics['active_connections']}")
                print(f"   - テーブル数: {len(db_metrics['table_sizes'])}")
            else:
                print(f"   - データベースエラー: {db_metrics['error']}")
        else:
            print(f"❌ パフォーマンスメトリクス取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ パフォーマンスメトリクス取得エラー: {e}")
    
    # 3. エラーログ取得
    print("\n3️⃣ エラーログ取得")
    try:
        response = requests.get(f"{base_url}/api/v1/monitoring/logs?hours=24&level=ERROR", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ エラーログ取得成功:")
            print(f"   - ログ件数: {result['total_count']}件")
            print(f"   - 表示件数: {len(result['logs'])}件")
            
            # 最新のログを表示
            for i, log in enumerate(result['logs'][:3]):
                print(f"   {i+1}. {log['timestamp']}: {log['message'][:100]}...")
        else:
            print(f"❌ エラーログ取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ エラーログ取得エラー: {e}")
    
    # 4. アラート機能テスト
    print("\n4️⃣ アラート機能テスト")
    try:
        # テストアラートを作成
        test_alert_data = {
            'type': 'test',
            'message': '統合テスト用のアラートです',
            'severity': 'info'
        }
        response = requests.post(
            f"{base_url}/api/v1/monitoring/alerts",
            json=test_alert_data,
            timeout=10
        )
        
        if response.status_code == 201:
            result = response.json()
            created_alert = result['alert']
            print(f"✅ テストアラート作成成功:")
            print(f"   - アラートID: {created_alert['id']}")
            print(f"   - タイプ: {created_alert['type']}")
            print(f"   - メッセージ: {created_alert['message']}")
            print(f"   - 重要度: {created_alert['severity']}")
            
            # アラート一覧を取得
            response = requests.get(f"{base_url}/api/v1/monitoring/alerts", timeout=10)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ アラート一覧取得成功:")
                print(f"   - 総アラート数: {len(result['alerts'])}件")
                
                # 最新のアラートを表示
                for i, alert in enumerate(result['alerts'][:3]):
                    status = "解決済み" if alert['resolved'] else "未解決"
                    print(f"   {i+1}. {alert['timestamp']}: {alert['message']} ({status})")
                
                # 作成したアラートを解決
                if created_alert['id']:
                    response = requests.post(
                        f"{base_url}/api/v1/monitoring/alerts/{created_alert['id']}/resolve",
                        timeout=10
                    )
                    if response.status_code == 200:
                        print(f"✅ テストアラート解決成功")
                    else:
                        print(f"❌ テストアラート解決失敗: {response.status_code}")
            else:
                print(f"❌ アラート一覧取得失敗: {response.status_code}")
        else:
            print(f"❌ テストアラート作成失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ アラート機能テストエラー: {e}")
    
    # 5. データベース健全性チェック
    print("\n5️⃣ データベース健全性チェック")
    try:
        response = requests.get(f"{base_url}/api/v1/monitoring/database", timeout=10)
        if response.status_code == 200:
            result = response.json()
            db_health = result['database_health']
            print(f"✅ データベース健全性チェック成功:")
            print(f"   - ステータス: {db_health['status']}")
            print(f"   - 接続テスト: {'成功' if db_health['connection_test'] else '失敗'}")
            print(f"   - データベースサイズ: {db_health['database_size']}")
            print(f"   - アクティブ接続数: {db_health['active_connections']}")
            print(f"   - テーブル数: {db_health['total_tables']}")
            
            if db_health['missing_tables']:
                print(f"   - 不足テーブル: {db_health['missing_tables']}")
        else:
            print(f"❌ データベース健全性チェック失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ データベース健全性チェックエラー: {e}")
    
    # 6. システムリソースチェック
    print("\n6️⃣ システムリソースチェック")
    try:
        response = requests.get(f"{base_url}/api/v1/monitoring/system", timeout=10)
        if response.status_code == 200:
            result = response.json()
            system_resources = result['system_resources']
            print(f"✅ システムリソースチェック成功:")
            print(f"   - ステータス: {system_resources['status']}")
            print(f"   - CPU使用率: {system_resources['cpu_percent']}%")
            print(f"   - メモリ使用率: {system_resources['memory_percent']}%")
            print(f"   - ディスク使用率: {system_resources['disk_percent']}%")
            print(f"   - 利用可能メモリ: {system_resources['memory_available'] / (1024**3):.2f}GB")
            print(f"   - 空きディスク容量: {system_resources['disk_free'] / (1024**3):.2f}GB")
        else:
            print(f"❌ システムリソースチェック失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ システムリソースチェックエラー: {e}")
    
    # 7. サービス状況チェック
    print("\n7️⃣ サービス状況チェック")
    try:
        response = requests.get(f"{base_url}/api/v1/monitoring/services", timeout=15)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ サービス状況チェック成功:")
            
            # アプリケーションサービス
            app_services = result['application_services']
            print(f"   - アプリケーションサービス: {app_services['status']}")
            if 'services' in app_services:
                for service_name, service_status in app_services['services'].items():
                    status_icon = "✅" if service_status['status'] == 'healthy' else "❌"
                    print(f"     * {service_name}: {status_icon} {service_status['status']}")
            
            # 外部サービス
            external_services = result['external_services']
            print(f"   - 外部サービス: {external_services['status']}")
            if 'services' in external_services:
                for service_name, service_status in external_services['services'].items():
                    status_icon = "✅" if service_status['status'] == 'healthy' else "⚠️" if service_status['status'] == 'warning' else "❌"
                    print(f"     * {service_name}: {status_icon} {service_status['status']}")
        else:
            print(f"❌ サービス状況チェック失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ サービス状況チェックエラー: {e}")
    
    # 8. 監視サマリー取得
    print("\n8️⃣ 監視サマリー取得")
    try:
        response = requests.get(f"{base_url}/api/v1/monitoring/summary", timeout=15)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 監視サマリー取得成功:")
            print(f"   - タイムスタンプ: {result['timestamp']}")
            print(f"   - アクティブアラート数: {result['alert_count']}件")
            
            if result['health']:
                print(f"   - システム健全性: {result['health']['overall_status']}")
            
            if result['performance']:
                perf = result['performance']
                print(f"   - CPU使用率: {perf['system_metrics']['cpu_percent']}%")
                print(f"   - メモリ使用率: {perf['system_metrics']['memory_percent']}%")
        else:
            print(f"❌ 監視サマリー取得失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 監視サマリー取得エラー: {e}")
    
    # 9. テストアラート作成
    print("\n9️⃣ テストアラート作成")
    try:
        test_alert_data = {
            'type': 'integration_test',
            'message': '統合テスト用のアラートです',
            'severity': 'info'
        }
        response = requests.post(
            f"{base_url}/api/v1/monitoring/test-alert",
            json=test_alert_data,
            timeout=10
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ テストアラート作成成功: {result['message']}")
            print(f"   - アラートID: {result['alert']['id']}")
        else:
            print(f"❌ テストアラート作成失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ テストアラート作成エラー: {e}")
    
    print("\n🎉 システム監視機能統合テスト完了")
    return True

def test_monitoring_with_real_data():
    """実際のデータを使用した監視テスト"""
    print("\n=== 実際のデータを使用した監視テスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    # システム健全性の詳細チェック
    try:
        response = requests.get(f"{base_url}/api/v1/monitoring/health", timeout=15)
        if response.status_code == 200:
            result = response.json()
            health_status = result['health_status']
            
            print(f"🔍 システム健全性詳細分析:")
            print(f"   - 全体ステータス: {health_status['overall_status']}")
            
            # 各チェック項目の詳細分析
            for check_name, check_result in health_status['checks'].items():
                print(f"\n📊 {check_name}詳細:")
                print(f"   - ステータス: {check_result['status']}")
                
                if check_name == 'database':
                    print(f"   - 接続テスト: {'成功' if check_result['connection_test'] else '失敗'}")
                    print(f"   - データベースサイズ: {check_result['database_size']}")
                    print(f"   - アクティブ接続数: {check_result['active_connections']}")
                    if check_result['missing_tables']:
                        print(f"   - 不足テーブル: {check_result['missing_tables']}")
                
                elif check_name == 'system_resources':
                    print(f"   - CPU使用率: {check_result['cpu_percent']}%")
                    print(f"   - メモリ使用率: {check_result['memory_percent']}%")
                    print(f"   - ディスク使用率: {check_result['disk_percent']}%")
                
                elif check_name == 'application_services':
                    if 'services' in check_result:
                        for service_name, service_status in check_result['services'].items():
                            print(f"   - {service_name}: {service_status['status']}")
                            if service_name == 'flask_app':
                                print(f"     * プロセス数: {service_status['process_count']}")
                
                elif check_name == 'external_services':
                    if 'services' in check_result:
                        for service_name, service_status in check_result['services'].items():
                            print(f"   - {service_name}: {service_status['status']}")
                            if 'error' in service_status:
                                print(f"     * エラー: {service_status['error']}")
        else:
            print("❌ システム健全性取得に失敗しました")
    except Exception as e:
        print(f"❌ システム健全性詳細分析エラー: {e}")

def test_monitoring_export():
    """監視データエクスポート機能のテスト"""
    print("\n=== 監視データエクスポート機能テスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    # エクスポートタイプのリスト
    export_types = ['summary', 'performance', 'logs', 'alerts']
    
    for export_type in export_types:
        try:
            print(f"📤 {export_type}エクスポートテスト")
            
            # エクスポートパラメータを設定
            params = {'type': export_type}
            if export_type == 'logs':
                params.update({'hours': 24, 'level': 'ERROR'})
            
            response = requests.get(f"{base_url}/api/v1/monitoring/export", params=params, timeout=15)
            
            if response.status_code == 200:
                print(f"✅ {export_type}エクスポート成功")
                print(f"   - ファイルサイズ: {len(response.content)} bytes")
                
                # レスポンスヘッダーからファイル名を取得
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('"')
                    print(f"   - ファイル名: {filename}")
            else:
                print(f"❌ {export_type}エクスポート失敗: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {export_type}エクスポートエラー: {e}")

def test_monitoring_performance():
    """監視機能パフォーマンステスト"""
    print("\n=== 監視機能パフォーマンステスト ===")
    
    base_url = "http://127.0.0.1:5000"
    
    # 各エンドポイントの応答時間を測定
    endpoints = [
        ('health', '/api/v1/monitoring/health'),
        ('performance', '/api/v1/monitoring/performance'),
        ('database', '/api/v1/monitoring/database'),
        ('system', '/api/v1/monitoring/system'),
        ('services', '/api/v1/monitoring/services'),
        ('summary', '/api/v1/monitoring/summary')
    ]
    
    performance_results = {}
    
    for name, endpoint in endpoints:
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}{endpoint}", timeout=30)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # ミリ秒
            
            if response.status_code == 200:
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

def main():
    """メイン関数"""
    print("🚀 システム監視機能テストを開始します")
    
    # 基本的な統合テスト
    if test_monitoring_integration():
        print("✅ 基本的な統合テストが完了しました")
    else:
        print("❌ 基本的な統合テストに失敗しました")
        return
    
    # 実際のデータを使用したテスト
    test_monitoring_with_real_data()
    
    # エクスポート機能テスト
    test_monitoring_export()
    
    # パフォーマンステスト
    test_monitoring_performance()

if __name__ == "__main__":
    main() 