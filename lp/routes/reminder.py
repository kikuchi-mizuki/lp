from flask import Blueprint, request, jsonify
from lp.services.reminder_service import reminder_service
import json

reminder_bp = Blueprint('reminder', __name__, url_prefix='/api/v1/reminder')

@reminder_bp.route('/companies/<int:company_id>/schedules', methods=['POST'])
def create_reminder_schedule(company_id):
    """リマインダースケジュールを作成"""
    try:
        data = request.get_json() or {}
        reminder_type = data.get('reminder_type')
        custom_days = data.get('custom_days')
        custom_message = data.get('custom_message')
        
        if not reminder_type:
            return jsonify({
                'success': False,
                'error': 'reminder_type は必須です'
            }), 400
        
        result = reminder_service.create_reminder_schedule(
            company_id, 
            reminder_type, 
            custom_days, 
            custom_message
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'リマインダースケジュール作成エラー: {str(e)}'
        }), 500

@reminder_bp.route('/companies/<int:company_id>/schedules', methods=['GET'])
def get_reminder_schedules(company_id):
    """リマインダースケジュール一覧を取得"""
    try:
        reminder_type = request.args.get('reminder_type')
        status = request.args.get('status')
        
        result = reminder_service.get_reminder_schedules(
            company_id, 
            reminder_type, 
            status
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'リマインダースケジュール取得エラー: {str(e)}'
        }), 500

@reminder_bp.route('/schedules', methods=['GET'])
def get_all_reminder_schedules():
    """全リマインダースケジュール一覧を取得"""
    try:
        reminder_type = request.args.get('reminder_type')
        status = request.args.get('status')
        
        result = reminder_service.get_reminder_schedules(
            None, 
            reminder_type, 
            status
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'リマインダースケジュール取得エラー: {str(e)}'
        }), 500

@reminder_bp.route('/schedules/<int:reminder_id>', methods=['PUT'])
def update_reminder_schedule(reminder_id):
    """リマインダースケジュールを更新"""
    try:
        data = request.get_json() or {}
        
        # 更新可能なフィールドのみを抽出
        updates = {}
        allowed_fields = ['days_before', 'custom_message', 'status', 'next_send_at']
        
        for field in allowed_fields:
            if field in data:
                updates[field] = data[field]
        
        if not updates:
            return jsonify({
                'success': False,
                'error': '更新するフィールドが指定されていません'
            }), 400
        
        result = reminder_service.update_reminder_schedule(reminder_id, **updates)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'リマインダースケジュール更新エラー: {str(e)}'
        }), 500

@reminder_bp.route('/schedules/<int:reminder_id>', methods=['DELETE'])
def delete_reminder_schedule(reminder_id):
    """リマインダースケジュールを削除"""
    try:
        result = reminder_service.delete_reminder_schedule(reminder_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'リマインダースケジュール削除エラー: {str(e)}'
        }), 500

@reminder_bp.route('/schedules/<int:reminder_id>/send', methods=['POST'])
def send_reminder(reminder_id):
    """リマインダーを送信"""
    try:
        result = reminder_service.send_reminder(reminder_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'リマインダー送信エラー: {str(e)}'
        }), 500

@reminder_bp.route('/companies/<int:company_id>/send-welcome', methods=['POST'])
def send_welcome_reminder(company_id):
    """ウェルカムリマインダーを送信"""
    try:
        # ウェルカムリマインダーを作成して送信
        result = reminder_service.create_reminder_schedule(
            company_id, 
            'welcome'
        )
        
        if result['success']:
            reminder_id = result['reminder']['id']
            send_result = reminder_service.send_reminder(reminder_id)
            
            if send_result['success']:
                return jsonify({
                    'success': True,
                    'message': 'ウェルカムリマインダーを送信しました',
                    'reminder': result['reminder']
                }), 200
            else:
                return jsonify(send_result), 400
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'ウェルカムリマインダー送信エラー: {str(e)}'
        }), 500

@reminder_bp.route('/companies/<int:company_id>/send-trial-ending', methods=['POST'])
def send_trial_ending_reminder(company_id):
    """トライアル終了リマインダーを送信"""
    try:
        data = request.get_json() or {}
        days_before = data.get('days_before', 3)
        
        # トライアル終了リマインダーを作成して送信
        result = reminder_service.create_reminder_schedule(
            company_id, 
            'trial_ending',
            custom_days=[days_before]
        )
        
        if result['success']:
            reminder_id = result['reminder']['id']
            send_result = reminder_service.send_reminder(reminder_id)
            
            if send_result['success']:
                return jsonify({
                    'success': True,
                    'message': f'トライアル終了リマインダーを送信しました（{days_before}日前）',
                    'reminder': result['reminder']
                }), 200
            else:
                return jsonify(send_result), 400
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'トライアル終了リマインダー送信エラー: {str(e)}'
        }), 500

@reminder_bp.route('/companies/<int:company_id>/send-payment-due', methods=['POST'])
def send_payment_due_reminder(company_id):
    """支払い期限リマインダーを送信"""
    try:
        data = request.get_json() or {}
        days_before = data.get('days_before', 3)
        
        # 支払い期限リマインダーを作成して送信
        result = reminder_service.create_reminder_schedule(
            company_id, 
            'payment_due',
            custom_days=[days_before]
        )
        
        if result['success']:
            reminder_id = result['reminder']['id']
            send_result = reminder_service.send_reminder(reminder_id)
            
            if send_result['success']:
                return jsonify({
                    'success': True,
                    'message': f'支払い期限リマインダーを送信しました（{days_before}日前）',
                    'reminder': result['reminder']
                }), 200
            else:
                return jsonify(send_result), 400
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'支払い期限リマインダー送信エラー: {str(e)}'
        }), 500

@reminder_bp.route('/companies/<int:company_id>/send-renewal', methods=['POST'])
def send_renewal_reminder(company_id):
    """契約更新リマインダーを送信"""
    try:
        data = request.get_json() or {}
        days_before = data.get('days_before', 7)
        
        # 契約更新リマインダーを作成して送信
        result = reminder_service.create_reminder_schedule(
            company_id, 
            'subscription_renewal',
            custom_days=[days_before]
        )
        
        if result['success']:
            reminder_id = result['reminder']['id']
            send_result = reminder_service.send_reminder(reminder_id)
            
            if send_result['success']:
                return jsonify({
                    'success': True,
                    'message': f'契約更新リマインダーを送信しました（{days_before}日前）',
                    'reminder': result['reminder']
                }), 200
            else:
                return jsonify(send_result), 400
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'契約更新リマインダー送信エラー: {str(e)}'
        }), 500

@reminder_bp.route('/companies/<int:company_id>/send-usage', methods=['POST'])
def send_usage_reminder(company_id):
    """利用状況リマインダーを送信"""
    try:
        data = request.get_json() or {}
        days_before = data.get('days_before', 30)
        
        # 利用状況リマインダーを作成して送信
        result = reminder_service.create_reminder_schedule(
            company_id, 
            'usage_reminder',
            custom_days=[days_before]
        )
        
        if result['success']:
            reminder_id = result['reminder']['id']
            send_result = reminder_service.send_reminder(reminder_id)
            
            if send_result['success']:
                return jsonify({
                    'success': True,
                    'message': f'利用状況リマインダーを送信しました（{days_before}日前）',
                    'reminder': result['reminder']
                }), 200
            else:
                return jsonify(send_result), 400
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'利用状況リマインダー送信エラー: {str(e)}'
        }), 500

@reminder_bp.route('/companies/<int:company_id>/bulk-send', methods=['POST'])
def bulk_send_reminders(company_id):
    """複数のリマインダーを一括送信"""
    try:
        data = request.get_json() or {}
        reminder_types = data.get('reminder_types', [])
        
        if not reminder_types:
            return jsonify({
                'success': False,
                'error': 'reminder_types は必須です'
            }), 400
        
        results = []
        success_count = 0
        
        for reminder_type in reminder_types:
            # リマインダーを作成して送信
            create_result = reminder_service.create_reminder_schedule(
                company_id, 
                reminder_type
            )
            
            if create_result['success']:
                reminder_id = create_result['reminder']['id']
                send_result = reminder_service.send_reminder(reminder_id)
                
                if send_result['success']:
                    success_count += 1
                    results.append({
                        'reminder_type': reminder_type,
                        'status': 'success',
                        'message': '送信成功'
                    })
                else:
                    results.append({
                        'reminder_type': reminder_type,
                        'status': 'error',
                        'message': send_result.get('error', '送信失敗')
                    })
            else:
                results.append({
                    'reminder_type': reminder_type,
                    'status': 'error',
                    'message': create_result.get('error', '作成失敗')
                })
        
        return jsonify({
            'success': True,
            'message': f'{success_count}/{len(reminder_types)}件のリマインダーを送信しました',
            'results': results,
            'success_count': success_count,
            'total_count': len(reminder_types)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'一括リマインダー送信エラー: {str(e)}'
        }), 500

@reminder_bp.route('/statistics', methods=['GET'])
def get_reminder_statistics():
    """リマインダー統計を取得"""
    try:
        company_id = request.args.get('company_id', type=int)
        
        result = reminder_service.get_reminder_statistics(company_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'リマインダー統計取得エラー: {str(e)}'
        }), 500

@reminder_bp.route('/types', methods=['GET'])
def get_reminder_types():
    """リマインダータイプ一覧を取得"""
    try:
        result = reminder_service.get_reminder_types()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'リマインダータイプ取得エラー: {str(e)}'
        }), 500

@reminder_bp.route('/test', methods=['POST'])
def test_reminder():
    """テストリマインダーを送信"""
    try:
        data = request.get_json() or {}
        company_id = data.get('company_id')
        reminder_type = data.get('reminder_type', 'welcome')
        custom_message = data.get('custom_message')
        
        if not company_id:
            return jsonify({
                'success': False,
                'error': 'company_id は必須です'
            }), 400
        
        # テストリマインダーを作成して送信
        result = reminder_service.create_reminder_schedule(
            company_id, 
            reminder_type,
            custom_message=custom_message
        )
        
        if result['success']:
            reminder_id = result['reminder']['id']
            send_result = reminder_service.send_reminder(reminder_id)
            
            if send_result['success']:
                return jsonify({
                    'success': True,
                    'message': 'テストリマインダーを送信しました',
                    'reminder': result['reminder']
                }), 200
            else:
                return jsonify(send_result), 400
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'テストリマインダー送信エラー: {str(e)}'
        }), 500

@reminder_bp.route('/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    try:
        # リマインダータイプを取得してサービスが正常に動作しているかチェック
        result = reminder_service.get_reminder_types()
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'リマインダーサービスは正常に動作しています',
                'service_status': 'healthy',
                'available_types': len(result['reminder_types']),
                'timestamp': '2024-07-30T12:00:00Z'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'リマインダーサービスに問題があります',
                'service_status': 'error',
                'error': result.get('error', '不明なエラー')
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'リマインダーサービスに問題があります',
            'service_status': 'error',
            'error': str(e)
        }), 500 