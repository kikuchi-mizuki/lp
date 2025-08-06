#!/usr/bin/env python3
"""
Stripe決済用ルート
企業の決済管理APIエンドポイント
"""

from flask import Blueprint, request, jsonify
from lp.services.stripe_payment_service import stripe_payment_service
from lp.services.company_service import CompanyService
import json

stripe_payment_bp = Blueprint('stripe_payment', __name__, url_prefix='/api/v1/stripe')

# インスタンスを作成
company_service = CompanyService()

@stripe_payment_bp.route('/companies/<int:company_id>/create-customer', methods=['POST'])
def create_company_customer(company_id):
    """企業用のStripe顧客を作成"""
    try:
        # 企業情報を取得
        company = company_service.get_company(company_id)
        if not company:
            return jsonify({
                'success': False,
                'error': '企業が見つかりません'
            }), 404
        
        data = request.get_json()
        email = data.get('email', '')
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'メールアドレスが指定されていません'
            }), 400
        
        # Stripe顧客を作成
        result = stripe_payment_service.create_company_customer(
            company_id, 
            company['company_name'], 
            email
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

@stripe_payment_bp.route('/companies/<int:company_id>/create-subscription', methods=['POST'])
def create_subscription(company_id):
    """企業用のサブスクリプションを作成"""
    try:
        data = request.get_json()
        price_id = data.get('price_id', '')
        trial_days = data.get('trial_days', 14)
        
        if not price_id:
            return jsonify({
                'success': False,
                'error': '価格IDが指定されていません'
            }), 400
        
        # サブスクリプションを作成
        result = stripe_payment_service.create_subscription(
            company_id, price_id, trial_days
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

@stripe_payment_bp.route('/companies/<int:company_id>/cancel-subscription', methods=['POST'])
def cancel_subscription(company_id):
    """企業のサブスクリプションを解約"""
    try:
        result = stripe_payment_service.cancel_subscription(company_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stripe_payment_bp.route('/companies/<int:company_id>/payment-status', methods=['GET'])
def get_payment_status(company_id):
    """企業の決済状況を取得"""
    try:
        result = stripe_payment_service.get_payment_status(company_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stripe_payment_bp.route('/payments', methods=['GET'])
def get_all_payments():
    """全企業の決済情報を取得"""
    try:
        result = stripe_payment_service.get_all_payments()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stripe_payment_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Stripe Webhookを処理"""
    try:
        payload = request.get_data()
        signature = request.headers.get('Stripe-Signature', '')
        
        if not signature:
            return jsonify({
                'success': False,
                'error': 'Stripe-Signatureヘッダーが見つかりません'
            }), 400
        
        # Webhookを処理
        result = stripe_payment_service.process_webhook(payload, signature)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stripe_payment_bp.route('/test-payment/<int:company_id>', methods=['POST'])
def test_payment(company_id):
    """テスト用決済処理"""
    try:
        data = request.get_json()
        payment_type = data.get('type', 'success')  # success, failed
        
        # 企業情報を取得
        company = company_service.get_company(company_id)
        if not company:
            return jsonify({
                'success': False,
                'error': '企業が見つかりません'
            }), 404
        
        # テスト通知を送信
        if payment_type == 'success':
            message = f'テスト: 支払いが完了しました。金額: ¥2,980'
            notification_type = 'payment_completion'
        else:
            message = f'テスト: 支払いに失敗しました。'
            notification_type = 'payment_failure'
        
        from lp.services.line_api_service import line_api_service
        result = line_api_service.send_notification_to_company(
            company_id, notification_type, message
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': f'テスト決済通知が送信されました: {company["company_name"]}',
                'details': result
            }), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stripe_payment_bp.route('/health', methods=['GET'])
def health_check():
    """Stripe決済API ヘルスチェック"""
    return jsonify({
        'success': True,
        'message': 'Stripe決済API サービスが正常に動作しています',
        'timestamp': '2024-07-30T12:00:00Z'
    }), 200 