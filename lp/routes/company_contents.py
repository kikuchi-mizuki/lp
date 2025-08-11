#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
企業別コンテンツ管理API
"""

from flask import Blueprint, request, jsonify
import json

company_contents_bp = Blueprint('company_contents', __name__, url_prefix='/api/v1/company-contents')

@company_contents_bp.route('/companies/<int:company_id>/create', methods=['POST'])
def create_company_content(company_id):
    """企業用のコンテンツを作成"""
    try:
        data = request.get_json() or {}
        content_name = data.get('content_name', '')
        content_type = data.get('content_type', 'line')
        
        # データベースにコンテンツを追加
        from utils.db import get_db_connection
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO company_contents (company_id, content_name, content_type, status, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        ''', (company_id, content_name, content_type, 'active'))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'コンテンツを作成しました'
        }), 201
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'コンテンツ作成エラー: {str(e)}'
        }), 500

@company_contents_bp.route('/companies/<int:company_id>', methods=['GET'])
def get_company_contents(company_id):
    """企業のコンテンツ一覧を取得"""
    try:
        from utils.db import get_db_connection
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT id, content_name, content_type, status, created_at
            FROM company_contents
            WHERE company_id = %s
            ORDER BY created_at DESC
        ''', (company_id,))
        
        contents = []
        for row in c.fetchall():
            contents.append({
                'id': row[0],
                'content_name': row[1],
                'content_type': row[2],
                'status': row[3],
                'created_at': row[4].isoformat() if row[4] else None
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'contents': contents,
            'total_count': len(contents)
        }), 200
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'コンテンツ取得エラー: {str(e)}'
        }), 500

@company_contents_bp.route('/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    return jsonify({
        'success': True,
        'message': 'Company Contents API is healthy'
    }), 200 