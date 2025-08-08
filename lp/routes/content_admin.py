#!/usr/bin/env python3
"""
コンテンツ管理用APIエンドポイント
スプレッドシート連携コンテンツの管理機能
"""

from flask import Blueprint, request, jsonify
from services.spreadsheet_content_service import spreadsheet_content_service
import os

content_admin_bp = Blueprint('content_admin', __name__)

@content_admin_bp.route('/api/v1/content/refresh', methods=['POST'])
def refresh_content_cache():
    """コンテンツキャッシュを強制更新"""
    try:
        result = spreadsheet_content_service.refresh_cache()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_admin_bp.route('/api/v1/content/list', methods=['GET'])
def list_available_contents():
    """利用可能なコンテンツ一覧を取得"""
    try:
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        result = spreadsheet_content_service.get_available_contents(force_refresh=force_refresh)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_admin_bp.route('/api/v1/content/<content_id>', methods=['GET'])
def get_content_info(content_id):
    """特定のコンテンツ情報を取得"""
    try:
        content = spreadsheet_content_service.get_content_by_id(content_id)
        if content:
            return jsonify({
                'success': True,
                'content': content
            })
        else:
            return jsonify({
                'success': False,
                'error': f'コンテンツID「{content_id}」が見つかりません'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_admin_bp.route('/api/v1/content/add', methods=['POST'])
def add_new_content():
    """新しいコンテンツをスプレッドシートに追加"""
    try:
        data = request.get_json()
        
        # 必須フィールドのチェック
        required_fields = ['id', 'name', 'description', 'url', 'price']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'必須フィールド「{field}」が不足しています'
                }), 400
        
        # コンテンツを追加
        result = spreadsheet_content_service.add_content_to_spreadsheet(data)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_admin_bp.route('/api/v1/content/<content_id>/status', methods=['PUT'])
def update_content_status(content_id):
    """コンテンツのステータスを更新"""
    try:
        data = request.get_json()
        status = data.get('status')
        
        if not status:
            return jsonify({
                'success': False,
                'error': 'ステータスが指定されていません'
            }), 400
        
        if status not in ['active', 'inactive', 'maintenance']:
            return jsonify({
                'success': False,
                'error': '無効なステータスです。active, inactive, maintenanceのいずれかを指定してください'
            }), 400
        
        result = spreadsheet_content_service.update_content_status(content_id, status)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_admin_bp.route('/api/v1/content/health', methods=['GET'])
def check_content_service_health():
    """コンテンツサービスの健全性チェック"""
    try:
        # スプレッドシート接続テスト
        result = spreadsheet_content_service.get_available_contents(force_refresh=True)
        
        health_status = {
            'success': True,
            'spreadsheet_connection': result['success'],
            'contents_count': len(result.get('contents', {})),
            'cache_status': result.get('cached', False),
            'fallback_mode': result.get('fallback', False)
        }
        
        return jsonify(health_status)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_admin_bp.route('/api/v1/content/sync', methods=['POST'])
def sync_content_with_database():
    """スプレッドシートのコンテンツ情報をデータベースと同期"""
    try:
        from services.content_management_service import content_management_service
        
        # スプレッドシートから最新情報を取得
        contents_result = spreadsheet_content_service.get_available_contents(force_refresh=True)
        
        if not contents_result['success']:
            return jsonify({
                'success': False,
                'error': 'スプレッドシートからの情報取得に失敗しました'
            }), 500
        
        # データベースのcompany_contentsテーブルを更新
        from utils.db import get_db_connection
        conn = get_db_connection()
        c = conn.cursor()
        
        sync_results = []
        for content_id, content_info in contents_result['contents'].items():
            try:
                # 既存レコードをチェック
                c.execute('''
                    SELECT id FROM company_contents 
                    WHERE content_type = %s
                ''', (content_id,))
                
                existing = c.fetchone()
                
                if existing:
                    # 既存レコードを更新
                    c.execute('''
                        UPDATE company_contents 
                        SET content_name = %s, content_description = %s, 
                            status = %s, updated_at = NOW()
                        WHERE content_type = %s
                    ''', (
                        content_info['name'],
                        content_info['description'],
                        content_info['status'],
                        content_id
                    ))
                    sync_results.append({
                        'content_id': content_id,
                        'action': 'updated',
                        'status': 'success'
                    })
                else:
                    # 新規レコードを追加
                    c.execute('''
                        INSERT INTO company_contents 
                        (content_type, content_name, content_description, status, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, NOW(), NOW())
                    ''', (
                        content_id,
                        content_info['name'],
                        content_info['description'],
                        content_info['status']
                    ))
                    sync_results.append({
                        'content_id': content_id,
                        'action': 'created',
                        'status': 'success'
                    })
                    
            except Exception as e:
                sync_results.append({
                    'content_id': content_id,
                    'action': 'failed',
                    'status': 'error',
                    'error': str(e)
                })
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'データベースとの同期が完了しました',
            'sync_results': sync_results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
