from flask import Blueprint, request, jsonify
from services.notification_service import notification_service
from services.company_service import CompanyService
import json

notification_bp = Blueprint('notification', __name__, url_prefix='/api/v1/notification')

# インスタンスを作成
company_service = CompanyService()

@notification_bp.route('/companies/<int:company_id>/send', methods=['POST'])
def send_notification(company_id):
    """企業に通知を送信"""
    try:
        data = request.get_json() or {}
        notification_type = data.get('notification_type')
        payment_data = data.get('payment_data', {})
        
        if not notification_type:
            return jsonify({
                'success': False,
                'error': 'notification_type is required'
            }), 400
        
        result = notification_service.send_payment_notification(
            company_id, notification_type, payment_data
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'通知送信エラー: {str(e)}'
        }), 500

@notification_bp.route('/companies/<int:company_id>/trial-reminder', methods=['POST'])
def send_trial_reminder(company_id):
    """トライアル終了リマインダーを送信"""
    try:
        data = request.get_json() or {}
        days_before = data.get('days_before', 3)
        
        result = notification_service.send_trial_ending_reminder(
            company_id, days_before
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'トライアルリマインダーエラー: {str(e)}'
        }), 500

@notification_bp.route('/companies/<int:company_id>/renewal-reminder', methods=['POST'])
def send_renewal_reminder(company_id):
    """契約更新リマインダーを送信"""
    try:
        data = request.get_json() or {}
        days_before = data.get('days_before', 7)
        
        result = notification_service.send_renewal_reminder(
            company_id, days_before
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'契約更新リマインダーエラー: {str(e)}'
        }), 500

@notification_bp.route('/companies/<int:company_id>/deletion-reminder', methods=['POST'])
def send_deletion_reminder(company_id):
    """データ削除リマインダーを送信"""
    try:
        data = request.get_json() or {}
        days_before = data.get('days_before', 7)
        
        result = notification_service.send_deletion_reminder(
            company_id, days_before
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'データ削除リマインダーエラー: {str(e)}'
        }), 500

@notification_bp.route('/history', methods=['GET'])
def get_notification_history():
    """通知履歴を取得"""
    try:
        company_id = request.args.get('company_id', type=int)
        notification_type = request.args.get('notification_type')
        limit = request.args.get('limit', 50, type=int)
        
        result = notification_service.get_notification_history(
            company_id, notification_type, limit
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'通知履歴取得エラー: {str(e)}'
        }), 500

@notification_bp.route('/statistics', methods=['GET'])
def get_notification_statistics():
    """通知統計を取得"""
    try:
        result = notification_service.get_notification_statistics()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'通知統計取得エラー: {str(e)}'
        }), 500

@notification_bp.route('/types', methods=['GET'])
def get_notification_types():
    """通知タイプ一覧を取得"""
    try:
        return jsonify({
            'success': True,
            'notification_types': notification_service.notification_types
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'通知タイプ取得エラー: {str(e)}'
        }), 500

@notification_bp.route('/companies/<int:company_id>/test-notification', methods=['POST'])
def test_notification(company_id):
    """テスト通知を送信"""
    try:
        data = request.get_json() or {}
        notification_type = data.get('notification_type', 'payment_success')
        
        # テスト用のデータ
        test_data = {
            'next_billing_date': '2024年8月30日',
            'amount': 3900,
            'retry_date': '2024年8月5日',
            'renewal_date': '2024年8月30日',
            'trial_end_date': '2024年8月15日',
            'cancellation_date': '2024年8月1日',
            'reason': 'テスト用',
            'deletion_days': 30,
            'deletion_date': '2024年9月1日'
        }
        
        result = notification_service.send_payment_notification(
            company_id, notification_type, test_data
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'テスト通知エラー: {str(e)}'
        }), 500

@notification_bp.route('/companies/<int:company_id>/bulk-reminders', methods=['POST'])
def send_bulk_reminders(company_id):
    """複数のリマインダーを一括送信"""
    try:
        data = request.get_json() or {}
        reminder_types = data.get('reminder_types', [])
        
        if not reminder_types:
            return jsonify({
                'success': False,
                'error': 'reminder_types is required'
            }), 400
        
        results = {}
        
        for reminder_type in reminder_types:
            if reminder_type == 'trial':
                result = notification_service.send_trial_ending_reminder(company_id)
            elif reminder_type == 'renewal':
                result = notification_service.send_renewal_reminder(company_id)
            elif reminder_type == 'deletion':
                result = notification_service.send_deletion_reminder(company_id)
            else:
                result = {
                    'success': False,
                    'error': f'不明なリマインダータイプ: {reminder_type}'
                }
            
            results[reminder_type] = result
        
        return jsonify({
            'success': True,
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'一括リマインダーエラー: {str(e)}'
        }), 500

@notification_bp.route('/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    return jsonify({
        'success': True,
        'message': '通知・アラートサービスが正常に動作しています',
        'timestamp': '2024-07-30T12:00:00Z'
    }), 200 