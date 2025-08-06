from flask import Blueprint, request, jsonify
from services.cancellation_service import cancellation_service
from services.company_service import CompanyService
import json
from datetime import datetime

cancellation_bp = Blueprint('cancellation', __name__, url_prefix='/api/v1/cancellation')

# インスタンスを作成
company_service = CompanyService()

@cancellation_bp.route('/companies/<int:company_id>/cancel', methods=['POST'])
def cancel_company(company_id):
    """企業の解約処理"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'other')
        notes = data.get('notes', '')
        
        result = cancellation_service.process_company_cancellation(
            company_id, reason, notes
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'解約処理エラー: {str(e)}'
        }), 500

@cancellation_bp.route('/companies/<int:company_id>/schedule-deletion', methods=['POST'])
def schedule_company_deletion(company_id):
    """企業データの削除スケジュール"""
    try:
        data = request.get_json() or {}
        deletion_days = data.get('deletion_days', 30)
        
        result = cancellation_service.schedule_data_deletion(
            company_id, deletion_days
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'削除スケジュールエラー: {str(e)}'
        }), 500

@cancellation_bp.route('/companies/<int:company_id>/execute-deletion', methods=['POST'])
def execute_company_deletion(company_id):
    """企業データの即座削除"""
    try:
        result = cancellation_service.execute_data_deletion(company_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'データ削除エラー: {str(e)}'
        }), 500

@cancellation_bp.route('/companies/<int:company_id>/cancel-deletion-schedule', methods=['POST'])
def cancel_deletion_schedule(company_id):
    """削除スケジュールのキャンセル"""
    try:
        result = cancellation_service.cancel_deletion_schedule(company_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'スケジュールキャンセルエラー: {str(e)}'
        }), 500

@cancellation_bp.route('/history', methods=['GET'])
def get_cancellation_history():
    """解約履歴の取得"""
    try:
        company_id = request.args.get('company_id', type=int)
        
        result = cancellation_service.get_cancellation_history(company_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'履歴取得エラー: {str(e)}'
        }), 500

@cancellation_bp.route('/pending-deletions', methods=['GET'])
def get_pending_deletions():
    """削除予定企業の取得"""
    try:
        result = cancellation_service.get_pending_deletions()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'削除予定取得エラー: {str(e)}'
        }), 500

@cancellation_bp.route('/reasons', methods=['GET'])
def get_cancellation_reasons():
    """解約理由の一覧取得"""
    try:
        return jsonify({
            'success': True,
            'reasons': cancellation_service.cancellation_reasons
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'理由一覧取得エラー: {str(e)}'
        }), 500

@cancellation_bp.route('/companies/<int:company_id>/cancellation-status', methods=['GET'])
def get_company_cancellation_status(company_id):
    """企業の解約状況取得"""
    try:
        # 企業情報を取得
        company_result = company_service.get_company(company_id)
        if not company_result['success']:
            return jsonify(company_result), 404
        
        company = company_result['company']
        
        # 解約履歴を取得
        cancellation_result = cancellation_service.get_cancellation_history(company_id)
        
        status = {
            'company_id': company_id,
            'company_name': company['company_name'],
            'company_status': company['status'],
            'is_cancelled': company['status'] == 'cancelled',
            'cancellation_info': None,
            'deletion_info': None
        }
        
        if cancellation_result['success'] and cancellation_result['cancellations']:
            latest_cancellation = cancellation_result['cancellations'][0]
            status['cancellation_info'] = {
                'cancelled_at': latest_cancellation['cancelled_at'],
                'reason': latest_cancellation['cancellation_reason'],
                'notes': latest_cancellation['cancellation_notes']
            }
            
            if latest_cancellation['scheduled_deletion_date']:
                status['deletion_info'] = {
                    'scheduled_date': latest_cancellation['scheduled_deletion_date'],
                    'is_pending': latest_cancellation['scheduled_deletion_date'] <= datetime.now().isoformat()
                }
        
        return jsonify({
            'success': True,
            'status': status
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'解約状況取得エラー: {str(e)}'
        }), 500

@cancellation_bp.route('/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    return jsonify({
        'success': True,
        'message': '解約・データ削除サービスが正常に動作しています',
        'timestamp': '2024-07-30T12:00:00Z'
    }), 200 