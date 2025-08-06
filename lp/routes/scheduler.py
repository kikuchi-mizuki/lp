from flask import Blueprint, request, jsonify
from services.scheduler_service import scheduler_service
import json

scheduler_bp = Blueprint('scheduler', __name__, url_prefix='/api/v1/scheduler')

@scheduler_bp.route('/start', methods=['POST'])
def start_scheduler():
    """スケジューラーを開始"""
    try:
        result = scheduler_service.start_scheduler()
        
        if result:
            return jsonify({
                'success': True,
                'message': '自動スケジューラーを開始しました'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'スケジューラーの開始に失敗しました'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'スケジューラー開始エラー: {str(e)}'
        }), 500

@scheduler_bp.route('/stop', methods=['POST'])
def stop_scheduler():
    """スケジューラーを停止"""
    try:
        result = scheduler_service.stop_scheduler()
        
        if result:
            return jsonify({
                'success': True,
                'message': '自動スケジューラーを停止しました'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'スケジューラーの停止に失敗しました'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'スケジューラー停止エラー: {str(e)}'
        }), 500

@scheduler_bp.route('/status', methods=['GET'])
def get_scheduler_status():
    """スケジューラーの状態を取得"""
    try:
        result = scheduler_service.get_scheduler_status()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'スケジューラー状態取得エラー: {str(e)}'
        }), 500

@scheduler_bp.route('/config', methods=['GET', 'PUT'])
def manage_schedule_config():
    """スケジュール設定の取得・更新"""
    try:
        if request.method == 'GET':
            # 設定を取得
            result = scheduler_service.get_scheduler_status()
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'schedule_config': result['schedule_config']
                }), 200
            else:
                return jsonify(result), 400
                
        elif request.method == 'PUT':
            # 設定を更新
            data = request.get_json() or {}
            
            result = scheduler_service.update_schedule_config(data)
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'スケジュール設定管理エラー: {str(e)}'
        }), 500

@scheduler_bp.route('/tasks/<task_name>/run', methods=['POST'])
def run_manual_task(task_name):
    """手動でタスクを実行"""
    try:
        result = scheduler_service.run_manual_task(task_name)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'タスク実行エラー: {str(e)}'
        }), 500

@scheduler_bp.route('/tasks', methods=['GET'])
def get_available_tasks():
    """利用可能なタスク一覧を取得"""
    try:
        tasks = [
            {
                'name': 'data_deletion_check',
                'description': '削除予定企業のチェックと削除実行',
                'schedule': '毎日午前2時',
                'enabled': True
            },
            {
                'name': 'trial_ending_reminder',
                'description': 'トライアル終了リマインダーの送信',
                'schedule': '毎日午前9時',
                'enabled': True
            },
            {
                'name': 'renewal_reminder',
                'description': '契約更新リマインダーの送信',
                'schedule': '毎日午前10時',
                'enabled': True
            },
            {
                'name': 'deletion_reminder',
                'description': 'データ削除リマインダーの送信',
                'schedule': '毎日午前11時',
                'enabled': True
            },
            {
                'name': 'notification_cleanup',
                'description': '古い通知履歴のクリーンアップ',
                'schedule': '毎週日曜日午前3時',
                'enabled': True
            }
        ]
        
        return jsonify({
            'success': True,
            'tasks': tasks
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'タスク一覧取得エラー: {str(e)}'
        }), 500

@scheduler_bp.route('/tasks/bulk-run', methods=['POST'])
def run_bulk_tasks():
    """複数のタスクを一括実行"""
    try:
        data = request.get_json() or {}
        task_names = data.get('task_names', [])
        
        if not task_names:
            return jsonify({
                'success': False,
                'error': 'task_names is required'
            }), 400
        
        results = {}
        
        for task_name in task_names:
            result = scheduler_service.run_manual_task(task_name)
            results[task_name] = result
        
        return jsonify({
            'success': True,
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'一括タスク実行エラー: {str(e)}'
        }), 500

@scheduler_bp.route('/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    try:
        status = scheduler_service.get_scheduler_status()
        
        return jsonify({
            'success': True,
            'message': '自動スケジューラーサービスが正常に動作しています',
            'is_running': status.get('is_running', False),
            'timestamp': '2024-07-30T12:00:00Z'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'スケジューラーヘルスチェックエラー: {str(e)}'
        }), 500 