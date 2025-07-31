#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
企業別LINEアカウント管理API
"""

from flask import Blueprint, request, jsonify
from services.company_line_account_service import company_line_service
import json

company_line_accounts_bp = Blueprint('company_line_accounts', __name__, url_prefix='/api/v1/company-line-accounts')

@company_line_accounts_bp.route('/companies/<int:company_id>/create', methods=['POST'])
def create_company_line_account(company_id):
    """企業用のLINEアカウントを作成"""
    try:
        data = request.get_json() or {}
        company_name = data.get('company_name', '')
        
        result = company_line_service.create_company_line_account(company_id, company_name)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'LINEアカウントを作成しました',
                'data': result
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'LINEアカウント作成エラー: {str(e)}'
        }), 500

@company_line_accounts_bp.route('/companies/<int:company_id>', methods=['GET'])
def get_company_line_account(company_id):
    """企業のLINEアカウント情報を取得"""
    try:
        result = company_line_service.get_company_line_account(company_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['account']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'LINEアカウント取得エラー: {str(e)}'
        }), 500

@company_line_accounts_bp.route('/companies/<int:company_id>', methods=['PUT'])
def update_company_line_account(company_id):
    """企業のLINEアカウント情報を更新"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '更新データがありません'
            }), 400
        
        result = company_line_service.update_company_line_account(company_id, data)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'LINEアカウント更新エラー: {str(e)}'
        }), 500

@company_line_accounts_bp.route('/companies/<int:company_id>', methods=['DELETE'])
def delete_company_line_account(company_id):
    """企業のLINEアカウントを削除"""
    try:
        result = company_line_service.delete_company_line_account(company_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'LINEアカウント削除エラー: {str(e)}'
        }), 500

@company_line_accounts_bp.route('/list', methods=['GET'])
def list_company_line_accounts():
    """企業のLINEアカウント一覧を取得"""
    try:
        status = request.args.get('status')
        
        result = company_line_service.list_company_line_accounts(status)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['accounts']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'LINEアカウント一覧取得エラー: {str(e)}'
        }), 500

@company_line_accounts_bp.route('/companies/<int:company_id>/send-message', methods=['POST'])
def send_message_to_company(company_id):
    """企業のLINEアカウントにメッセージを送信"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'メッセージが指定されていません'
            }), 400
        
        message = data['message']
        result = company_line_service.send_message_to_company(company_id, message)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'メッセージ送信エラー: {str(e)}'
        }), 500

@company_line_accounts_bp.route('/companies/<int:company_id>/qr-code', methods=['GET'])
def get_company_qr_code(company_id):
    """企業のLINEアカウントQRコードを取得"""
    try:
        result = company_line_service.get_company_line_account(company_id)
        
        if result['success']:
            account = result['account']
            return jsonify({
                'success': True,
                'data': {
                    'qr_code_url': account['qr_code_url'],
                    'basic_id': account['basic_id'],
                    'channel_id': account['channel_id']
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'QRコード取得エラー: {str(e)}'
        }), 500

@company_line_accounts_bp.route('/companies/<int:company_id>/webhook-url', methods=['GET'])
def get_company_webhook_url(company_id):
    """企業のLINEアカウントWebhook URLを取得"""
    try:
        result = company_line_service.get_company_line_account(company_id)
        
        if result['success']:
            account = result['account']
            return jsonify({
                'success': True,
                'data': {
                    'webhook_url': account['webhook_url'],
                    'channel_id': account['channel_id']
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Webhook URL取得エラー: {str(e)}'
        }), 500

@company_line_accounts_bp.route('/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    return jsonify({
        'success': True,
        'message': 'Company Line Accounts API is running',
        'status': 'healthy'
    }), 200 