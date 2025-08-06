from flask import Blueprint, request, jsonify
from lp.services.dashboard_service import dashboard_service
import json
import os
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/v1/dashboard')

@dashboard_bp.route('/overview', methods=['GET'])
def get_overview():
    """概要統計を取得"""
    try:
        result = dashboard_service.get_overview_statistics()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'概要統計取得エラー: {str(e)}'
        }), 500

@dashboard_bp.route('/cancellation', methods=['GET'])
def get_cancellation_stats():
    """解約統計を取得"""
    try:
        result = dashboard_service.get_cancellation_statistics()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'解約統計取得エラー: {str(e)}'
        }), 500

@dashboard_bp.route('/notification', methods=['GET'])
def get_notification_stats():
    """通知統計を取得"""
    try:
        result = dashboard_service.get_notification_statistics()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'通知統計取得エラー: {str(e)}'
        }), 500

@dashboard_bp.route('/backup', methods=['GET'])
def get_backup_stats():
    """バックアップ統計を取得"""
    try:
        result = dashboard_service.get_backup_statistics()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'バックアップ統計取得エラー: {str(e)}'
        }), 500

@dashboard_bp.route('/revenue', methods=['GET'])
def get_revenue_analytics():
    """収益分析を取得"""
    try:
        result = dashboard_service.get_revenue_analytics()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'収益分析取得エラー: {str(e)}'
        }), 500

@dashboard_bp.route('/companies', methods=['GET'])
def get_companies_analytics():
    """企業分析を取得"""
    try:
        company_id = request.args.get('company_id', type=int)
        result = dashboard_service.get_company_analytics(company_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'企業分析取得エラー: {str(e)}'
        }), 500

@dashboard_bp.route('/summary', methods=['GET'])
def get_dashboard_summary():
    """ダッシュボード全体のサマリーを取得"""
    try:
        result = dashboard_service.get_dashboard_summary()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'ダッシュボードサマリー取得エラー: {str(e)}'
        }), 500

@dashboard_bp.route('/companies/<int:company_id>/analytics', methods=['GET'])
def get_company_analytics(company_id):
    """特定企業の分析を取得"""
    try:
        result = dashboard_service.get_company_analytics(company_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'企業分析取得エラー: {str(e)}'
        }), 500

@dashboard_bp.route('/export', methods=['GET'])
def export_dashboard_data():
    """ダッシュボードデータをエクスポート"""
    try:
        export_type = request.args.get('type', 'summary')
        
        if export_type == 'summary':
            result = dashboard_service.get_dashboard_summary()
        elif export_type == 'overview':
            result = dashboard_service.get_overview_statistics()
        elif export_type == 'cancellation':
            result = dashboard_service.get_cancellation_statistics()
        elif export_type == 'notification':
            result = dashboard_service.get_notification_statistics()
        elif export_type == 'backup':
            result = dashboard_service.get_backup_statistics()
        elif export_type == 'revenue':
            result = dashboard_service.get_revenue_analytics()
        elif export_type == 'companies':
            result = dashboard_service.get_company_analytics()
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
                download_name=f'dashboard_export_{export_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                mimetype='application/json'
            )
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'ダッシュボードエクスポートエラー: {str(e)}'
        }), 500

@dashboard_bp.route('/realtime', methods=['GET'])
def get_realtime_stats():
    """リアルタイム統計を取得"""
    try:
        # 現在時刻の統計を取得
        realtime_stats = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'stats': {}
        }
        
        # 概要統計を取得
        overview = dashboard_service.get_overview_statistics()
        if overview['success']:
            realtime_stats['stats']['overview'] = overview['overview']
        
        # 今日の通知数を取得
        try:
            from lp.utils.db import get_db_connection
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT COUNT(*) FROM company_notifications 
                WHERE DATE(sent_at) = CURRENT_DATE
            ''')
            today_notifications = c.fetchone()[0]
            
            c.execute('''
                SELECT COUNT(*) FROM companies 
                WHERE DATE(created_at) = CURRENT_DATE
            ''')
            today_new_companies = c.fetchone()[0]
            
            conn.close()
            
            realtime_stats['stats']['today'] = {
                'notifications': today_notifications,
                'new_companies': today_new_companies
            }
            
        except Exception as e:
            realtime_stats['stats']['today'] = {
                'error': str(e)
            }
        
        return jsonify(realtime_stats), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'リアルタイム統計取得エラー: {str(e)}'
        }), 500

@dashboard_bp.route('/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    try:
        # 基本的な統計を取得してサービスが動作することを確認
        overview = dashboard_service.get_overview_statistics()
        
        return jsonify({
            'success': True,
            'message': '管理ダッシュボードサービスが正常に動作しています',
            'service_status': 'healthy' if overview['success'] else 'error',
            'timestamp': '2024-07-30T12:00:00Z'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'ダッシュボードヘルスチェックエラー: {str(e)}'
        }), 500 