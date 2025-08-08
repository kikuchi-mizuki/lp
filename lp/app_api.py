import os
import logging
from flask import request, jsonify
from utils.db import get_db_connection

logger = logging.getLogger(__name__)

def check_company_restriction_api():
    """企業制限チェックAPI"""
    try:
        data = request.get_json()
        line_channel_id = data.get('line_channel_id')
        content_type = data.get('content_type')
        
        if not line_channel_id or not content_type:
            return jsonify({
                'success': False,
                'error': 'line_channel_id と content_type は必須です'
            }), 400
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業とLINEアカウントの関連を確認
        c.execute('''
            SELECT c.id, c.company_name, c.status,
                   cms.subscription_status, cc.content_status
            FROM companies c
            JOIN company_line_accounts cla ON c.id = cla.company_id
            LEFT JOIN company_monthly_subscriptions cms ON c.id = cms.company_id
            LEFT JOIN company_contents cc ON c.id = cc.company_id AND cc.content_type = %s
            WHERE cla.line_channel_id = %s
        ''', (content_type, line_channel_id))
        
        result = c.fetchone()
        conn.close()
        
        if not result:
            return jsonify({
                'success': False,
                'error': '企業が見つかりません'
            }), 404
        
        company_id, company_name, company_status, subscription_status, content_status = result
        
        # 制限チェック
        is_restricted = (
            company_status != 'active' or
            subscription_status != 'active' or
            content_status != 'active'
        )
        
        return jsonify({
            'success': True,
            'company_id': company_id,
            'company_name': company_name,
            'is_restricted': is_restricted,
            'restriction_reasons': {
                'company_status': company_status,
                'subscription_status': subscription_status,
                'content_status': content_status
            }
        })
        
    except Exception as e:
        logger.error(f"❌ 企業制限チェックAPIエラー: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def get_company_info_api(line_channel_id):
    """企業情報取得API"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業情報を取得
        c.execute('''
            SELECT c.id, c.company_name, c.email, c.status, c.created_at,
                   cms.stripe_subscription_id, cms.subscription_status,
                   cla.line_user_id, cla.line_display_name
            FROM companies c
            JOIN company_line_accounts cla ON c.id = cla.company_id
            LEFT JOIN company_monthly_subscriptions cms ON c.id = cms.company_id
            WHERE cla.line_channel_id = %s
        ''', (line_channel_id,))
        
        result = c.fetchone()
        conn.close()
        
        if not result:
            return jsonify({
                'success': False,
                'error': '企業が見つかりません'
            }), 404
        
        company_id, company_name, email, status, created_at, \
        stripe_subscription_id, subscription_status, line_user_id, line_display_name = result
        
        return jsonify({
            'success': True,
            'company': {
                'id': company_id,
                'company_name': company_name,
                'email': email,
                'status': status,
                'created_at': created_at.isoformat() if created_at else None,
                'stripe_subscription_id': stripe_subscription_id,
                'subscription_status': subscription_status,
                'line_user_id': line_user_id,
                'line_display_name': line_display_name
            }
        })
        
    except Exception as e:
        logger.error(f"❌ 企業情報取得APIエラー: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def cancel_company_content_api(company_id, content_type):
    """企業コンテンツ解約API"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # コンテンツの状態を更新
        c.execute('''
            UPDATE company_contents 
            SET content_status = 'cancelled', updated_at = CURRENT_TIMESTAMP
            WHERE company_id = %s AND content_type = %s
        ''', (company_id, content_type))
        
        # 解約履歴を記録
        c.execute('''
            INSERT INTO company_cancellations (
                company_id, content_type, cancellation_reason
            ) VALUES (%s, %s, %s)
        ''', (company_id, content_type, 'API経由での解約'))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ 企業コンテンツ解約完了: {company_id}, {content_type}")
        
        return jsonify({
            'success': True,
            'message': f'{content_type}の解約が完了しました'
        })
        
    except Exception as e:
        logger.error(f"❌ 企業コンテンツ解約APIエラー: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
