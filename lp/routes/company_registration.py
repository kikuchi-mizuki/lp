#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
企業情報登録API
"""

from flask import Blueprint, request, jsonify, render_template
from services.company_registration_service import company_registration_service
import json

company_registration_bp = Blueprint('company_registration', __name__, url_prefix='/api/v1')

@company_registration_bp.route('/company-registration', methods=['POST'])
def register_company():
    """企業情報を登録"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'データが提供されていません'
            }), 400
        
        # 必須フィールドのチェック
        required_fields = [
            'company_name', 'contact_email', 'line_channel_id',
            'line_access_token', 'line_channel_secret'
        ]
        
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'必須フィールド "{field}" が不足しています'
                }), 400
        
        # 企業情報を登録
        result = company_registration_service.register_company(data)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': '企業情報の登録が完了しました',
                'data': {
                    'company_id': result['company_id'],
                    'line_account_id': result['line_account_id'],
                    'company_code': result.get('company_code', ''),
                    'railway_result': result.get('railway_result')
                }
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'企業登録エラー: {str(e)}'
        }), 500

@company_registration_bp.route('/company-registration/<int:company_id>', methods=['GET'])
def get_company_registration(company_id):
    """企業登録情報を取得"""
    try:
        result = company_registration_service.get_company_registration(company_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['data']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'企業情報取得エラー: {str(e)}'
        }), 500

@company_registration_bp.route('/company-registration/<int:company_id>', methods=['PUT'])
def update_company_registration(company_id):
    """企業登録情報を更新"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '更新データがありません'
            }), 400
        
        result = company_registration_service.update_company_registration(company_id, data)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': '企業情報を更新しました'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'企業情報更新エラー: {str(e)}'
        }), 500

@company_registration_bp.route('/company-registration/list', methods=['GET'])
def list_company_registrations():
    """企業登録一覧を取得"""
    try:
        status = request.args.get('status', 'active')
        result = company_registration_service.list_company_registrations()
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['data']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'企業一覧取得エラー: {str(e)}'
        }), 500

@company_registration_bp.route('/company-registration/<int:company_id>/deploy', methods=['POST'])
def deploy_company_line_bot(company_id):
    """企業のLINEボットをRailwayにデプロイ"""
    try:
        result = company_registration_service.deploy_company_line_bot(company_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'LINEボットのデプロイを開始しました',
                'data': {
                    'deployment_id': result['deployment_id'],
                    'railway_url': result['railway_url']
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'デプロイエラー: {str(e)}'
        }), 500

@company_registration_bp.route('/company-registration/<int:company_id>/deployment-status', methods=['GET'])
def get_deployment_status(company_id):
    """デプロイ状況を確認"""
    try:
        result = company_registration_service.get_deployment_status(company_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['status']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'デプロイ状況取得エラー: {str(e)}'
        }), 500

@company_registration_bp.route('/company-registration/<int:company_id>/test-line', methods=['POST'])
def test_line_connection(company_id):
    """LINE接続をテスト"""
    try:
        data = request.get_json() or {}
        test_message = data.get('message', 'テストメッセージです')
        
        result = company_registration_service.test_line_connection(company_id, test_message)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'LINE接続テストが成功しました'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'LINE接続テストエラー: {str(e)}'
        }), 500

@company_registration_bp.route('/company-registration/validate-line-credentials', methods=['POST'])
def validate_line_credentials():
    """LINE認証情報を検証"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '認証情報が提供されていません'
            }), 400
        
        result = company_registration_service.validate_line_credentials(data)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'LINE認証情報が有効です',
                'data': result['channel_info']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'認証情報検証エラー: {str(e)}'
        }), 500

@company_registration_bp.route('/company-registration/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    return jsonify({
        'success': True,
        'message': 'Company Registration API is running',
        'status': 'healthy'
    }), 200 