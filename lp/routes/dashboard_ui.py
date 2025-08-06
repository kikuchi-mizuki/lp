from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from lp.services.security_service import require_auth, require_admin
from lp.services.dashboard_service import dashboard_service
import json

dashboard_ui_bp = Blueprint('dashboard_ui', __name__)

@dashboard_ui_bp.route('/dashboard')
@require_auth
def dashboard():
    """管理ダッシュボードのメインページ"""
    try:
        return render_template('dashboard.html')
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'ダッシュボード表示エラー: {str(e)}'
        }), 500

@dashboard_ui_bp.route('/dashboard/login')
def login_page():
    """ログインページ"""
    try:
        return render_template('login.html')
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'ログインページ表示エラー: {str(e)}'
        }), 500

@dashboard_ui_bp.route('/dashboard/companies')
@require_auth
def companies_page():
    """企業管理ページ"""
    try:
        return render_template('companies.html')
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'企業管理ページ表示エラー: {str(e)}'
        }), 500

@dashboard_ui_bp.route('/dashboard/analytics')
@require_auth
def analytics_page():
    """分析ページ"""
    try:
        return render_template('analytics.html')
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'分析ページ表示エラー: {str(e)}'
        }), 500

@dashboard_ui_bp.route('/dashboard/notifications')
@require_auth
def notifications_page():
    """通知管理ページ"""
    try:
        return render_template('notifications.html')
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'通知管理ページ表示エラー: {str(e)}'
        }), 500

@dashboard_ui_bp.route('/dashboard/security')
@require_auth
def security_page():
    """セキュリティページ"""
    try:
        return render_template('security.html')
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'セキュリティページ表示エラー: {str(e)}'
        }), 500

@dashboard_ui_bp.route('/dashboard/settings')
@require_auth
def settings_page():
    """設定ページ"""
    try:
        return render_template('settings.html')
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'設定ページ表示エラー: {str(e)}'
        }), 500

@dashboard_ui_bp.route('/dashboard/activities')
@require_auth
def get_activities():
    """最新アクティビティを取得"""
    try:
        # ダッシュボードサービスからアクティビティを取得
        result = dashboard_service.get_recent_activities()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'アクティビティ取得エラー: {str(e)}'
        }), 500

@dashboard_ui_bp.route('/dashboard/export')
@require_auth
def export_dashboard_data():
    """ダッシュボードデータのエクスポート"""
    try:
        export_type = request.args.get('type', 'json')
        
        if export_type == 'json':
            # JSON形式でエクスポート
            result = dashboard_service.get_dashboard_summary()
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 400
        else:
            return jsonify({
                'success': False,
                'error': 'サポートされていないエクスポート形式です'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'データエクスポートエラー: {str(e)}'
        }), 500

@dashboard_ui_bp.route('/dashboard/realtime')
@require_auth
def get_realtime_data():
    """リアルタイムデータを取得"""
    try:
        # リアルタイム統計を取得
        result = dashboard_service.get_realtime_statistics()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'リアルタイムデータ取得エラー: {str(e)}'
        }), 500

@dashboard_ui_bp.route('/dashboard/health')
def dashboard_health():
    """ダッシュボードの健全性チェック"""
    try:
        return jsonify({
            'success': True,
            'message': 'ダッシュボードUIは正常に動作しています',
            'status': 'healthy',
            'timestamp': '2024-07-30T12:00:00Z'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'ダッシュボードUIに問題があります',
            'status': 'error',
            'error': str(e)
        }), 500 