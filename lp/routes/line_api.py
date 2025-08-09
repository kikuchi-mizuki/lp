#!/usr/bin/env python3
"""
LINE API用ルート
企業のLINEアカウント管理APIエンドポイント
"""

from flask import Blueprint, request, jsonify
from services.line_api_service import line_api_service
from services.company_service import CompanyService
from utils.db import get_db_connection
from services.line_service import send_company_welcome_message

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

# --- LIFF連携: 決済直後にメールとLINE userIdで企業を紐付けし、自動案内を送信 ---
@line_api_bp.route('/link-company-user', methods=['POST'])
def link_company_user():
    """LIFFから送られた email と line_user_id を使って企業レコードを紐付け、案内メッセージを自動送信。

    Request JSON:
    {
      "email": "example@company.com",
      "line_user_id": "Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }
    """
    try:
        data = request.get_json() or {}
        email = (data.get('email') or '').strip().lower()
        line_user_id = (data.get('line_user_id') or '').strip()

        if not email or not line_user_id:
            return jsonify({
                'success': False,
                'error': 'email と line_user_id は必須です'
            }), 400

        conn = get_db_connection()
        c = conn.cursor()

        # 該当企業を取得
        c.execute('SELECT id, company_name, email, line_user_id FROM companies WHERE email = %s', (email,))
        company = c.fetchone()
        if not company:
            conn.close()
            return jsonify({'success': False, 'error': '企業が見つかりません'}), 404

        company_id, company_name, stored_email, stored_line_user_id = company

        # すでに同じIDが設定済みなら何もしない（Idempotent）
        if stored_line_user_id == line_user_id:
            conn.close()
            # 案内は既送かもしれないが、重複送信は避ける
            return jsonify({'success': True, 'message': '既に紐付け済みです'})

        # 他のユーザーIDが入っている場合でも上書き（重複登録防止のため最新を採用）
        c.execute('UPDATE companies SET line_user_id = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s', (line_user_id, company_id))
        conn.commit()
        conn.close()

        # 紐付け後に自動案内を送信
        try:
            sent = send_company_welcome_message(line_user_id, company_name, stored_email)
        except Exception:
            sent = False

        return jsonify({
            'success': True,
            'company_id': company_id,
            'message': '紐付けが完了しました',
            'push_sent': bool(sent)
        })

    except Exception as e:
        try:
            conn.close()
        except Exception:
            pass
        return jsonify({'success': False, 'error': str(e)}), 500