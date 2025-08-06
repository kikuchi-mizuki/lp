#!/usr/bin/env python3
"""
コンテンツ管理用ルート
企業のコンテンツ管理APIエンドポイント
"""

from flask import Blueprint, request, jsonify
from services.content_management_service import content_management_service
from services.company_service import CompanyService
import json

content_management_bp = Blueprint('content_management', __name__, url_prefix='/api/v1/content')

# インスタンスを作成
company_service = CompanyService()

@content_management_bp.route('/available', methods=['GET'])
def get_available_contents():
    """利用可能なコンテンツ一覧を取得"""
    try:
        result = content_management_service.get_available_contents()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_management_bp.route('/companies/<int:company_id>/add', methods=['POST'])
def add_company_content(company_id):
    """企業にコンテンツを追加"""
    try:
        # 企業情報を取得
        company = company_service.get_company(company_id)
        if not company:
            return jsonify({
                'success': False,
                'error': '企業が見つかりません'
            }), 404
        
        data = request.get_json()
        content_type = data.get('content_type', '')
        status = data.get('status', 'active')
        
        if not content_type:
            return jsonify({
                'success': False,
                'error': 'コンテンツタイプが指定されていません'
            }), 400
        
        # コンテンツを追加
        result = content_management_service.add_company_content(
            company_id, content_type, status
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

@content_management_bp.route('/companies/<int:company_id>/remove', methods=['POST'])
def remove_company_content(company_id):
    """企業からコンテンツを削除"""
    try:
        data = request.get_json()
        content_type = data.get('content_type', '')
        
        if not content_type:
            return jsonify({
                'success': False,
                'error': 'コンテンツタイプが指定されていません'
            }), 400
        
        # コンテンツを削除
        result = content_management_service.remove_company_content(
            company_id, content_type
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

@content_management_bp.route('/companies/<int:company_id>/update-status', methods=['PUT'])
def update_content_status(company_id):
    """コンテンツのステータスを更新"""
    try:
        data = request.get_json()
        content_type = data.get('content_type', '')
        status = data.get('status', '')
        
        if not content_type:
            return jsonify({
                'success': False,
                'error': 'コンテンツタイプが指定されていません'
            }), 400
        
        if not status:
            return jsonify({
                'success': False,
                'error': 'ステータスが指定されていません'
            }), 400
        
        # ステータスを更新
        result = content_management_service.update_content_status(
            company_id, content_type, status
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

@content_management_bp.route('/companies/<int:company_id>/contents', methods=['GET'])
def get_company_contents(company_id):
    """企業のコンテンツ一覧を取得"""
    try:
        result = content_management_service.get_company_contents(company_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_management_bp.route('/all-contents', methods=['GET'])
def get_all_company_contents():
    """全企業のコンテンツ一覧を取得"""
    try:
        result = content_management_service.get_all_company_contents()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_management_bp.route('/companies/<int:company_id>/notify', methods=['POST'])
def send_content_notification(company_id):
    """コンテンツ関連の通知を送信"""
    try:
        data = request.get_json()
        content_type = data.get('content_type', '')
        message_type = data.get('message_type', 'custom')
        custom_message = data.get('custom_message', '')
        
        if not content_type:
            return jsonify({
                'success': False,
                'error': 'コンテンツタイプが指定されていません'
            }), 400
        
        # 通知を送信
        result = content_management_service.send_content_notification(
            company_id, content_type, message_type, custom_message
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

@content_management_bp.route('/statistics', methods=['GET'])
def get_content_statistics():
    """コンテンツ利用統計を取得"""
    try:
        company_id = request.args.get('company_id', type=int)
        result = content_management_service.get_content_statistics(company_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_management_bp.route('/test-content/<int:company_id>', methods=['POST'])
def test_content_management(company_id):
    """テスト用コンテンツ管理"""
    try:
        data = request.get_json()
        test_type = data.get('type', 'add')  # add, remove, notify
        
        # 企業情報を取得
        company = company_service.get_company(company_id)
        if not company:
            return jsonify({
                'success': False,
                'error': '企業が見つかりません'
            }), 404
        
        if test_type == 'add':
            # テスト用コンテンツ追加
            result = content_management_service.add_company_content(
                company_id, 'ai_accounting', 'active'
            )
        elif test_type == 'remove':
            # テスト用コンテンツ削除
            result = content_management_service.remove_company_content(
                company_id, 'ai_accounting'
            )
        elif test_type == 'notify':
            # テスト用通知送信
            result = content_management_service.send_content_notification(
                company_id, 'ai_accounting', 'custom', 'テスト通知です。'
            )
        else:
            return jsonify({
                'success': False,
                'error': f'無効なテストタイプ: {test_type}'
            }), 400
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': f'テスト{test_type}が成功しました: {company["company_name"]}',
                'details': result
            }), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_management_bp.route('/health', methods=['GET'])
def health_check():
    """コンテンツ管理API ヘルスチェック"""
    return jsonify({
        'success': True,
        'message': 'コンテンツ管理API サービスが正常に動作しています',
        'timestamp': '2024-07-30T12:00:00Z'
    }), 200 