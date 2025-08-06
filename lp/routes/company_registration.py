#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
企業情報登録API
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for
import os
import json
from services.company_registration_service import CompanyRegistrationService
from services.automated_ai_schedule_clone import AutomatedAIScheduleClone
from utils.db import get_db_connection

company_registration_bp = Blueprint('company_registration', __name__)

def save_company_settings_to_db(company_id, company_name, line_channel_id, line_access_token, 
                               line_channel_secret, railway_project_id=None, railway_project_url=None, 
                               webhook_url=None):
    """企業の設定情報をcompany_line_accountsテーブルに保存"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 環境変数の設定情報
        environment_variables = {
            "PORT": "3000",
            "COMPANY_ID": str(company_id),
            "COMPANY_NAME": company_name,
            "LINE_CHANNEL_ID": line_channel_id,
            "LINE_CHANNEL_ACCESS_TOKEN": line_access_token,
            "LINE_CHANNEL_SECRET": line_channel_secret,
            "FLASK_SECRET_KEY": "your_flask_secret_key_here",
            "TIMEZONE": "Asia/Tokyo",
            "DEFAULT_EVENT_DURATION": "60"
        }
        
        # 設定サマリー
        settings_summary = f"""
企業ID: {company_id}
企業名: {company_name}
LINEチャネルID: {line_channel_id}
RailwayプロジェクトID: {railway_project_id or '未設定'}
Webhook URL: {webhook_url or '未設定'}

環境変数設定:
- PORT=3000
- COMPANY_ID={company_id}
- COMPANY_NAME={company_name}
- LINE_CHANNEL_ID={line_channel_id}
- LINE_CHANNEL_ACCESS_TOKEN={line_access_token[:10]}...
- LINE_CHANNEL_SECRET={line_channel_secret[:10]}...
- FLASK_SECRET_KEY=your_flask_secret_key_here
- TIMEZONE=Asia/Tokyo
        """.strip()
        
        # 既存のレコードを確認
        c.execute('''
            SELECT id FROM company_line_accounts 
            WHERE company_id = %s AND line_channel_id = %s
        ''', (company_id, line_channel_id))
        
        existing_record = c.fetchone()
        
        if existing_record:
            # 既存レコードを更新
            c.execute('''
                UPDATE company_line_accounts 
                SET line_channel_access_token = %s,
                    line_channel_secret = %s,
                    railway_project_id = %s,
                    railway_project_url = %s,
                    webhook_url = %s,
                    environment_variables = %s,
                    settings_summary = %s,
                    deployment_status = 'completed',
                    updated_at = CURRENT_TIMESTAMP
                WHERE company_id = %s AND line_channel_id = %s
            ''', (
                line_access_token,
                line_channel_secret,
                railway_project_id,
                railway_project_url,
                webhook_url,
                json.dumps(environment_variables),
                settings_summary,
                company_id,
                line_channel_id
            ))
            print(f"✅ 企業設定を更新しました: 企業ID {company_id}")
        else:
            # 新規レコードを作成
            c.execute('''
                INSERT INTO company_line_accounts (
                    company_id, line_channel_id, line_channel_access_token, line_channel_secret,
                    railway_project_id, railway_project_url, webhook_url,
                    environment_variables, settings_summary, deployment_status, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'completed', 'active')
            ''', (
                company_id,
                line_channel_id,
                line_access_token,
                line_channel_secret,
                railway_project_id,
                railway_project_url,
                webhook_url,
                json.dumps(environment_variables),
                settings_summary
            ))
            print(f"✅ 企業設定を保存しました: 企業ID {company_id}")
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'company_id': company_id,
            'railway_project_id': railway_project_id,
            'webhook_url': webhook_url,
            'environment_variables': environment_variables
        }
        
    except Exception as e:
        print(f"❌ 企業設定保存エラー: {e}")
        return {'success': False, 'error': str(e)}

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
                # company_line_accountsテーブルに設定情報を保存
                save_result = save_company_settings_to_db(
                    company_id=result['company_id'],
                    company_name=company_name,
                    line_channel_id=line_channel_id,
                    line_access_token=line_access_token,
                    line_channel_secret=line_channel_secret,
                    railway_project_id=result.get('project_id'),
                    railway_project_url=result.get('project_url'),
                    webhook_url=result.get('webhook_url')
                )
                
                if save_result['success']:
                    print(f"✅ 企業設定をデータベースに保存完了: 企業ID {result['company_id']}")
                else:
                    print(f"⚠️ 企業設定の保存に失敗: {save_result['error']}")
                
                return jsonify({
                    'success': True,
                    'message': 'AI予定秘書の複製が完了しました！',
                    'company_id': result['company_id'],
                    'deployment_url': result.get('deployment_url', ''),
                    'webhook_url': result.get('webhook_url', ''),
                    'project_url': result.get('project_url', ''),
                    'settings_saved': save_result['success']
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
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT 
                c.company_name, 
                c.company_code, 
                cla.webhook_url, 
                cla.line_channel_id,
                cla.railway_project_id,
                cla.railway_project_url,
                cla.deployment_status,
                cla.environment_variables,
                cla.settings_summary,
                cla.updated_at
            FROM companies c
            LEFT JOIN company_line_accounts cla ON c.id = cla.company_id
            WHERE c.id = %s
        ''', (company_id,))
        
        result = c.fetchone()
        conn.close()
        
        if result:
            (company_name, company_code, webhook_url, line_channel_id, 
             railway_project_id, railway_project_url, deployment_status, 
             environment_variables, settings_summary, updated_at) = result
            
            # 環境変数をJSONから復元
            env_vars = {}
            if environment_variables:
                try:
                    env_vars = json.loads(environment_variables)
                except:
                    env_vars = {}
            
            return jsonify({
                'company_name': company_name,
                'company_code': company_code,
                'webhook_url': webhook_url,
                'line_channel_id': line_channel_id,
                'railway_project_id': railway_project_id,
                'railway_project_url': railway_project_url,
                'deployment_status': deployment_status,
                'environment_variables': env_vars,
                'settings_summary': settings_summary,
                'updated_at': updated_at.isoformat() if updated_at else None,
                'status': 'registered'
            })
        else:
            return jsonify({'error': '企業が見つかりません'}), 404
            
    except Exception as e:
        return jsonify({'error': f'エラーが発生しました: {str(e)}'}), 500

@company_registration_bp.route('/company/settings/list')
def list_company_settings():
    """全企業の設定情報を一覧表示"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT 
                cla.company_id,
                c.company_name,
                cla.line_channel_id,
                cla.railway_project_id,
                cla.webhook_url,
                cla.deployment_status,
                cla.updated_at
            FROM company_line_accounts cla
            JOIN companies c ON cla.company_id = c.id
            WHERE cla.status = 'active'
            ORDER BY cla.updated_at DESC
        ''')
        
        records = c.fetchall()
        conn.close()
        
        companies = []
        for record in records:
            company_id, company_name, line_channel_id, railway_project_id, webhook_url, deployment_status, updated_at = record
            companies.append({
                'company_id': company_id,
                'company_name': company_name,
                'line_channel_id': line_channel_id,
                'railway_project_id': railway_project_id,
                'webhook_url': webhook_url,
                'deployment_status': deployment_status,
                'updated_at': updated_at.isoformat() if updated_at else None
            })
        
        return jsonify({
            'success': True,
            'count': len(companies),
            'companies': companies
        })
        
    except Exception as e:
        return jsonify({'error': f'エラーが発生しました: {str(e)}'}), 500 