from flask import Blueprint, request, jsonify
from services.automation_service import automation_service
from services.security_service import require_auth, require_admin
import json
from datetime import datetime, timedelta

automation_bp = Blueprint('automation', __name__, url_prefix='/api/v1/automation')

@automation_bp.route('/start', methods=['POST'])
@require_admin
def start_automation():
    """自動化サービスを開始"""
    try:
        result = automation_service.start_automation()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'自動化開始エラー: {str(e)}'
        }), 500

@automation_bp.route('/stop', methods=['POST'])
@require_admin
def stop_automation():
    """自動化サービスを停止"""
    try:
        result = automation_service.stop_automation()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'自動化停止エラー: {str(e)}'
        }), 500

@automation_bp.route('/status', methods=['GET'])
@require_auth
def get_automation_status():
    """自動化サービスの状態を取得"""
    try:
        result = automation_service.get_automation_status()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'状態取得エラー: {str(e)}'
        }), 500

@automation_bp.route('/config', methods=['GET', 'PUT'])
@require_admin
def manage_automation_config():
    """自動化設定の取得・更新"""
    try:
        if request.method == 'GET':
            # 設定を取得
            result = automation_service.get_automation_status()
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'config': result['status']['config']
                }), 200
            else:
                return jsonify(result), 400
                
        elif request.method == 'PUT':
            # 設定を更新
            new_config = request.get_json()
            
            if not new_config:
                return jsonify({
                    'success': False,
                    'error': '設定データが提供されていません'
                }), 400
            
            result = automation_service.update_automation_config(new_config)
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'設定管理エラー: {str(e)}'
        }), 500

@automation_bp.route('/backup', methods=['POST'])
@require_admin
def run_manual_backup():
    """手動バックアップを実行"""
    try:
        data = request.get_json() or {}
        company_id = data.get('company_id')
        
        result = automation_service.run_manual_backup(company_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'手動バックアップエラー: {str(e)}'
        }), 500

@automation_bp.route('/cleanup', methods=['POST'])
@require_admin
def run_manual_cleanup():
    """手動クリーンアップを実行"""
    try:
        data = request.get_json() or {}
        cleanup_type = data.get('type', 'all')
        
        result = automation_service.run_manual_cleanup(cleanup_type)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'手動クリーンアップエラー: {str(e)}'
        }), 500

@automation_bp.route('/sync', methods=['POST'])
@require_admin
def run_manual_sync():
    """手動データ同期を実行"""
    try:
        data = request.get_json() or {}
        sync_type = data.get('type', 'all')
        
        result = automation_service.run_manual_sync(sync_type)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'手動同期エラー: {str(e)}'
        }), 500

@automation_bp.route('/tasks', methods=['GET'])
@require_auth
def get_automation_tasks():
    """利用可能な自動化タスクを取得"""
    try:
        tasks = {
            'backup': {
                'name': 'バックアップ',
                'description': '企業データの自動バックアップ',
                'schedule': 'daily',
                'enabled': True
            },
            'cleanup': {
                'name': 'クリーンアップ',
                'description': '古いログ・一時ファイル・期限切れセッションの削除',
                'schedule': 'weekly',
                'enabled': True
            },
            'data_sync': {
                'name': 'データ同期',
                'description': 'Stripe・LINEデータとの同期',
                'schedule': 'hourly',
                'enabled': True
            },
            'health_check': {
                'name': 'ヘルスチェック',
                'description': 'システム健全性の監視・自動復旧',
                'schedule': 'every_5_minutes',
                'enabled': True
            }
        }
        
        return jsonify({
            'success': True,
            'tasks': tasks
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'タスク取得エラー: {str(e)}'
        }), 500

@automation_bp.route('/tasks/<task_name>/run', methods=['POST'])
@require_admin
def run_specific_task(task_name):
    """特定の自動化タスクを実行"""
    try:
        if task_name == 'backup':
            result = automation_service.run_manual_backup()
        elif task_name == 'cleanup':
            result = automation_service.run_manual_cleanup()
        elif task_name == 'sync':
            result = automation_service.run_manual_sync()
        elif task_name == 'health_check':
            # ヘルスチェックは自動実行されるため、手動実行は状態確認のみ
            result = automation_service.get_automation_status()
        else:
            return jsonify({
                'success': False,
                'error': f'不明なタスク: {task_name}'
            }), 400
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'タスク実行エラー: {str(e)}'
        }), 500

@automation_bp.route('/logs', methods=['GET'])
@require_auth
def get_automation_logs():
    """自動化ログを取得"""
    try:
        # 実際の実装ではデータベースからログを取得
        logs = [
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'message': '自動化サービスが開始されました',
                'task': 'startup'
            },
            {
                'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(),
                'level': 'INFO',
                'message': 'バックアップが完了しました',
                'task': 'backup'
            },
            {
                'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
                'level': 'WARNING',
                'message': 'CPU使用率が高い: 85%',
                'task': 'health_check'
            }
        ]
        
        return jsonify({
            'success': True,
            'logs': logs
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'ログ取得エラー: {str(e)}'
        }), 500

@automation_bp.route('/statistics', methods=['GET'])
@require_auth
def get_automation_statistics():
    """自動化統計を取得"""
    try:
        # 実際の実装ではデータベースから統計を取得
        stats = {
            'total_backups': 150,
            'total_cleanups': 25,
            'total_syncs': 720,
            'total_health_checks': 8640,
            'success_rate': 99.5,
            'average_execution_time': 2.3,
            'last_24_hours': {
                'backups': 1,
                'cleanups': 0,
                'syncs': 24,
                'health_checks': 288
            }
        }
        
        return jsonify({
            'success': True,
            'statistics': stats
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'統計取得エラー: {str(e)}'
        }), 500

@automation_bp.route('/health', methods=['GET'])
def automation_health():
    """自動化サービスの健全性チェック"""
    try:
        status = automation_service.get_automation_status()
        
        if status['success']:
            return jsonify({
                'success': True,
                'message': '自動化サービスは正常に動作しています',
                'status': 'healthy',
                'is_running': status['status']['is_running'],
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '自動化サービスに問題があります',
                'status': 'error',
                'error': status['error'],
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '自動化サービスの健全性チェックに失敗しました',
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500 