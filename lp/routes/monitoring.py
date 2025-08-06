from flask import Blueprint, request, jsonify
from services.monitoring_service import monitoring_service
import json
import os
from datetime import datetime, timedelta

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/api/v1/monitoring')

@monitoring_bp.route('/health', methods=['GET'])
def get_system_health():
    """システム健全性を取得"""
    try:
        result = monitoring_service.get_system_health()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'システム健全性取得エラー: {str(e)}'
        }), 500

@monitoring_bp.route('/performance', methods=['GET'])
def get_performance_metrics():
    """パフォーマンスメトリクスを取得"""
    try:
        result = monitoring_service.get_performance_metrics()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'パフォーマンスメトリクス取得エラー: {str(e)}'
        }), 500

@monitoring_bp.route('/logs', methods=['GET'])
def get_error_logs():
    """エラーログを取得"""
    try:
        hours = request.args.get('hours', 24, type=int)
        level = request.args.get('level', 'ERROR')
        
        result = monitoring_service.get_error_logs(hours, level)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'エラーログ取得エラー: {str(e)}'
        }), 500

@monitoring_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """アラート一覧を取得"""
    try:
        resolved = request.args.get('resolved', type=lambda v: v.lower() == 'true' if v else None)
        
        result = monitoring_service.get_alerts(resolved)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'アラート取得エラー: {str(e)}'
        }), 500

@monitoring_bp.route('/alerts', methods=['POST'])
def create_alert():
    """アラートを作成"""
    try:
        data = request.get_json() or {}
        alert_type = data.get('type')
        message = data.get('message')
        severity = data.get('severity', 'info')
        
        if not alert_type or not message:
            return jsonify({
                'success': False,
                'error': 'type と message は必須です'
            }), 400
        
        result = monitoring_service.create_alert(alert_type, message, severity)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'アラート作成エラー: {str(e)}'
        }), 500

@monitoring_bp.route('/alerts/<alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """アラートを解決済みにする"""
    try:
        result = monitoring_service.resolve_alert(alert_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'アラート解決エラー: {str(e)}'
        }), 500

@monitoring_bp.route('/database', methods=['GET'])
def get_database_health():
    """データベース健全性を取得"""
    try:
        from services.monitoring_service import monitoring_service
        
        # データベース健全性チェックを直接実行
        db_health = monitoring_service.check_database_health()
        
        return jsonify({
            'success': True,
            'database_health': db_health
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'データベース健全性取得エラー: {str(e)}'
        }), 500

@monitoring_bp.route('/system', methods=['GET'])
def get_system_resources():
    """システムリソースを取得"""
    try:
        from services.monitoring_service import monitoring_service
        
        # システムリソースチェックを直接実行
        resource_health = monitoring_service.check_system_resources()
        
        return jsonify({
            'success': True,
            'system_resources': resource_health
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'システムリソース取得エラー: {str(e)}'
        }), 500

@monitoring_bp.route('/services', methods=['GET'])
def get_services_status():
    """サービス状況を取得"""
    try:
        from services.monitoring_service import monitoring_service
        
        # アプリケーションサービスチェックを直接実行
        app_health = monitoring_service.check_application_services()
        
        # 外部サービスチェックを直接実行
        external_health = monitoring_service.check_external_services()
        
        return jsonify({
            'success': True,
            'application_services': app_health,
            'external_services': external_health
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'サービス状況取得エラー: {str(e)}'
        }), 500

@monitoring_bp.route('/summary', methods=['GET'])
def get_monitoring_summary():
    """監視サマリーを取得"""
    try:
        # 各監視項目を取得
        health_result = monitoring_service.get_system_health()
        performance_result = monitoring_service.get_performance_metrics()
        alerts_result = monitoring_service.get_alerts(resolved=False)
        
        summary = {
            'success': True,
            'timestamp': '2024-07-30T12:00:00Z',
            'health': health_result.get('health_status') if health_result['success'] else None,
            'performance': performance_result.get('metrics') if performance_result['success'] else None,
            'active_alerts': alerts_result.get('alerts', []) if alerts_result['success'] else [],
            'alert_count': len(alerts_result.get('alerts', [])) if alerts_result['success'] else 0
        }
        
        return jsonify(summary), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'監視サマリー取得エラー: {str(e)}'
        }), 500

@monitoring_bp.route('/export', methods=['GET'])
def export_monitoring_data():
    """監視データをエクスポート"""
    try:
        export_type = request.args.get('type', 'summary')
        
        if export_type == 'summary':
            result = monitoring_service.get_system_health()
        elif export_type == 'performance':
            result = monitoring_service.get_performance_metrics()
        elif export_type == 'logs':
            hours = request.args.get('hours', 24, type=int)
            level = request.args.get('level', 'ERROR')
            result = monitoring_service.get_error_logs(hours, level)
        elif export_type == 'alerts':
            result = monitoring_service.get_alerts()
        else:
            return jsonify({
                'success': False,
                'error': f'不明なエクスポートタイプ: {export_type}'
            }), 400
        
        if result['success']:
            # JSONファイルとしてダウンロード
            from flask import send_file
            import tempfile
            
            # 一時ファイルを作成
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                temp_path = f.name
            
            return send_file(
                temp_path,
                as_attachment=True,
                download_name=f'monitoring_export_{export_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                mimetype='application/json'
            )
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'監視データエクスポートエラー: {str(e)}'
        }), 500

@monitoring_bp.route('/test-alert', methods=['POST'])
def create_test_alert():
    """テストアラートを作成"""
    try:
        data = request.get_json() or {}
        alert_type = data.get('type', 'test')
        message = data.get('message', 'テストアラートです')
        severity = data.get('severity', 'info')
        
        result = monitoring_service.create_alert(alert_type, message, severity)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'テストアラートを作成しました',
                'alert': result['alert']
            }), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'テストアラート作成エラー: {str(e)}'
        }), 500

@monitoring_bp.route('/cleanup', methods=['POST'])
def cleanup_monitoring_data():
    """監視データをクリーンアップ"""
    try:
        data = request.get_json() or {}
        days_to_keep = data.get('days_to_keep', 30)
        
        # ログファイルのクリーンアップ
        
        monitoring_dir = "monitoring"
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        cleaned_files = []
        if os.path.exists(monitoring_dir):
            for filename in os.listdir(monitoring_dir):
                file_path = os.path.join(monitoring_dir, filename)
                if os.path.isfile(file_path):
                    file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_modified < cutoff_date:
                        os.remove(file_path)
                        cleaned_files.append(filename)
        
        return jsonify({
            'success': True,
            'message': f'{len(cleaned_files)}件の古い監視ファイルを削除しました',
            'cleaned_files': cleaned_files
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'監視データクリーンアップエラー: {str(e)}'
        }), 500 