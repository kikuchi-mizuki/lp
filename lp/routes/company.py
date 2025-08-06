"""
企業管理システム APIルート
"""

from flask import Blueprint, request, jsonify
from lp.services.company_service import CompanyService
from lp.services.company_line_service import CompanyLineService
import json

company_bp = Blueprint('company', __name__, url_prefix='/api/v1/companies')

# サービスインスタンス
company_service = CompanyService()
line_service = CompanyLineService()

@company_bp.route('', methods=['POST'])
def create_company():
    """企業を新規作成"""
    try:
        data = request.get_json()
        
        # 必須フィールドの検証
        required_fields = ['company_name', 'email']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'error': f'必須フィールドが不足しています: {field}'
                }), 400
        
        # 企業作成
        result = company_service.create_company(data)
        
        if result['success']:
            company_id = result['company_id']
            
            # LINEアカウント作成
            line_result = line_service.create_line_account(company_id, data)
            
            if line_result['success']:
                return jsonify({
                    'success': True,
                    'message': '企業とLINEアカウントの作成が完了しました',
                    'company_id': company_id,
                    'company_code': result['company_code'],
                    'line_account': line_result['line_account']
                }), 201
            else:
                return jsonify({
                    'success': False,
                    'error': f'企業は作成されましたが、LINEアカウントの作成に失敗しました: {line_result["error"]}',
                    'company_id': company_id,
                    'company_code': result['company_code']
                }), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'企業作成エラー: {str(e)}'
        }), 500

@company_bp.route('/<int:company_id>', methods=['GET'])
def get_company(company_id):
    """企業情報を取得"""
    try:
        result = company_service.get_company(company_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'企業情報取得エラー: {str(e)}'
        }), 500

@company_bp.route('/<int:company_id>', methods=['PUT'])
def update_company(company_id):
    """企業情報を更新"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '更新データが提供されていません'
            }), 400
        
        result = company_service.update_company(company_id, data)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': '企業情報の更新が完了しました'
            }), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'企業情報更新エラー: {str(e)}'
        }), 500

@company_bp.route('/<int:company_id>', methods=['DELETE'])
def delete_company(company_id):
    """企業を削除"""
    try:
        result = company_service.delete_company(company_id)
        
        if result['success']:
            # LINEアカウントも削除
            line_service.delete_line_account(company_id)
            
            return jsonify({
                'success': True,
                'message': '企業の削除が完了しました'
            }), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'企業削除エラー: {str(e)}'
        }), 500

@company_bp.route('', methods=['GET'])
def list_companies():
    """企業一覧を取得"""
    try:
        # クエリパラメータの取得
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        status = request.args.get('status')
        
        result = company_service.list_companies(page, limit, status)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'企業一覧取得エラー: {str(e)}'
        }), 500

@company_bp.route('/code/<company_code>', methods=['GET'])
def get_company_by_code(company_code):
    """企業コードで企業を検索"""
    try:
        result = company_service.get_company_by_code(company_code)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'企業検索エラー: {str(e)}'
        }), 500

@company_bp.route('/<int:company_id>/statistics', methods=['GET'])
def get_company_statistics(company_id):
    """企業の統計情報を取得"""
    try:
        result = company_service.get_company_statistics(company_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'統計情報取得エラー: {str(e)}'
        }), 500

# LINEアカウント関連のAPI

@company_bp.route('/<int:company_id>/line-account', methods=['GET'])
def get_company_line_account(company_id):
    """企業のLINEアカウント情報を取得"""
    try:
        result = line_service.get_line_account(company_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'LINEアカウント取得エラー: {str(e)}'
        }), 500

@company_bp.route('/<int:company_id>/line-account', methods=['PUT'])
def update_company_line_account(company_id):
    """企業のLINEアカウント情報を更新"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '更新データが提供されていません'
            }), 400
        
        result = line_service.update_line_account(company_id, data)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'LINEアカウント情報の更新が完了しました'
            }), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'LINEアカウント更新エラー: {str(e)}'
        }), 500

@company_bp.route('/<int:company_id>/line-account/disable', methods=['POST'])
def disable_company_line_account(company_id):
    """企業のLINEアカウントを無効化"""
    try:
        result = line_service.disable_line_account(company_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'LINEアカウントの無効化が完了しました'
            }), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'LINEアカウント無効化エラー: {str(e)}'
        }), 500

@company_bp.route('/<int:company_id>/line-account/enable', methods=['POST'])
def enable_company_line_account(company_id):
    """企業のLINEアカウントを有効化"""
    try:
        result = line_service.enable_line_account(company_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'LINEアカウントの有効化が完了しました'
            }), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'LINEアカウント有効化エラー: {str(e)}'
        }), 500

@company_bp.route('/<int:company_id>/line-account/message', methods=['POST'])
def send_company_line_message(company_id):
    """企業のLINEアカウントからメッセージを送信"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'メッセージデータが提供されていません'
            }), 400
        
        result = line_service.send_line_message(company_id, data['message'])
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'メッセージの送信が完了しました'
            }), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'メッセージ送信エラー: {str(e)}'
        }), 500

@company_bp.route('/<int:company_id>/line-account/statistics', methods=['GET'])
def get_company_line_statistics(company_id):
    """企業のLINEアカウント統計情報を取得"""
    try:
        result = line_service.get_line_statistics(company_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'LINE統計情報取得エラー: {str(e)}'
        }), 500

@company_bp.route('/<int:company_id>/line-account/webhook', methods=['POST'])
def setup_company_webhook(company_id):
    """企業のLINEアカウントのWebhookを設定"""
    try:
        data = request.get_json()
        
        if not data or 'webhook_url' not in data:
            return jsonify({
                'success': False,
                'error': 'Webhook URLが提供されていません'
            }), 400
        
        result = line_service.setup_webhook(company_id, data['webhook_url'])
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Webhook設定が完了しました'
            }), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Webhook設定エラー: {str(e)}'
        }), 500

# エラーハンドラー

@company_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'リソースが見つかりません'
    }), 404

@company_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '内部サーバーエラーが発生しました'
    }), 500 