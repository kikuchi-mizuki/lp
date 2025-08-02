#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
企業情報登録API
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for
import os
from services.company_registration_service import CompanyRegistrationService
from services.automated_ai_schedule_clone import AutomatedAIScheduleClone

company_registration_bp = Blueprint('company_registration', __name__)

@company_registration_bp.route('/company/register', methods=['GET', 'POST'])
def register_company():
    if request.method == 'POST':
        try:
            # フォームデータを取得
            company_name = request.form.get('company_name')
            line_channel_id = request.form.get('line_channel_id', '')
            line_access_token = request.form.get('line_access_token', '')
            line_channel_secret = request.form.get('line_channel_secret', '')
            
            if not company_name:
                return jsonify({'error': '企業名は必須です'}), 400
            
            # 完全自動化スクリプトを実行
            print(f"🚀 AI予定秘書の完全自動複製を開始: {company_name}")
            
            cloner = AutomatedAIScheduleClone()
            result = cloner.create_ai_schedule_clone(
                company_name, line_channel_id, line_access_token, line_channel_secret
            )
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': 'AI予定秘書の複製が完了しました！',
                    'company_id': result['company_id'],
                    'deployment_url': result['deployment_url'],
                    'webhook_url': result['webhook_url']
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'複製に失敗しました: {result["error"]}'
                }), 500
                
        except Exception as e:
            return jsonify({'error': f'エラーが発生しました: {str(e)}'}), 500
    
    return render_template('company_registration.html')

@company_registration_bp.route('/company/register/status/<int:company_id>')
def registration_status(company_id):
    """登録状況を確認"""
    try:
        from utils.db import get_db_connection
        
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT c.company_name, c.company_code, cla.webhook_url, cla.line_channel_id
            FROM companies c
            LEFT JOIN company_line_accounts cla ON c.id = cla.company_id
            WHERE c.id = %s
        ''', (company_id,))
        
        result = c.fetchone()
        conn.close()
        
        if result:
            company_name, company_code, webhook_url, line_channel_id = result
            return jsonify({
                'company_name': company_name,
                'company_code': company_code,
                'webhook_url': webhook_url,
                'line_channel_id': line_channel_id,
                'status': 'registered'
            })
        else:
            return jsonify({'error': '企業が見つかりません'}), 404
            
    except Exception as e:
        return jsonify({'error': f'エラーが発生しました: {str(e)}'}), 500 