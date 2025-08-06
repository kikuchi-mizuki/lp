from flask import Blueprint, request, jsonify, send_file
from lp.services.backup_service import backup_service
import os

backup_bp = Blueprint('backup', __name__, url_prefix='/api/v1/backup')

@backup_bp.route('/companies/<int:company_id>/create', methods=['POST'])
def create_company_backup(company_id):
    """企業データのバックアップを作成"""
    try:
        data = request.get_json() or {}
        backup_type = data.get('backup_type', 'full')
        
        result = backup_service.create_company_backup(company_id, backup_type)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'バックアップ作成エラー: {str(e)}'
        }), 500

@backup_bp.route('/companies/<int:company_id>/restore', methods=['POST'])
def restore_company_backup(company_id):
    """企業データのバックアップを復元"""
    try:
        data = request.get_json() or {}
        backup_file_path = data.get('backup_file_path')
        restore_mode = data.get('restore_mode', 'preview')
        
        if not backup_file_path:
            return jsonify({
                'success': False,
                'error': 'backup_file_path is required'
            }), 400
        
        result = backup_service.restore_company_backup(backup_file_path, restore_mode)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'バックアップ復元エラー: {str(e)}'
        }), 500

@backup_bp.route('/companies/<int:company_id>/list', methods=['GET'])
def list_company_backups(company_id):
    """企業のバックアップ一覧を取得"""
    try:
        result = backup_service.list_backups(company_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'バックアップ一覧取得エラー: {str(e)}'
        }), 500

@backup_bp.route('/list', methods=['GET'])
def list_all_backups():
    """全バックアップ一覧を取得"""
    try:
        result = backup_service.list_backups()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'バックアップ一覧取得エラー: {str(e)}'
        }), 500

@backup_bp.route('/download/<filename>', methods=['GET'])
def download_backup(filename):
    """バックアップファイルをダウンロード"""
    try:
        backup_path = os.path.join(backup_service.backup_dir, filename)
        
        if not os.path.exists(backup_path):
            return jsonify({
                'success': False,
                'error': 'バックアップファイルが見つかりません'
            }), 404
        
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'バックアップダウンロードエラー: {str(e)}'
        }), 500

@backup_bp.route('/delete/<filename>', methods=['DELETE'])
def delete_backup(filename):
    """バックアップファイルを削除"""
    try:
        result = backup_service.delete_backup(filename)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'バックアップ削除エラー: {str(e)}'
        }), 500

@backup_bp.route('/cleanup', methods=['POST'])
def cleanup_old_backups():
    """古いバックアップファイルをクリーンアップ"""
    try:
        data = request.get_json() or {}
        days_to_keep = data.get('days_to_keep', 30)
        
        result = backup_service.cleanup_old_backups(days_to_keep)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'バックアップクリーンアップエラー: {str(e)}'
        }), 500

@backup_bp.route('/companies/<int:company_id>/preview/<filename>', methods=['GET'])
def preview_backup(company_id, filename):
    """バックアップファイルの内容をプレビュー"""
    try:
        backup_path = os.path.join(backup_service.backup_dir, filename)
        
        if not os.path.exists(backup_path):
            return jsonify({
                'success': False,
                'error': 'バックアップファイルが見つかりません'
            }), 404
        
        result = backup_service.restore_company_backup(backup_path, 'preview')
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'バックアッププレビューエラー: {str(e)}'
        }), 500

@backup_bp.route('/companies/<int:company_id>/bulk-create', methods=['POST'])
def bulk_create_backups(company_id):
    """複数のバックアップタイプを作成"""
    try:
        data = request.get_json() or {}
        backup_types = data.get('backup_types', ['full'])
        
        if not backup_types:
            return jsonify({
                'success': False,
                'error': 'backup_types is required'
            }), 400
        
        results = {}
        
        for backup_type in backup_types:
            result = backup_service.create_company_backup(company_id, backup_type)
            results[backup_type] = result
        
        return jsonify({
            'success': True,
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'一括バックアップ作成エラー: {str(e)}'
        }), 500

@backup_bp.route('/statistics', methods=['GET'])
def get_backup_statistics():
    """バックアップ統計を取得"""
    try:
        # 全バックアップ一覧を取得
        result = backup_service.list_backups()
        
        if not result['success']:
            return jsonify(result), 400
        
        backups = result['backups']
        
        # 統計を計算
        total_backups = len(backups)
        total_size_mb = sum(backup['file_size_mb'] for backup in backups)
        
        # 企業別統計
        company_stats = {}
        for backup in backups:
            company_id = backup['company_id']
            if company_id not in company_stats:
                company_stats[company_id] = {
                    'company_name': backup['company_name'],
                    'backup_count': 0,
                    'total_size_mb': 0
                }
            company_stats[company_id]['backup_count'] += 1
            company_stats[company_id]['total_size_mb'] += backup['file_size_mb']
        
        # タイプ別統計
        type_stats = {}
        for backup in backups:
            backup_type = backup['backup_type']
            if backup_type not in type_stats:
                type_stats[backup_type] = {
                    'count': 0,
                    'total_size_mb': 0
                }
            type_stats[backup_type]['count'] += 1
            type_stats[backup_type]['total_size_mb'] += backup['file_size_mb']
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_backups': total_backups,
                'total_size_mb': round(total_size_mb, 2),
                'company_stats': company_stats,
                'type_stats': type_stats
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'バックアップ統計取得エラー: {str(e)}'
        }), 500

@backup_bp.route('/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    try:
        # バックアップディレクトリの存在確認
        backup_dir_exists = os.path.exists(backup_service.backup_dir)
        
        # バックアップファイル数を取得
        backup_count = 0
        if backup_dir_exists:
            backup_count = len([f for f in os.listdir(backup_service.backup_dir) 
                              if f.endswith('.zip') and f.startswith('company_')])
        
        return jsonify({
            'success': True,
            'message': 'データバックアップサービスが正常に動作しています',
            'backup_directory_exists': backup_dir_exists,
            'backup_count': backup_count,
            'timestamp': '2024-07-30T12:00:00Z'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'バックアップヘルスチェックエラー: {str(e)}'
        }), 500 