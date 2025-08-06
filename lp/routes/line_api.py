#!/usr/bin/env python3
"""
LINE API用ルート
企業のLINEアカウント管理APIエンドポイント
"""

from flask import Blueprint, request, jsonify
from lp.services.line_api_service import line_api_service
from lp.services.company_service import CompanyService

# インスタンスを作成
company_service = CompanyService()
import json

line_api_bp = Blueprint('line_api', __name__, url_prefix='/api/v1/line')

@line_api_bp.route('/companies/<int:company_id>/create-channel', methods=['POST'])
def create_line_channel(company_id):
    """企業用のLINEチャンネルを作成"""
    try:
        # 企業情報を取得
        company = company_service.get_company(company_id)
        if not company:
            return jsonify({
                'success': False,
                'error': '企業が見つかりません'
            }), 404
        
        # LINEチャンネルを作成
        result = line_api_service.create_line_channel(
            company_id, 
            company['company_name'], 
            company['company_code']
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@line_api_bp.route('/companies/<int:company_id>/send-message', methods=['POST'])
def send_line_message(company_id):
    """企業のLINEアカウントからメッセージを送信"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        message_type = data.get('type', 'text')
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'メッセージが指定されていません'
            }), 400
        
        result = line_api_service.send_line_message(company_id, message, message_type)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@line_api_bp.route('/companies/<int:company_id>/statistics', methods=['GET'])
def get_line_statistics(company_id):
    """企業のLINE利用統計を取得"""
    try:
        result = line_api_service.get_line_statistics(company_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@line_api_bp.route('/companies/<int:company_id>/webhook', methods=['POST'])
def setup_webhook(company_id):
    """企業のLINE Webhookを設定"""
    try:
        data = request.get_json()
        webhook_url = data.get('webhook_url', '')
        
        if not webhook_url:
            return jsonify({
                'success': False,
                'error': 'Webhook URLが指定されていません'
            }), 400
        
        result = line_api_service.setup_webhook(company_id, webhook_url)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@line_api_bp.route('/companies/<int:company_id>/disable', methods=['POST'])
def disable_line_account(company_id):
    """企業のLINEアカウントを無効化"""
    try:
        result = line_api_service.disable_line_account(company_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@line_api_bp.route('/companies/<int:company_id>/enable', methods=['POST'])
def enable_line_account(company_id):
    """企業のLINEアカウントを有効化"""
    try:
        result = line_api_service.enable_line_account(company_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@line_api_bp.route('/companies/<int:company_id>/delete', methods=['DELETE'])
def delete_line_account(company_id):
    """企業のLINEアカウントを削除"""
    try:
        result = line_api_service.delete_line_account(company_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@line_api_bp.route('/companies/<int:company_id>/notify', methods=['POST'])
def send_notification(company_id):
    """企業に通知を送信"""
    try:
        data = request.get_json()
        notification_type = data.get('type', '')
        message = data.get('message', '')
        
        if not notification_type or not message:
            return jsonify({
                'success': False,
                'error': '通知タイプとメッセージが指定されていません'
            }), 400
        
        result = line_api_service.send_notification_to_company(
            company_id, notification_type, message
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@line_api_bp.route('/accounts', methods=['GET'])
def get_all_line_accounts():
    """全企業のLINEアカウント情報を取得"""
    try:
        result = line_api_service.get_all_line_accounts()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@line_api_bp.route('/test-message', methods=['POST'])
def test_line_message():
    """テスト用メッセージ送信"""
    try:
        data = request.get_json()
        company_id = data.get('company_id')
        message = data.get('message', 'テストメッセージです')
        
        if not company_id:
            return jsonify({
                'success': False,
                'error': '企業IDが指定されていません'
            }), 400
        
        result = line_api_service.send_line_message(company_id, message)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'テストメッセージが送信されました',
                'details': result
            }), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@line_api_bp.route('/health', methods=['GET'])
def health_check():
    """LINE API ヘルスチェック"""
    return jsonify({
        'success': True,
        'message': 'LINE API サービスが正常に動作しています',
        'timestamp': '2024-07-30T12:00:00Z'
    }), 200 